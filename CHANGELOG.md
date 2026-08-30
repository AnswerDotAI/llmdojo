# Release notes

<!-- do not remove -->

## 0.0.4

### New Features

- Rebake the dojo round for the renamed clikernel py tool ([#24](https://github.com/AnswerDotAI/llmdojo/pull/24)), thanks to [@jph00](https://github.com/jph00)
- Switch Claude capture to fastclaude astream and drop the agent SDK dependency ([#23](https://github.com/AnswerDotAI/llmdojo/issues/23))


## 0.0.3

### New Features

- Launchers exec claude/codex directly with config-file args instead of printing session ids; forward extra flags ([#20](https://github.com/AnswerDotAI/llmdojo/issues/20))
- rules: credit key-verified doced() declarations in the same cell, so nodoc no longer fires when a doc key is provided ([#19](https://github.com/AnswerDotAI/llmdojo/issues/19))
- rules: doced() now warns on key mismatch instead of returning it in the result string ([#18](https://github.com/AnswerDotAI/llmdojo/issues/18))
- Clarify orient kata routing hint and startup instructions; simplify dojo test to call sh.run directly without `run_sync` ([#17](https://github.com/AnswerDotAI/llmdojo/issues/17))
- llmdojo: friendly error when resuming with no session; relax `s_long` rule to allow long s-replacements; drop receipt expiry note ([#16](https://github.com/AnswerDotAI/llmdojo/issues/16))
- Suggest no-args form when  has no session to append to ([#7](https://github.com/AnswerDotAI/llmdojo/pull/7)), thanks to [@ncoop57](https://github.com/ncoop57)

### Bugs Squashed

- prefer `CLAUDE_CODE_SESSION_ID` for host id, add `forget_doced`(before) so post-compaction doc reads survive ([#21](https://github.com/AnswerDotAI/llmdojo/issues/21))


## 0.0.2

### New Features

- `compact_dojo`: strip previously dealt dojo rounds before compacting, via shared `_turns` helper and per-host `strip_dojo` ([#15](https://github.com/AnswerDotAI/llmdojo/issues/15))
- Add doc(acp) to the dojo bootstrap reads ([#14](https://github.com/AnswerDotAI/llmdojo/issues/14))
- Key-verify doced() declarations against live doc() output ([#12](https://github.com/AnswerDotAI/llmdojo/issues/12))
- Add doced() to acknowledge in-context docs, skip transform-injected calls in nodoc rule ([#11](https://github.com/AnswerDotAI/llmdojo/issues/11))
- Ship compiled template stores as package data instead of building them per-user on first launch ([#10](https://github.com/AnswerDotAI/llmdojo/issues/10))
- Extract shared template layer into llmdojo.tmpl with dojobuild CLI, one canonical template dialog, and deterministic round replay ([#9](https://github.com/AnswerDotAI/llmdojo/issues/9))
- Replace `pick_turns` with sentinel-based `pick_span` for live capture, add codexdojo capture event logging, and harden `dojo_score` cwd recovery ([#6](https://github.com/AnswerDotAI/llmdojo/issues/6))

### Bugs Squashed

- fix tmpl.py being ignored ([#5](https://github.com/AnswerDotAI/llmdojo/pull/5)), thanks to [@RensDimmendaal](https://github.com/RensDimmendaal)


## 0.0.1

### New Features

- Unify capture prompts, migrate Codex to clikernel MCP, add `compact_dojo` and --capture, remove Claude hooks ([#4](https://github.com/AnswerDotAI/llmdojo/issues/4))
- Rename `exhash_`{file,cell} to {file,cell}`_exhash`, rewrite capture system prompt as numbered steps, add MCP server config and adaptive thinking with effort param ([#3](https://github.com/AnswerDotAI/llmdojo/issues/3))
- Add codexdojo for Codex session templating, refine dojo/rules startup and host resolution ([#2](https://github.com/AnswerDotAI/llmdojo/issues/2))
- Add `append_dojo` for post-compaction re-injection, ship packaged template as package data, and refactor store loading ([#1](https://github.com/AnswerDotAI/llmdojo/issues/1))
