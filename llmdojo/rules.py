"""Best-practice detection rules shared by the live cell inspectors and the dojo scorer. Each note teaches exactly one route, since agents reproduce whatever patterns their context shows them."""
import ast,importlib.util,os,re,sys,tokenize
from pathlib import Path
from io import StringIO
from fastcore.basics import store_attr
from fastcore.xdg import xdg_state_home
from IPython.core.error import InputRejected

class RuleBlock(InputRejected):
    "Raised to deliberately block a cell; clikernel's kernel-side inspector hook propagates any `InputRejected`, and everything else fails open"

def _state_root():
    if d := os.environ.get("LLMDOJO_STATE_DIR"): return Path(d).expanduser()
    return xdg_state_home()/'llmdojo'

_TOOLING = {'lnhashview','lnhashview_file','lnhashview_cell','lnhashview_cells','rg','nbrg','fd',
    'find_msgs','summary_dlg','view_dlg','view_msg','view_msgs','view_file','view_cell','doc','info_md'}


class Session:
    "Cross-cell rule state: the namespace for resolving calls"
    def __init__(self, ns=None):
        self.ns = {} if ns is None else ns


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
    "Top-level command-tuple nodes of an exhash/file_exhash/cell_exhash call"
    if _callee(c) == 'exhash':
        a = c.args[1] if len(c.args) > 1 else None
        return a.elts if isinstance(a, (ast.List, ast.Tuple)) and any(isinstance(e, ast.Tuple) for e in a.elts) else []
    return c.args[2 if _callee(c) == 'cell_exhash' else 1:]

def _tuple_payload(tree, src, sess):
    "A lone constant a/i/c payload that is long or contains quotes/backslashes belongs in a %%exhash cell; multi-command calls are exempt, since the one-command magic can't express them atomically"
    for c in _calls(tree):
        if _callee(c) not in ('exhash','file_exhash','cell_exhash'): continue
        cmds = _cmds(c)
        if len(cmds) != 1 or not isinstance(cmds[0], ast.Tuple): continue
        n = cmds[0]
        if len(n.elts) < 3: continue
        cmd,payload = n.elts[1],n.elts[2]
        if not (isinstance(cmd, ast.Constant) and cmd.value in ('a','i','c')): continue
        if not (isinstance(payload, ast.Constant) and isinstance(payload.value, str)): continue
        if len(payload.value) > 20 or any(ch in payload.value for ch in '\'"\\'): return True


def _s_repls(tree):
    "String-constant replacement fields of s-commands in exhash calls"
    for c in _calls(tree):
        if _callee(c) not in ('exhash','file_exhash','cell_exhash'): continue
        for n in ast.walk(c):
            if not (isinstance(n, ast.Tuple) and len(n.elts) >= 4): continue
            if not (isinstance(n.elts[1], ast.Constant) and n.elts[1].value == 's'): continue
            if isinstance(n.elts[3], ast.Constant) and isinstance(n.elts[3].value, str): yield n.elts[3].value


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
_EXEMPT = _BOOT | {'dojo_start','dojo_score','dojo_redo','dojo_resume','forget_dojo'}   # the prescribed interfaces are called bare by design

def _piecemeal(tree, src, sess):
    for n in ast.walk(tree):
        if isinstance(n, ast.ImportFrom) and n.module and n.names[0].name != '*':
            if {a.name for a in n.names} <= _BOOT: continue   # bootstrap lines are piecemeal by design
            if n.module.endswith('.skill'): return True
            try: found = importlib.util.find_spec(f'{n.module.split(".")[0]}.skill')
            except ModuleNotFoundError: found = None
            if found: return True


def _shell_escape(tree, src, sess):
    for n in ast.walk(tree):
        if isinstance(n, ast.Import) and any(a.name.split('.')[0] == 'subprocess' for a in n.names): return True
        if isinstance(n, ast.ImportFrom) and (n.module or '').split('.')[0] == 'subprocess': return True
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.func.attr in ('system','popen'): return True


def _sys_path(tree, src, sess):
    for c in _calls(tree):
        f = c.func
        if isinstance(f, ast.Attribute) and f.attr in ('insert','append') and isinstance(f.value, ast.Attribute) \
           and f.value.attr == 'path' and isinstance(f.value.value, ast.Name) and f.value.value.id == 'sys': return True


RULES = [
    Rule('read_file', 'Read files with lnhashview_file (for editing) or view_file(nums=False).', _read_file),
    Rule('big_replace', 'Replace a whole cell or file with %%exhash <path> [<cell_id>] % c; an inner region with a range-c address.', _big_replace),
    Rule('cell_str_replace', 'Edit notebook cells with %%exhash <path> <cell_id>.', _cell_str_replace),
    Rule('rawstr', 'Write non-trivial strings as r""" raw strings; %%exhash text needs no escaping at all.', _rawstr),
    Rule('hashcalc', 'exhash addresses come only from a fresh lnhashview; never compute them.', _hashcalc),
    Rule('tuple_payload', 'Apply a/i/c text with the %%exhash magic: it needs no quoting or escaping.', _tuple_payload),
    Rule('s_newline', r'A 2-char \n in an s-replacement stays literal text: use a real newline in the string.', _s_newline),
    Rule('s_long', 'Use a c command (%%exhash <addr> c) for an s-replacement over 120 chars, except when the line is much longer still.', _s_long),
    Rule('postproc', "Show tooling results bare; narrow with the tool's own parameters.", _postproc),
    Rule('run_magic', 'Invoke magics directly with % syntax.', _run_magic, raw=True),
    Rule('piecemeal', 'Load skill modules whole: from <pkg>.skill import *, after doc(<pkg>.skill).', _piecemeal),
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


def make_inspector():
    "A clikernel cell inspector applying `RULES` live: blocking rules raise, the rest prepend a one-line note"
    sess = Session()
    def _inspect(tree, src):
        from IPython import get_ipython
        sess.ns = getattr(get_ipython(), 'user_ns', {}) or {}
        out = []
        for f in scan(src, sess):
            r = next(r for r in RULES if r.name == f.rule)
            if r.block: raise RuleBlock(f'{f.note} (This check is an early version: if the block seems wrong here, stop and tell your user.)')
            if not os.environ.get('CLIKERNEL_QUIET'): out.append(f'<{r.tag}>\n{f.note}\n</{r.tag}>\n')
        return ''.join(out)
    return _inspect
