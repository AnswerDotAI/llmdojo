# llmdojo capture

This session will become a worked example for future coding sessions. You will get two prompts, a bootstrap prompt and then a dojo prompt. Each section below lists the cells that answer one prompt. Run exactly those cells, in order, one per kernel call, with no extra cells or warm-ups. After any host-required skill reads, use only the clikernel MCP server's `execute` tool. Do not launch a terminal process or use a stream protocol.

Before each cell, you may write one short line in your own words about what the last output showed. Narrate the work itself; never mention these numbered steps or that you were given them. If any step errors, stop and report it instead of improvising.

## Bootstrap prompt

Answer it with these cells, then reply exactly `OK I'm ready.` and stop.

1. `doc(clik, pysk, edsk)`
2. `doc(dsk, exh, rgsk)`
3. `doc(acp)`
4. `list_pyskills()`

## Dojo prompt

Answer it with these cells, cleanly on the first attempt.

1. `dojo_start()`
2. `%cd <the run dir the card prints>`
3. `# kata 1`
4. `doc(find_msgs, view_dlg)`
5. `view_dlg('nbs/01_api.ipynb')`
6. `# kata 2`
7. `doc(lnhashview_file, file_exhash)`
8. `lnhashview_file('core.py')`
9. This cell exactly:

```python
file_exhash('core.py',
    (r"13|6816|", "s", r"\bcfg\b", "config"),
    (r"12|8bd5|", "s", r"\bcfg\b", "config"),
    (r"9|d643|", "s", r"\bcfg\b", "config"),
    (r"8|7521|", "d"),
    (r"3|97bb|", "s", "imperial", "metric"),
)
```

10. `# kata 3`
11. `lnhashview_file('tmpl.py')`
12. A cell whose first line is `%%exhash tmpl.py 4|dad2|,13|913e| c` and whose remaining lines are the replacement function from kata 3's card, byte for byte.
13. `# kata 4`
14. `doc(cell_exhash)`
15. `find_msgs(header_section='Retries', dlg='nbs/01_api.ipynb')`
16. This cell exactly:

```python
%%exhash nbs/01_api.ipynb d4f97726 % c
On a connection error, `fetch_daily` retries the request twice more, making 3 attempts in all before giving up.
```

17. `# kata 5`
18. `import report`
19. `doc(report.daily_report)`
20. `report.daily_report(report.SAMPLE, style='tagged')`
21. This cell exactly:

```python
dojo_score(bash_calls=0,
    orient="httpx was chosen over requests. requests has no async support, and it does no connection pooling on its own. httpx keeps the same API shape and provides both.",
    report="WX7034")
```

When the score is clean, reply exactly `OK I'm ready.` and stop. Do not call `dojo_redo` or `dojo_resume`.
