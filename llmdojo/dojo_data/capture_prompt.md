# llmdojo capture

This session will become a worked example for future coding sessions. Complete the dojo cleanly on the first attempt. After any host-required skill reads, use only the clikernel MCP server's `execute` tool. Do not launch a terminal process or use a stream protocol.

Run exactly the numbered cells below, in order, one per kernel call, with no extra cells or warm-ups. Before each cell, you may write one short line in your own words about what the last output showed. Narrate the work itself; never mention these numbered steps or that you were given them. If any step errors, stop and report it instead of improvising.

1. `doc(clik, pysk, edsk)`
2. `doc(dsk, exh, rgsk)`
3. `doc(acp)`
4. `list_pyskills()`
5. `dojo_start()`
6. `%cd <the run dir the card prints>`
7. `# kata 1`
8. `doc(find_msgs, view_dlg)`
9. `view_dlg('nbs/01_api.ipynb')`
10. `# kata 2`
11. `doc(lnhashview_file, file_exhash)`
12. `lnhashview_file('core.py')`
13. This cell exactly:

```python
file_exhash('core.py',
    (r"13|6816|", "s", r"\bcfg\b", "config"),
    (r"12|8bd5|", "s", r"\bcfg\b", "config"),
    (r"9|d643|", "s", r"\bcfg\b", "config"),
    (r"8|7521|", "d"),
    (r"3|97bb|", "s", "imperial", "metric"),
)
```

14. `# kata 3`
15. `lnhashview_file('tmpl.py')`
16. A cell whose first line is `%%exhash tmpl.py 4|dad2|,13|913e| c` and whose remaining lines are the replacement function from kata 3's card, byte for byte.
17. `# kata 4`
18. `doc(cell_exhash)`
19. `find_msgs(header_section='Retries', dlg='nbs/01_api.ipynb')`
20. This cell exactly:

```python
%%exhash nbs/01_api.ipynb d4f97726 % c
On a connection error, `fetch_daily` retries the request twice more, making 3 attempts in all before giving up.
```

21. `# kata 5`
22. `import report`
23. `doc(report.daily_report)`
24. `report.daily_report(report.SAMPLE, style='tagged')`
25. This cell exactly:

```python
dojo_score(bash_calls=0,
    orient="httpx was chosen over requests. requests has no async support, and it does no connection pooling on its own. httpx keeps the same API shape and provides both.",
    report="WX7034")
```

When the score is clean, reply exactly `OK I'm ready.` and stop. Do not call `dojo_redo` or `dojo_resume`.
