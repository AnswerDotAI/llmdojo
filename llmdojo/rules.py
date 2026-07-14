"""Best-practice detection rules shared by the live cell inspectors and the dojo scorer. Each note teaches exactly one route, since agents reproduce whatever patterns their context shows them.

Doc-state persists per host conversation: if the conversation survived a kernel restart and the relevant `doc()` output is still visible, call `doced(name1, name2, ...)` to restore doc state without reprinting it; after context compaction, call `forget_doced()` and read the docs again."""
import ast,importlib.util,json,os,re,sys,time,tokenize
from pathlib import Path
from io import StringIO
from fastcore.basics import store_attr
from fastcore.xdg import xdg_state_home
from clikernel.base import RuleBlock

def _state_root():
    if d := os.environ.get("LLMDOJO_STATE_DIR"): return Path(d).expanduser()
    return xdg_state_home()/'llmdojo'

_TOOLING = {'lnhashview','lnhashview_file','lnhashview_cell','lnhashview_cells','rg','nbrg','fd',
    'find_cells','summary_nb','view_nb','view_cell','view_cells','file_view','doc','info_md'}


class Session:
    "Cross-cell rule state: the namespace for resolving calls, and names already doc'd"
    def __init__(self, ns=None):
        self.ns = {} if ns is None else ns
        self.doced,self.undoced = set(),set()


class Finding:
    def __init__(self, rule, note): self.rule,self.note = rule,note
    def __repr__(self): return f'{self.rule}: {self.note}'


class Rule:
    def __init__(self, name, note, fn, block=False, raw=False, tag='note'): store_attr()




def _calls(tree):
    for n in ast.walk(tree):
        if isinstance(n, ast.Call): yield n


def _callee(c): return c.func.id if isinstance(c.func, ast.Name) else None


_DATA_EXTS = ('.json','.jsonl','.ndjson','.csv','.tsv','.log')

def _textpath(node):
    "A string constant under `node` recognisably names a non-data file: only then is a view-note earned"
    return any(isinstance(n, ast.Constant) and isinstance(n.value, str) and '.' in n.value
        and not n.value.lower().endswith(_DATA_EXTS) for n in ast.walk(node))


def _is_read(c):
    "A read_text()/open().read() call on a recognisably-named non-data file"
    if not (isinstance(c, ast.Call) and isinstance(c.func, ast.Attribute)): return False
    if c.func.attr == 'read_text': return _textpath(c.func.value)
    return c.func.attr == 'read' and isinstance(c.func.value, ast.Call) and _callee(c.func.value) == 'open' and _textpath(c.func.value)


def _read_file(tree, src, sess):
    "Only a displayed read (bare expression or print) earns the note: a parser-bound or assigned read never enters context"
    for n in ast.walk(tree):
        if isinstance(n, ast.Expr):
            v = n.value
            if _is_read(v): return True
            if isinstance(v, ast.Call) and _callee(v) == 'print' and any(_is_read(a) for a in v.args): return True


def _big_replace(tree, src, sess):
    for c in _calls(tree):
        if _callee(c) in ('file_replace_lines','cell_replace_lines'):
            for k in c.keywords:
                if k.arg == 'new_content' and isinstance(k.value, ast.Constant) and str(k.value.value).count('\n') >= 6: return True


def _cell_str_replace(tree, src, sess):
    "Only the obvious single-cell form (a literal id that isn't 'all'): batch replaces over many cells are sanctioned"
    for c in _calls(tree):
        if _callee(c) != 'cell_str_replace': continue
        cid = c.args[0] if c.args else next((k.value for k in c.keywords if k.arg == 'id'), None)
        if isinstance(cid, ast.Constant) and isinstance(cid.value, str) and cid.value != 'all': return True


def _rawstr(tree, src, sess):
    try: toks = list(tokenize.generate_tokens(StringIO(src).readline))
    except tokenize.TokenizeError: return
    for t in toks:
        if t.type == tokenize.STRING:
            m = re.match(r"""([A-Za-z]*)('''|\"\"\")""", t.string)
            if m and 'r' not in m[1].lower() and '\\' in t.string: return True


def _hashcalc(tree, src, sess): return any(_callee(c) in ('lnhash','line_hash') for c in _calls(tree))


def _cmds(c):
    "Top-level command-tuple nodes of an exhash/exhash_file/exhash_cell call"
    if _callee(c) == 'exhash':
        a = c.args[1] if len(c.args) > 1 else None
        return a.elts if isinstance(a, (ast.List, ast.Tuple)) and any(isinstance(e, ast.Tuple) for e in a.elts) else []
    return c.args[2 if _callee(c) == 'exhash_cell' else 1:]

def _tuple_payload(tree, src, sess):
    "A lone constant a/i/c payload that is long or contains quotes/backslashes belongs in a %%exhash cell; multi-command calls are exempt, since the one-command magic can't express them atomically"
    for c in _calls(tree):
        if _callee(c) not in ('exhash','exhash_file','exhash_cell'): continue
        cmds = _cmds(c)
        if len(cmds) != 1 or not isinstance(cmds[0], ast.Tuple): continue
        n = cmds[0]
        if len(n.elts) >= 3 \
           and isinstance(n.elts[1], ast.Constant) and n.elts[1].value in ('a','i','c') \
           and isinstance(n.elts[2], ast.Constant) and isinstance(n.elts[2].value, str) \
           and (len(n.elts[2].value) > 20 or any(ch in n.elts[2].value for ch in '\'"\\')): return True


def _s_repls(tree):
    "String-constant replacement fields of s-commands in exhash calls"
    for c in _calls(tree):
        if _callee(c) not in ('exhash','exhash_file','exhash_cell'): continue
        for n in ast.walk(c):
            if isinstance(n, ast.Tuple) and len(n.elts) >= 4 \
               and isinstance(n.elts[1], ast.Constant) and n.elts[1].value == 's' \
               and isinstance(n.elts[3], ast.Constant) and isinstance(n.elts[3].value, str):
                yield n.elts[3].value


def _s_newline(tree, src, sess): return any('\\n' in r for r in _s_repls(tree))


def _s_long(tree, src, sess): return any(len(r) > 120 for r in _s_repls(tree))



def _postproc(tree, src, sess):
    for n in ast.walk(tree):
        if isinstance(n, ast.Attribute) and isinstance(n.value, ast.Call) and _callee(n.value) in _TOOLING \
           and n.attr in ('splitlines','split','join'): return True
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.func.attr == 'join' \
           and isinstance(n.func.value, ast.Constant) \
           and any(_callee(c) in _TOOLING for a in n.args for c in _calls(a)): return True


def _run_magic(tree, src, sess):
    # raw-source rule: in the transformed cell every magic becomes run_*_magic, so only literal raw uses count
    return 'run_line_magic' in src or 'run_cell_magic' in src


_BOOT = {'doc','list_pyskills'}   # live at the package top level, so the bootstrap line imports them piecemeal by design
_EXEMPT = _BOOT | {'dojo_start','dojo_score','dojo_redo','dojo_resume','doced','forget_doced','forget_dojo'}   # the prescribed interfaces are called bare by design

def _piecemeal(tree, src, sess):
    for n in ast.walk(tree):
        if isinstance(n, ast.ImportFrom) and n.module and n.names[0].name != '*':
            if {a.name for a in n.names} <= _BOOT | {'doced','forget_doced'}: continue   # bootstrap and session-reset lines are piecemeal by design
            if n.module.endswith('.skill'): return True
            try: found = importlib.util.find_spec(f'{n.module.split(".")[0]}.skill')
            except ModuleNotFoundError: found = None
            if found: return True


def _needs_doc(o):
    "Editable-install tooling gets doc() before first use; fastcore is ambient vocabulary, and __main__ was authored in-session"
    m = getattr(o, '__module__', None) or ''
    if m == '__main__' or m.split('.')[0] == 'fastcore': return False
    f = str(getattr(sys.modules.get(m), '__file__', None) or '')   # some loaders set __file__ to a Path
    return bool(f) and 'site-packages' not in f and not f.startswith((sys.prefix, sys.base_prefix))


def _docnames(s):
    "Both spellings of a doc'd name, so `doc(mod.func)` also registers the bare name a call site uses"
    return {s, s.rsplit('.', 1)[-1]}


def _nodoc(tree, src, sess):
    for c in _calls(tree):                          # record doc() reads first, so doc-then-call in one cell is quiet
        if _callee(c) == 'doc': sess.doced.update(x for a in c.args for x in _docnames(ast.unparse(a)))
        if _callee(c) == 'doced': sess.doced.update(x for a in c.args for x in _docnames(a.value if isinstance(a, ast.Constant) else ast.unparse(a)))
    for n in ast.walk(tree):                        # doc(f) looped over literal names docs each element
        if isinstance(n, (ast.For, ast.ListComp, ast.SetComp, ast.GeneratorExp)):
            g = n if isinstance(n, ast.For) else n.generators[0]
            if isinstance(g.target, ast.Name) and isinstance(g.iter, (ast.Tuple, ast.List)) \
               and any(_callee(c) == 'doc' and any(isinstance(a, ast.Name) and a.id == g.target.id for a in c.args) for c in _calls(n)):
                sess.doced.update(x for e in g.iter.elts for x in _docnames(ast.unparse(e)))
    new = {nm for c in _calls(tree) if (nm := _callee(c)) and not nm.startswith('_') and nm not in _EXEMPT and nm not in sess.doced
        and callable(sess.ns.get(nm)) and _needs_doc(sess.ns[nm])}
    sess.undoced |= new
    return ', '.join(sorted(new)) if new else None


def _shell_escape(tree, src, sess):
    for n in ast.walk(tree):
        if isinstance(n, ast.Import) and any(a.name == 'subprocess' for a in n.names): return True
        if isinstance(n, ast.ImportFrom) and n.module == 'subprocess': return True
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.func.attr in ('system','popen'): return True


def _sys_path(tree, src, sess):
    for c in _calls(tree):
        f = c.func
        if isinstance(f, ast.Attribute) and f.attr in ('insert','append') and isinstance(f.value, ast.Attribute) \
           and f.value.attr == 'path' and isinstance(f.value.value, ast.Name) and f.value.value.id == 'sys': return True


RULES = [
    Rule('read_file', 'Read files with lnhashview_file.', _read_file),
    Rule('big_replace', 'Replace a whole cell or file with %%exhash <path> [<cell_id>] % c; an inner region with a range-c address.', _big_replace),
    Rule('cell_str_replace', 'Edit notebook cells with %%exhash <path> <cell_id>.', _cell_str_replace),
    Rule('rawstr', 'Write non-trivial strings as r""" raw strings; %%exhash payloads need no escaping at all.', _rawstr),
    Rule('hashcalc', 'exhash addresses come only from a fresh lnhashview; never compute them.', _hashcalc),
    Rule('tuple_payload', 'Apply a/i/c payloads with the %%exhash magic: its payload needs no quoting or escaping.', _tuple_payload),
    Rule('s_newline', r'A 2-char \n in an s-replacement stays literal text: use a real newline in the string.', _s_newline),
    Rule('s_long', 'An s-replacement over 120 chars rewrites the line: use a c command (%%exhash <addr> c) instead.', _s_long),
    Rule('postproc', "Show tooling results bare; narrow with the tool's own parameters.", _postproc),
    Rule('run_magic', 'Invoke magics directly with % syntax.', _run_magic, raw=True),
    Rule('piecemeal', 'Load skill modules whole: from <pkg>.skill import *, after doc(<pkg>.skill).', _piecemeal),
    Rule('nodoc', 'Rule violation: `{0}` docs not read before first use. Run `doc({0})` as your next tool call.', _nodoc, tag='warn'),
    Rule('shell_escape', 'Run shell commands with the Bash tool.', _shell_escape, block=True),
    Rule('sys_path', 'Never modify sys.path; stop and ask the user.', _sys_path, block=True)]


_tm = None

def _transform(src):
    "IPython-transform `src` so magics and `!` escapes parse; the raw text comes back if transformation fails"
    global _tm
    if _tm is None:
        from IPython.core.inputtransformer2 import TransformerManager
        _tm = TransformerManager()
    try: return _tm.transform_cell(src)
    except Exception: return src


def scan(src, sess):
    "Run every rule on cell `src` (IPython-transformed, except raw-source rules), returning all `Finding`s"
    tsrc = _transform(src)
    try: tree = ast.parse(tsrc)
    except SyntaxError: return []
    out = []
    for r in RULES:
        if (res := r.fn(tree, src if r.raw else tsrc, sess)):
            out.append(Finding(r.name, r.note.format(res) if isinstance(res, str) else r.note))
    return out


_LIVE = None

_HOST = None

def _resolve_host():
    "The stable host conversation id: the most recent transcript for this project survives worker restarts AND resumes; fall back to the per-spawn session id, then our parent pid"
    if (pd := os.environ.get('CLAUDE_PROJECT_DIR')):
        d = Path.home()/'.claude'/'projects'/re.sub(r'[^A-Za-z0-9]', '-', pd)
        try: return max(d.glob('*.jsonl'), key=lambda p: p.stat().st_mtime).stem
        except ValueError: pass
    return os.environ.get('CLAUDE_CODE_SESSION_ID') or os.getppid()

def _host_session():
    "Resolved once per worker: at spawn, the spawning conversation's transcript is the freshest"
    global _HOST
    if _HOST is None: _HOST = _resolve_host()
    return _HOST

def _doced_file():
    "One doc-state file per host conversation (see `_resolve_host`)"
    d = _state_root()/'doced'
    d.mkdir(parents=True, exist_ok=True)
    return d/f'{_host_session()}.json'

def _save_doced(sess):
    "Persist the doc-state, sweeping abandoned sessions' files after a day"
    f = _doced_file()
    for g in f.parent.iterdir():
        if g.stat().st_mtime < time.time() - 86400: g.unlink(missing_ok=True)
    f.write_text(json.dumps(sorted(sess.doced)))

def _load_doced(sess):
    "Re-read the persisted doc-state: the file is the source of truth, and other processes (the compaction hook) write it too"
    sf = _doced_file()
    sess.doced = set(json.loads(sf.read_text())) if sf.exists() else set()

def live_session(ns=None):
    "A Session seeded from the persisted doc-state file: the same record the live rules keep"
    sess = Session(ns=ns)
    _load_doced(sess)
    return sess

def doced(*names):
    "Declare tooling functions (bare symbols or name strings) whose docs are verbatim in your context (a host restart where the conversation survived): doc-state is restored without re-reading. With no names, show the current set. If you cannot see a function's docs in context, read doc(f) instead."
    global _LIVE
    if _LIVE is None: _LIVE = Session()
    _load_doced(_LIVE)
    if not names: return sorted(_LIVE.doced)
    _LIVE.doced.update(getattr(n, '__name__', n) for n in names)
    _save_doced(_LIVE)

def forget_doced():
    "Reset the doc-state record (e.g. after context compaction): every tooling function needs a fresh doc(f) before its next use."
    global _LIVE
    if _LIVE is None: _LIVE = Session()
    _LIVE.doced.clear()
    _save_doced(_LIVE)


def make_inspector():
    "A clikernel cell inspector applying `RULES` live: blocking rules raise, the rest prepend a one-line note"
    global _LIVE
    sess = live_session()
    _LIVE = sess
    def _inspect(tree, src):
        from IPython import get_ipython
        sess.ns = getattr(get_ipython(), 'user_ns', {}) or {}
        _load_doced(sess)
        n0 = len(sess.doced)
        fs = scan(src, sess)
        if len(sess.doced) != n0: _save_doced(sess)
        out = []
        for f in fs:
            r = next(r for r in RULES if r.name == f.rule)
            if r.block: raise RuleBlock(f'{f.note} (This check is an early version: if the block seems wrong here, stop and tell your user.)')
            out.append(f'<{r.tag}>\n{f.note}\n</{r.tag}>\n')
        return ''.join(out)
    return _inspect
