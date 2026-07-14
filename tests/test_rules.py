from llmdojo.rules import scan, Session

def fires(src, name, sess=None): return any(f.rule == name for f in scan(src, sess or Session()))


def test_rules():
    "Each rule fires on its anti-pattern and stays quiet on the blessed route."
    # read_text/open().read on a recognisable text file -> lnhashview
    assert fires("Path('core.py').read_text()", "read_file")
    assert fires("open('notes.txt').read()", "read_file")
    assert not fires("lnhashview_file(p)", "read_file")
    assert not fires("p.read_text()", "read_file")            # unrecognisable path: variables stay quiet
    assert not fires("open(p).read()", "read_file")
    assert not fires("open(p, 'r').read()", "read_file")      # a mode string is not a filename
    assert not fires("Path('trace.jsonl').read_text()", "read_file")  # data files: a hashed line view can't help
    assert not fires("open(d/'rows.csv').read()", "read_file")
    assert fires("(d/'core.py').read_text()", "read_file")
    assert fires("print(Path('a.py').read_text())", "read_file")                  # printed is displayed
    assert not fires("yaml.safe_load(Path('wf.yaml').read_text())", "read_file")  # parser-bound: never enters context
    assert not fires("src = Path('a.py').read_text()", "read_file")               # assigned: consumption unknown, stay quiet

    # big replace_lines payload -> delete + %%exhash a
    big = "x = 1\n" * 9
    assert fires(f"file_replace_lines(p, new_content={big!r})", "big_replace")
    assert fires(f"cell_replace_lines(cid, new_content={big!r})", "big_replace")
    assert not fires("file_replace_lines(p, new_content='x = 1')", "big_replace")

    # single-cell cell_str_replace -> %%exhash path cellid; batch replaces (id list / 'all') are sanctioned
    assert fires("cell_str_replace('ab12', 'a', 'b', fname=p)", "cell_str_replace")
    assert not fires("cell_str_replace(['ab12','cd34'], 'a', 'b')", "cell_str_replace")
    assert not fires("cell_str_replace('all', 'a', 'b')", "cell_str_replace")
    assert not fires("cell_str_replace(cids, 'a', 'b')", "cell_str_replace")   # variables unknowable: stay quiet

    # non-raw triple-quote containing backslashes -> r-string
    assert fires('s = """a\\nb"""', "rawstr")
    assert not fires('s = r"""a\\nb"""', "rawstr")
    assert not fires('s = """plain text"""', "rawstr")

    # computing exhash addresses -> views only
    assert fires("addr = lnhash(3, line)", "hashcalc")
    assert fires("line_hash(s)", "hashcalc")

    # post-processing tooling results -> bare repr / tool params
    assert fires("'\\n'.join(lnhashview_file(p))", "postproc")
    assert fires("rg('x', p).splitlines()[:5]", "postproc")
    assert not fires("lnhashview_file(p)", "postproc")

    # programmatic magic invocation -> % syntax
    assert fires("get_ipython().run_line_magic('nbrun', 'abc')", "run_magic")
    assert not fires("%nbrun abc", "run_magic")                  # a real magic is the blessed route

    # tuple a/i/c payloads -> %%exhash magic (short quote-free payloads tolerated)
    assert fires("exhash_file(p, (a, 'c', 'a longer replacement line here'))", "tuple_payload")
    assert fires('exhash_file(p, (a, "a", "it\'s"))', "tuple_payload")             # quote in payload
    assert fires("exhash_cell(p, cid, (a, 'i', 'x = \\\\n'))", "tuple_payload")    # backslash in payload
    assert not fires("exhash_file(p, (a, 'c', 'metric'))", "tuple_payload")        # short one-worder: fine
    assert not fires("exhash_file(p, (a, 's', 'longer than twenty chars ok'))", "tuple_payload")  # s is not a payload command
    assert not fires("exhash_file(p, (a, 'c', body))", "tuple_payload")            # variables unknowable: stay quiet
    assert not fires("exhash_file(p, (a, 'd'), (b, 'c', 'a longer replacement line here'))", "tuple_payload")  # multi-command batch: the one-command magic can't express it atomically
    assert not fires("exhash_cell(p, cid, (a, 's', 'x', 'y'), (b, 'i', 'it\'s a long insertion here'))", "tuple_payload")
    assert fires("exhash_cell(p, cid, (a, 'c', 'a longer replacement line here'))", "tuple_payload")  # single command: the magic is strictly better
    assert fires("exhash(t, [(a, 'c', 'a longer replacement line here')])", "tuple_payload")           # one command in a list works the same

    # literal \n in an s-replacement -> real newline; oversized s-replacement -> c command
    assert fires(r"exhash_file(p, ('1|aa|', 's', 'x', r'a\nb'))", "s_newline")     # 2-char \n stays literal: a mistake
    assert not fires(r"exhash_file(p, ('1|aa|', 's', 'x', 'a\nb'))", "s_newline")  # real newline: intended multiline
    assert not fires(r"exhash_file(p, ('1|aa|', 's', r'x\n', 'y'))", "s_newline")  # pattern field: regex \n is meaningful
    assert fires(f"exhash_file(p, ('1|aa|', 's', 'x', {'y'*121!r}))", "s_long")
    assert not fires(f"exhash_file(p, ('1|aa|', 's', 'x', {'y'*120!r}))", "s_long")

    # blockers
    assert fires("import subprocess", "shell_escape")
    assert fires("os.system('ls')", "shell_escape")
    assert fires("!ls", "shell_escape")                          # `!` escapes are seen via the transformed cell
    assert fires("%nbrun ab12\nPath('f.py').read_text()", "read_file")  # rules still run on cells containing magics
    assert fires("sys.path.insert(0, 'x')", "sys_path")
    assert fires("sys.path.append('x')", "sys_path")


def test_session_rules(monkeypatch):
    "Cross-cell rules: piecemeal skill imports, doc-before-first-call, and re-nagging on every miss."
    s = Session()
    assert fires("from rgapi import rg", "piecemeal", s)          # rgapi has a .skill module
    assert not fires("from rgapi.skill import *", "piecemeal", s)
    assert not fires("from pathlib import Path", "piecemeal", s)  # no pathlib.skill: fine
    assert not fires("from pyskills import list_pyskills, doc", "piecemeal", s)  # the blessed bootstrap line
    assert not fires("from llmdojo.rules import doced, forget_doced", "piecemeal", s)  # the prescribed session-reset line

    # doc(f) before first call: rg resolves to an editable-install function in this session
    import rgapi.skill  # ensure resolvable
    ns = {"rg": rgapi.skill.rg}
    assert fires("rg('x', '.')", "nodoc", Session(ns=ns))
    s3 = Session(ns=ns)
    assert not fires("doc(rg)", "nodoc", s3)
    assert not fires("rg('x', '.')", "nodoc", s3)                 # doc'd first: quiet
    notes = [f.note for f in scan("rg('x', '.')", Session(ns=ns))]
    assert any('doc(rg)' in n for n in notes)                      # the note names the specific function
    assert not fires("len('abc')", "nodoc", Session(ns=ns))       # stdlib: quiet
    assert not fires("_helper()", "nodoc", Session(ns={"_helper": rgapi.skill.rg}))  # private names are internals, not curated API
    import fastcore.basics
    assert not fires("store_attr()", "nodoc", Session(ns={"store_attr": fastcore.basics.store_attr}))  # fastcore is ambient vocabulary, not tooling
    import llmdojo.dojo as dj
    assert not fires("dojo_score()", "nodoc", Session(ns={"dojo_score": dj.dojo_score}))  # the dojo interface is the blessed route
    # __main__ functions were authored in-session: never need doc(), even when a Path __file__ leaks into the namespace
    import sys, types
    from pathlib import Path
    fake_main = types.ModuleType('__main__'); fake_main.__file__ = Path('/tmp/proj/nb.py')
    monkeypatch.setitem(sys.modules, '__main__', fake_main)
    def mainfn(): pass
    mainfn.__module__ = '__main__'
    assert not fires("mainfn()", "nodoc", Session(ns={"mainfn": mainfn}))
    # exotic loaders can set any module's __file__ to a Path: coerced, not crashed
    fakemod = types.ModuleType('fakemod'); fakemod.__file__ = Path('/tmp/proj/fakemod.py')
    monkeypatch.setitem(sys.modules, 'fakemod', fakemod)
    def toolfn(): pass
    toolfn.__module__ = 'fakemod'
    assert fires("toolfn()", "nodoc", Session(ns={"toolfn": toolfn}))

    # doc(f) in a loop or comprehension over literal names docs each of them
    s5 = Session(ns={"rg": rgapi.skill.rg, "fd": rgapi.skill.fd})
    assert not fires("for f in (rg, fd): print(doc(f))", "nodoc", s5)
    assert not fires("rg('x', '.')", "nodoc", s5)
    assert not fires("fd('.')", "nodoc", s5)
    s6 = Session(ns={"rg": rgapi.skill.rg, "fd": rgapi.skill.fd})
    assert not fires("[doc(f) for f in (rg, fd)]", "nodoc", s6)
    assert not fires("rg('x', '.')", "nodoc", s6)

    # doc(mod.func) registers the bare name the call site uses
    s10 = Session(ns={"rg": rgapi.skill.rg})
    assert not fires("doc(rgapi.skill.rg)", "nodoc", s10)
    assert not fires("rg('x', '.')", "nodoc", s10)
    s11 = Session(ns={"rg": rgapi.skill.rg, "fd": rgapi.skill.fd})
    assert not fires("for f in (rgapi.skill.rg, fd): doc(f)", "nodoc", s11)
    assert not fires("rg('x', '.')\nfd('.')", "nodoc", s11)

    # re-nag: findings repeat on every offending cell until the habit is fixed
    s4 = Session()
    assert fires("Path('a.py').read_text()", "read_file", s4)
    assert fires("Path('b.py').read_text()", "read_file", s4)
    s7 = Session(ns=ns)
    assert fires("rg('x', '.')", "nodoc", s7)
    assert fires("rg('y', '.')", "nodoc", s7)                     # keeps nagging until doc'd
    assert not fires("doc(rg)\nrg('x', '.')", "nodoc", s7)        # compliance ends the nag
    s8 = Session(ns=ns)
    assert not fires("doced('rg')\nrg('x', '.')", "nodoc", s8)    # declaring is recorded at scan time, like doc()
    s9 = Session(ns=ns)
    assert not fires("doced(rg)\nrg('y', '.')", "nodoc", s9)      # bare symbols declare too
    import llmdojo.rules as cr
    assert not fires("doced('x')\nforget_doced()", "nodoc", Session(ns={"doced": cr.doced, "forget_doced": cr.forget_doced}))  # the prescribed interfaces are exempt


def test_notes_single_way():
    "Notes teach exactly one route and never name exceptions."
    from llmdojo.rules import RULES
    for r in RULES:
        assert r.note and len(r.note) < 120
        for word in ("unless", "except when", "sometimes", "usually"): assert word not in r.note.lower()


def test_doced_state(tmp_path, monkeypatch):
    "doced survives worker restarts via a ppid-keyed state file; doced() declares; forget_doced() resets; stale files swept on save; external writes win"
    monkeypatch.setenv("LLMDOJO_STATE_DIR", str(tmp_path))
    import os, llmdojo.rules as cr
    stale = tmp_path/'doced'/'99999.json'
    stale.parent.mkdir(parents=True)
    stale.write_text('[]')
    os.utime(stale, (0, 0))
    insp = cr.make_inspector()
    insp(None, "doc(rg)")
    assert not stale.exists()                       # abandoned session state swept on save
    cr.make_inspector()                             # a fresh worker in the same session
    assert 'rg' in cr._LIVE.doced                   # state survived the restart
    cr.doced('lnhashview_file')
    cr.doced(cr.forget_doced)                       # plain symbols work too, like doc()
    cr.make_inspector()
    assert {'rg','lnhashview_file','forget_doced'} <= set(cr.doced())
    cr.forget_doced()
    cr.make_inspector()
    assert not cr._LIVE.doced                       # post-compaction reset: everything needs doc() again
    cr.doced('rg')
    cr._doced_file().write_text('["fd"]')           # an external writer (the compaction hook) owns the file
    assert cr.doced() == ['fd']                     # the file is the source of truth: external writes win
    monkeypatch.delenv("CLAUDE_PROJECT_DIR", raising=False)
    monkeypatch.setenv("CLAUDE_CODE_SESSION_ID", "sid-123")
    monkeypatch.setattr(cr, "_HOST", None)
    assert cr._doced_file().name == 'sid-123.json'  # per-spawn session id when no transcript is found
    monkeypatch.delenv("CLAUDE_CODE_SESSION_ID")
    monkeypatch.setattr(cr, "_HOST", None)
    assert cr._doced_file().name == f'{os.getppid()}.json'
    home = tmp_path/'home'
    tdir = home/'.claude'/'projects'/'-my-proj'
    tdir.mkdir(parents=True)
    (tdir/'aaa.jsonl').write_text('')
    (tdir/'bbb.jsonl').write_text('')
    os.utime(tdir/'aaa.jsonl', (0, 0))
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv("CLAUDE_PROJECT_DIR", "/my/proj")
    monkeypatch.setattr(cr, "_HOST", None)
    assert cr._doced_file().name == 'bbb.json'      # most recent transcript: the conversation that spawned this worker


def test_note_tag(tmp_path, monkeypatch):
    "Each rule picks its wrapper tag: nodoc renders as <warn>, others default to <note>."
    monkeypatch.setenv("LLMDOJO_STATE_DIR", str(tmp_path))
    import IPython, rgapi.skill, llmdojo.rules as cr
    class _FakeIp: user_ns = {'rg': rgapi.skill.rg}
    monkeypatch.setattr(IPython, 'get_ipython', lambda: _FakeIp)
    insp = cr.make_inspector()
    out = insp(None, "rg('x', '.')")
    assert out.startswith('<warn>') and '</warn>' in out and 'doc(rg)' in out
    insp(None, "doc(rg)")
    assert insp(None, "rg('y', '.')") == ''          # doc'd: quiet
    cr._doced_file().write_text('[]')                # the compaction hook truncates while the kernel lives on
    assert 'doc(rg)' in insp(None, "rg('z', '.')")   # reloaded per cell: nodoc re-fires
    out = insp(None, "Path('a.py').read_text()")
    assert out.startswith('<note>') and '</note>' in out
