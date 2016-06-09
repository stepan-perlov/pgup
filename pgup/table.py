# -*- coding: utf-8 -*-
import os
from copy import copy
from collections import OrderedDict

import yaml
from jinja2 import Environment, FileSystemLoader
j2 = Environment(
    loader=FileSystemLoader(os.path.join(os.path.dirname(__file__), "templates")),
    trim_blocks=True,
    lstrip_blocks=True
)

from errors import TableException, ColumnException


class Table(object):

    _alter = 0
    _create = 0
    _drop = 0

    def __init__(self, fpath):
        self._fpath = fpath
        self._like = []
        self._columns = OrderedDict([])
        self._inherits = []
        with open(fpath) as fstream:
            table = yaml.load(fstream)

        self._parse(table)

    def __str__(self):
        return self._name

    def __repr__(self):
        return "<Table object {}>".format(self._name)

    @classmethod
    def overview(cls):
        return u"TABLE: CREATE {} / DROP {} / ALTER {}".format(
            cls._create, cls._drop, cls._alter
        )

    def alter(self, table):
        exists, columns_actions, columns_comments = [], [], []
        for name, old_clm in self._columns.iteritems():
            if name in table._columns:
                new_clm = table._columns[name]
                # store result to Column class
                if old_clm != new_clm:
                    columns_actions += Column.actions
                    if Column.comment:
                        columns_comments.append(Column.comment)
                exists.append(name)
            else:
                columns_actions.append(old_clm.drop())

        for new_name in set(table._columns.keys()) - set(exists):
            new_clm = table._columns[new_name]
            actions, comment = new_clm.add()
            columns_actions += actions
            columns_comments.append(comment)

        Table._alter += 1

        return j2.get_template("alter_table.j2").render({
            "name": str(self),
            "columns_actions": columns_actions,
            "columns_comments": columns_comments
        })

    def create(self):
        columns = []
        comments_on_columns = []
        for name, clm in self._columns.iteritems():
            columns.append({"name": name, "definition": clm.definition})
            comments_on_columns.append({"name": name, "comment": clm.description})

        Table._create += 1

        return j2.get_template("create_table.j2").render({
            "name": str(self),
            "comment": self.description,
            "like": self._like,
            "columns": columns,
            "comments_on_columns": comments_on_columns,
            "inherits": self._inherits
        })

    def drop(self):
        Table._drop += 1
        return u"DROP TABLE {};".format(self)

    def _add_column(self, column):
        if column.name in self._columns:
            raise TableException("Duplicate column name {}.{}".format(self, column.name))

        self._columns[column.name] = column

    def _parse(self, table):
        if "table" in table:
            self._name = table["table"]
        else:
            raise TableException("table must specified - {}".format(self._fpath))

        if "description" in table:
            self.description = table["description"]
        else:
            self.description = None

        HAVE_COLUMNS = "columns" in table
        HAVE_INHERITS = "inherits" in table

        if not HAVE_COLUMNS or not HAVE_INHERITS:
            raise TableException("columns or inherits must specified".format(self._fpath))

        if HAVE_COLUMNS:
            for i, clm in enumerate(table["columns"]):
                # new yaml style by olap mans
                dump = {}
                if len(clm.keys()) == 1:
                    name = clm.keys()[0]
                    value = clm[name]
                    if name.upper() == "LIKE":
                        self._like.append(value)
                        continue
                    else:
                        if type(value) == str:
                            dump = {
                                "name": name,
                                "type": value
                            }
                        elif type(value) == dict:
                            if "type" in value:
                                dump = copy(value)
                                dump["name"] = name
                            else:
                                raise TableException("type must specified - {}:{}".format(self._fpath, clm))
                        else:
                            raise TableException("Incorrect value type - {}:{}".format(self._fpath, clm))
                    self._add_column(Column(i, dump))
                # old mezzo table yaml style
                else:
                    if not "name" in clm:
                        raise TableException("name must specified - {}:{}".format(self._fpath, clm))
                    if not "type" in clm:
                        raise TableException("type must specified - {}:{}".format(self._fpath, clm))

                    self._add_column(Column(i, clm))

        if HAVE_INHERITS:
            self._inherits = table["inherits"]


class Column(object):
    actions = []
    comment = None

    _add = 0
    _drop = 0
    _set_data_type = 0
    _set_default = 0
    _drop_default = 0
    _set_not_null = 0
    _drop_not_null = 0

    ADD_COLUMN = u"ADD COLUMN {name} {type}"
    DROP_COLUMN = u"DROP COLUMN IF EXISTS {name}"
    SET_DATA_TYPE = u"ALTER COLUMN {name} SET DATA TYPE {type}"
    DROP_DEFAULT = u"ALTER COLUMN {name} DROP DEFAULT"
    SET_DEFAULT = u"ALTER COLUMN {name} SET DEFAULT {default}"
    SET_NOT_NULL = u"ALTER COLUMN {name} SET NOT NULL"
    DROP_NOT_NULL = u"ALTER COLUMN {name} DROP NOT NULL"

    @classmethod
    def overview(cls):
        return u"COLUMN: ADD {} / DROP {} / SET DATA TYPE {} / SET DEFAULT {} / DROP DEFAULT {} / SET NOT NULL {} / DROP NOT NULL {}".format(
            cls._add, cls._drop, cls._set_data_type, cls._set_default, cls._drop_default, cls._set_not_null, cls._drop_not_null
        )

    def add(self):
        actions = []
        actions.append(Column.ADD_COLUMN.format(name=self.name, type=self.type))

        if self.not_null:
            actions.append(Column.SET_NOT_NULL.format(name=self.name))

        if self.default != None:
            actions.append(Column.SET_DEFAULT.format(name=self.name, default=self.default))

        if self.description == None:
            comment = u"{} IS 'NULL'".format(self.name)
        else:
            comment = u"{} IS '{}'".format(self.name, self.description)

        Column._add += 1
        return actions, comment

    def drop(self):
        Column._drop += 1
        return Column.DROP_COLUMN.format(name=self.name)

    def __init__(self, index, params):
        self.index = index
        self.name = params["name"]
        self.type = params["type"]
        self.not_null = False
        self.default = None
        self.description = None
        self.definition = u"{} {}".format(self.name, self.type)
        if "not_null" in params:
            self.not_null = params["not_null"]
            if self.not_null:
                self.definition = u"{} NOT NULL".format(self.definition)
        if "default" in params:
            self.default = params["default"]
            self.definition = u"{} DEFAULT {}".format(self.definition, self.default)
        if "description" in params:
            self.description = params["description"]

    def __ne__(self, column):
        if type(column) != Column:
            raise ColumnException("Column object can't compare with {}".format(type(column)))

        ne = False
        Column.actions = []
        Column.comment = None

        if self.type != column.type:
            Column.actions.append(Column.SET_DATA_TYPE.format(name=column.name, type=column.type))
            Column._set_data_type += 1
            ne = True

        if self.not_null != column.not_null:
            if column.not_null:
                Column.actions.append(Column.SET_NOT_NULL.format(name=column.name))
                Column._set_not_null += 1
            else:
                Column.actions.append(Column.DROP_NOT_NULL.format(name=column.name))
                Column._drop_not_null += 1
            ne = True

        if self.default != column.default:
            if column.default == None:
                Column.actions.append(Column.DROP_DEFAULT.format(name=column.name))
                Column._drop_default += 1
            else:
                Column.actions.append(Column.SET_DEFAULT.format(name=column.name, default=column.default))
                Column._set_default += 1
            ne = True

        if self.description != column.description:
            if column.description == None:
                Column.comment = u"{} IS 'NULL'".format(column.name)
            else:
                Column.comment = u"{} IS '{}'".format(column.name, column.description)
            ne = True

        return ne
