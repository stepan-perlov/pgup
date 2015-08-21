from fabric.api import task, local, execute

@task
def up():
    """
        Deploy new release to pypi. Using twine util
    """
    local("rm -rf dist")
    local("rm -rf pgup.egg-info")
    local("python ./setup.py sdist")
    local("twine upload dist/{}".format(local("ls dist", capture=True).strip()))
    execute(syncMezzo)

@task
def docs():
    """
        Deploy documentation to pythonhosted. Using sphinx
    """
    local("rm -rf build/html")
    local("python ./setup.py build_sphinx")
    local("python ./setup.py upload_sphinx")

@task
def syncMezzo():
    """
        Copy current module version to mezzo project
    """
    local("rm -rf /opt/mezzo/pgup")
    local("mkdir /opt/mezzo/pgup")
    local("cp -R etc pgup /opt/mezzo/pgup")
    local("cp LICENSE MANIFEST.in README.md setup.py /opt/mezzo/pgup")
