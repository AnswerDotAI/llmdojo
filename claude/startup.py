from fastcore.utils import *
if Path('pyproject.toml').exists():
    from pyskills import list_pyskills, doc
    from llmdojo.rules import doced, forget_doced
    from fastcore.tools import *
    from llmsurgery.dlgskill import *
    from exhash.skill import *
    from ipykernel_helper import info_md
    import clikernel.skill as clik, pyskills.skill as pysk, fastcore.tools as fct, llmsurgery.dlgskill as dsk, exhash.skill as exh
    _p = (Path(__file__).parent)/'startup.txt'
    print(_p.read_text())
