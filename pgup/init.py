# -*- coding: utf-8 -*-
import io
import yaml
from table import Table
from errors import PgupException

def get_sql_from_structure(structure):
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
    return queries, names


def init(gui_db_structure_path, cached_db_structure_path, config):
    with open(gui_db_structure_path) as fstream:
        gui_db_structure = yaml.load(fstream)

    queries, names = {}, {}
    queries["gui_db"], names["gui_db"] = get_sql_from_structure(gui_db_structure)

    if cached_db_structure_path and cached_db_structure_path != "gui_db":
        with open(cached_db_structure_path) as fstream:
            cached_db_structure = yaml.load(fstream)
        queries["cached_db"], names["cached_db"] = get_sql_from_structure(cached_db_structure)

    res = {
        "overview": Table.overview(),
        "queries": queries,
        "names": names
    }
    return res
