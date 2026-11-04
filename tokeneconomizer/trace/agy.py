"""Antigravity (agy): a session stored as JSONL rows of a conversation transcript.

A conversation lives in ``~/.gemini/antigravity-cli/brain/<conversationId>/`` and its
transcript is ``.system_generated/logs/transcript_full.jsonl``. Every row carries a
``step_index`` and a ``type``:

  * ``USER_INPUT``      -- what the person asked (the content wraps it in ``<USER_REQUEST>``);
  * ``PLANNER_RESPONSE`` -- a model step: its ``tool_calls`` (the calls the model asked for),
    its ``thinking``, and its usage (``input_tokens``, ``cache_read_tokens``,
    ``output_tokens``);
  * ``GENERIC``         -- the result of the tool calls of the step before it.

Usage is per model step, so the ledger's fields map directly: ``input_tokens`` is the fresh
input, ``cache_read_tokens`` the cached re-read, ``output_tokens`` the output.
``agy_session_to_claude`` writes the transcript as the Claude Code envelope the other
readers already handle, so no mechanism needs an Antigravity branch.
"""
import json
import os
import re

from .jsonl import records

# The user request is wrapped in this tag by the CLI.
_USER_REQUEST = re.compile(r"<USER_REQUEST>\s*(.*?)\s*</USER_REQUEST>", re.S)
# Everything else the CLI adds around it (local time, settings changes).
_USER_SETTINGS = re.compile(r"<USER_SETTINGS_CHANGE>.*?</USER_SETTINGS_CHANGE>", re.S)
_USER_METADATA = re.compile(r"<ADDITIONAL_METADATA>.*?</ADDITIONAL_METADATA>", re.S)


def _agy_entries(path):
    return list(records(path))


def _agy_user_text(content):
    """What the person actually asked, without the CLI's wrapper tags."""
    if not isinstance(content, str):
        return ""
    text = content
    for tag in (_USER_SETTINGS, _USER_METADATA):
        text = tag.sub("", text)
    m = _USER_REQUEST.search(text)
    return (m.group(1) if m else text).strip()


def agy_session_to_claude(path, out_path):
    """Write an Antigravity transcript as Claude Code transcript lines.

    A model step's ``tool_calls`` become tool uses, and the ``GENERIC`` row that follows
    them becomes their results. Returns the number of tool calls written, or None when the
    file is missing.
    """
    if not path or not os.path.exists(path):
        return None
    n = 0
    entries = _agy_entries(path)
    pending: list[dict] = []
    with open(out_path, "w", encoding="utf-8") as out:
        for e in entries:
            kind = e.get("type")
            if kind == "USER_INPUT":
                text = _agy_user_text(e.get("content"))
                if text:
                    out.write(json.dumps({"type": "user", "message": {
                        "role": "user", "content": text}}) + "\n")
            elif kind == "PLANNER_RESPONSE":
                blocks = []
                for i, call in enumerate(e.get("tool_calls") or []):
                    if not isinstance(call, dict):
                        continue
                    blocks.append({"type": "tool_use",
                                   "id": f"agy-{e.get('step_index', i)}-{i}",
                                   "name": call.get("name") or "",
                                   "input": call.get("args") or {}})
                    n += 1
                content = e.get("content")
                if isinstance(content, str) and content.strip():
                    blocks.append({"type": "text", "text": content})
                thinking = e.get("thinking")
                if isinstance(thinking, str) and thinking.strip():
                    blocks.insert(0, {"type": "text", "text": thinking})
                msg = {"id": f"agy-{e.get('step_index', 0)}", "role": "assistant",
                       "content": blocks, "model": e.get("model")}
                usage = agy_usage(e)
                if usage:
                    msg["usage"] = usage
                out.write(json.dumps({"type": "assistant", "message": msg}) + "\n")
                pending = blocks
            elif kind == "GENERIC" and pending:
                results = []
                content = e.get("content")
                text = content if isinstance(content, str) else ""
                for block in pending:
                    if block.get("type") != "tool_use":
                        continue
                    results.append({"type": "tool_result",
                                    "tool_use_id": block.get("id"),
                                    "content": text,
                                    "is_error": False})
                if results:
                    out.write(json.dumps({"type": "user", "message": {
                        "role": "user", "content": results}}) + "\n")
                pending = []
    return n


def agy_usage(row):
    """The ledger's usage fields for one model step, or None when the row has none."""
    if not isinstance(row, dict):
        return None
    fresh = row.get("input_tokens")
    if not isinstance(fresh, (int, float)):
        return None
    return {
        "input_tokens": int(fresh or 0),
        "cache_read_input_tokens": int(row.get("cache_read_tokens") or 0),
        "cache_creation_input_tokens": 0,
        "output_tokens": int(row.get("output_tokens") or 0),
    }


def agy_session_usage(path):
    """Token breakdown of an Antigravity transcript, in the ledger's fields.

    The rows are per model step, so the totals are the sums over them. ``model`` is the model
    the session ran on, when the transcript names one.
    """
    if not path or not os.path.exists(path):
        return None
    totals = None
    model = ""
    for e in _agy_entries(path):
        if e.get("type") != "PLANNER_RESPONSE":
            continue
        usage = agy_usage(e)
        if not usage:
            continue
        totals = totals or dict.fromkeys(usage, 0)
        for k, v in usage.items():
            totals[k] += v
        model = model or (e.get("model") or "")
    if totals is None:
        return None
    if model:
        totals["model"] = model
    return totals


def agy_prompt_count(path):
    """How many prompts the transcript records."""
    if not path or not os.path.exists(path):
        return None
    n = 0
    for e in _agy_entries(path):
        if e.get("type") == "USER_INPUT":
            n += 1
    return n or None
