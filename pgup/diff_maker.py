import os
import logging
from pake.shell import git, find
from table import Table, Column
from procedure import SqlFile, Procedure


class DbChanges(object):
    def __init__(self, db, config):
        self._db = db
        self._config = config
        self._schemas = []
        self._current_tables = {}
        self._current_procedures = {}
        self._modify_tables = {}
        self._modify_procedures = {}
        self._deleted_tables = []
        self._deleted_procedures = []

    def add_schema(self, schema):
        if not schema in self._schemas:
            self._schemas.append(schema)

    def add_modify_file(self, file_type, fpath):
        if file_type == "table":
            table = Table(fpath)
            self._modify_tables[str(table)] = table
        elif file_type == "procedure":
            sql_file = SqlFile(fpath)
            for header in sql_file.find_procedures_headers():
                procedure = Procedure(sql_file, header)
                if str(procedure) in self._modify_procedures:
                    self._modify_procedures[str(procedure)].add_overloaded(procedure)
                else:
                    self._modify_procedures[str(procedure)] = procedure

    def add_deleted_file(self, file_type, fpath):
        if file_type == "table":
            self._deleted_tables.append(fpath)
        elif file_type == "procedure":
            self._deleted_procedures.append(fpath)

    def _load_current_tables(self, schema):
        for table_path in ["{}/{}/{}".format(self._db, schema, path) for path in self._config.tables]:
            if os.path.exists(table_path):
                for fpath in find("{} -name *.yaml".format(table_path)).split():
                    table = Table(fpath)
                    self._current_tables[str(table)] = table

    def _load_current_procedures(self, schema):
        for procedure_path in ["{}/{}/{}".format(self._db, schema, path) for path in self._config.procedures]:
            if os.path.exists(procedure_path):
                for fpath in find("{} -name *.sql".format(procedure_path)).split():
                    sql_file = SqlFile(fpath)
                    for header in sql_file.find_procedures_headers():
                        procedure = Procedure(sql_file, header)
                        if str(procedure) in self._current_procedures:
                            self._current_procedures[str(procedure)].add_overloaded(procedure)
                        else:
                            self._current_procedures[str(procedure)] = procedure

    def load_schemas_objects(self):
        for schema in self._schemas:
            self._load_current_tables(schema)
            self._load_current_procedures(schema)

    def _drop_deleted(self):
        queries = []
        names = []
        for fpath in self._deleted_tables:
            table = Table(fpath)
            queries.append(table.drop())
            names.append("drop-table")

        for fpath in self._deleted_procedures:
            sql_file = SqlFile(fpath)
            for header in sql_file.find_procedures_headers():
                procedure = Procedure(sql_file, header)
                queries.append(procedure.drop())
                names.append("drop-procedure")
        return queries, names

    def make_diff(self):
        queries, names = self._drop_deleted()

        for name, table in self._modify_tables.iteritems():
            if name in self._current_tables:
                old = self._current_tables[name]
                queries.append(old.alter(table))
                names.append("alter-table")
            else:
                queries.append(table.create())
                names.append("create-table")

        for name, procedure in self._modify_procedures.iteritems():
            if name in self._current_procedures:
                old = self._current_procedures[name]
                queries.append(old.drop())
                names.append("drop-procedure")
            queries.append(procedure.create())
            names.append("create-procedure")

        return queries, names


class DiffMaker(object):
    def _get_diff(self, commit, config):
        """
            Find [A]dded, [D]eleted, [M]odify, [R]enamed files
            from commit
            which started with config.databases names
        """
        regexp = "\\\\|".join(["^[ADMR]\\\\s\\\\+{}".format(db) for db in config.databases])
        pipe = git("diff --name-status {} HEAD".format(self._commit), pipe=True)
        res = pipe.grep(regexp).strip()
        if res:
            diff = res.split("\n")
        else:
            diff = []
        return diff

    def _init_changes(self, config):
        changes = {}
        for db in config.databases:
            changes[db] = DbChanges(db, config)
        return changes

    def __init__(self, commit, config):
        self._commit = commit
        self._config = config
        self._diff = self._get_diff(commit, config)
        self._changes = self._init_changes(config)
        self._logger = logging.getLogger('pgup.diff.DiffMaker')

    def _add_change(self, line):
        """
            Example:

                line = "D    gui_db/system/internal/_get_param.sql
                action, fpath = "D", "gui_db/system/internal/_get_param.sql"
                split = ["gui_db", "system", "internal", "_get_params.sql"]
                db, schema, path = "gui_db", "system", "internal"
        """
        action, fpath = line.split("\t")
        split = fpath.split("/")
        path = None
        schema = None
        if len(split) > 2:
            db, schema, path = split[0], split[1], split[2]
        elif len(split) == 2:
            db, schema = split[0], split[1]

        if path in self._config.tables:
            file_type = "table"
        elif path in self._config.procedures:
            file_type = "procedure"
        elif os.path.islink(fpath):
            file_type = "symlink"
            # TODO add symlink logic
            return
        else:
            file_type = "unknow"
            self._logger.warning("Unknow file type: {}".format(fpath))
            return

        if schema:
            self._changes[db].add_schema(schema)

        if action == "D":
            self._changes[db].add_deleted_file(file_type, fpath)
        else:
            self._changes[db].add_modify_file(file_type, fpath)

    def prepare(self):
        """
            Sorted finded files to databases-types
        """
        [self._add_change(line) for line in self._diff]
        current_branch = git("rev-parse --abbrev-ref HEAD").strip()
        if current_branch == "HEAD":
            HEAD = git("rev-parse HEAD").strip()
        else:
            HEAD = current_branch

        git("checkout {}".format(self._commit))
        [dbchange.load_schemas_objects() for db, dbchange in self._changes.iteritems()]
        git("checkout {}".format(HEAD))

    def make(self):
        queries = {}
        names = {}
        for db, dbchange in self._changes.iteritems():
            queries[db], names[db] = dbchange.make_diff()
        return queries, names

    def overview(self):
        overview_list = ["  " + cls.overview() for cls in [Table, Column, Procedure]]
        return "\n".join(overview_list) + "\n"
