# -*- coding: utf-8 -*-
import io
import logging
import subprocess
from diff_maker import DiffMaker
from counter import Counter


def build_diff(argv, structures, pgup_config):
    logger = logging.getLogger("pgup.build_diff")

    diffMaker = DiffMaker(argv, pgup_config)
    diffMaker.prepare()
    queries, names = diffMaker.make()
    overview = diffMaker.overview()

    for dbname, dbqueries in queries.iteritems():
        if dbqueries:
            dbnames = names[dbname]
            DBDIR = u"{}/{}".format(argv["build"], dbname)
            DBFILES = u"{}/sql".format(DBDIR)
            subprocess.check_call("mkdir -p {}".format(DBFILES), shell=True)
            files = []
            counter = Counter()
            for qry, name in zip(dbqueries, dbnames):
                counter.next()
                fpath = u"{}/{}:{}-{}.sql".format(
                    DBFILES,
                    counter.get_textnum(),
                    counter.get_intnum(),
                    name
                )
                with io.open(fpath, "w", encoding="utf-8") as fstream:
                    fstream.write(qry)
                files.append(u"\\i '{}';".format(fpath))
            # main file, which execute all saved sql
            with io.open(u"{}/execute.sql".format(DBDIR), "w", encoding="utf-8") as fstream:
                fstream.write(u"\n".join(files))
            # overview about created objects
            with io.open(u"{}/overview.txt".format(argv["build"]), "a", encoding="utf-8") as fstream:
                fstream.write("{}:\n".format(dbname) + overview)
            logger.info("{}: {}".format(dbname, DBDIR))
        else:
            with io.open(u"{}/overview.txt".format(argv["build"]), "a", encoding="utf-8") as fstream:
                fstream.write(u"{}: Queries not exists\n".format(dbname))

            logger.info("{}: Queries not exists".format(dbname))
