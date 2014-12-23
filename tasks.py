from pake.runner import Pake
from pake.shell import python, twine, rm, ls

@Pake.add_task
def up():
    """
        Deploy new release to pypi
        Using twine util
    """
    rm("-rf dist")
    rm("-rf pgup.egg-info")
    python("./setup.py sdist")
    twine("upload dist/{}".format(ls("dist").strip()))

@Pake.add_task
def docs():
    """
        Deploy documentation to pythonhosted
        Using sphinx
    """
    rm("-rf build/html")
    python("./setup.py build_sphinx")
    python("./setup.py upload_sphinx")
