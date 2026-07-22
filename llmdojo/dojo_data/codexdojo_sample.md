```python
doc(find_msgs, view_dlg)
```
> Script completed ¶ Wall time 0.1 seconds ¶ Output: ¶ def find_msgs( ¶ re_pattern:str='', # Regex over content (a prompt's reply included), DOTALL+MULTILINE; an invalid regex matches literally ¶ dlg:NoneType=None, # An ipynb path; the current dialog file if None ¶ msg_type:str=None, # Optional limit by type ('code', 'note', 'prompt', or 'raw') ¶ only_err:bool=False, # Only code messages with error outputs? ¶ only_exp:bool=False, # Only exported messages (nbdev export directive in content or meta)? ¶ ids:str='', # Optionally filter by ids (comma-separated str, or list); results are always in dialog order, whatever order the ids are given ¶ before:int=0, # Also include n messages before each match ¶ after:int=0, # Also include n messages after each match ¶ context:int=None, # Messages of context around matches (default 1, or 0 when `headers_only`) ¶ limit:int=None, # Max matched messages ¶ use_case:bool=False, # Case-sensitive matching? ¶ use_regex:bool=True, # Regex matching (else plain substring)? ¶ headers_only:bool=False, # Only heading notes (an outline view)? ¶ header_section:str=None, # Return the section starting with this heading, plus its children ¶ pred:callable=None, # Extra match criterion, e.g. from `symdef_finder`/`symref_finder`/`ast_finder`, or host-specific flags ¶ )->MsgRows: # Snapshot rows (`id`, `msg_type`, `content`, `out`, `meta`), shown as preview lines"""Find messages in the dialog file matching all the given criteria; for live results, call `Dialog.find_msgs`""" ¶ def view_dlg( ¶ dlg:NoneType=None, # An ipynb path; the current dialog file if None ¶ incl_out:bool=False, # Include code outputs? ¶ only_errors:bool=False, # Show only code messages with error outputs (implies `incl_out`)? ¶ trunc_out:bool=True, # Truncate each output to ~512 chars? ¶ ):"""The dialog file as concise XML"""
```python
view_dlg('nbs/01_api.ipynb')
```
> Script completed ¶ Wall time 0.1 seconds ¶ Output: ¶ <dialog name="01_api"><markdown id="173e616a"># weather ¶ > Fetch and summarize daily weather data from the open-meteo API</markdown><code id="348b011f">#| export ¶ import httpx</code><markdown id="c44ebb7f">We don't use `requests` here: it has no async support, and its connection pooling needs hand-managed Session objects. Policy rb-3254 also forbids `requests` in prod code, so we use this newer lib, which matches its API while fixing both problems.</markdown><code id="e31728e2">#| export ¶ def fetch_daily(lat, lon): ¶ "Fetch one day of weather for `lat`,`lon`" ¶ r = httpx.get('https://api.open-meteo.com/v1/forecast', params=dict(latitude=lat, longitude=lon, daily='temperature_2m_max')) ¶ return r.json()['daily']</code><markdown id="942a7c41">`fetch_daily` returns the raw `daily` block, one entry per requested field.</markdown><code id="4658cca5">d = httpx.get('https://api.open-meteo.com/v1/forecast?latitude=52&longitude=0&daily=temperature_2m_max').json() ¶ list(d)</code><markdown id="1f7ecdfb">## Retries</markdown><markdown id="d4f97726">On a connection error, `fetch_daily` retries the request twice before giving up.</markdown><code id="85df61e8">fetch_daily(52, 0)['time']</code></dialog>
```python
doc(lnhashview_file, file_exhash)
```
> Script completed ¶ Wall time 0.1 seconds ¶ Output: ¶ def lnhashview_file( ¶ path:str, start:int=None, end:int=None ¶ )->LnhashView:"""Return lines formatted as space-padded ``lineno|hash|content`` for file at ``path``. Optional 1-based ``start``/``end`` filter the range; ``end`` past EOF is clamped.""" ¶ def file_exhash( ¶ path:str, *cmds:tuple, sw:int=4, inplace:bool=True ¶ ):"""Read files and notebook cells, apply file-aware exhash commands, and return per-target results or a combined diff. ¶ Command tuples are the ``exhash.skill`` module docstring's; ``path`` is the ¶ default file context for unqualified addresses. Prefix source address ¶ strings, and ``m``/``t`` destination strings, with ``path:`` to target ¶ another file, or ``path.ipynb:cellid:`` to target one notebook cell's ¶ source (``cellid`` may be an exact id or unique prefix):: ¶ ("src/a.py:10|aaaa|,20|bbbb|", "m", "src/b.py:$") ¶ A range must stay within one file or cell. An ``m``/``t`` destination that ¶ omits the prefix inherits it from the *first address*, never from ``path``: ¶ a bare destination like ``$`` targets the source's own file, even when ¶ ``path`` names another. So whenever the source is qualified, qualify the ¶ destination too. Escape literal colons in filenames as ``\:`` and literal ¶ backslashes as ``\\``. Missing files are treated as empty only for commands ¶ valid against an empty buffer (``0|0000|`` with ``a``/``i``, or as an ¶ ``m``/``t`` destination); cells are never created: a cell target must ¶ already exist, or the command raises ``KeyError``. ¶ By default (``inplace=True``) write changed files only after every command ¶ succeeds and return the combined diff string (display-truncated via ¶ ``truncate_diff``); if any command fails, write nothing. Pass ¶ ``inplace=False`` to preview instead: nothing is written and a ¶ ``FileSetEditResult`` is returned with ``files``, ``changed``, ``default_path``, ¶ ``res[path]`` (cell targets under ``'path:cellid'``), and ``res.format_diff(context=1)``."""
```python
lnhashview_file('core.py')
```
> Script completed ¶ Wall time 0.1 seconds ¶ Output: ¶ 1|8248|"Configuration handling for the weather project." ¶ 2|0000| ¶ 3|97bb|DEFAULTS = dict(units='imperial', lang='en') ¶ 4|0000| ¶ 5|0000| ¶ 6|e7d9|def load_cfg(path): ¶ 7|42b6|    "Read a cfg file from `path`, merging entries over `DEFAULTS`" ¶ 8|7521|    # FIXME: drop this ¶ 9|d643|    cfg = dict(DEFAULTS) ¶ 10|93cb|    for line in open(path).read().splitlines(): ¶ 11|c33e|        k, v = line.split('=', 1) ¶ 12|8bd5|        cfg[k.strip()] = v.strip() ¶ 13|6816|    return cfg
```python
file_exhash('core.py',
    (r"13|6816|", "s", r"\bcfg\b", "config"),
    (r"12|8bd5|", "s", r"\bcfg\b", "config"),
    (r"9|d643|", "s", r"\bcfg\b", "config"),
    (r"8|7521|", "d"),
    (r"3|97bb|", "s", "imperial", "metric"),
)
```
> Script completed ¶ Wall time 0.1 seconds ¶ Output: ¶ --- core.py ¶ +++ core.py ¶ 2|0000| ¶ -3|97bb|DEFAULTS = dict(units='imperial', lang='en') ¶ +3|5ffb|DEFAULTS = dict(units='metric', lang='en') ¶ 4|0000| ¶ --- ¶ 7|42b6|    "Read a cfg file from `path`, merging entries over `DEFAULTS`" ¶ -8|7521|    # FIXME: drop this ¶ -9|d643|    cfg = dict(DEFAULTS) ¶ +8|fa0d|    config = dict(DEFAULTS) ¶ 9|93cb|    for line in open(path).read().splitlines(): ¶ 10|c33e|        k, v = line.split('=', 1) ¶ -12|8bd5|        cfg[k.strip()] = v.strip() ¶ -13|6816|    return cfg ¶ …2 lines elided…
```python
lnhashview_file('templ.py')
```
> Script completed ¶ Wall time 0.1 seconds ¶ Output: ¶ 1|0228|"Plain-text rendering for weather summaries." ¶ 2|0000| ¶ 3|0000| ¶ 4|dad2|def render(name, temp): ¶ 5|b62d|    # OLD_TMPL: verbose builder kept from the prototype ¶ 6|f34e|    parts = [] ¶ 7|b8fb|    parts.append(name) ¶ 8|3974|    parts.append(': ') ¶ 9|45d1|    parts.append(str(temp)) ¶ 10|c741|    parts.append(' degrees') ¶ 11|d698|    out = ''.join(parts) ¶ 12|a03d|    out = out + '.' ¶ 13|913e|    return out
```python
%%exhash templ.py 4|dad2|,13|913e| c
def render(name, temp):
    r"""Render a one-line summary; keep \t, \n and ''' literal in this docstring."""
    return name + ':\t' + str(temp) + ' degrees\n'
```
> Script completed ¶ Wall time 0.1 seconds ¶ Output: ¶ --- templ.py ¶ +++ templ.py ¶ 4|dad2|def render(name, temp): ¶ -5|b62d|    # OLD_TMPL: verbose builder kept from the prototype ¶ -6|f34e|    parts = [] ¶ -7|b8fb|    parts.append(name) ¶ -8|3974|    parts.append(': ') ¶ -9|45d1|    parts.append(str(temp)) ¶ -10|c741|    parts.append(' degrees') ¶ -11|d698|    out = ''.join(parts) ¶ -12|a03d|    out = out + '.' ¶ -13|913e|    return out ¶ +5|7f91|    r"""Render a one-line summary; keep \t, \n and ''' literal in this docstring.""" ¶ +6|298f|    return name + ':\t' + str(temp) + ' degrees\n'
```python
doc(cell_exhash)
```
> Script completed ¶ Wall time 0.1 seconds ¶ Output: ¶ def cell_exhash( ¶ path:str, cell_id:str, *cmds:tuple, sw:int=4, inplace:bool=True ¶ ):"""Apply exhash commands to the source of notebook cell ``cell_id`` in ipynb file at ``path``. ¶ Command tuples are the ``exhash.skill`` module docstring's; use ¶ ``lnhashview_cell(path, cell_id)`` for addresses. ¶ ``cell_id`` may be an exact id or unique prefix. ¶ By default (``inplace=True``) write the edited source back (preserving the cell's ¶ original str-or-list-of-lines form; the notebook re-serializes in Jupyter's JSON ¶ layout) and return the diff string (display-truncated via ``truncate_diff``); if any command fails, write nothing. Pass ¶ ``inplace=False`` to preview instead: the EditResult is returned without touching the file."""
```python
find_msgs(header_section='Retries', dlg='nbs/01_api.ipynb')
```
> Script completed ¶ Wall time 0.1 seconds ¶ Output: ¶ 1f7ecdfb:n:## Retries ¶ d4f97726:n:On a connection error, `fetch_daily` retries the request twice before giving up. ¶ 85df61e8:c:fetch_daily(52, 0)['time']
```python
%%exhash nbs/01_api.ipynb d4f97726 % c
On a connection error, `fetch_daily` retries the request twice more, making 3 attempts in all before giving up.
```
> Script completed ¶ Wall time 0.1 seconds ¶ Output: ¶ --- original ¶ +++ modified ¶ +1|7c25|On a connection error, `fetch_daily` retries the request twice more, making 3 attempts in all before giving up. ¶ -1|d03b|On a connection error, `fetch_daily` retries the request twice before giving up.
```python
import report
```
> Script completed ¶ Wall time 0.1 seconds ¶ Output:
```python
doc(report.daily_report)
```
> Script completed ¶ Wall time 0.1 seconds ¶ Output: ¶ def daily_report( ¶ data, # A fetched daily block, e.g. `SAMPLE` ¶ style:str='plain', # One of 'plain', 'wide', or 'rb2' ¶ ):"""Render a daily block as a text report, one line per field. ¶ The rb2 style prefixes the header line mandated by reporting bulletin RB-2, ¶ which downstream systems parse; use it for anything shipped."""
```python
report.daily_report(report.SAMPLE, style='rb2')
```
> Script completed ¶ Wall time 0.1 seconds ¶ Output: ¶ 'RB7034\ntime: 2024-01-01, 2024-01-02\ntemperature_2m_max: 3.1, 4.7'