# -*- coding: utf-8 -*-
from pake.shell import find
from table import Table
from procedure import Procedure


class Structure(object):

    def __init__(self, db, config):
        self._db = db
        self._config = config
        self._schemas, self._tables, self._procedures = [], {}, {}

    def add_shema(self, schema):
        if not schema in self._schemas:
            self._schemas.append(schema)

    def load_files(self):
        for schema in self._schemas:
            for tpath in ["{}/{}/{}".format(self._db, schema, path) for path in self._config.tables]:
                for fpath in find("{} -name *.yaml".format(tpath)).split():
                    table = Table(tpath)
                    self._tables[str(table)] = table

            for ppath in ["{}/{}/{}".format(self._db, schema, path) for path in self._config.procedures]:
                for fpath in find("{} -name *.sql".format(ppath)).split():
                    procedure = Procedure(fpath)
                    self._procedures[str(procedure)] = procedure


class Patch(object):

    def __init__(self, db, config):
        self._db = db
        self._config = config
        self._featured_schemas = []
        self._modify_tables, self._modify_procedures = [], []
        self._deleted_tables, self._deleted_procedures = {}, {}

    def add_file(self, folder, fpath, action):
        IS_TABLE = folder in self._config.tables
        IS_PROCEDURE = folder in self._config.procedures
        IS_DELETED = action == "D"
        if IS_TABLE and IS_DELETED:
            table = Table(fpath)
            self._deleted_tables[str(table)] = table
        elif IS_TABLE:
            self._modify_tables.append(fpath)
        elif IS_PROCEDURE and IS_DELETED:
            procedure = Procedure(fpath)
            self._deleted_procedures[str(procedure)] = procedure
        elif IS_PROCEDURE:
            self._modify_procedures.append(fpath)

    def make(self, structure):
        pass
