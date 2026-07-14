from fastcore.utils import *
if Path('pyproject.toml').exists():
    from pyskills import list_pyskills, doc
    from llmdojo.rules import doced, forget_doced
    from pyskills.edit import *
    from exhash.skill import *
    from ipykernel_helper import info_md
    import clikernel.skill as clik, pyskills.skill as pysk, pyskills.edit as pyse, exhash.skill as exh
    _p = (Path(__file__).parent)/'startup.txt'
    print(_p.read_text())
