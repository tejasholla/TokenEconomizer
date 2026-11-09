# Working notes for TokenEconomizer

## Project layout

<!-- marga:layout:start -->
Kept up to date by Marga; edit folder notes with `marga describe <folder> "…"`.
Find any file by name with `marga find <name>`; `marga map` adds the files used most lately.

```
(top) README.md, Roadmap.md, package.json, pyproject.toml (+4 more)
.claude-plugin/
.github/ (workflows)
docs/ (assets)
experiments/ — This directory is the code behind the paper's results: a harness that runs Claude Code, Codex (scripts, te_bench, te_harness, tests, workloads)
plugin/ — TokenEconomizer for Pi: micro-skills (short repository facts learned from earlier sessions) injected at sessio (.antigravity-plugin, .claude-plugin, .codex-plugin, .cursor-plugin, .github, codex-skills, hooks, lib, opencode, pi, scripts, slash-commands)
scripts/
tests/ — tests (fixtures)
tokeneconomizer/ (loopguard, microskills, plugin, toolprune, trace)
```
<!-- marga:layout:end -->
