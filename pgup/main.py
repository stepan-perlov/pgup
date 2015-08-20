import os
import logging
import subprocess
from pgup import Config as PgupConfig
from build_init import build_init
from build_diff import build_diff

logger = logging.getLogger('pgup.main')


def pgup(**argv):
    argv["build"] = ("build" in argv and argv["build"]) or "build/pgup"
    argv["config"] = ("config" in argv and argv["config"]) or "/etc/pgup.yaml"
    argv["commit"] = ("commit" in argv and argv["commit"]) or None

    pgup_config = PgupConfig(argv["config"])

    structures = []
    ANY_STRUCTURE_EXISTS = False
    for dbname in pgup_config.databases:
        param = "{}_structure".format(dbname)
        structures.append((dbname, param))
        if param in argv:
            ANY_STRUCTURE_EXISTS = True
        else:
            logger.info("{} not exists".format(param))

    # Remove build directory
    if os.path.exists(argv["build"]):
        logging.debug("rm -rf {}".format(argv["build"]))
        subprocess.check_call(u"rm -rf {}".format(argv["build"]), shell=True)

    subprocess.check_call(u"mkdir -p {}".format(argv["build"]), shell=True)

    if argv["commit"]:
        build_diff(argv, structures, pgup_config)
    elif ANY_STRUCTURE_EXISTS:
        build_init(argv, structures, pgup_config)
