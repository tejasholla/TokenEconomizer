# TokenEconomizer Roadmap

The plan, the parked ideas, and what has shipped. Update when work lands or an idea is parked;
the README and the plugin's own docs stay the source of truth for behaviour.

## Shipped

- **Claude Code (2.1.300 → 2.1.310).** Verified end-to-end: micro-skills inject at
  `SessionStart`, the loop guard nudges failing edits, facts form over sessions, tool pruning
  leaves unused tools out of `.claude/settings.local.json`.
- **Codex (0.153.1 → 0.164.0).** Installed via `codex plugin marketplace add` and `codex plugin
  add`. Tool pruning removes Codex capability packages from `.codex/config.toml`. The hooks
  show in the detailed transcript (Codex's headless `codex exec` prints no hook messages).
- **Copilot CLI (1.0.83 → 1.0.102).** Whole MCP servers are removed from
  `.github/copilot/settings.local.json`. BYOK providers route the side call through the user's
  own model.
- **Pi (1.2.0 → 1.3.0).** A TypeScript extension (`plugin/pi/tokeneconomizer.ts`) hooks the
  same three events the other hosts expose.
- **Cursor Agent (3.24.9, experimental).** Records hook events locally because Cursor's
  transcript format and per-session token usage are not a supported public interface.
- **opencode (1.19.5 and 2.2.0, experimental).** A plugin file works on both versions (the
  `server` entry on 1.x, the `setup` entry on 2.x); session exports are folded at end of turn.
- **Antigravity / agy (1.4.7, experimental, 2026-11-04).** The host adapter translates the
  Antigravity hook protocol into the Claude Code envelope the rest of the runtime speaks.
  Verified against a synthetic payload and transcript (`tests/test_agy.py`); end-to-end on a
  live session is the next step.

## In progress

- **End-to-end live verification of Antigravity.** The adapter, the transcript reader and the
  side call are all in place; they pass the offline tests, but no real `agy` session has been
  folded yet. Owner: open.
- **The paper's five combinations.** Claude Code + Sonnet 5 / Opus 4.8, Codex + GPT-5.6 Terra /
  Sol, Copilot CLI + Sonnet 5 — all reproduced in `experiments/`. Newer model releases are
  tracked on the [project page](https://tokeneconomizer.github.io).
- **Web-Bench and the security-auditing benchmarks.** Live in `experiments/` and reproduced on
  commit. Owner: open for benchmark-version updates.

## Parked

- **opencode 2.x TUI notices.** The "still stuck" line goes to the server's stderr, not a
  toast. No path the plugin can take changes that.
- **Cursor tool pruning.** Cursor's published hooks provide session / prompt / tool-result /
  completion events but no deny surface the plugin can write to. Skipped until that changes.
- **Codex `codex exec` headless hook messages.** Codex prints nothing on stdout from
  `codex exec`; the plugin cannot surface its line in that mode. Owner: upstream Codex.
- **The benchmark guard for live use.** The harness has it (the answer key, the `/etc/hosts`
  block, the dropped web tools); the plugin does not. A real session has no answer key.
- **Pi 0.99.x as a first-class install.** The path load works; the documented install command
  is `pi install` from 1.2.0.

## Compatibility surface

These names are part of the contract with anyone who has learned from sessions; renaming them
strands what users have learned:

- On-disk state files: `injection.json`, `untool.json`, `envelope.json`, the event kinds.
- Settings keys (current names, with the earlier ones as aliases): `microskills`,
  `toolprune`, `loopguard`, `inject`, `untool`, `spiral`, ... (full list in
  [`plugin/config.py`](plugin/config.py)).
- The plugin CLI: `te <command>` from a terminal, the per-agent slash-command prefixes
  (`/tokeneconomizer:`, `$tokeneconomizer:`, `/te`).

A new agent can land without breaking any of this. It registers itself in
`tokeneconomizer/plugin/hosts.py`, brings its own manifest under `plugin/.<agent>-plugin/`,
adds a hook file under `plugin/hooks/`, and writes a transcript reader under
`tokeneconomizer/trace/`. The CLI picks it up through `hosts.HOSTS` and the dispatcher's
`--host` argparse choice.
