# -*- coding: utf-8 -*-
from pake.shell import git
from patch import Structure
from patch import Patch


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
