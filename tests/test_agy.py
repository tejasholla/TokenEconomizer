"""Antigravity (agy): the host adapter, its transcript reader, and the hook bridge.

Offline and synthetic. The payload and the transcript shape are the ones Antigravity sends
(verified against agy 1.4.7): the payload names the conversation, the model, the workspace and
the tool call but NOT the event, and the transcript is JSONL rows of a conversation.
"""
import json
import os
import subprocess

import pytest

from tokeneconomizer import trace
from tokeneconomizer.plugin import hosts


AGY_PAYLOAD = {
    "artifactDirectoryPath": "/home/u/.gemini/antigravity-cli/brain/conv-1",
    "conversationId": "conv-1",
    "lastUserInput": "read the file",
    "modelName": "claude-opus-4-6-thinking",
    "stepIdx": 2,
    "toolCall": {"args": {"Path": "/tmp/f.txt"}, "name": "read_file"},
    "transcriptPath": "/home/u/.gemini/antigravity-cli/brain/conv-1/.system_generated/logs/transcript_full.jsonl",
    "workspacePaths": ["/tmp/work"],
}


def _write_transcript(path, rows):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row) + "\n")


AGY_ROWS = [
    {"step_index": 0, "source": "USER_EXPLICIT", "type": "USER_INPUT", "status": "DONE",
     "created_at": "2026-11-03T09:57:33Z",
     "content": "<USER_REQUEST>\nread the file\n</USER_REQUEST>\n"
                "<ADDITIONAL_METADATA>\nThe current local time is: x\n</ADDITIONAL_METADATA>"},
    {"step_index": 1, "source": "MODEL", "type": "PLANNER_RESPONSE", "status": "DONE",
     "created_at": "2026-11-03T09:57:37Z", "input_tokens": 21591, "cache_read_tokens": 4161,
     "output_tokens": 87, "thinking": "the user wants the file",
     "tool_calls": [{"name": "read_file", "args": {"Path": "/tmp/f.txt"}}]},
    {"step_index": 2, "source": "MODEL", "type": "GENERIC", "status": "DONE",
     "created_at": "2026-11-03T09:57:41Z", "content": "1: hello"},
    {"step_index": 3, "source": "MODEL", "type": "PLANNER_RESPONSE", "status": "DONE",
     "created_at": "2026-11-03T09:57:41Z", "input_tokens": 643, "cache_read_tokens": 25273,
     "output_tokens": 4, "content": "hello"},
]


# ---- the host adapter ------------------------------------------------------------------
def test_the_agy_payload_is_translated_into_the_common_envelope():
    host = hosts.Antigravity()
    p = host.prepare(dict(AGY_PAYLOAD), {"TE_AGY_EVENT": "PostToolUse"})
    assert p["hook_event_name"] == "PostToolUse"
    assert p["session_id"] == "conv-1"
    assert p["transcript_path"] == AGY_PAYLOAD["transcriptPath"]
    assert p["cwd"] == "/tmp/work"
    assert p["tool_name"] == "read_file"
    assert p["tool_input"] == {"Path": "/tmp/f.txt"}
    assert p["tool_use_id"] == "agy-2"


def test_the_session_is_the_conversation_and_the_turn_is_the_step():
    host = hosts.Antigravity()
    p = host.prepare(dict(AGY_PAYLOAD), {"TE_AGY_EVENT": "PostToolUse"})
    assert host.session_id(p) == "conv-1"
    assert host.turn_key(p) == "conv-1"


def test_antigravity_has_no_prompt_event_so_the_model_call_stands_in_for_it():
    host = hosts.Antigravity()
    p = host.prepare(dict(AGY_PAYLOAD), {"TE_AGY_EVENT": "PreInvocation"})
    assert p["hook_event_name"] == "UserPromptSubmit"
    assert p["prompt_id"] == "conv-1"


def test_the_session_start_is_a_start_and_names_its_source():
    host = hosts.Antigravity()
    p = host.prepare(dict(AGY_PAYLOAD), {"TE_AGY_EVENT": "SessionStart"})
    assert p["hook_event_name"] == "SessionStart"
    assert p["source"] == "startup"


def test_a_failed_tool_carries_its_error_as_the_result():
    host = hosts.Antigravity()
    payload = dict(AGY_PAYLOAD, error="read_file: no such file")
    p = host.prepare(payload, {"TE_AGY_EVENT": "PostToolUse"})
    name, args, text, code = host.tool_call(p)
    assert name == "read_file"
    assert "no such file" in text


def test_the_hook_bridge_answers_the_agy_event_it_is_told():
    """The dispatcher is told which event fired, because agy's payload does not name it."""
    payload = dict(AGY_PAYLOAD)
    out = subprocess.run(
        ["python3", "-m", "tokeneconomizer.plugin.hook", "--host", "agy"],
        input=json.dumps(payload), capture_output=True, text=True,
        env={**os.environ, "TE_AGY_EVENT": "SessionStart", "TE_DISABLE": "1"},
    )
    # TE_DISABLE makes the dispatcher a no-op that still answers with valid JSON.
    assert out.returncode == 0
    assert out.stdout.strip() in ("{}", "")


# ---- the transcript reader ---------------------------------------------------------------
def test_the_transcript_is_read_as_the_common_envelope(tmp_path):
    path = str(tmp_path / "transcript_full.jsonl")
    _write_transcript(path, AGY_ROWS)
    out = str(tmp_path / "trace.jsonl")
    n = trace.agy_session_to_claude(path, out)
    assert n == 1
    rows = [json.loads(line) for line in open(out, encoding="utf-8")]
    kinds = [r["type"] for r in rows]
    assert kinds == ["user", "assistant", "user", "assistant"]
    # the user's request is unwrapped from the CLI's tags
    assert rows[0]["message"]["content"] == "read the file"
    # the assistant's first block is thinking, second is tool_use
    use = rows[1]["message"]["content"][1]
    assert use["type"] == "tool_use" and use["name"] == "read_file"
    result = rows[2]["message"]["content"][0]
    assert result["type"] == "tool_result" and "hello" in result["content"]
    # the final assistant response
    assert rows[3]["type"] == "assistant"
    assert rows[3]["message"]["content"][0]["text"] == "hello"


def test_the_usage_is_the_sum_of_the_model_steps(tmp_path):
    path = str(tmp_path / "transcript_full.jsonl")
    _write_transcript(path, AGY_ROWS)
    usage = trace.agy_session_usage(path)
    assert usage["input_tokens"] == 21591 + 643
    assert usage["cache_read_input_tokens"] == 4161 + 25273
    assert usage["output_tokens"] == 87 + 4


def test_the_prompt_count_is_the_number_of_user_turns(tmp_path):
    path = str(tmp_path / "transcript_full.jsonl")
    _write_transcript(path, AGY_ROWS)
    assert trace.agy_prompt_count(path) == 1


def test_a_missing_transcript_is_not_an_error(tmp_path):
    missing = str(tmp_path / "nope.jsonl")
    assert trace.agy_session_to_claude(missing, str(tmp_path / "out.jsonl")) is None
    assert trace.agy_session_usage(missing) is None
    assert trace.agy_prompt_count(missing) is None


def test_the_host_reads_its_own_transcript(tmp_path):
    path = str(tmp_path / "transcript_full.jsonl")
    _write_transcript(path, AGY_ROWS)
    host = hosts.Antigravity()
    assert host.session_usage(path)["input_tokens"] == 21591 + 643
    assert host.prompt_count(path) == 1
    trace_path = host.mechanism_trace(path, str(tmp_path))
    assert trace_path and os.path.exists(trace_path)
