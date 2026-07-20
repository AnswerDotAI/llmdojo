# llmdojo development notes

The README documents what llmdojo provides: session rules, a scored practice round, and pre-baked warm-start session templates. This file documents why it is built the way it is and what we know about the LLM agents that use it, since much of the design only makes sense in light of that.

The one-sentence thesis: prose instructions decay over a session; mechanisms don't. Everything here moves guidance out of standing prompt text and into the execution path, using clikernel's documented extension points (the inspector hook and the startup file) rather than kernel code.

## Layout

- `rules.py`: the behavior layer. Built-in inspectors ("session rules"), the `Rule` type, and doc-state tracking with per-conversation persistence. `RuleBlock` itself belongs to clikernel (the mechanism defines the blocking contract); rules here raise it.
- `dojo.py`: the scored practice round an agent completes before real work.
- `claudedojo` (notebook-sourced): capture a clean round from a live session (or headlessly: `capture_dojo`/`claudedojo --capture` plays a scripted round via the Agent SDK, gated by `is_clean`), curate it into a deterministic template, store it, and launch Claude Code sessions that resume it. See "The session template" below; `llmdojo/dojo_data/dojo_template.ipynb` is the current curated template dialog, shipped as package data.
- `codexdojo` (notebook-sourced): convert a completed Codex rollout to a dialog, curate its reply, store native Responses items, and create or refresh Codex threads through app-server. `llmdojo/dojo_data/codexdojo_template.ipynb` is the reviewed Codex template.
- `dojo_data/proj/`: the fixture project the dojo copies for each round.
- `claude/`: the user-level Claude Code config that deploys all of this (SessionStart hook, kernel startup file), symlinked into `~/.claude/hooks/` and `~/.config/clikernel/`; see `claude/README.md`.

## The rules

Each kernel cell reaches `scan` via clikernel's inspector hook (registered in `$XDG_CONFIG_HOME/clikernel/inspectors.py` with `make_inspector()`). The built-in rules in `RULES` fall into three families. Routing rules push work to the designed tools (read files with `lnhashview_file`, edit cells through `%%exhash`, run magics as magics, show tooling results bare instead of post-processing them, import skill modules whole). String-safety rules catch the quoting mistakes LLMs actually make (non-raw strings holding escapes, two-character `\n` in an s-replacement, oversized replacements that should be `c` commands, computed hash addresses). Gating rules block outright: shell escapes (use the permission-checked Bash tool) and `sys.path` edits (ask the user). The `nodoc` rule does the most work: first use of a workspace function before `doc()` earns a correction note, which is what makes the curated docs actually get read.

Why this works when the same guidance already exists in skills and prompts: we measured the difference. Standing instructions ("always read docs first") hold for a few turns and then lose to task focus. A note that arrives in the tool result, at the exact moment of the mistake, gets acted on essentially every time; compliance with inspector notes across sessions has been effectively total, including mid-task where prompt text is weakest. The general finding: prohibitions with bright-line triggers bind well in prose (a "never run git" rule has held across all sessions), but anything stateful or conditional ("have I done X yet this session?") must live in the harness, because models don't reliably track state across a long context.

## Doc-state

The tooling this ecosystem runs on (pyskills, exhash, rgapi) has docments-annotated signatures whose details matter; an agent that guesses a remembered signature costs a round trip per miss. `Session.doced` tracks which functions have had `doc()` read this conversation, and `nodoc` fires on undoc'd first use.

The set persists to `~/.local/state/llmdojo/doced/<host>.json`, where `<host>` is the conversation id. Codex provides `CODEX_THREAD_ID` directly. Under Claude, llmdojo uses the stem of the newest transcript `.jsonl` under `~/.claude/projects/<sanitized CLAUDE_PROJECT_DIR>`, resolved once per worker at first use. The file is read back before every cell inspection, so external writes such as the compaction hook truncating it take effect immediately on a running kernel. Files older than a day are swept. Claude fallbacks when there is no project dir or no transcript are `CLAUDE_CODE_SESSION_ID`, then parent pid, which is why stray numeric `.json` files appear in the state dir after test runs. `doced(*names)` and `forget_doced()` exist for the two context events described below.

## The dojo

`dojo_start()` copies the fixture project into a private state dir, registers a `pre_run_cell` tracer, and prints katas covering the intended workflow: orient with search tooling, batch hash-verified edits bottom-to-top, verbatim payloads through the `%%exhash` magic, notebook cell replacement by id, doc-before-call on elided overview lines. Every kernel cell costs a stroke (doc reads, imports, kata-tag cells, and chdir cells are free; Bash costs double — chdir is never penalized because a %cd into the run dir makes every later path relative, saving tokens on each subsequent cell), each kata has a par, and scoring reveals the par route so the agent learns the intended path even when it found another. Undoc'd tool use adds penalties. A clean round (par or better, all katas ok, no penalties) registers a 4-hex completion id in `dojo_complete.json`, which is machine-global and version-stamped; a clean score also resets the kernel namespace (announcing it), so every session starts real work from the same fresh state whether its round was live or baked; `dojo_start(id)` skips the round in later sessions, and `forget_dojo()` truncates the registry after tooling changes so everyone replays.

The dojo is the enforcement mechanism for the session bootstrap. Telling an agent to read skills produces skimming; requiring one cheap scored round produces a demonstrated pass through every designed tool before real files are touched, and the stroke budget penalizes exactly the ad-hoc habits (Bash detours, print-wrapping, skipping docs) the rules exist to catch. Par-matching doubles as a signal that the tooling's best route is discoverable.

## How Claude Code behaves, and how we know

The design leans on facts about Claude Code that aren't documented anywhere authoritative, so we established them by experiment. Dated observations, all from live sessions (most recently 2026-07-16):

- A conversation keeps one transcript file for its whole life. We watched a session's `.jsonl` keep the same stem and keep advancing across a compaction and an app close/resume, while `CLAUDE_CODE_SESSION_ID` changed on each spawn. That stem is therefore the right persistence key, and `_resolve_host`'s newest-transcript heuristic finds it because the active conversation is nearly always the most recently written (`llmsurgery.ant.cur_sess` now uses the same heuristic).
- The MCP server (and so the kernel) dies with the app and restarts on resume, but survives compaction: the same kernel pid keeps answering across a compact, with its namespace intact.
- On resume the model's context is replayed in full, `doc()` output included. On compaction the context is rewritten to a summary: skill texts survive as stale snapshots of whenever they were first read, and `doc()` output is gone.
- Assistant text emitted between tool calls is dropped by the interface (anthropics/claude-code#75900), so agent narration must travel inside tool calls. Kata-tag and comment-only cells are free in dojo scoring for this reason.
- An API error mid-run (e.g. a safety-layer flag on a message) ends the SDK's `query()` stream with an error result, but the spawned CLI session retries and plays on to completion. Observed 2026-07-16: three capture attempts declared failed ("0 records") each finished the full round as zombies, scoring clean and registering real completion receipts at ~2.5-minute intervals after the runner exited. Hence capture attempts now run with `LLMDOJO_STATE_DIR` in the scratch project, so no attempt - zombie or not - can write machine-global state; only `save_template`/`prep_dojo` touch the real registry, for the accepted template's cid.

What each event changes:

| event | model context | kernel namespace | doced record |
|---|---|---|---|
| compact | docs gone, skills stale | survives | truncated by the compact hook |
| close/resume | fully intact | fresh (startup re-runs) | restored from disk, correct |

The doced file is the source of truth, not a backup: the inspector re-reads it before every cell, so an external writer can change doc-state under a live kernel. The compact case uses exactly that: the user-level SessionStart hook truncates the file mechanically on compaction, and after a plain resume nothing needs doing at all. This matters because the user often closes the app right after compacting, so any instruction-based reset might never run; per-event instructions can't cover that path, mechanism can. The bootstrap gate wording has been through several iterations; the current form is a prohibition ("never touch files before the bootstrap") rather than a mandate, because prohibition-form rules are the ones that have held in practice.


## The session template (Claude and Codex)

A fresh session gets its tooling *instructions* up front but no *examples*, and models imitate what their context shows far more reliably than what it tells — so the first tool calls of every session were being produced cold, and early mistakes compounded into session habits. claudedojo fixes this with in-context learning: every session opens as if it had just finished a clean dojo round, by *resuming* a curated session file. Two facts make this cheap: transcripts are just JSONL files the CLI trusts (records chain via `parentUuid`; synthetic tool calls resume fine), and the template is byte-for-byte deterministic (ids re-derived from position + salt, timestamps pinned), so every session shares one identical prefix — ideal for prompt caching.

Four stages. **Capture**: play one clean round — live (`pick_turns` lifts kernel cells from a real session's transcript; the "Rebuilding the template" recipe in the notebook) or unattended (`capture_dojo` / `claudedojo --capture`: an Agent SDK session steered by a script in the system prompt, which never appears in transcript records, gated by `is_clean` — one round, first-try clean score, no tool errors, no script phrases in visible text — since a fumbled round baked into a template teaches every future session the fumbles). **Curate**: `curate_dojo` mechanically keeps the active thread, strips thinking, drops hook noise and failed calls; then the human pass — a clean capture writes the round as a dialog (one prompt whose reply holds the whole round, each tool call a details block spelling the full `mcp__clikernel__execute(code=...)` call, as llmsurgery renders it), and the reviewed copy lives at `llmdojo/dojo_data/dojo_template.ipynb` (shipped as package data). The template is the role model every session imitates, so it must be *exemplary*, not merely clean: anything may be edited to make it a better role model — narration freely, and tool calls/outputs too, so long as edited receipts stay faithful to what the live tooling prints (when a change would touch many outputs, replaying the round is the cheaper generator of true ones); turns whose content session-start machinery re-injects live get cut — skill-reading turns especially, since baking a skill text ships a stale snapshot. Environment attachments survive in the directly-stored capture but drop in the dialog round-trip: they carry no message, and a spawned session gets its environment injected live as deltas anyway. **Store** (`save_template`): per-user state dir; template plus metadata (completion id, dojo tooling version, the round's `doced` list). **Launch** (`prep_dojo` / the CLI): write the template as a session of the target project (a fresh sid every launch), register the completion id, seed the spawned conversation's doc-state, `exec claude -r <sid>`.

Codex uses the same four stages with Responses items. `llmsurgery.oai` converts native `exec` calls to readable `tools.exec_command(...)` and `tools.write_stdin(...)` blocks, then reconstructs the custom calls after review. A manual refresh runs Codex in a separate scratch project, converts the completed rollout with `items2dlg`, edits the prompt reply with `reply2dlg`, and writes `llmdojo/dojo_data/codexdojo_template.ipynb`. `capture_current` handles a source thread that already scored clean on its first attempt. `prep_dojo` creates a fresh thread through app-server and injects the reviewed items before `codex resume`.

The completed manual capture used this exact command. Before running it, create a minimal `/tmp/codexdojo-capture/pyproject.toml` and copy `llmdojo/dojo_data/codex_capture_AGENTS.md` to `/tmp/codexdojo-capture/AGENTS.md`.

```sh
env LLMDOJO_STATE_DIR=/tmp/codexdojo-capture/state-manual codex -a never -s workspace-write exec --json --skip-git-repo-check -C /tmp/codexdojo-capture "Bootstrap and complete the dojo and tell me when you're ready."
```

The template does not clear the kernel namespace. A new Claude or Codex session starts a new clikernel process, so its empty namespace agrees with the baked history. `prep_dojo` registers the versioned completion receipt and seeds the template's `doced` list for the new session. Completion receipts are machine-local and expire after a week; a dojo version change invalidates the stored template and makes the launcher warn until it is rebuilt.
## Known sharp edges

- Host resolution can mis-key when two conversations are live in the same project dir at once; newest-transcript picks whichever wrote last at the moment the worker first resolves.
- Test runs that spawn workers without `LLMDOJO_STATE_DIR` write pid-keyed state files into the real state dir.

## Testing and release

`pytest -q` covers the rule and scoring modules. `nbdev-test` covers both session-template notebooks; live Claude capture and Codex app-server integration cells use `#| eval: false`. Each notebook's "Rebuilding" section documents its refresh workflow. Development follows the fastai conventions in the `coding-patterns` skill. Versioning is bump-after-release, and releases use `ship-gh`, `ship-pypi`, then `ship-bump`.
