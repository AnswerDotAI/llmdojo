from fastcore.utils import *
if Path('pyproject.toml').exists():
    from pyskills import list_pyskills, doc
    from fastcore.editskill import *
    from llmsurgery.dlgskill import *
    from exhash.skill import *
    from rgapi.skill import *
    from llmdojo.dojo import *
    from ipykernel_helper import info_md
    import clikernel.skill as clik, pyskills.skill as pysk, fastcore.editskill as edsk, llmsurgery.dlgskill as dsk, exhash.skill as exh, rgapi.skill as rgsk, aai_coding.coding_patterns as acp
    _p = (Path(__file__).parent)/'startup.txt'
    print(_p.read_text())
else: print(f'startup: no pyproject.toml in {Path.cwd()}; project imports skipped')
