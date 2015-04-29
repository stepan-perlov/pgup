# -*- coding: utf-8 -*-
import io
import logging
from pake.shell import mkdir
from diff_maker import DiffMaker
from counter import Counter


def build_diff(args, argv, structures, pgup_config):
    logger = logging.getLogger("pgup.build_diff")

    diffMaker = DiffMaker(args.commit, pgup_config)
    diffMaker.prepare()
    queries, names = diffMaker.make()
    overview = diffMaker.overview()

    for dbname, dbqueries in queries.iteritems():
        if dbqueries:
            dbnames = names[dbname]
            DBDIR = u"{}/{}".format(args.build, dbname)
            DBFILES = u"{}/sql".format(DBDIR)
            mkdir("-p {}".format(DBFILES))
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
            with io.open(u"{}/overview.txt".format(DBDIR), "w", encoding="utf-8") as fstream:
                fstream.write(overview)
            logger.info("{}: {}".format(dbname, DBDIR))
        else:
            logger.info("{}: Queries not exists".format(dbname))
