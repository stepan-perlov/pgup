# -*- coding: utf-8 -*-
from pake.shell import git
from patch import Structure
from patch import Patch
from table import Table


def diff(commit, config):
    pipe = git("diff --name-status {} HEAD".format(commit), pipe=True)
    regexp = "\\\\|".join( ["^[ADMR]\\\\s\\\\+{}".format(db) for db in config.databases] )
    diff = pipe.grep(regexp).strip().split("\n")

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
        """
        split = fpath.split("/")
        db, schema = split[0], split[1]
        [current_tables.append("{}/{}/{}".format(db, schema, table)) for table in config.tables if os.path.exists("{}/{}/{}".format(db, schema, table))]
        [current_procedures.append("{}/{}/{}".format(db, schema, procedure)) for procedure in config.procedures if os.path.exists("{}/{}/{}".format(db, schema, table))]

        if action == "D":
            deleted.append(fpath)
        else:
            patch.append(fpath)

        """
    # load structure of commit to update
    HEAD = git("rev-parse HEAD").strip()
    git("checkout {}".format(commit))
    [structure[db].load_files() for db in structure]
    git("checkout {}".format(HEAD))

    queries = []
    for fpath in patch:
        split = fpath.split("/")
        db, schema, path = split[0], split[1], split[2]
        sql = None

        if path in config.tables:
            t = Table(fpath)
            if str(t) in current_tables:
                sql = current_tables[str(t)].alter(t)
            else:
                sql = t.create()
        elif path in config.procedures:
            with open(fpath) as fstream:
                sql = fstream.read()

        if sql:
            queries.append({"fpath": fpath, "sql": sql})
    print queries
