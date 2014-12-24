# -*- coding: utf-8 -*-
import os
from pake.shell import find
from table import Table
from table import Column
from procedure import SqlFile
from procedure import Procedure


class Structure(object):

    def __init__(self, db, config):
        self._db = db
        self._config = config
        self._schemas, self._tables, self._procedures = [], {}, {}

    def add_schema(self, schema):
        if not schema in self._schemas:
            self._schemas.append(schema)

    def load_files(self):
        for schema in self._schemas:
            for tpath in ["{}/{}/{}".format(self._db, schema, path) for path in self._config.tables]:
                if os.path.exists(tpath):
                    for fpath in find("{} -name *.yaml".format(tpath)).split():
                        table = Table(fpath)
                        self._tables[str(table)] = table

            for ppath in ["{}/{}/{}".format(self._db, schema, path) for path in self._config.procedures]:
                if os.path.exists(ppath):
                    for fpath in find("{} -name *.sql".format(ppath)).split():
                        sql_file = SqlFile(fpath)
                        for header in sql_file.find_procedures_headers():
                            procedure = Procedure(sql_file, header)
                            if str(procedure) in self._procedures:
                                self._procedures[str(procedure)].add_overloaded(procedure)
                            else:
                                self._procedures[str(procedure)] = procedure


class Patch(object):

    def __init__(self, db, config):
        self._db = db
        self._config = config
        self._featured_schemas = []
        self._modify_tables, self._modify_procedures = {}, {}
        self._deleted_tables, self._deleted_procedures = {}, {}

    @staticmethod
    def overview():
        overview_list = [cls.overview() for cls in [Table, Column, Procedure]]
        return "\n".join(overview_list)

    def add_file(self, folder, fpath, action):
        IS_TABLE = folder in self._config.tables
        IS_PROCEDURE = folder in self._config.procedures
        IS_DELETED = action == "D"
        if IS_TABLE:
            table = Table(fpath)
            if IS_DELETED:
                self._deleted_tables[str(table)] = table
            else:
                self._modify_tables[str(table)] = table
        elif IS_PROCEDURE:
            sql_file = SqlFile(fpath)
            for header in sql_file.find_procedures_headers():
                print header
                procedure = Procedure(sql_file, header)
                if IS_DELETED:
                    if str(procedure) in self._deleted_procedures:
                        self._deleted_procedures[str(procedure)].add_overloaded(procedure)
                    else:
                        self._deleted_procedures[str(procedure)] = procedure
                else:
                    if str(procedure) in self._modify_procedures:
                        self._modify_procedures[str(procedure)].add_overloaded(procedure)
                    else:
                        self._modify_procedures[str(procedure)] = procedure

    def make(self, structure):
        queries = []
        queries += [table.drop() for table in self._deleted_tables]
        queries += [procedure.drop() for procedure in self._deleted_procedures]

        for name, table in self._modify_tables.iteritems():
            if name in structure._tables:
                old = structure._tables[name]
                queries.append(old.alter(table))
            else:
                queries.append(table.create())

        for name, procedure in self._modify_procedures.iteritems():
            if name in structure._procedures:
                old = structure._procedures[name]
                queries.append(old.drop())
            queries.append(procedure.create())

        return queries
