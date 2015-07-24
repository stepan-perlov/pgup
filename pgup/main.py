import os
import logging
from pake.shell import rm, mkdir
from pgup import Config as PgupConfig
from pgup import build_init
from pgup import build_diff

logger = logging.getLogger('pgup.main')


def pgup(config="/etc/pgup.yaml", **argv):
    argv["build"] = ("build" in argv and argv["build"]) or "build/pgup"
    argv["commit"] = ("commit" in argv and argv["commit"]) or None

    pgup_config = PgupConfig(config)

    structures = []
    ANY_STRUCTURE_EXISTS = False
    for dbname in pgup_config.databases:
        param = "{}_structure".format(dbname)
        structures.append((dbname, param))
        if argv[param]:
            ANY_STRUCTURE_EXISTS = True
        else:
            logger.info("{} not exists".format(param))

    # Remove build directory
    if os.path.exists(argv["build"]):
        logging.debug("rm -rf {}".format(argv["build"]))
        rm(u"-rf {}".format(argv["build"]))

    mkdir(u"-p {}".format(argv["build"]))

    if argv["commit"]:
        build_diff(argv, structures, pgup_config)
    elif ANY_STRUCTURE_EXISTS:
        build_init(argv, structures, pgup_config)