# llmdojo capture

This session will become a worked example for future coding sessions. Complete the dojo cleanly on the first attempt. After any host-required skill reads, use only the clikernel MCP server's `execute` tool. Do not launch a terminal process or use a stream protocol.

Run exactly the numbered cells below, in order, one per kernel call, with no extra cells or warm-ups. Before each cell, you may write one short line in your own words about what the last output showed. Narrate the work itself; never mention these numbered steps or that you were given them. If any step errors, stop and report it instead of improvising.

1. `doc(clik, pysk, edsk)`
2. `doc(dsk, exh, rgsk)`
3. `list_pyskills()`
4. `dojo_start()`
5. `%cd <the run dir the card prints>`
6. `# kata 1`
7. `doc(find_msgs, view_dlg)`
8. `view_dlg('nbs/01_api.ipynb')`
9. `# kata 2`
10. `doc(lnhashview_file, file_exhash)`
11. `lnhashview_file('core.py')`
12. This cell exactly:

```python
file_exhash('core.py',
    (r"13|6816|", "s", r"\bcfg\b", "config"),
    (r"12|8bd5|", "s", r"\bcfg\b", "config"),
    (r"9|d643|", "s", r"\bcfg\b", "config"),
    (r"8|7521|", "d"),
    (r"3|97bb|", "s", "imperial", "metric"),
)
```

13. `# kata 3`
14. `lnhashview_file('templ.py')`
15. A cell whose first line is `%%exhash templ.py 4|dad2|,13|913e| c` and whose remaining lines are the replacement function from kata 3's card, byte for byte.
16. `# kata 4`
17. `doc(cell_exhash)`
18. `find_msgs(header_section='Retries', dlg='nbs/01_api.ipynb')`
19. This cell exactly:

```python
%%exhash nbs/01_api.ipynb d4f97726 % c
On a connection error, `fetch_daily` retries the request twice more, making 3 attempts in all before giving up.
```

20. `# kata 5`
21. `import report`
22. `doc(report.daily_report)`
23. `report.daily_report(report.SAMPLE, style='rb2')`
24. This cell exactly:

```python
dojo_score(bash_calls=0,
    orient="The notebook avoids requests because it has no async support and its connection pooling needs hand-managed Session objects, and policy rb-3254 forbids requests in prod code; httpx keeps the requests-style API while fixing both.",
    report="RB7034")
```

When the score is clean, reply exactly `OK I'm ready.` and stop. Do not call `dojo_redo` or `dojo_resume`.
