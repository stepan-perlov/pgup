# -*- coding: utf-8 -*-
import re
import io
import logging
import collections

import yaml
from pake.shell import mkdir
from table import Table
from errors import PgupException
from counter import Counter


def parse_structure(structure_path):
    with open(structure_path) as fstream:
        structure = yaml.load(fstream)

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
            [u"{} {}".format(name, count) for name, count in created.iteritems()]
        )
    }

def build_init(args, argv, structures, pgup_config):
    logger = logging.getLogger("pgup.build_init")
    data = []
    for dbname, param in structures:
        if argv[param]:
            structure_path = argv[param]
            data.append( (dbname, parse_structure(structure_path)) )

    for dbname, dbdata in data:
        if dbdata["queries"]:
            DBDIR = u"{}/{}".format(args.build, dbname)
            DBFILES = u"{}/sql".format(DBDIR)
            mkdir("-p {}".format(DBFILES))
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
            with io.open(u"{}/overview.txt".format(DBDIR), "w", encoding="utf-8") as fstream:
                fstream.write(dbdata["overview"])

            logger.info("{}: {}".format(dbname, DBDIR))
        else:
            logger.info("{}: Queries not exists".format(dbname))
