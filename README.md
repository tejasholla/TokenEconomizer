# TokenEconomizer: Experience-Driven Black-Box Cost Control for Coding Agents

<p align="center">
  Aaron J. Li<sup>1</sup>,
  Weijia Xu<sup>2</sup>,
  Chandan Singh<sup>2</sup>,
  Zixiao Chen<sup>3</sup>,
  Jeevana Priya Inala<sup>2</sup>,
  Charlotte Siska<sup>3</sup>,
  <br>
  Acar Tamersoy<sup>3</sup>,
  Bin Yu<sup>1</sup>,
  Ion Stoica<sup>1</sup>,
  Michel Galley<sup>2</sup>,
  Jianfeng Gao<sup>2</sup>
</p>
<p align="center">
  <sup>1</sup>UC Berkeley &nbsp; <sup>2</sup>Microsoft Research &nbsp; <sup>3</sup>Microsoft Security
</p>

<p align="center">
  <a href="https://arxiv.org/abs/2610.22732"><img src="https://img.shields.io/badge/arXiv-2610.22732-b31b1b.svg" alt="arXiv"></a>
  <a href="https://tokeneconomizer.github.io"><img src="https://img.shields.io/badge/project-page-2f6fb0.svg" alt="Project page"></a>
  <a href="https://x.com/aaron_jli/status/2114797313613053952"><img src="https://img.shields.io/badge/X-post-000000.svg?logo=x&logoColor=white" alt="X post"></a>
  <img src="https://img.shields.io/badge/python-3.10%2B-3776ab.svg" alt="Python 3.10+">
  <img src="https://img.shields.io/badge/license-Apache%202.0-blue.svg" alt="Apache 2.0 license">
</p>

<p align="center">
  Our measurement on SWE-Bench tasks: <b>18.4–30.9% lower mean cost</b> across five agent–model
  combinations, cheaper in <b>all 30</b> repository × combination cells, and Pass@1 up in
  <b>4 of 5</b>. <a href="#results">Results</a>
</p>

<p align="center">
  <picture>
    <source media="(prefers-reduced-motion: reduce)" srcset="docs/assets/teaser.png">
    <img src="docs/assets/teaser.gif" width="100%" alt="An animation that opens on a title card: TokenEconomizer, experience-driven black-box cost control for coding agents, with its three mechanisms (micro-skills, tool pruning, failure-loop intervention), the agents it works with (Claude Code, Codex, GitHub Copilot CLI, Pi) and the UC Berkeley and Microsoft logos. Then a schematic of six sessions in one repository, each a bar of what it cost: the work itself plus three kinds of waste, namely re-learning the repo, tools never used, and getting stuck in loops. Each of the first three sessions teaches TokenEconomizer one thing, in order: 1 micro-skills remember how the repo works (run tests with python -m pytest), 2 tool pruning skips tools never used here (Read and Edit kept, Notebook and Browser left out), and 3 failure-loop intervention spots loops and steps in (the same error three times meets a nudge to try another way). In the session after each lesson that waste shrinks, so the bars step down below a dashed line marking the cost without TokenEconomizer. It ends on results measured on SWE-Bench tasks: 18.4–30.9% lower mean cost across five agent–model combinations, cheaper than default in 30 of 30 repository × combination cells, and Pass@1 up in 4 of 5; per combination, cost 23.6% lower and Pass@1 +1.3 for Claude Code with Sonnet 5, 30.9% and −1.0 with Opus 4.8, 24.7% and +0.9 for Codex with GPT-5.6 Terra, 26.1% and +1.6 with GPT-5.6 Sol, and 18.4% and +2.6 for Copilot CLI with Sonnet 5.">
  </picture>
</p>

**What is this, in one paragraph.** Coding agents are expensive: every turn pays again for the
agent's instructions, every loaded tool's definition, and the conversation so far. If you use
the same agent on the same repository day after day, much of that cost repeats — the same
facts rediscovered, the same unused tools sent, the same kinds of failing loops. TokenEconomizer
sits beside the agent, watches its sessions, and applies what it learned to the next ones in
the same repository. It is **not** a wrapper, a model change, or a different agent; it is a
plugin that reads finished sessions and changes what later sessions pay for.

**Who it's for.** You run the same agent (Claude Code, Codex, the GitHub Copilot CLI, Pi,
opencode, Cursor, or Antigravity) in the same repository often enough that the cost adds up,
and you want that cost to fall without changing the agent itself. The plugin needs no API key
of its own, never handles credentials, and never reads your source code beyond the commands
and paths it needs to learn from.

**What it does, in one paragraph.** Three mechanisms, each learned per repository and applied
to the next session: micro-skills inject short, repository-specific facts at session start
(commands that work here, environment quirks, where generated files live); tool pruning leaves
tools that go unused out of the next session's tool list, through the agent's own settings;
the loop guard watches a turn in progress and, when it shows signs of failing in a loop, asks
a judge model whether to nudge the agent toward a different approach. None of these change
what the agent does when it is working; they only stop the agent from repeating work it has
already done badly.

**The four ideas behind it.** (1) The agent already reads `additionalContext` and respects
its own settings, so facts inject at session start and tools are removed through the settings
file — no new tool the agent has to learn. (2) Cost is counted as it is billed: most tokens
in a session are cached re-reads, so the cost numbers include cache pricing and the plugin's
own model calls. (3) Task success is protected: facts only form from repeated evidence, tools
are only removed after going unused, the guard leaves a turn alone while it is making progress.
(4) Every action is reversible: a fact later sessions contradict is dropped, removed tools can
be given back, the guard only redirects and tells you — stopping a turn is your call.

**What it does not do.** It does not call a model on every turn (only when micro-skills is on,
on the proposer's schedule, or when the loop guard's judge is asked); it does not edit the
agent's code, weights, or system prompt; it does not change which tools the agent can use
without your settings file; it does not stop a turn itself; it does not read your secrets,
your source code beyond the commands and paths it needs, or your shell history; it does not
phone home or upload anything.

TokenEconomizer is a plugin for **Claude Code**, **Codex**, the **GitHub Copilot CLI** and **Pi**,
with experimental support for **opencode**, **Cursor Agent** and **Antigravity (agy)**. Each italic
letter above is a setting, shown with its default ([Settings](#settings)), and each mechanism can
be turned on or off. The plugin announces each action in one line, and if any part of it fails,
your session carries on as if it were not installed. Its model calls (the fact proposer, and the
judge with the redirect it writes) run through your own agent, on the same plan or login, and
their cost is included in its reports. What it learns stays on your machine, in
`~/.tokeneconomizer`.

- **Micro-skills: remember how the repository works.** Sessions keep rediscovering the same
  facts: a build step that must run first, the spelling of a command that works here
  (`python -m pytest` where `pytest` is missing, `npx tsc` where `tsc` is), an environment
  variable a command needs, where generated files live. Micro-skills learns such facts, in any
  language, from two sources: failures that repeat across sessions, and a model that reviews the
  recent sessions every *k* sessions (*k* = 3) and proposes facts. A fact is stated at the start
  of each session once three sessions have confirmed it, and dropped when later sessions
  contradict it.
- **Tool pruning: stop loading tools that go unused.** Every loaded tool's definition is sent with
  every request. A tool that goes unused over *p* prompts spread across at least *m* sessions, or
  over *s* sessions of any length (*p* = 10, *m* = 2, *s* = 5), is left out of the next sessions
  through the agent's own settings. One command brings it back.
- **Failure-loop intervention (the loop guard): step in when a turn is stuck.** When a turn (the
  agent's work on one prompt) keeps hitting the same failures, a judge model checks whether it is
  stuck. If the judge is at least *c* sure (*c* = 0.7), the agent gets a redirect (a short note,
  added to its context, to try another approach), at most *r* times per turn (*r* = 1). If the
  turn is still stuck after that, TokenEconomizer tells you how to stop it; it never stops a turn
  itself.

## The three mechanisms in detail

Each mechanism reads from the same place (a finished session's transcript) and writes back
into the next session (its context, its settings, or its turn in progress). They can be turned
on or off independently, and they only talk to the agent through the agent's own protocol, so
the agent does not know any of them are running.

### 1. Micro-skills — short, repository-specific facts at session start

**The problem.** Every new session, the model has to rediscover the same things about your
repository: which command runs the tests (`pytest` is missing here, `python -m pytest` is
what works), which build step must come first, which environment variable the build needs,
where generated files live. That rediscovery costs tokens on every prompt, and it costs
attention when the model spends a turn on it.

**How it learns.** Two layers:

- **EnvFacts (always on when micro-skills is on).** Reads every finished session for failures
  that look like environmental problems — "the host can't reach this URL", "this binary is
  missing", "this file lives somewhere else here". Each candidate fact needs three independent
  sessions to confirm it; one contradictory session drops it. No model call, no extra cost.
- **The proposer (when `microskills=on`, on every `microskills_propose_every` sessions, default 3).**
  Reads the same transcripts, distills the commands and edits into a small digest, and asks a
  model (through your own agent's CLI, so on your plan or login) to propose one to three
  additional facts. Existing facts and confirmed environmental facts are sent as context, so
  the proposer doesn't repeat them.

**When it triggers.** At session start, the plugin renders the facts (most-confirmed first,
under `microskills_max_facts` items and `microskills_max_tokens` tokens) and injects them as
`additionalContext` on Claude Code / Codex / Copilot / Pi, or through the agent's own injection
channel on the others. The model sees them as part of the system prompt; you don't have to do
anything.

**What it produces.** A short paragraph of plain-text facts, like:

```
Repository facts (3 of 4 confirmed):
- Tests run with `python -m pytest`; `pytest` is not on PATH.
- The build needs `CI=1` set, otherwise lint fails on first run.
- Generated CSS lives in `static/dist/`; do not edit it by hand.
```

**Settings that tune it.** `microskills` (off / envfacts / on, default `off`), `microskills_max_facts`
(default 4), `microskills_max_tokens` (default 150), `microskills_propose_every` (default 3
sessions between proposer runs). The proposer charges the session ledger: it appears in the
session's token total.

**What can go wrong.** The proposer may invent facts. The plugin lints every proposed fact
(`lint_ok`, in `tokeneconomizer/microskills/envfacts.py`) and refuses ones that look like noise
(a markdown bullet, a file path with no verb, a sentence without a subject); facts that make
it through still need three sessions to confirm them. `envfacts` alone makes no model call, so
it is the safer choice if you only want the cheap layer.

### 2. Tool pruning — leave tools that go unused out of the next session

**The problem.** Every loaded tool's definition is sent with every request. In a Python
repository the model never asks for the `Notebook` tool, in a TypeScript repository it never
asks for `Browser`. Those definitions still cost tokens every prompt — across a session that
might be thousands of tokens of definitions the model has no reason to read.

**How it learns.** Watches the loaded tool catalog at session start (`refresh-catalog` writes
the list of tools your agent loaded, with no model call), then watches which tools the model
actually calls over time. A tool is proposed for removal when **all** of:

- it has been loaded in at least `toolprune_min_sessions` sessions (default 2), or has been
  loaded in `toolprune_sessions` sessions of any length (default 5);
- across `toolprune_evidence` (default 10) prompts in those sessions, it was never called.

Tools you actually need (AskUserQuestion, plan-mode, sub-agents, the web) are protected by
name pattern (`toolprune_protect`) and never proposed. A tool the plugin proposed for a
repository is removed from the proposal list the next time you use it.

**When it triggers.** After the evidence forms a deny list, the plugin waits until the
repository's sessions have been idle for `toolprune_quiet_minutes` (default 60 minutes), so
that no conversation resumed with a warm prompt cache loses it. Once that window has passed,
the deny list is written to the agent's own settings file (`mode=auto`, the default), and the
next session starts with the new tool list. `mode=propose` only shows the proposal; nothing
changes until you run `toolprune apply`.

**What it produces.** An entry in the agent's settings file:

| Agent | File | What is removed |
|---|---|---|
| Claude Code | `.claude/settings.local.json` | one tool's name |
| Codex | `.codex/config.toml` | a capability package (a group of tools) |
| Copilot CLI | `.github/copilot/settings.local.json` | one whole MCP server |
| Pi | nothing | Pi loads only four tools; the deny list never forms |
| Cursor | nothing | no public deny surface |
| opencode | nothing | no public deny surface |
| Antigravity | nothing | no public deny surface |

The plugin adds only its own entries; it never touches deny rules you wrote. Settings files
it creates are kept out of git (`.git/info/exclude`).

**Settings that tune it.** `toolprune` (off / propose / auto, default `auto`), `toolprune_evidence`
(default 10 prompts), `toolprune_min_sessions` (default 2), `toolprune_sessions` (default 5),
`toolprune_quiet_minutes` (default 60), `toolprune_protect` (a comma-separated list of tool
name patterns). `toolprune restore` gives a removed tool back and never removes it again;
`toolprune apply` makes `propose` mode write the proposal as `auto` would.

**What can go wrong.** On Claude Code the line that says what was left out shows only in the
detailed transcript (**Ctrl+O**), so check with `toolprune show` if you're not sure. On a
repository whose `.codex/config.toml` is committed, the plugin refuses to edit it and the
list stays a proposal until you decide. If a tool gets removed and you actually need it back,
`toolprune restore` is one command.

### 3. The loop guard — nudge a turn that is failing in a loop

**The problem.** A turn (the agent's work on one prompt) sometimes loops: the same edit,
the same test, the same failure, in the same shape, for many calls. The model is not
exploring; it is stuck. Letting it run wastes tokens and time; aborting it throws away the
useful work in the turn.

**How it learns.** Watches every turn end. A turn that ended green (the agent stopped on
its own, was not stopped by the guard, and no verification after its last edit failed) feeds
a per-repository *envelope*: how long a turn usually runs, how often it edits a file, how
many distinct files it touches, how often it produces a failing tool result. The guard waits
until the envelope has at least `loopguard.envelope_min_samples` (=5) ended-green turns in
the repository before it acts. Until then, the guard only steps in at the hard backstop.

**When it triggers.** Two ways, both after the envelope is learned:

- **The judge's verdict.** A turn that shows signs of trouble (repeated failures, dense
  errors, scattered edits) goes to a judge model (through your own agent's CLI, so on your
  plan or login). The judge gets the recent tool calls and outputs and answers with how sure
  it is that the turn is stuck. If the verdict is at least `loopguard.judge_confidence`
  (=0.7) sure, the agent gets a redirect — a short note added to the next tool result, asking
  it to try a different approach. At most `loopguard_nudges` (=1) redirect per turn; if the
  turn is still stuck after that, the guard only notifies.
- **The hard backstop.** A turn that runs past `loopguard.backstop_mult` (=2.5) times its
  usual length while churning the same edits through the same failures is redirected without
  the judge. This is the only way the guard acts before the envelope is learned.

**What it produces.** A redirect (a short note attached to the next tool result, asking the
agent to try a different approach) and, if the turn is still stuck, one line that ends with
how to stop it:

```
TokenEconomizer: this turn still looks stuck after a redirect (judge-stuck@0.82, 46 tool
calls). Press Esc to interrupt it.
```

The plugin never stops a turn itself. Stopping is your call.

**Settings that tune it.** `loopguard` (off / nudge / stop, default `nudge`; `stop` is read
as `nudge` with a warning), `loopguard_aggr` (conservative / default / aggressive, the
threshold preset), `loopguard_nudges` (default 1), `loopguard_aggr` shifts the bar for "is
this turn stuck", `loopguard.<name>` (a single threshold pinned over the preset and the
envelope), `loopguard.envelope_min_samples` (default 5 ended-green turns before the guard
acts).

**What can go wrong.** The judge is a model: it can be wrong. A turn the guard thinks is
stuck may have been one short hop from succeeding; a turn the guard thinks is fine may be
spinning its wheels. The redirects are short and additive — they do not overwrite the agent's
plan, only add a hint. The redirect's cost is charged to the session ledger; the judge and
the writer are two model calls, both through your own agent's CLI.

## What "supporting an agent" means here

Each agent in the list above exposes its own way of letting an outside program watch what happens
in a session — a hook protocol. Most of the agents we support use Claude Code's protocol (a JSON
payload on stdin, one event per call, an `additionalContext` field for things the model should
read). That makes the runtime simple: the dispatcher reads the payload, runs the right mechanism
for the event, and prints the result on stdout. **Antigravity is the only agent we support that
uses a different protocol.** Its hooks have a different shape and a different name for almost
every concept, so the plugin translates between them and the Claude Code envelope the rest of the
runtime already speaks. That translation is one host adapter
([`tokeneconomizer/plugin/hosts.py`](tokeneconomizer/plugin/hosts.py)) and one transcript reader
([`tokeneconomizer/trace/agy.py`](tokeneconomizer/trace/agy.py)); the three mechanisms do not know
which agent they are running in.

## Results

The paper ran five agent–model combinations on the same 277 SWE-Bench tasks from six repositories.
Each task ran as its own session, and each repository's tasks ran in order, starting with nothing
learned. Costs include every model call TokenEconomizer made. Within each repository and
combination, cost fell by 5–40%. The savings held on Web-Bench (16–21% lower) and on two
security-auditing benchmarks where every task is in a new repository (6–20% lower). The
[project page](https://tokeneconomizer.github.io) has interactive charts, per-repository numbers
and nine annotated runs, and [`experiments/`](experiments/README.md) reruns the SWE-Bench and
Web-Bench experiments.

## How it works

<p align="center"><img src="docs/assets/framework_overview.png" width="100%" alt="TokenEconomizer: the plugin keeps what it knows about a repository and applies micro-skills, tool pruning and failure-loop intervention to your unchanged coding agent; each finished session's log updates all three"></p>

Coding agents are built to finish tasks, not to keep them cheap. Every turn pays again for the
agent's instructions, every loaded tool, and the conversation so far. Developers use the same
agent on the same repository again and again, so much of that cost repeats: the same facts
rediscovered, the same unused tools sent, the same kinds of failing loops. TokenEconomizer leaves
the agent's model, weights and code alone and learns across a repository's sessions instead of
treating each one on its own, so whatever the plugin spends is paid back over the sessions that
follow. Four principles guide the mechanisms:

- **Work through what the agent already reads.** Facts enter the context at session start, and
  tools are removed through the agent's own settings, so nothing depends on the agent learning a
  new tool.
- **Count cost as it is billed.** Most tokens in a session are cached re-reads, so cost is
  computed with cache pricing, and it includes the plugin's own model calls.
- **Protect task success.** Facts form only from repeated evidence, tools are removed only after
  going unused, and the loop guard leaves alone a turn that is still making progress.
- **Keep every action reversible.** A fact that later sessions contradict is dropped, removed
  tools can be given back, and the loop guard only redirects and tells you: stopping a turn is
  your call.

## Quick start

You need one of these agents, signed in any way it supports, and Python 3.10 or newer on
`PATH`. The plugin needs no API key of its own and never handles credentials, so any plan or
login works.

### Install

Run these commands in the folder where you want to keep the clone. Claude Code, Codex, the
Copilot CLI, opencode and Antigravity run the plugin from the clone, so leave it in place. Then
start the agent in one of your repositories.

**Claude Code**

```sh
git clone https://github.com/microsoft/TokenEconomizer.git
claude plugin marketplace add "$PWD/TokenEconomizer"
claude plugin install tokeneconomizer@tokeneconomizer
```

Start `claude`, trust the folder (**Yes, I trust this folder**), and run
`/tokeneconomizer:status`, allowing its script if asked. Once per machine, and again after Claude
Code updates, run `/tokeneconomizer:toolprune refresh-catalog`.

**Codex**

```sh
git clone https://github.com/microsoft/TokenEconomizer.git
codex plugin marketplace add "$PWD/TokenEconomizer"
codex plugin add tokeneconomizer@tokeneconomizer
```

Start `codex`, choose **Trust and continue** for the folder, then at **Hooks need review**
choose **Trust all and continue**. The hooks take effect from your next Codex session, so quit
(`/exit`), start `codex` again, and check with `$tokeneconomizer:status`.

**Copilot CLI**

```sh
git clone https://github.com/microsoft/TokenEconomizer.git
copilot plugin marketplace add "$PWD/TokenEconomizer"
copilot plugin install tokeneconomizer@tokeneconomizer
```

Start `copilot`, choose **Yes, and remember this folder for future sessions**, and run
`/tokeneconomizer:status`, choosing **Yes** to run its script. Once per machine, and again after
Copilot updates, run `/tokeneconomizer:toolprune refresh-catalog`.

**Pi**

```sh
pi install git:github.com/microsoft/TokenEconomizer
```

Start `pi` and run `/te status`.

**Cursor Agent** (experimental)

```sh
python scripts/build_plugin.py --out ~/.cursor/plugins/local/
```

Reload Cursor, confirm `tokeneconomizer` appears in Customize, then send a prompt in a repository.
Check its state from a terminal with `~/.tokeneconomizer/bin/te --host cursor status`. Cursor's
published hooks provide session, prompt, tool-result and completion events. Its transcript format
and per-session token usage are not a supported public interface, so the adapter records needed
hook events locally and reports session cost as unavailable. Cursor support is macOS and Linux
only: on Windows, Cursor runs hook commands through PowerShell, and this plugin's launcher is a
POSIX shell script.

**opencode** (experimental)

```sh
git clone https://github.com/microsoft/TokenEconomizer.git
mkdir -p ~/.config/opencode/plugins
ln -s "$PWD/TokenEconomizer/plugin/opencode/tokeneconomizer.ts" ~/.config/opencode/plugins/
```

Start `opencode` and send a prompt, then check in the repository with
`~/.tokeneconomizer/bin/te --host opencode status`. opencode has no plugin commands, so the
plugin's commands run from a terminal.

**Antigravity (agy)** (experimental)

```sh
git clone https://github.com/microsoft/TokenEconomizer.git
mkdir -p ~/.gemini/antigravity-cli/plugins
ln -s "$PWD/TokenEconomizer/plugin" ~/.gemini/antigravity-cli/plugins/tokeneconomizer
```

Start `agy` in a repository, send a prompt, and check its state from a terminal with
`~/.tokeneconomizer/bin/te --host agy status`. Antigravity has no plugin slash commands, so the
plugin's commands run from a terminal — the same `te` CLI the other agents share, only with
`--host agy` so the dispatcher knows which adapter to use. What the link gives Antigravity:

- `plugin/hooks.json` (at the plugin root) is the dispatcher source of truth. Each handler has a
  matching `TE_AGY_EVENT=…` environment variable so the dispatcher knows which event fired,
  because Antigravity's hook payload does **not** name the event itself.
- `plugin/.antigravity-plugin/plugin.json` is the manifest Antigravity reads to discover the
  plugin.

Two details that often surprise first-time users:

1. **Antigravity fires `PreInvocation` before every model call, not before every user message.**
   One user prompt that calls the model several times in a row sends several `PreInvocation`
   events. The host adapter flags this with `prompt_repeats_in_turn = True`, so the loop guard
   keeps the same turn open across them instead of closing and reopening it on every call.
2. **The conversation id is the session id.** Antigravity has no per-message id, and its sessions
   are conversations, not user-attributed runs. The plugin's session folder under
   `~/.tokeneconomizer/repos/.../agy/` is keyed by `conversationId`, which is stable across the
   turns of one conversation.

The transcript lives at
`~/.gemini/antigravity-cli/brain/<conversationId>/.system_generated/logs/transcript_full.jsonl`.
The reader ([`tokeneconomizer/trace/agy.py`](tokeneconomizer/trace/agy.py)) unwraps the CLI's
`<USER_REQUEST>` and `<ADDITIONAL_METADATA>` tags around the user's text and folds the model
steps' tool calls and results into the same Claude Code envelope every other host produces, so the
mechanisms never need an Antigravity-specific branch.

If the install worked, the status command prints a short status block. `refresh-catalog`
records every tool a session loads (without a model call), so that tool pruning can consider all
of them. Keep the marketplace path absolute, as above: the Copilot CLI reads a relative path such
as `./TokenEconomizer` as the name of a GitHub repository.

To update:

| Agent | Update |
|---|---|
| Claude Code, Copilot CLI, opencode, Antigravity | `git pull` in the clone |
| Codex | `git pull` in the clone, then the `codex plugin add` line again |
| Pi | `pi update --extensions` |

**[`plugin/README.md`](plugin/README.md)** walks through each agent in more detail, including
uninstalling, using Copilot with your own model key, and troubleshooting.

### Supported versions

| Agent | Supported | Older versions |
|---|---|---|
| Claude Code | 2.1.300 to 2.1.310 | not supported |
| Codex | 0.153.1 to 0.164.0 | not supported |
| Copilot CLI | 1.0.83 to 1.0.102 | not supported |
| Pi | 1.2.0 to 1.3.0 | 0.99.x: load the extension by path (below) |
| Cursor Agent (experimental) | 3.24.9, macOS and Linux (below) | not tested |
| opencode (experimental) | 1.19.5 and 2.2.0 | not tested |
| Antigravity (agy) (experimental) | 1.4.7 | earlier 1.4.x: not verified; the event names must match what `plugin/hooks.json` declares (`SessionStart`, `PreInvocation`, `PreToolUse`, `PostToolUse`, `Stop`) |

The commands above were tested on the oldest and newest version in each range; newer versions
have not been tested yet.

- **Codex before 0.141.0** does not run plugin hooks at all.
- **Pi 0.99.x**: instead of `pi install`, clone the repository and start each session with
  `pi --extension /path/to/TokenEconomizer/plugin/pi/tokeneconomizer.ts`, using your clone's
  full path; `git pull` in the clone updates it.
- **opencode** support is experimental: it was tested on 1.19.5 and 2.2.0 only, and not in the
  2.x terminal UI.
- **Cursor Agent** support is experimental. Cursor 3.24.9 loaded the local plugin, but hook delivery
  from a live Agent session has not yet been verified.
- **Antigravity** support is experimental and was developed against agy 1.4.7. The host adapter
  depends on the event names listed in `plugin/hooks.json` and the JSONL shape under
  `~/.gemini/antigravity-cli/brain/<conversationId>/.system_generated/logs/transcript_full.jsonl`;
  any change there means a fresh review, not just a version bump.

### Everyday commands

Work as usual; the plugin needs nothing from you. To see or change what it does, use its
commands. They have the same names on every agent; only the way you type them differs:

| Agent | Type a command as |
|---|---|
| Claude Code, Copilot CLI | `/tokeneconomizer:<command>` |
| Codex | `$tokeneconomizer:<command>` |
| Pi | `/te <command>` |
| opencode | from a terminal: `~/.tokeneconomizer/bin/te --host opencode <command>` |
| Cursor Agent | from a terminal: `~/.tokeneconomizer/bin/te --host cursor <command>` |
| Antigravity (agy) | from a terminal: `~/.tokeneconomizer/bin/te --host agy <command>` |
| a terminal, in the repository | `~/.tokeneconomizer/bin/te <command>` |

| Command | What it does |
|---|---|
| `status` | what it learned and did here, and what your sessions cost |
| `microskills` | the facts it injects, and those still forming |
| `toolprune` | the tools it left out, and the evidence (not on Pi, opencode or agy) |
| `toolprune restore` | give them back; they will not be removed again |
| `config` | every setting in effect |
| `config set microskills=on` | turn a mechanism on (or `=off`) in this repository; add `--global` for every repository |

Inside an agent, a command costs one model turn; from a terminal it is free. The other commands
(`repos`, `doctor`, `config unset`, ...) and each agent's permission prompts are listed under
[Commands](plugin/README.md#commands).

## Day-to-day usage

You install once, leave it running, and the plugin does its work between sessions. This section
walks through what a typical week looks like, the commands you actually use, and how to read
what the plugin prints.

### A typical week

- **Day 1 (just installed).** Nothing learned yet. Sessions start, the plugin reads the
  transcript when they end, and `status` shows zero facts, zero deny rules, zero redirects.
  Micro-skills is off; the loop guard has no envelope yet; tool pruning has no evidence.
  Nothing you do is changed, and nothing is added to your settings file.
- **Day 2–3.** If you have `microskills=on`, the proposer's first run happens on the second
  session. It reads the day's transcripts, proposes one to three facts, and those facts are
  injected into the next session start (they need three confirming sessions before they
  become "active"). The loop guard's envelope is filling up — every ended-green turn is
  added; the guard stays in backstop-only mode until the envelope is full.
- **Day 4–7.** Tool pruning's evidence is collecting. A tool that was loaded ten times and
  never used across at least two sessions is proposed for removal. If `toolprune=auto` and
  the repository has been idle for an hour, the deny list is written to your settings file
  and the next session starts with the new tool list. The plugin announces this at session
  start in one line.
- **Week 2+.** A few facts are confirmed and injected at every session start. A few tools
  are left out. The loop guard has an envelope and may nudge a turn that is failing in a
  loop. `status` shows numbers: how many sessions were folded, how many facts are confirmed,
  how many redirects the guard made. The plugin's overhead on a normal session is well under
  1% of the session's tokens.

### Commands you actually use

The commands below are the ones you'll come back to. The full list is in
[plugin/README.md → Commands](plugin/README.md#commands).

| When | Command | What it does |
|---|---|---|
| Want to know what the plugin has learned | `te status` (or `/tokeneconomizer:status`) | prints the running totals: facts confirmed, tools pruned, redirects made, total session cost |
| Want to know what it would prune next | `te toolprune show` | shows the proposed deny list and the evidence for each tool |
| Want to give a removed tool back | `te toolprune restore [tool ...]` | restores one tool or every tool; the restored tool is never removed again |
| Want to make `propose` mode write the list | `te toolprune apply` | applies the proposed list as `auto` would |
| Want to know what facts it injects | `te microskills` | lists the facts the next session will inject, and the candidates still forming |
| Want to know what a setting does | `te config show` | lists every setting and its value, with the source it came from |
| Want to change a setting for this repo | `te config set microskills=on` | writes a setting to `<repo>/config.json`; add `--global` to write the user's global config instead |
| Want to change a setting for one session | `TE_LOOPGUARD=off codex` | environment variables override the config file for one session |
| Want to see if the plugin is healthy | `te doctor` | checks Python version, state directory, recent error log lines, agent-specific trust |
| Want to see every repo the plugin has learned about | `te repos list` | lists every repository folder under `~/.tokeneconomizer/repos/`, with its host and settings |

### Reading the status output

A real `status` block looks like this:

```
TokenEconomizer -- myorg/myrepo (claude)
  repository   /home/me/work/myrepo, identified by its origin remote (github.com/myorg/myrepo)
  state        /home/me/.tokeneconomizer/repos/myrepo-9a4f7c12ab/claude
  config       microskills=on toolprune=auto loopguard=nudge repomap=off mode=auto shadow=False
  sessions     47 folded, 1.2M effective tokens, plugin overhead 0.6% (7.4k tokens)
  microskills  5 fact(s) injected at session start (5 active, 1 forming); proposer last ran on session 41
  toolprune    3 tool(s) removed (.claude/settings.local.json), 1 proposed
  loopguard    envelope learned (12 ended-green turns, p95 18 calls); 4 redirect(s), 0 still-stuck notice(s) over 47 turns
```

Each line tells you one thing:

- **repository / state** — which repo and where its state lives; the `state` folder is the
  place to look if you want to see what the plugin has remembered.
- **config** — the effective setting values for this repo; `mode` is `auto` (running
  normally), `interactive` (an interactive session, no judge), or `headless` (no TTY,
  notifications go to stderr). `shadow=True` would mean "compute everything, apply nothing"
  — the way to test a mechanism without trusting it.
- **sessions** — how many sessions have been folded, the total effective tokens, and the
  fraction of those tokens the plugin accounted for (its own model calls + the injected
  facts).
- **microskills** — the number of facts being injected at the next session start, and how
  many candidates are still forming. "Forming" means they have fewer than three confirming
  sessions; they will be dropped if the next sessions contradict them.
- **toolprune** — the deny list that is in force, and whether there is a new proposal waiting
  for `apply` or for `toolprune_quiet_minutes` of idle time.
- **loopguard** — the envelope's status (learned or not, how many turns, the p95 turn length),
  and the running totals of redirects and still-stuck notices.

### When to step in

The plugin is meant to be invisible until you ask it a question. The few cases where you'll
want to:

- **`toolprune restore` after a denied tool turns out to be needed.** This is the most common
  intervention. The plugin never removes a tool you have given back.
- **`config set microskills=envfacts` if the proposer's calls cost too much.** The envfacts
  layer alone learns a useful subset (the most-cited environmental facts) at no model cost.
- **`TE_DISABLE=1 <agent>` for one session** when you want the plugin completely out of the
  way (debugging the agent, running a benchmark, testing a specific change).
- **`te doctor` when something looks wrong.** It prints the recent error log lines and the
  state-directory checks; most issues are visible there.
- **A new repo, a fresh start:** `te repos migrate <path>` and `te repos merge <path>` move
  state between repositories (e.g. when the `origin` URL of a repo changes); `te repos list`
  shows what's there.

## Settings

Tool pruning and the loop guard are on by default; with these defaults, the plugin calls a model
only when a turn shows signs of looping: the judge, and the redirect it writes if it finds the
turn stuck. Micro-skills is off by default, because its proposer adds model calls and how much it
saves depends on the repository and the work you do there. Each mechanism has its own switch
(`microskills`, `toolprune`, `loopguard`) that takes `on` or `off`, and the italic letters above
are these settings:

| | Setting | Default | What it sets |
|---|---|---|---|
| *k* | `microskills_propose_every` | 3 | sessions between runs of micro-skills' fact proposer |
| *p* | `toolprune_evidence` | 10 | prompts a tool must go unused before it is left out |
| *m* | `toolprune_min_sessions` | 2 | sessions those prompts must span |
| *s* | `toolprune_sessions` | 5 | or this many sessions, of any length |
| *q* | `toolprune_quiet_minutes` | 60 | minutes your sessions here must be idle before a deny list is written |
| *e* | `loopguard.envelope_min_samples` | 5 | turns here that ended well (no failing check after the last edit) before the loop guard acts |
| *c* | `loopguard.judge_confidence` | 0.7 | how sure the judge must be that a turn is stuck |
| *r* | `loopguard_nudges` | 1 | redirects per turn before the guard only tells you |
| *b* | `loopguard.backstop_mult` | 2.5 | how many times its usual length a churning turn may run before it is redirected without the judge |

Change them with `config set`, shown here in Claude Code's form (other agents type it as in
[Everyday commands](#everyday-commands)):

```text
/tokeneconomizer:config set microskills=on                 # turn micro-skills on
/tokeneconomizer:config set microskills_propose_every=5    # k = 5: propose facts less often
/tokeneconomizer:config set toolprune_evidence=20          # p = 20: wait for twenty unused prompts
/tokeneconomizer:config set loopguard_nudges=2             # r = 2: redirect twice before telling you
```

Tool pruning counts prompts so that long sessions weigh more, and requires *m* sessions so that a
single session never decides alone. It writes the deny list only once your sessions in the
repository have been idle for *q* minutes (or, at the latest, a day after the list formed): a
conversation resumed after its tools change must write its whole history to the prompt cache again
instead of reading it, and after an idle hour that cache has expired anyway.

Besides `on` and `off`, two modes are useful: `toolprune=propose` only proposes the deny list, and
nothing changes until you run `toolprune apply`; `microskills=envfacts` learns facts only from
repeated failures, with no model calls.

To change a single session, set an environment variable when you start the agent:
`TE_DISABLE=1 claude` turns the whole plugin off, and `TE_LOOPGUARD=off codex` turns off one
mechanism (likewise `TE_MICROSKILLS` and `TE_TOOLPRUNE`). Every setting and its default are
listed under [Settings](plugin/README.md#settings); each one's environment variable is `TE_` plus
its name in capitals.

## What it does on each agent

Micro-skills and the loop guard work the same way on every agent. Each agent learns on its own:
facts, tool evidence and the loop guard's sense of a usual turn are kept per agent and
repository, while settings are shared. Tool pruning acts through each agent's own settings, so
what it can leave out differs:

| Agent | Tool pruning leaves out | Written to |
|---|---|---|
| Claude Code | single tools | `.claude/settings.local.json` |
| Codex | capability packages | `.codex/config.toml` |
| Copilot CLI | whole MCP servers | `.github/copilot/settings.local.json` |
| Pi | nothing (Pi loads only four tools) | — |
| Cursor Agent | nothing yet | — |
| opencode | nothing yet | — |
| Antigravity (agy) | nothing yet (agy has no public deny surface) | — |

Tool pruning adds only its own entries and never touches deny rules you wrote; a settings file it
creates is kept out of git (`.git/info/exclude`). On Claude Code, the session-start line that says
what it left out shows only in the detailed transcript (**Ctrl+O**), so check with
`/tokeneconomizer:toolprune`. `toolprune restore` removes the plugin's entries and nothing else,
and tools you give back are not removed again. If the plugin cannot edit a file safely (a
`.codex/config.toml` your repository commits, a settings file that is not valid JSON, a symlink
that leads out of the repository), the list stays a proposal and the session start says why;
`toolprune apply` tries again. **[`docs/PLUGIN.md`](docs/PLUGIN.md)** records how each agent's
hooks and settings were verified to behave, and **[`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md)**
how the package fits together.

### When a turn gets stuck

The loop guard first learns how long a turn in this repository usually runs: it waits until *e*
turns here have ended well, on their own and with no failing check after the last edit. After
that, a turn that shows signs of looping (the same failures repeating, or errors piling up) goes
to the judge. One case is redirected without the judge: a turn that runs past *b* times the usual
length while churning the same edits through the same failures. If a turn is still stuck after its
redirects, you see one line that ends with how to stop it:

> TokenEconomizer: this turn still looks stuck after a redirect (judge-stuck@0.82, 46 tool
> calls). Press Esc to interrupt it.

Where that line appears, and how to stop the turn, in the terminal UI and in a headless run
(`claude -p`, `codex exec`, `copilot -p`, `pi -p`, `opencode run`):

| Agent | Interactive: where it shows | How to stop | Headless: where it shows | How to stop |
|---|---|---|---|---|
| Claude Code | in Claude's reply | Esc | in the final reply | Ctrl+C |
| Codex | in the conversation | Esc, then `/stop` | not shown | Ctrl+C |
| Copilot CLI | in the conversation | Esc twice | on stdout | Ctrl+C |
| Pi | as a notification | Esc | on stderr | Ctrl+C |
| opencode | as a notification | Esc | on stderr | Ctrl+C |
| Antigravity (agy) | as a notification | Esc (agy sends `Stop` when the turn ends; in `agy --print` it answers once and exits) | on stderr | Ctrl+C |

- **Claude Code** shows a plugin's own lines only in its detailed transcript (Ctrl+O), so the
  plugin asks Claude to repeat this one in its reply; the model may word it differently or leave
  it out.
- **Codex**: Esc interrupts the turn, but a command it started keeps running until `/stop`.
  `codex exec` prints no hook messages.
- **Pi**: Ctrl+C ends a headless run, but a command it started runs on until it finishes.
- **opencode** 2.x prints the line to the opencode server's error output, not in its terminal UI.

In a headless run nobody may be watching, so a flagged turn runs until it ends or reaches the
agent's own limits; afterwards, `te status` counts the redirects and "still stuck" notices.

## Where data lives, what the plugin touches

This section is the privacy and data-handling answer: a precise list of what the plugin reads
from your environment, what it writes, and what it never touches.

### What it reads

| From | What | When |
|---|---|---|
| your shell command transcripts | the commands the agent ran, with their exit codes and short error lines | at the end of every session, on every host |
| file paths from those commands | absolute paths to the files the agent read, edited, or wrote | at session end |
| the agent's tool-catalog snapshot | the list of tools the agent loaded | once, when you run `toolprune refresh-catalog` (Claude Code and Copilot) |
| the agent's session id and your `cwd` | enough to key per-repository state | on every hook event |
| one of your agent's tool results | the most recent failure's text, when the loop guard's judge is asked | only when the guard is acting, after the envelope is learned |
| a digest of recent sessions | the commands and edits of the last *k* sessions, when the micro-skills proposer runs | only when `microskills=on`, every `microskills_propose_every` sessions |

What the plugin **does not** read: your source files (it sees paths and commands; it does not
read the file contents); your shell history; your SSH keys, tokens, keyrings, or any file in
`~/.ssh`, `~/.aws`, `~/.config/gh`, `~/.password-store`; environment variables beyond what the
hooks expose; your browser history; your email; anything in `~/.cache` other than the agent's
own transcript files.

### What it writes

| To | What | When |
|---|---|---|
| `~/.tokeneconomizer/` | everything it learns (facts, evidence, envelopes, settings) and its error log | on every session end and every hook event |
| `<repo>/.claude/settings.local.json` | the deny list, on Claude Code | when `toolprune=auto` and the evidence forms and the repo has been idle long enough |
| `<repo>/.codex/config.toml` | the deny list (a Codex capability package), on Codex | same |
| `<repo>/.github/copilot/settings.local.json` | the deny list (a whole MCP server), on the Copilot CLI | same |
| `<repo>/config.json` (TokenEconomizer's own) | the per-repository settings you changed | when you run `te config set …` |
| `~/.tokeneconomizer/config.json` | the global settings | when you run `te config set --global …` |
| `<repo>/.git/info/exclude` | one line marking the settings file the plugin writes | the first time it writes to that file |
| the agent's context | the rendered facts (`additionalContext`), the redirect | only through the agent's own protocol |
| the agent's terminal | one line per action, at session start and end | on every session |

### Files on disk

```
~/.tokeneconomizer/
├── repos/                                  # one folder per repository
│   └── <name>-<hash>/                      # state for one repo (hash of its identity)
│       ├── repo.json                       # which repo this is: path, origin remote, host
│       └── <host>/                         # per-host state (claude, codex, pi, agy, ...)
│           ├── injection.json              # the rendered micro-skills block (cached)
│           ├── mechanisms/                 # each mechanism's own state
│           │   ├── envfacts_state/         # confirmed and forming environmental facts
│           │   └── interface_state/        # the proposer's own state
│           ├── envelope.json               # the loop guard's per-repository envelope
│           ├── untool.json                 # the deny list and the evidence behind it
│           ├── events.jsonl                # the event log (one JSON line per hook call)
│           ├── ledger.jsonl                # the session ledger: token counts per call
│           ├── folded.json                 # which sessions have been folded
│           ├── fold.log                    # the fold log
│           ├── sessions/                   # the transcript traces the plugin wrote
│           │   ├── claude_trace.jsonl
│           │   ├── codex_exec_trace.jsonl
│           │   └── agy_trace.jsonl
│           └── .mechanisms.lock, …         # lock files, so two sessions never race
├── sessions/                               # per-host session traces not tied to a repo
├── bin/te                                  # the CLI launcher (a tiny shell wrapper)
├── config.json                             # your global settings
├── index.json                              # the index of known repositories
└── errors.log                              # every hook error and traceback, append-only
```

The state files are a compatibility surface: renaming one strands what you have learned. The
settings (`<repo>/config.json`, `~/.tokeneconomizer/config.json`) keep their earlier
names as aliases (`inject`, `untool`, `spiral`) so an existing config keeps working; new code
reads and writes the current names.

### Privacy commitments

- **No network calls.** The plugin never opens a socket to anywhere except the agents whose
  hooks fired the event (the hooks themselves are already in your environment). Its model
  calls run through your own agent's CLI, on your plan or login. No telemetry, no analytics,
  no remote endpoint of any kind.
- **No source code.** The plugin sees paths and commands; it never reads file contents beyond
  the error lines of a failed command (and only when it must). It does not exfiltrate your
  repository.
- **No credentials.** The plugin never handles API keys, OAuth tokens, SSH keys, or anything
  in your keyrings. Its side calls (`te judge`, `te proposer`) use your agent's existing
  authenticated CLI.
- **Everything stays local.** No cloud sync, no backup, no "send to phone". To move state
  between machines, copy `~/.tokeneconomizer/` (or the specific repo folder under `repos/`).
- **Fail open.** Any error in a hook becomes an empty output (no change) and a line in
  `errors.log`. A broken plugin never stops the agent's session.
- **Reversible.** `toolprune restore` gives every removed tool back. A fact later sessions
  contradict is dropped. The guard only redirects; you decide when to stop the turn.

## Troubleshooting

| Symptom | Cause and fix |
|---|---|
| a slash command prints an import error, or the hooks seem to do nothing | run `~/.tokeneconomizer/bin/te doctor` and read its `errors.log` lines |
| `errors.log` says "the package was not found for the plugin" | the clone the plugin was installed from moved or is gone; add it again, or use the self-contained bundle (`python3 scripts/build_plugin.py --out dist/marketplace` and install from `dist/marketplace`) |
| `TokenEconomizer needs Python >= 3.10 (this is 3.x)` | install Python 3.10+ or set `TE_PYTHON=/path/to/python3.10+` |
| the deny list leaves nothing out after many sessions | on Claude Code and the Copilot CLI, run `toolprune refresh-catalog` once on this machine and again after the agent updates |
| a Codex deny list was applied but nothing changed | Codex only honours a plugin's settings in folders it trusts; `~/.tokeneconomizer/bin/te --host codex doctor` says whether the project is trusted |
| `errors.log` has "sidecall copilot: no reply", and a session start says the plugin's model calls are paused | Copilot with a BYOK provider cannot run the plugin's side calls from the same context; micro-skills stays on `envfacts`, and the loop guard redirects only at its backstop. Once Copilot is signed in again, `config set microskills=on` (or `loopguard=on`) retries |
| `te status` shows another agent's state | add `--host claude`, `codex`, `copilot`, `pi`, `cursor`, `opencode` or `agy` |
| the plugin ran but no facts were learned | micro-skills is off by default; `config set microskills=on` (or `envfacts`) and run a few more sessions |
| the loop guard never acts | the envelope has not been learned yet; the guard waits until `loopguard.envelope_min_samples` (=5) turns here have ended green. Until then, only the backstop can step in |
| a tool the agent actually needs was removed | `te toolprune restore <tool>`; the restored tool is never removed again |
| a `TE_AGY_EVENT`-related entry in `errors.log` | Antigravity requires its hook manifest at `plugin/hooks.json`; check the symlink under `~/.gemini/antigravity-cli/plugins/tokeneconomizer` points at the `plugin/` directory (not the repo root) and restart agy |
| `~/.gemini/antigravity-cli/plugins/tokeneconomizer` is missing | re-create it: `mkdir -p ~/.gemini/antigravity-cli/plugins && ln -s /path/to/TokenEconomizer/plugin ~/.gemini/antigravity-cli/plugins/tokeneconomizer` |
| the opencode 2.x TUI doesn't show the still-stuck notice | opencode 2.x writes its plugin logs to the server's stderr, not to a toast; check `te status` afterwards |
| `claude` runs in `--dangerously-skip-permissions` and the plugin's commands need approval | run `te …` from a terminal instead — it costs no model turn and does not need approval |
| the plugin is too quiet in the TUI | on Claude Code, only the detailed transcript (Ctrl+O) shows a plugin's own lines; `/tokeneconomizer:status` (or `te status` from a terminal) is the canonical view |
| the plugin is too loud | `config set loopguard=off` (or `TE_LOOPGUARD=off` for one session); the per-mechanism switch is the right knob |
| I want to remove the plugin and start over | uninstall the plugin from your agent, then `rm -rf ~/.tokeneconomizer` (this is destructive — copy `repos/` if you want to keep what was learned) |

If `doctor` does not name the problem, the next thing to look at is `~/.tokeneconomizer/errors.log`
(the most recent lines are the most recent failures). The full per-host troubleshooting
section, including each agent's permission prompts and uninstall steps, is in
[plugin/README.md → Troubleshooting](plugin/README.md#troubleshooting).

## FAQ

**Does it change my agent's model?** No. The agent's model, weights, code and system prompt
are not touched. The plugin only reads finished sessions and writes into the next session
through the agent's own protocol (`additionalContext` for context, the agent's own settings
file for tool removal).

**Does it slow my agent down?** A typical hook call is well under 200 ms and never waits on a
model. The exception is the loop guard's judge, which is called only when a turn shows signs
of trouble; the judge runs as a detached job (`te judge`), so the hook returns immediately and
a later `PostToolUse` picks up the verdict.

**Does it cost me more in API calls?** It depends on the mechanism. Tool pruning never calls a
model. The loop guard's judge and writer are two model calls per turn it acts on, which is
uncommon. Micro-skills is the only mechanism that calls a model on a schedule
(`microskills_propose_every` sessions, default 3); on `envfacts` alone it makes no model
calls. The `status` block shows the running total so you can see what it is costing.

**Is the redirect trustworthy?** It is written by a model call (the same one that judged the
turn) through your own agent's CLI. It is short — one paragraph, at most a redirect a person
would write. It does not change the agent's plan, only adds a hint attached to the next tool
result. You can always read it in the agent's transcript.

**Can I run the plugin in shadow mode to test it first?** Yes. `te config set shadow=on` makes
the plugin compute every decision (facts, deny lists, redirects) and log them, but apply
nothing to the next session. `te status` and the per-mechanism commands show what it would
have done.

**Will it work on my private / offline model?** Yes, as long as it is exposed as an OpenAI- or
Anthropic-style endpoint and your agent's CLI can reach it. The plugin's side calls go
through your agent's CLI on your plan or login; if the agent can use the model, the plugin
can too.

**How do I uninstall?** Uninstall the plugin from your agent (the per-agent steps are in
[plugin/README.md](plugin/README.md)), then `rm -rf ~/.tokeneconomizer` (or keep
`repos/<hash>-<name>/` if you want the learned state for a future install). The plugin's
settings file (`.claude/settings.local.json`, `.codex/config.toml`,
`.github/copilot/settings.local.json`) is the agent's own file; remove the plugin's entries
with `te toolprune restore` before uninstalling, or remove them by hand.

**Why doesn't it just patch the agent's source?** That would make the savings depend on every
agent's release. The plugin keeps the agent unchanged and applies what it learns through the
agent's own protocol, so an agent update does not silently regress the savings.

**Why is it open source?** The paper, the harness, the plugin and the docs are all open so the
results can be checked and rerun. The design (per-repository learning, the three mechanisms,
the host adapters) is what the paper claims, and the only honest way to publish a claim like
that is to publish everything that backs it.

## Repository

| | |
|---|---|
| [`tokeneconomizer/microskills`](tokeneconomizer/microskills/) | Micro-skill synthesis and injection: facts learned from finished sessions |
| [`tokeneconomizer/toolprune`](tokeneconomizer/toolprune/) | Tool pruning: unused tools and Codex capability packages |
| [`tokeneconomizer/loopguard`](tokeneconomizer/loopguard/) | Failure-loop intervention: the per-call guard and its per-repository envelope |
| [`tokeneconomizer/trace`](tokeneconomizer/trace/) | Each agent's session log, read into one shape |
| [`tokeneconomizer/plugin`](tokeneconomizer/plugin/) | The runtime the hooks and the `te` command run |
| [`plugin`](plugin/) | The installable plugin: manifests, hook files, launchers, slash commands, the Pi extension, the opencode plugin, the Antigravity plugin (`plugin/hooks.json` + `plugin/.antigravity-plugin/`) |
| [`experiments`](experiments/) | The harness, launchers and task sets behind the paper's results |
| [`docs`](docs/) | `PLUGIN.md` (design, verified agent behavior) and `ARCHITECTURE.md` (how the package fits together) |
| [`tests`](tests/) | Offline tests for the package and the plugin |

The package is standard-library only. Run the tests with `python -m pytest tests` (add
`experiments/tests` for the benchmark side), and build a self-contained plugin bundle with
`python3 scripts/build_plugin.py --out dist/marketplace`.

## Reproducing the experiments

The code behind the paper's results -- a harness that runs Claude Code, Codex and the Copilot CLI
on SWE-Bench and Web-Bench, the launchers, and the evaluated task sets -- is in
**[`experiments/`](experiments/README.md)**, whose README gives the setup and one command per
result. It is not part of the installed plugin; the two share only `tokeneconomizer/`.

## Citation

```bibtex
@misc{li2026tokeneconomizer,
  title         = {{TokenEconomizer}: Experience-Driven Black-Box Cost Control for Coding Agents},
  author        = {Li, Aaron J. and Xu, Weijia and Singh, Chandan and Chen, Zixiao and
                   Inala, Jeevana Priya and Siska, Charlotte and Tamersoy, Acar and Yu, Bin and
                   Stoica, Ion and Galley, Michel and Gao, Jianfeng},
  year          = {2026},
  eprint        = {2610.22732},
  archivePrefix = {arXiv},
  primaryClass  = {cs.CL},
  url           = {https://arxiv.org/abs/2610.22732}
}
```

## License

Apache 2.0; see [`LICENSE`](LICENSE).
