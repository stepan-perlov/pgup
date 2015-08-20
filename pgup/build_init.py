# -*- coding: utf-8 -*-
import os
import io
import json
import logging
import subprocess
import collections

import yaml
from table import Table
from errors import PgupException
from counter import Counter


def load_structure(structure_string):
    if structure_string.endswith(".yaml"):
        fpath = structure_string
        if os.path.exists(fpath):
            with open(fpath) as fstream:
                structure = yaml.load(fstream)
        else:
            raise Exception("Structure file not exists: {}".format(fpath))
    else:
        structure = json.loads(structure_string)
    return structure

def parse_structure(structure):
    created = collections.defaultdict(int)
    queries = []
    names = []
    for obj in structure["modules"]:
        keys = obj.keys()
        if len(keys) != 1:
            raise PgupException("Incorrect keys length in modules {} - {}".format(keys, obj))
        name = keys[0]
        value = obj[name]
        if name == "schema":
            queries.append(u"CREATE SCHEMA IF NOT EXISTS {};".format(value))
        elif name == "table":
            queries.append(Table(value).create())
        elif name == "sql":
            queries.append(value.rstrip(u";") + u";")
        else:
            with io.open(value, "r", encoding="utf-8") as fstream:
                queries.append(fstream.read())
        names.append(name)
        created[name] += 1
    return {
        "queries": queries,
        "names": names,
        "overview": u" / ".join(
            [u"{} {}".format(obj_type, count) for obj_type, count in created.iteritems()]
        ) + "\n"
    }


def build_init(argv, structures, pgup_config):
    logger = logging.getLogger("pgup.build_init")
    data = []
    for dbname, param in structures:
        if param in argv:
            structure_string = argv[param]
            structure = load_structure(structure_string)
            data.append((dbname, parse_structure(structure)))

    for dbname, dbdata in data:
        if dbdata["queries"]:
            DBDIR = u"{}/{}".format(argv["build"], dbname)
            DBFILES = u"{}/sql".format(DBDIR)
            subprocess.check_call("mkdir -p {}".format(DBFILES), shell=True)
            files = []
            counter = Counter()
            # save prepared sql
            for qry, name in zip(dbdata["queries"], dbdata["names"]):
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
                fstream.write("{}:\n".format(dbname) + dbdata["overview"])

            logger.info("{}: {}".format(dbname, DBDIR))
        else:
            with io.open(u"{}/overview.txt".format(argv["build"]), "a", encoding="utf-8") as fstream:
                fstream.write(u"{}: Queries not exists\n".format(dbname))

            logger.info("{}: Queries not exists".format(dbname))
