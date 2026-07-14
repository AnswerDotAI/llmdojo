# llmdojo development notes

The README documents what llmdojo provides: session rules, a scored practice round, and pre-baked warm-start session templates. This file documents why it is built the way it is and what we know about the LLM agents that use it, since much of the design only makes sense in light of that.

The one-sentence thesis: prose instructions decay over a session; mechanisms don't. Everything here moves guidance out of standing prompt text and into the execution path, using clikernel's documented extension points (the inspector hook and the startup file) rather than kernel code.

## Layout

- `rules.py`: the behavior layer. Built-in inspectors ("session rules"), the `Rule` type, and doc-state tracking with per-conversation persistence. `RuleBlock` itself belongs to clikernel (the mechanism defines the blocking contract); rules here raise it.
- `dojo.py`: the scored practice round an agent completes before real work.
- `claudedojo` (notebook-sourced): capture a clean round from a live session (or headlessly: `capture_dojo`/`claudedojo --capture` plays a scripted round via the Agent SDK, gated by `is_clean`), curate it into a deterministic template, store it, and launch Claude Code sessions that resume it. `meta/predojo.md` is the design document for this pipeline; `meta/dojo_template.ipynb` is the current template dialog.
- `dojo_data/proj/`: the fixture project the dojo copies for each round.
- `claude/`: the user-level Claude Code config that deploys all of this (SessionStart hook, kernel startup file), symlinked into `~/.claude/hooks/` and `~/.config/clikernel/`; see `claude/README.md`.

## The rules

Each kernel cell reaches `scan` via clikernel's inspector hook (registered in `$XDG_CONFIG_HOME/clikernel/inspectors.py` with `make_inspector()`). The built-in rules in `RULES` fall into three families. Routing rules push work to the designed tools (read files with `lnhashview_file`, edit cells through `%%exhash`, run magics as magics, show tooling results bare instead of post-processing them, import skill modules whole). String-safety rules catch the quoting mistakes LLMs actually make (non-raw strings holding escapes, two-character `\n` in an s-replacement, oversized replacements that should be `c` commands, computed hash addresses). Gating rules block outright: shell escapes (use the permission-checked Bash tool) and `sys.path` edits (ask the user). The `nodoc` rule does the most work: first use of a workspace function before `doc()` earns a correction note, which is what makes the curated docs actually get read.

Why this works when the same guidance already exists in skills and prompts: we measured the difference. Standing instructions ("always read docs first") hold for a few turns and then lose to task focus. A note that arrives in the tool result, at the exact moment of the mistake, gets acted on essentially every time; compliance with inspector notes across sessions has been effectively total, including mid-task where prompt text is weakest. The general finding: prohibitions with bright-line triggers bind well in prose (a "never run git" rule has held across all sessions), but anything stateful or conditional ("have I done X yet this session?") must live in the harness, because models don't reliably track state across a long context.

## Doc-state

The tooling this ecosystem runs on (pyskills, exhash, rgapi) has docments-annotated signatures whose details matter; an agent that guesses a remembered signature costs a round trip per miss. `Session.doced` tracks which functions have had `doc()` read this conversation, and `nodoc` fires on undoc'd first use.

The set persists to `~/.local/state/llmdojo/doced/<host>.json`, where `<host>` is the conversation id: the stem of the newest transcript `.jsonl` under `~/.claude/projects/<sanitized CLAUDE_PROJECT_DIR>`, resolved once per worker at first use. The file is read back before every cell inspection, so external writes (such as the compaction hook truncating it) take effect immediately on a running kernel. Files older than a day are swept. Fallbacks when there is no project dir or no transcript: `CLAUDE_CODE_SESSION_ID`, then parent pid, which is why stray numeric `.json` files appear in the state dir after test runs. `doced(*names)` and `forget_doced()` exist for the two context events described below.

## The dojo

`dojo_start()` copies the fixture project into a private state dir, registers a `pre_run_cell` tracer, and prints katas covering the intended workflow: orient with search tooling, batch hash-verified edits bottom-to-top, verbatim payloads through the `%%exhash` magic, notebook cell replacement by id, doc-before-call on elided overview lines. Every kernel cell costs a stroke (doc reads, imports, and kata-tag cells are free; Bash costs double), each kata has a par, and scoring reveals the par route so the agent learns the intended path even when it found another. Undoc'd tool use adds penalties. A clean round (par or better, all katas ok, no penalties) registers a 4-hex completion id in `dojo_complete.json`, which is machine-global and version-stamped; a clean score also resets the kernel namespace (announcing it), so every session starts real work from the same fresh state whether its round was live or baked; `dojo_start(id)` skips the round in later sessions, and `forget_dojo()` truncates the registry after tooling changes so everyone replays.

The dojo is the enforcement mechanism for the session bootstrap. Telling an agent to read skills produces skimming; requiring one cheap scored round produces a demonstrated pass through every designed tool before real files are touched, and the stroke budget penalizes exactly the ad-hoc habits (Bash detours, print-wrapping, skipping docs) the rules exist to catch. Par-matching doubles as a signal that the tooling's best route is discoverable.

## How Claude Code behaves, and how we know

The design leans on facts about Claude Code that aren't documented anywhere authoritative, so we established them by experiment. Dated observations, all from live sessions (most recently 2026-07-14):

- A conversation keeps one transcript file for its whole life. We watched a session's `.jsonl` keep the same stem and keep advancing across a compaction and an app close/resume, while `CLAUDE_CODE_SESSION_ID` changed on each spawn. That stem is therefore the right persistence key, and `_resolve_host`'s newest-transcript heuristic finds it because the active conversation is nearly always the most recently written (`llmsurgery.ant.cur_sess` now uses the same heuristic).
- The MCP server (and so the kernel) dies with the app and restarts on resume, but survives compaction: the same kernel pid keeps answering across a compact, with its namespace intact.
- On resume the model's context is replayed in full, `doc()` output included. On compaction the context is rewritten to a summary: skill texts survive as stale snapshots of whenever they were first read, and `doc()` output is gone.
- Assistant text emitted between tool calls is dropped by the interface (anthropics/claude-code#75900), so agent narration must travel inside tool calls. Kata-tag and comment-only cells are free in dojo scoring for this reason.

What each event changes:

| event | model context | kernel namespace | doced record |
|---|---|---|---|
| compact | docs gone, skills stale | survives | truncated by the compact hook |
| close/resume | fully intact | fresh (startup re-runs) | restored from disk, correct |

The doced file is the source of truth, not a backup: the inspector re-reads it before every cell, so an external writer can change doc-state under a live kernel. The compact case uses exactly that: the user-level SessionStart hook truncates the file mechanically on compaction, and after a plain resume nothing needs doing at all. This matters because the user often closes the app right after compacting, so any instruction-based reset might never run; per-event instructions can't cover that path, mechanism can. The bootstrap gate wording has been through several iterations; the current form is a prohibition ("never touch files before the bootstrap") rather than a mandate, because prohibition-form rules are the ones that have held in practice.

## Known sharp edges

- Host resolution can mis-key when two conversations are live in the same project dir at once; newest-transcript picks whichever wrote last at the moment the worker first resolves.
- Test runs that spawn workers without `LLMDOJO_STATE_DIR` write pid-keyed state files into the real state dir.

## Testing and release

`pytest -q` for `tests/test_rules.py` (each session rule against minimal sources) and `tests/test_dojo.py` (checkers, scoring, completion receipts). `nbdev-test` covers the claudedojo notebook; its capture and launch cells are `#| eval: false` (they need a live session), and "Rebuilding the template" in that notebook is the worked rebuild recipe. Development style follows the fastai conventions (see the `coding-patterns` skill); versioning is bump-after-release, so the tree always carries the next version. Release is `ship-gh`, `ship-pypi`, `ship-bump`.
