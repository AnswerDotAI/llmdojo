# Codexdojo capture

This session will become a worked example for future Codex sessions. Complete the dojo cleanly on the first attempt, with no speculative calls or retries. Keep visible narration about the work itself. After the clean score, reply exactly `OK I'm ready.` and stop.

Read the required persistent-python and coding-patterns skills first. Then launch the one persistent kernel with a native terminal call equivalent to:

```python
tools.exec_command(dict(cmd='clikernel', workdir='/tmp/codexdojo-capture', tty=True, yield_time_ms=1000, max_output_tokens=50000))
```

The PTY and short yield are required. Do not run `clikernel` as a blocking shell command. Save the returned session id and use `tools.write_stdin` with `yield_time_ms=1000` and `max_output_tokens=50000` for every kernel cell. Follow the startup output exactly: read the six module overviews with `doc(clik, pysk, fct, dsk, exh, rgsk)`, run `list_pyskills()` as its own cell, then run `dojo_start()`.

Change to the run directory printed by `dojo_start()` before doing anything else. Tag each kata with the exact comment-only `# kata N` cell. Read each function's docs immediately before its first use. Use the par route printed on the card.

For kata 1, call `doc(find_msgs)` and then call `find_msgs('httpx', dlg='nbs/01_api.ipynb')`. Its default context includes the neighbouring explanation. The final orientation answer must include policy `rb-3254`, requests' lack of async support, its manually managed Session objects for connection pooling, and that httpx matches the API while fixing those problems.

For kata 2, call `doc(lnhashview_file, exhash_file)`, view `core.py`, then make all three changes in one `exhash_file` call. Pass each edit as its own tuple and order edits bottom-to-top so line shifts cannot invalidate later addresses.

For kata 3, view `tmpl.py`, then use one `%%exhash` range replacement with a verbatim payload. The replacement is exactly:

```python
def render(name, temp):
    r"""Render a one-line summary; keep \t, \n and ''' literal in this docstring."""
    return name + ':\t' + str(temp) + ' degrees\n'
```

For kata 4, call `doc(exhash_cell)`, use `find_msgs(header_section='Retries', dlg='nbs/01_api.ipynb')` to obtain the target cell id, then replace that whole cell through `%%exhash <path> <cell-id> % c`. The markdown must say: `On a connection error, the request is retried twice more, making 3 attempts in all.`

For kata 5, import `report`, end the import cell with `doc(report.daily_report)`, then call `report.daily_report(report.SAMPLE, style='rb2')` as a bare expression. Its first line is `RB7034`.

Call `dojo_score` only once, passing `bash_calls=0`, the complete orientation answer, and `report='RB7034'`. Do not call `dojo_redo` or `dojo_resume`. The round is acceptable only when the score says `Clean round`.
