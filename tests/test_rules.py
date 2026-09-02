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
    assert fires("file_exhash(p, (a, 'c', 'a longer replacement line here'))", "tuple_payload")
    assert fires('file_exhash(p, (a, "a", "it\'s"))', "tuple_payload")             # quote in payload
    assert fires("cell_exhash(p, cid, (a, 'i', 'x = \\\\n'))", "tuple_payload")    # backslash in payload
    assert not fires("file_exhash(p, (a, 'c', 'metric'))", "tuple_payload")        # short one-worder: fine
    assert not fires("file_exhash(p, (a, 's', 'longer than twenty chars ok'))", "tuple_payload")  # s is not a payload command
    assert not fires("file_exhash(p, (a, 'c', body))", "tuple_payload")            # variables unknowable: stay quiet
    assert not fires("file_exhash(p, (a, 'd'), (b, 'c', 'a longer replacement line here'))", "tuple_payload")  # multi-command batch: the one-command magic can't express it atomically
    assert not fires("cell_exhash(p, cid, (a, 's', 'x', 'y'), (b, 'i', 'it\'s a long insertion here'))", "tuple_payload")
    assert fires("cell_exhash(p, cid, (a, 'c', 'a longer replacement line here'))", "tuple_payload")  # single command: the magic is strictly better
    assert fires("exhash(t, [(a, 'c', 'a longer replacement line here')])", "tuple_payload")           # one command in a list works the same

    # literal \n in an s-replacement -> real newline; oversized s-replacement -> c command
    assert fires(r"file_exhash(p, ('1|aa|', 's', 'x', r'a\nb'))", "s_newline")     # 2-char \n stays literal: a mistake
    assert not fires(r"file_exhash(p, ('1|aa|', 's', 'x', 'a\nb'))", "s_newline")  # real newline: intended multiline
    assert not fires(r"file_exhash(p, ('1|aa|', 's', r'x\n', 'y'))", "s_newline")  # pattern field: regex \n is meaningful
    assert fires(f"file_exhash(p, ('1|aa|', 's', 'x', {'y'*121!r}))", "s_long")
    assert not fires(f"file_exhash(p, ('1|aa|', 's', 'x', {'y'*120!r}))", "s_long")

    # blockers
    assert fires("import subprocess", "shell_escape")
    assert fires("os.system('ls')", "shell_escape")
    assert fires("!ls", "shell_escape")                          # `!` escapes are seen via the transformed cell
    assert fires("import subprocess.x", "shell_escape")          # submodule spellings
    assert fires("from subprocess.x import y", "shell_escape")
    assert not fires("!!ls", "shell_escape")                     # `!!` compiles to .getoutput: capture, not escape
    assert fires("%nbrun ab12\nPath('f.py').read_text()", "read_file")  # rules still run on cells containing magics
    assert fires("sys.path.insert(0, 'x')", "sys_path")
    assert fires("sys.path.append('x')", "sys_path")


def test_session_rules(monkeypatch):
    "Cross-cell rules: piecemeal skill imports, and re-nagging on every miss."
    s = Session()
    assert fires("from rgapi import rg", "piecemeal", s)          # rgapi has a .skill module
    assert not fires("from rgapi.skill import *", "piecemeal", s)
    assert not fires("from pathlib import Path", "piecemeal", s)  # no pathlib.skill: fine
    assert not fires("from pyskills import list_pyskills, doc", "piecemeal", s)  # the blessed bootstrap line
    # re-nag: findings repeat on every offending cell until the habit is fixed
    s4 = Session()
    assert fires("Path('a.py').read_text()", "read_file", s4)
    assert fires("Path('b.py').read_text()", "read_file", s4)


def test_notes_single_way():
    "Notes teach exactly one route."
    from llmdojo.rules import RULES
    for r in RULES:
        assert r.note and (r.block or len(r.note) < 120)
        for word in ("unless", "sometimes", "usually"): assert word not in r.note.lower()


def test_note_tag(monkeypatch):
    "Findings render in their rule's wrapper tag; a clean cell renders nothing."
    import IPython, llmdojo.rules as cr
    class _FakeIp: user_ns = {}
    monkeypatch.setattr(IPython, 'get_ipython', lambda: _FakeIp)
    insp = cr.make_inspector()
    out = insp(None, "Path('a.py').read_text()")
    assert out.startswith('<note>') and '</note>' in out
    assert insp(None, "x = 1") == ''
