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


"""
def diff(commit, config):
    pipe = git("diff --name-status {} HEAD".format(commit), pipe=True)
    regexp = "\\\\|".join( ["^[ADMR]\\\\s\\\\+{}".format(db) for db in config.databases] )
    diff = []
    res = pipe.grep(regexp).strip()
    if res:
        diff = res.split("\n")

    structure = {}
    patch = {}
    for db in config.databases:
        structure[db] = Structure(db, config)
        patch[db] = Patch(db, config)

    for line in diff:
        action, fpath = line.split("\t")
        split = fpath.split("/")
        db, schema, path = split[0], split[1], split[2]

        structure[db].add_schema(schema)
        patch[db].add_file(path, fpath, action)

    # load structure of commit to update
    # and make drop statements
    dump = git("rev-parse --abbrev-ref HEAD").strip()
    if dump == "HEAD":
        HEAD = git("rev-parse HEAD").strip()
    else:
        HEAD = dump

    git("checkout {}".format(commit))
    for db in config.databases:
        structure[db].load_files()
        patch[db].drop_statements()
    git("checkout {}".format(HEAD))

    queries = {}
    names = {}
    for db in config.databases:
        queries[db], names[db] = patch[db].make(structure[db])

    response = {
        "overview": Patch.overview(),
        "queries": queries,
        "names": names
    }
    return response
"""