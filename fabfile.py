from fabric.api import task, local

@task
def up():
    """
        Deploy new release to pypi. Using twine util
    """
    local("rm -rf dist")
    local("rm -rf pgup.egg-info")
    local("python ./setup.py sdist")
    local("twine upload dist/{}".format(local("ls dist", capture=True).strip()))

@task
def docs():
    """
        Deploy documentation to pythonhosted. Using sphinx
    """
    local("rm -rf build/html")
    local("python ./setup.py build_sphinx")
    local("python ./setup.py upload_sphinx")
