# Release notes

<!-- do not remove -->

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
