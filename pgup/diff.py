# -*- coding: utf-8 -*-
import os
from pake.shell import git, find
from table import Table


def diff(commit, config):
    pipe = git("diff --name-status {} HEAD".format(commit), pipe=True)
    regexp = "\\\\|".join( ["^[ADMR]\\\\s\\\\+{}".format(db) for db in config.databases] )
    diff = pipe.grep(regexp).strip().split("\n")

    deleted, patch, modify = [], [], []
    for line in diff:
        action, fpath = line.split("\t")

        split = fpath.split("/")
        db, schema = split[0], split[1]
        [modify.append("{}/{}/{}".format(db, schema, table)) for table in config.tables if os.path.exists("{}/{}/{}".format(db, schema, table))]

        if action == "D":
            deleted.append(fpath)
        else:
            patch.append(fpath)

    HEAD = git("rev-parse HEAD").strip()
    git("checkout {}".format(commit))

    current_tables = {}
    for path in set(modify):
        for fpath in find("{} -name *.yaml".format(path)).split():
            t = Table(fpath)
            current_tables[str(t)] = t

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
