import re, pytest
from pathlib import Path
from clikernel.cli import _stream_text
import llmdojo.dojo as dj


def test_dojo(tmp_path, monkeypatch):
    "Smoke: start copies seeds and traces cells; score counts strokes (Bash = 2), reports kata outcomes and par routes; redo resets files."
    monkeypatch.setenv("LLMDOJO_STATE_DIR", str(tmp_path))
    from execnb.shell import CaptureShell
    sh = CaptureShell()
    def run(code):
        out = _stream_text(sh.run(code))
        assert not sh.exc, out
        return out

    run("import llmdojo.dojo")
    run("from llmdojo.rules import doced")
    run("doced('pretool')")                                 # pre-round declaration: persists before any inspector exists
    run("from llmdojo.dojo import *")
    card = run("dojo_start()")
    assert "== llmdojo ==" in card and "(par 2)" in card and "(par 1)" in card and "par 3" not in card and "best route" in card and "%cd" in card and "print()" in card
    assert "not wrapped in print" in card.lower()           # free-cell rule says bare doc() calls only
    assert "early version" in card.lower()                  # card asks for imperfection reports
    assert "clean score" in card and "ascending order" in card  # completion gate + redo order spelled out
    hostile = dj._TMPL_PAYLOAD                               # kata 3 payload defeats every Python literal form
    assert "'"*3 in hostile and '"'*3 in hostile and '\\' in hostile and '\n' in hostile
    d = dj._RUN['dir']
    assert (d/'core.py').exists() and (d/'nbs'/'01_api.ipynb').exists() and (d/'report.py').exists()

    run("x = 1 + 1")                                      # 1 stroke
    run("help(len)")                                      # free
    run("import collections, json")                       # free: imports cost nothing
    run("# a narration comment")                          # free: comments cost nothing
    run("for f in (len, max): help(f)")                   # free: reading docs in a loop
    run("%cd .")                                          # free: chdir cells cost nothing
    run("import os; os.chdir('.')")                       # free: the os.chdir form too
    run("print(x)")                                       # free cell shape, but each print() costs 1
    out = run("dojo_score(bash_calls=1)")                 # free itself; +2 for the Bash call
    assert "strokes 4" in out and "par 8" in out                        # cell + print + 2*bash
    assert "1| x = 1 + 1" in out and "0| # a narration comment" in out  # per-cell stroke ledger
    assert "kata 'edit set'" in out and "par route" in out  # unedited files: fails, with the route shown
    assert "kata 'orient': no answer passed" in out and dj.KATAS[0]['route'] in out  # ungraded orient fails, route shown
    assert "kata 'doc first': no answer passed" in out       # kata 5 is graded via dojo_score(report=...)
    assert 'rb-3254' not in out and 'RB7' not in out         # a failed score never leaks the answers
    assert "early version" in out.lower()                   # scorer asks for imperfection reports
    assert "per-kata scoring" in out                        # no tags yet: gentle how-to nudge, old kata format kept
    assert dj._RUN                                          # not a clean round: run dir kept

    assert "| dojo_score" not in out                        # scoring machinery stays out of the stroke ledger

    run("nope = 1")                                         # ledger paused after scoring: uncounted
    out = run("dojo_score(bash_calls=1)")
    assert "strokes 4" in out                               # the stray cell stayed out of the ledger
    run("dojo_resume()")                                    # counted work resumes

    run("pretool = llmdojo.dojo._card; pretool()")        # 1 stroke; doced pre-round: no penalty
    run("fake = llmdojo.dojo._card")                      # 1 stroke
    run("fake()")                                           # 1 stroke, and a nodoc penalty
    out = run("dojo_score(bash_calls=1)")
    assert "doc penalties 1" in out and "undoc'd first uses: fake" in out   # pre-round doced honored: only fake flagged
    assert "never penalized" in out                                          # the report says how to clear the misses
    run("doced('fake')")                                    # free declaration remedies the miss
    decoy = "httpx is modern and async-friendly"                            # plausible guess: lacks the documented why
    out = run(f"dojo_score(bash_calls=1, orient={decoy!r})")
    assert "strokes 7 + doc penalties 0" in out and "habit miss" not in out # doc-fix forgiven on rescore
    assert "justification" in out                                           # guessed prose rejected: the token is missing
    half = "policy rb-3254 requires this client"
    out = run(f"dojo_score(bash_calls=1, orient={half!r})")
    assert "chosen over" in out                                             # names the missing half: the requests comparison

    run("dojo_resume()")                                  # counted work resumes
    run("# kata 2")                                         # free tag cell: the one exact format
    run("y = 2")                                            # 1 stroke -> kata 2
    run("# kata 2 done, kata 3 next")                       # narration, NOT a tag: kata 2 stays current
    run("z = 3")                                            # 1 stroke -> still kata 2
    run("# kata 99")                                        # invalid number: not a tag either
    run("# kata 3")                                         # tag switch
    run("v = 9")                                            # 1 stroke -> kata 3
    run("v2 = 8")                                           # 1 stroke -> kata 3
    run("v3 = 7")                                           # 1 stroke -> kata 3: now over par
    ans = "httpx replaces requests here because policy rb-3254 forbids requests in prod"
    tok = f"RB{2*3517}"                                     # computed like the kata does: never literal in any source
    out = run(f"dojo_score(bash_calls=1, orient={ans!r})")
    assert "strokes 12" in out                                          # 10 cell strokes + 2*bash
    assert "kata 'orient' (strokes 0, par 1): ok" in out                # graded answer, no strokes tagged 1
    assert "kata 'edit set' (strokes 2, par 2)" in out
    assert "kata 'hostile replace' (strokes 3, par 2, +1 over)" in out  # per-kata over-par surfaced
    assert "dojo_redo(3)" in out                                        # ...with the retry hint
    assert "looked like tags but aren't" in out and 'kata 2 done' in out  # near-miss narration flagged, quoted
    assert "'# kata 99'" in out                                         # ...as is the invalid number
    assert "5 untagged" in out                                          # pre-tag strokes surfaced, gently
    assert "dojo_redo(0)" in out                                        # ...with the discard hint

    out = run("dojo_redo(3)")                               # over-par kata: retry replaces its strokes, not adds
    assert "verbatim: ..." in out                           # reset banner shows the prompt's whole first line, elision marked
    out = run(f"dojo_score(bash_calls=1, orient={ans!r})")
    assert "strokes 9" in out                               # kata 3's three strokes cleared from the ledger
    assert "kata 'hostile replace' (strokes 0, par 2)" in out

    out = run("dojo_redo(0)")                               # untagged protocol mistakes: recoverable without a fresh round
    assert "untagged" in out.lower()
    out = run(f"dojo_score(bash_calls=1, orient={ans!r})")
    assert "strokes 4 + doc penalties 0" in out             # the five untagged strokes discarded; free untagged cells kept
    out = run("dojo_redo(1)")                               # read-only kata: nothing to reset
    assert "kata 4" not in out                              # no shared-file warning, no reapply tax on kata 4
    out = run(f"dojo_score(bash_calls=1, orient={ans!r})")
    assert "strokes 4" in out                               # nothing was tagged kata 1: reset changes nothing
    assert "kata 'orient' (strokes 0, par 1): ok" in out
    assert "kata 'notebook edit' (strokes 0, par 2)" in out

    (d/'core.py').write_text("broken")
    run("dojo_redo(2)")
    assert "units='imperial'" in (d/'core.py').read_text()  # pristine again

    ok_dir = d.parent/'zz'                                  # a genuine run dir: deletable
    ok_dir.mkdir()
    dj._rm_run(ok_dir)
    assert not ok_dir.exists()
    with pytest.raises(ValueError): dj._rm_run(tmp_path/'elsewhere')   # tampered path: refused

    orig = Path.cwd()
    run("dojo_start()")                                     # fresh round; this test edits its files directly
    run("# kata 3")                                        # exact tag; the overspend below is compensated by an under-par rest of round
    run("s1 = 1")
    run("s2 = 2")
    run("s3 = 3")
    d2 = dj._RUN['dir']
    core = (d2/'core.py').read_text().replace("'imperial'", "'metric'") \
        .replace('cfg = dict', 'config = dict').replace('cfg[k', 'config[k').replace('return cfg', 'return config').replace('    # FIXME: drop this\n', '')
    (d2/'core.py').write_text(core)
    (d2/'templ.py').write_text('"Plain-text rendering for weather summaries."\n\n\n' + dj._TMPL_PAYLOAD)
    raw = (d2/'nbs'/'01_api.ipynb').read_text().replace('retries the request twice before giving up.',
        'retries the request twice more before giving up, making 3 attempts in all.')
    (d2/'nbs'/'01_api.ipynb').write_text(raw)
    run(f"%cd {d2}")                                        # free: chdir cells cost nothing
    out = run(f"dojo_score(orient={ans!r}, report={tok!r})")   # under-par round total: clean, despite the kata-3 overspend
    assert "Clean round" in out and "cwd restored" in out and "Completion id:" in out and "compaction" in out
    assert "kata 'hostile replace' (strokes 3, par 2, +1 over)" in out  # over-par kata, under-par round
    assert "over-par katas" not in out and "dojo_redo(" not in out       # clean round: no contradictory redo demand
    cid = re.search(r"Completion id: ([0-9a-f]{4})", out)[1]
    assert "Kernel namespace cleared" not in out
    assert "and cwd restored" in out and Path.cwd() == orig
    assert run("print('s1' in globals())").strip() == 'True'          # clean round keeps the live namespace
    assert run("print('dojo_score' in globals())").strip() == 'True'
    out = run(f"dojo_start({cid!r})")
    assert "already complete" in out and not dj._RUN        # receipt honored: no tasks, no run started
    run("forget_dojo()")                                    # tooling changed: truncate the record
    out = run(f"dojo_start({cid!r})")
    assert "not on record" in out and "never deals" in out            # informational refusal, with the reason
    assert "== llmdojo ==" not in out and not dj._RUN           # ...and no round forced on a mere check
    out = run("dojo_start()")                                          # an explicit bare start still deals
    assert "== llmdojo ==" in out and dj._RUN


def test_kata_tag():
    "A tag is a cell containing ONLY a comment in the exact format; anything fancier is narration."
    assert dj._kata_tag('# kata 4') == 4
    assert dj._kata_tag('  # kata 2  ') == 2
    assert dj._kata_tag('# kata 4: reapply fix') is None
    assert dj._kata_tag('# katas 1+4: shared search') is None
    assert dj._kata_tag('# kata 2 done, kata 3 next') is None
    assert dj._kata_tag('# kata 99') is None
    assert dj._kata_tag('# plain narration, no tag') is None


def test_register_completion(tmp_path, monkeypatch):
    "Public registration: session-template launchers record a receipt, version-gated exactly like the dojo's own."
    monkeypatch.setenv("LLMDOJO_STATE_DIR", str(tmp_path))
    assert dj.register_completion('beef') == 'beef'
    assert dj._completions()['beef']['v'] == dj.dojo_version()
    dj.register_completion('dead', 'stale:0')                # a receipt from other tooling: kept, but won't validate
    assert dj._completions()['dead']['v'] == 'stale:0'


def test_start_refusals(tmp_path, monkeypatch, capsys):
    "An id that fails the completion check reports which reason applies, and never deals a round."
    monkeypatch.setenv("LLMDOJO_STATE_DIR", str(tmp_path))
    before = dict(dj._RUN)
    dj.register_completion('dead', 'stale:0')
    dj.dojo_start('dead')
    out = capsys.readouterr().out
    assert 'stale:0' in out and dj.dojo_version() in out    # version mismatch names both versions
    dj.dojo_start('cafe')
    assert 'never registered' in capsys.readouterr().out    # absent id: no record at all
    import json, time
    dj._complete_file().write_text(json.dumps({'old1': dict(t=time.time()-8*86400, v=dj.dojo_version())}))
    dj.dojo_start('old1')
    out = capsys.readouterr().out
    assert 'expired' in out and '8 days ago' in out         # expired id: age reported
    assert dict(dj._RUN) == before                          # no round was dealt by any refusal


def test_chk_core(tmp_path):
    "The cfg variable renames; load_cfg (the function) keeps its name -- a boundary-precise rename, not a substring one."
    from importlib.resources import files
    base = (files('llmdojo')/'dojo_data'/'proj'/'core.py').read_text()
    good = base.replace("'imperial'", "'metric'").replace('cfg = dict', 'config = dict') \
        .replace('cfg[k', 'config[k').replace('return cfg', 'return config').replace('    # FIXME: drop this\n', '')
    (tmp_path/'core.py').write_text(good)
    assert dj._chk_core(tmp_path) == []
    (tmp_path/'core.py').write_text(good.replace('load_cfg', 'load_config'))
    assert any('load_cfg' in m for m in dj._chk_core(tmp_path))
    (tmp_path/'core.py').write_text(good + '\n# FIXME: drop this\n')
    assert any('FIXME' in m for m in dj._chk_core(tmp_path))


def test_chk_orient():
    "Facts-only grading: the unguessable token proves the neighbor cell was actually rendered."
    dj._RUN['orient'] = 'httpx replaces requests here: policy rb-3254 forbids requests in prod'
    assert dj._chk_orient(None) == []
    dj._RUN['orient'] = 'requests has no async support so this async-friendly client is used'  # plausible, tokenless
    assert any('justification' in m for m in dj._chk_orient(None))
    dj._RUN['orient'] = 'policy rb-3254 mandates this http client'
    assert any('chosen over' in m for m in dj._chk_orient(None))
    dj._RUN.clear()


def test_orient_answer_buried():
    "The design invariants of the orient kata: the why-cell is markdown, refers to httpx only pronominally, and its token sits past the 120-char one-line-summary boundary."
    import json
    from importlib.resources import files
    nb = json.loads((files('llmdojo')/'dojo_data'/'proj'/'nbs'/'01_api.ipynb').read_text())
    cell = next(c for c in nb['cells'] if 'rb-3254' in ''.join(c['source']))
    src = ''.join(cell['source'])
    assert cell['cell_type'] == 'markdown' and 'httpx' not in src and 'rb-3254' not in src[:120]


def test_report_kata(tmp_path):
    "daily_report emits the RB-2 header only for the shipped style, computed so it appears in no source; the checker keys on it."
    import importlib.util
    from importlib.resources import files
    p = files('llmdojo')/'dojo_data'/'proj'/'report.py'
    assert 'RB7' not in p.read_text()                        # the token is computed, never literal
    spec = importlib.util.spec_from_file_location('dojo_report', p)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    out = m.daily_report(m.SAMPLE, style='rb2')
    assert out.splitlines()[0] == f'RB{2*3517}'
    assert f'RB{2*3517}' not in m.daily_report(m.SAMPLE)     # the guessed default call scores nothing
    dj._RUN['report'] = out.splitlines()[0]
    assert dj._chk_report(None) == []
    dj._RUN['report'] = 'RB-2 format report'
    assert dj._chk_report(None) != []
    dj._RUN.clear()


def test_free_chdir():
    "chdir cells are free in either form: relative paths save tokens in every later cell."
    assert dj._is_free('%cd /tmp/x')
    assert dj._is_free('%cd')
    assert dj._is_free('import os\nos.chdir("/tmp")')
    assert dj._is_free('from os import chdir\nchdir("/tmp")')
    assert not dj._is_free('%cd /tmp\ny = 1')
