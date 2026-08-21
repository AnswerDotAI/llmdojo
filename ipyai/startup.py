from fastcore.utils import *
from pyskills import list_pyskills, doc, xdir
from fastcore.editskill import *
from aidialog.dlgskill import *
from exhash.skill import *
from rgapi.skill import *
from llmdojo.dojo import *
from ipykernel_helper import info_md
import pyskills.skill as pysk, fastcore.editskill as edsk, aidialog.dlgskill as dsk, exhash.skill as exh, rgapi.skill as rgsk, aai_coding.coding_patterns as acp

# The session rules, applied to the model's cells only. ipyai runs the model's `py` cells with store_history=False
# and the user's typed cells with True, so IPython's pre_run_cell info tells them apart; the user's own cells are
# never inspected. A note prints ahead of the cell's output (so it reaches the model inside the tool result);
# a RuleBlock rejects the cell; any other inspector error prints and the cell runs anyway.
from IPython import get_ipython
from IPython.core.error import InputRejected
from llmdojo.rules import make_inspector

class _AIInspect:
    def __init__(self, f): self.f, self.src, self.ai = f, '', False
    def stash(self, info): self.src, self.ai = info.raw_cell, not info.store_history
    def visit(self, tree):
        if not self.ai: return tree
        try: note = self.f(tree, self.src)
        except InputRejected: raise
        except Exception as e: note = f'inspector error (cell runs anyway): {e!r}'
        if note: print(note, end='')
        return tree

_ai_inspect = _AIInspect(make_inspector())
get_ipython().events.register('pre_run_cell', _ai_inspect.stash)
get_ipython().ast_transformers.append(_ai_inspect)
