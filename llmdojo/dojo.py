"Practice katas for tooling best practices, scored on the route taken, not just the outcome. Start with `dojo_start()`."
import ast,json,re,shutil,sys,time,uuid
from importlib.resources import files
from pathlib import Path
from llmdojo.rules import _state_root, live_session, scan, _callee, _calls

__all__ = ['dojo_start','dojo_score','dojo_redo','dojo_resume','forget_dojo','dojo_version','register_completion']

_RUN = {}

_WEEK = 7*86400

def _version():
    from llmdojo import __version__
    return f"{__version__}:2"

def _complete_file():
    "Completion record path: a sibling of the swept run root, so the sweep never touches it"
    d = _state_root()
    d.mkdir(parents=True, exist_ok=True)
    return d/'dojo_complete.json'

def _completions():
    "Completion records {id: {t, v}} from the last week; older entries are pruned"
    f = _complete_file()
    recs = json.loads(f.read_text()) if f.exists() else {}
    return {k: r for k, r in recs.items() if r['t'] > time.time() - _WEEK}

def dojo_version():
    "The current dojo tooling version, as recorded with completion ids"
    return _version()

def register_completion(cid, v=None):
    "Record `cid` as a clean-round completion (e.g. from a session template whose round is in history), so `dojo_start(cid)` honors it"
    recs = _completions()
    recs[cid] = dict(t=time.time(), v=v or _version())
    _complete_file().write_text(json.dumps(recs))
    return cid

def forget_dojo():
    "Truncate the dojo completion record (e.g. after a tooling change): every session redoes the round"
    _complete_file().write_text('{}')

_SQ3 = "'''"   # can't appear literally inside the rf''' below: the same trap kata 3 sets
_TMPL_PAYLOAD = rf'''def render(name, temp):
    r"""Render a one-line summary; keep \t, \n and {_SQ3} literal in this docstring."""
    return name + ':\t' + str(temp) + ' degrees\n'
'''
_TMPL_IND = '\n'.join('    ' + l for l in _TMPL_PAYLOAD.splitlines())


def _chk_orient(d):
    a = _RUN.get('orient') or ''
    if not a: return ['no answer passed: dojo_score(orient="<your prose answer>")']
    out = []
    if 'rb-3254' not in a.lower():
        out.append('answer lacks the specific justification: the prose next to the relevant code names it')
    if 'requests' not in a.lower(): out.append('answer does not say what httpx was chosen over')
    return out

def _chk_core(d):
    t = (d/'core.py').read_text()
    out = []
    if "units='metric'" not in t or 'imperial' in t: out.append("default units is not 'metric'")
    if len(re.findall(r'\bcfg\b', t)) != 1 or len(re.findall(r'\bconfig\b', t)) != 3:
        out.append('cfg -> config rename incomplete, or the docstring was changed')
    if not re.search(r'\bload_cfg\b', t): out.append('load_cfg was renamed: only the cfg variable changes name')
    if 'FIXME' in t: out.append('the FIXME comment line is still there')
    return out

def _chk_tmpl(d):
    t = (d/'tmpl.py').read_text()
    out = []
    if 'OLD_TMPL' in t: out.append('old render() body still present')
    if _TMPL_PAYLOAD.strip() not in t: out.append('replacement render() does not match the provided text verbatim')
    if '\n\n\n\n' in t: out.append('stray blank lines left around the replacement')
    return out

def _chk_nb(d):
    raw = (d/'01_api.ipynb').read_text()
    return [] if '3 attempts' in raw and 'retries the request twice before giving up' not in raw else \
        ['the Retries markdown does not say "3 attempts"']


def _chk_report(d):
    a = _RUN.get('report') or ''
    if not a: return ['no answer passed: dojo_score(report="<the report\'s first line>")']
    return [] if f'RB{2*3517}' in a else ['not the form that ships: daily_report knows which style that is']


KATAS = [
    dict(name='orient', par=2, files=['01_api.ipynb'], check=_chk_orient, ro=True,
        route="find_cells('httpx'): its context= defaults to 1, and the why lives in the md cell next to the import, past where one-line summaries truncate. view_nb reads whole small notebooks fine too. nbrg's one-liners locate; they don't read",
        prompt="Why does this project use httpx? Answer in prose via dojo_score(orient=\"...\"), including the specific justification the notebook gives. Tip: find_cells' context= defaults to 1 for a reason - the why usually lives next to the what."),
    dict(name='edit set', par=2, files=['core.py'], check=_chk_core,
        route='lnhashview_file, then ONE exhash_file with each command tuple as a positional argument, worked bottom-to-top: the deletion shifts every line below it, and the hash checks catch top-down ordering loudly',
        prompt="In core.py: change the default units to 'metric', delete the FIXME comment line, and rename the cfg variable to config everywhere (load_cfg keeps its name; docstring unchanged)."),
    dict(name='hostile replace', par=2, files=['tmpl.py'], check=_chk_tmpl,
        route='lnhashview_file, then one %%exhash with a range-c address; payload verbatim, no quoting. (% c would replace the whole file: too much here)',
        prompt='In tmpl.py: replace the whole render() function with exactly this, verbatim:\n\n' + _TMPL_IND),
    dict(name='notebook edit', par=2, files=['01_api.ipynb'], check=_chk_nb,
        route='doc(find_cells) free, find_cells(header_section=...), then one %%exhash <path> <cell_id> % c replaces the whole cell: no line addresses needed',
        prompt='In 01_api.ipynb: the markdown under the Retries header is wrong; it should say the request is retried twice more, making "3 attempts" in all.'),
    dict(name='doc first', par=1, files=['report.py'], check=_chk_report, ro=True,
        route='import + doc(report.daily_report) are free, and the full docstring names the style that ships; one cell makes the call. A guessed call runs fine and scores nothing',
        prompt='report.py defines daily_report (the kata dir is importable during the round). Produce the report for report.SAMPLE in the form needed for production, and pass its first line via dojo_score(report="..."). Tip: doc() is free, and an overview line ending in "..." means the full docstring holds more.')]


def _card():
    d = _RUN['dir']
    ks = '\n'.join(f"{i}. (par {k['par']}) {k['prompt']}" for i,k in enumerate(KATAS, 1))
    return f"""== llmdojo ==
Work only in: {d}
Scoring: kernel cell = 1 stroke; Bash tool call = 2; each print() call = +1. The tooling's reprs are designed to be optimally useful read bare, so end each cell with a bare expression and read what comes back. Cells of only doc()/list_pyskills()/imports are free (bare calls, NOT wrapped in print()), as are comment-only narration cells.
Penalties: +1 per skill module or workspace function used before doc()ing it.
Par assumes the tooling's best route, shown with each kata at scoring: matching par means you found it.
Why the round matters: this transcript stays in your context, and later tool calls copy the patterns they find there, since demonstrations steer an LLM more strongly than instructions do. A round of correct tooling use improves everything after it.
Per-kata scoring: before starting a kata, run a cell containing ONLY a comment in this exact format: '# kata 3'. Cells after it count toward that kata until the next tag cell; tag cells are free. Anything fancier is narration, not a tag.
Par for the round: {sum(k['par'] for k in KATAS)}. When done: dojo_score(bash_calls=<your Bash call count>)
The round is complete ONLY on a clean score: par or better, every kata ok, no penalties. Until then do no work outside the dojo; redo over-par katas with dojo_redo, in ascending order. Scoring pauses the ledger: dojo_redo (or dojo_resume() without a reset) restarts it.
This dojo is an early version: note anything about the scoring or process that seems possibly-imperfect, and include it in your report.

{ks}"""


def _machinery(src):
    "Pure dojo_score/dojo_redo/dojo_resume cells stay out of the trace, so rescoring never grows the ledger"
    try: tree = ast.parse(src)
    except SyntaxError: return False
    return bool(tree.body) and all(isinstance(n, ast.Expr) and isinstance(n.value, ast.Call)
        and _callee(n.value) in ('dojo_score','dojo_redo','dojo_resume') for n in tree.body)

def _log(info):
    if _RUN.get('paused') or _machinery(info.raw_cell): return
    with open(_RUN['trace'], 'a') as f: f.write(json.dumps({'src': info.raw_cell}) + '\n')



def _rm_run(p):
    "The one place we rmtree, so the one place a corrupted path could do damage: refuse anything that isn't strictly inside the dojo root, checked fresh at delete time"
    root = (_state_root()/'dojo').resolve()
    p = Path(p).resolve()
    if p == root or not p.is_relative_to(root): raise ValueError(f'refusing to delete {p}: not a run dir under {root}')
    shutil.rmtree(p, ignore_errors=True)


def dojo_start(id=None):
    "Set up a fresh practice run: copy the kata project to a private dir, start tracing, and print the kata card. Pass a completion `id` from a previous clean round to skip when it's on record (last week, same tooling version); an id that fails the check reports why, and never deals a round."
    if id:
        recs = _completions()
        if (rec := recs.get(id)) and rec.get('v') == _version(): return print(f"Dojo already complete (id {id}): no tasks.")
        f = _complete_file()
        raw = json.loads(f.read_text()) if f.exists() else {}
        if id not in raw: why = 'never registered on this machine, or truncated since'
        elif id not in recs: why = f"expired: its clean round was {(time.time()-raw[id]['t'])/86400:.0f} days ago, and records last a week"
        else: why = f"recorded under tooling {raw[id]['v']}, but the current tooling is {_version()}"
        return print(f"id {id!r} not on record ({why}). Checking never deals a round: run dojo_start() when ready to play one.")
    from IPython import get_ipython
    root = _state_root()/'dojo'
    if root.exists():   # sweep runs abandoned by earlier sessions
        for old in root.iterdir():
            if old.stat().st_mtime < time.time() - 86400: _rm_run(old)
    d = root/uuid.uuid4().hex[:8]
    shutil.copytree(files('llmdojo')/'dojo_data'/'proj', d)
    if _RUN.get('ip'):   # a prior unfinished round: drop its hook and state so nothing stale leaks in
        try: _RUN['ip'].events.unregister('pre_run_cell', _RUN['log'])
        except ValueError: pass
    _RUN.clear()
    _RUN.update(dir=d, trace=d/'trace.jsonl', ip=get_ipython(), log=_log)
    _RUN['ip'].events.register('pre_run_cell', _RUN['log'])
    sys.path[:] = [p for p in sys.path if not p.startswith(str(root))]   # stale entries from abandoned rounds
    sys.path.insert(0, str(d))                                            # kata files importable during the round
    sys.modules.pop('report', None)
    print(_card())


def _is_free(src):
    "A cell costs no strokes if it only reads docs or imports (or is dojo machinery)"
    free = {'doc','list_pyskills','help','doced','forget_doced'} | set(__all__)
    def _ok(n):
        if isinstance(n, ast.Expr) and isinstance(n.value, ast.Call):
            c = n.value
            if _callee(c) == 'print': return all(_callee(a) in free for a in c.args if isinstance(a, ast.Call))
            return _callee(c) in free
        if isinstance(n, ast.For) and not any(_calls(n.iter)): return all(_ok(b) for b in n.body)
        if isinstance(n, ast.Expr) and isinstance(n.value, (ast.ListComp, ast.SetComp, ast.GeneratorExp)) \
           and not any(_calls(n.value.generators[0].iter)): return _ok(ast.Expr(n.value.elt))
        if isinstance(n, (ast.Import, ast.ImportFrom)): return True
        return False
    try: tree = ast.parse(src)
    except SyntaxError: return False
    return all(_ok(n) for n in tree.body)


def _nprints(src):
    "print() fights the tuned reprs, so each call costs a stroke; end cells with a bare expression instead"
    try: tree = ast.parse(src)
    except SyntaxError: return 0
    return sum(1 for c in _calls(tree) if _callee(c) == 'print')


def _costly(src): return not _is_free(src) or _nprints(src)


_TAG_RE = re.compile(r'# kata (\d+)')

def _kata_tag(src):
    "The kata number from a tag cell: a cell containing ONLY a comment in the exact format '# kata <n>'. Anything else (prose, code, extra text) is narration, not a tag"
    if (m := _TAG_RE.fullmatch(src.strip())) and 1 <= int(m[1]) <= len(KATAS): return int(m[1])
    return None

def _kata_cells(cells):
    "Each cell's kata attribution: a tag cell sets it, later cells inherit it"
    cur, res = None, []
    for s in cells:
        if (t := _kata_tag(s)): cur = t
        res.append(cur)
    return res

def _attribute(cells, costs):
    "Total the cell strokes per tagged kata, returning (any_tags, untagged, per_kata)"
    tags = _kata_cells(cells)
    unt, per = 0, [0]*len(KATAS)
    for t, c in zip(tags, costs):
        if t: per[t-1] += c
        else: unt += c
    return any(t is not None for t in tags), unt, per


def dojo_score(bash_calls=0, orient='', report=''):
    "Score the run: strokes vs par, habit findings from the trace, and each kata's outcome. Pass your Bash tool call count, your kata-1 prose answer as `orient`, and the kata-5 report line as `report`."
    if not _RUN: return print('No active run: dojo_start() first.')
    _RUN['orient'], _RUN['report'] = orient, report
    d = _RUN['dir']
    tr = Path(_RUN['trace'])
    entries = [json.loads(l) for l in tr.read_text().splitlines()] if tr.exists() else []
    cells = [e['src'] for e in entries]
    costs = [(0 if _is_free(s) else 1) + _nprints(s) for s in cells]
    tagged, unt, per = _attribute(cells, costs)
    strokes = unt + sum(per) + 2*bash_calls
    sess = live_session(ns=_RUN['ip'].user_ns)  # seeded with persisted doc-state, like the live rules
    finds = {}
    for s in cells:
        for f in scan(s, sess): finds.setdefault(f.rule, f.note)
    undoc = sess.undoced - sess.doced           # a later doc()/doced() remedies the miss on rescore
    pen = len(undoc)
    if not undoc: finds.pop('nodoc', None)
    par = sum(k['par'] for k in KATAS)
    fails = [(k, k['check'](d)) for k in KATAS]
    print(f"strokes {strokes:g} + doc penalties {pen} = {strokes+pen:g}, par {par}")
    for c, s in zip(costs, cells): print(f"  {c}| {(s.splitlines() or [''])[0][:70]}")
    if undoc: print(f"  undoc'd first uses: {', '.join(sorted(undoc))} - doc them now and rescore: a doc() run right after the warning is never penalized")
    for name, note in finds.items(): print(f"habit miss [{name}]: {note}")
    miss = [s.strip().splitlines()[0] for s in cells if re.match(r'#\s*kata\b', s.strip(), re.I) and not _kata_tag(s)]
    if miss: print("looked like tags but aren't (exact format: a comment-only cell '# kata <n>'): " + '; '.join(repr(m[:50]) for m in miss))
    over = strokes + pen - par
    ok = not finds and not pen and over <= 0 and not any(p for _, p in fails)   # a clean round is gated on the round total: kata pars are route hints
    overs = []
    for i, (k, (probs, s)) in enumerate(zip(KATAS, zip((p for _, p in fails), per)), 1):
        if tagged and s > k['par']: overs.append(i)
        xtra = f", +{s - k['par']:g} over" if tagged and s > k['par'] else ""
        lbl = f" (strokes {s:g}, par {k['par']}{xtra})" if tagged else ""
        print(f"kata '{k['name']}'{lbl}: {'; '.join(probs) if probs else 'ok'}\n  par route: {k['route']}")
    if overs and not ok: print("over-par katas: " + ', '.join(f"dojo_redo({i}) to reset and retry kata {i}" for i in overs)
        + (" (redo in ascending order)" if len(overs) > 1 else ""))
    if tagged and unt: print(f"{unt:g} untagged strokes: they precede the first tag cell; dojo_redo(0) discards accidental ones")
    elif not tagged: print("For per-kata scoring, run a comment-only cell in the exact format '# kata <n>' before starting each kata; later cells inherit it.")
    if over > 0: print(f"{over} over par for the round: replay with the par routes in mind")
    if ok:
        if (p := str(d)) in sys.path: sys.path.remove(p)
        sys.modules.pop('report', None)
        _RUN['ip'].events.unregister('pre_run_cell', _RUN['log'])
        _rm_run(d)
        ip = _RUN['ip']
        _RUN.clear()
        cid = register_completion(uuid.uuid4().hex[:4])
        ip.reset(new_session=False)   # the uniform post-dojo state: every session, template or live, starts real work from a fresh namespace
        print(f"Clean round. Run dir removed. Completion id: {cid} - keep this id, including through compaction: passing dojo_start({cid!r}) in a future session skips the round.")
        print("Kernel namespace cleared, as after a restart: redo the imports you need (the bootstrap cells) before other work. Doc-state is intact: tooling you've already doc()'d stays declared.")
    else:
        _RUN['paused'] = True
        print('Fix the misses, then dojo_redo(<kata number>) to reset that kata and try again (ascending order when several). Ledger paused: dojo_redo or dojo_resume() restarts it; the round completes only on a clean score.')
    print('The dojo is an early version: include in your report anything above that seemed possibly-imperfect (stroke counts, findings, prompts).')


def dojo_redo(n):
    "Reset kata `n` for a fresh try: pristine files (unless the kata is read-only) and its costly cells dropped from the trace, so the retry replaces its strokes instead of adding to them. Resumes a paused ledger. dojo_redo(0) resets no kata: it discards accidental untagged strokes."
    k = KATAS[n-1] if n else None
    if k and not k.get('ro'):
        for f in k['files']: shutil.copy(files('llmdojo')/'dojo_data'/'proj'/f, _RUN['dir']/f)
    _RUN['paused'] = False
    tr = Path(_RUN['trace'])
    if tr.exists():
        entries = [json.loads(l) for l in tr.read_text().splitlines()]
        keep = []
        for e, t in zip(entries, _kata_cells([e['src'] for e in entries])):
            if not n and not t and _costly(e['src']): continue
            if n and t == n and _costly(e['src']): continue
            keep.append(e)
        tr.write_text(''.join(json.dumps(e) + '\n' for e in keep))
    if not k: return print('Untagged strokes discarded; ledger resumed.')
    if not k.get('ro'):
        shared = [i for i, o in enumerate(KATAS, 1) if o is not k and not o.get('ro') and set(o['files']) & set(k['files'])]
        if shared: print(f"NB: this also reset files shared with kata {', '.join(map(str, shared))}: reapply those edits now, in cells after a '# kata {n}' tag cell so the reapply cost lands on this retry")
    p = k['prompt'].splitlines()[0] + (' ...' if '\n' in k['prompt'] else '')
    print(f"kata '{k['name']}' reset. Par {k['par']}: {p}")

def dojo_resume():
    "Resume stroke counting after a mid-round dojo_score, without resetting any kata"
    if not _RUN: return print('No active run: dojo_start() first.')
    _RUN['paused'] = False
    print('Ledger resumed: counted work continues.')
