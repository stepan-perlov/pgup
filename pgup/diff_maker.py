import os
import logging
import subprocess
from table import Table, Column
from procedure import SqlFile, Procedure
from build_init import load_structure, parse_structure

class DbChanges(object):
    def __init__(self, db, config):
        self._db = db
        self._config = config
        self._changed_schemas = []
        self._schemas_objects = {}
        self._symlinks = {}

        self._current_tables = {}
        self._current_procedures = {}

        self._schemas_diff = {}

    def _get_schema_ptr(self, schema):
        if not schema in self._changed_schemas:
            self._changed_schemas.append(schema)

            self._schemas_objects[schema] = {
                "modify_tables": {},
                "modify_procedures": {},
                "deleted_tables": [],
                "deleted_procedures": []
            }
        return self._schemas_objects[schema]

    def add_modify_file(self, schema, file_type, fpath):
        schema = self._get_schema_ptr(schema)

        if file_type == "table":
            table = Table(fpath)
            schema["modify_tables"][str(table)] = table
        elif file_type == "procedure":
            sql_file = SqlFile(fpath)
            for header in sql_file.find_procedures_headers():
                procedure = Procedure(sql_file, header)
                if str(procedure) in schema["modify_procedures"]:
                    schema["modify_procedures"][str(procedure)].add_overloaded(procedure)
                else:
                    schema["modify_procedures"][str(procedure)] = procedure


    def add_deleted_file(self, schema, file_type, fpath):
        schema = self._get_schema_ptr(schema)

        if file_type == "table":
            schema["deleted_tables"].append(fpath)
        elif file_type == "procedure":
            schema["deleted_procedures"].append(fpath)

    def find_symlink(self):
        """
            saved symlinks like ../<dbname>/<schema>
        """
        for symlink in subprocess.check_output("find {} -maxdepth 1 -type l".format(self._db), shell=True).split():
            linkPath = os.readlink(symlink)
            split = linkPath.split("/")
            if len(split) == 3:
                dbname, schema = split[1], split[2]
                if dbname in self._symlinks:
                    self._symlinks[dbname][schema] = "NEW"
                else:
                    self._symlinks[dbname] = dict([(schema, "NEW")])

    def find_symlink_diff(self):
        for symlink in subprocess.check_output("find {} -maxdepth 1 -type l".format(self._db), shell=True).split():
            linkPath = os.readlink(symlink)
            split = linkPath.split("/")
            if len(split) == 3:
                dbname, schema = split[1], split[2]
                if not dbname in self._symlinks:
                    self._symlinks[dbname] = {}

                if schema in self._symlinks[dbname]:
                    self._symlinks[dbname][schema] = "OLD"
                else:
                    self._symlinks[dbname][schema] = "DEL"

    def _load_tables(self, schema):
        for table_path in ["{}/{}/{}".format(self._db, schema, path) for path in self._config.tables]:
            if os.path.exists(table_path):
                for fpath in subprocess.check_output("find {} -name *.yaml".format(table_path), shell=True).split():
                    table = Table(fpath)
                    self._current_tables[str(table)] = table

    def _load_procedures(self, schema):
        for procedure_path in ["{}/{}/{}".format(self._db, schema, path) for path in self._config.procedures]:
            if os.path.exists(procedure_path):
                for fpath in subprocess.check_output("find {} -name *.sql".format(procedure_path), shell=True).split():
                    sql_file = SqlFile(fpath)
                    for header in sql_file.find_procedures_headers():
                        procedure = Procedure(sql_file, header)
                        if str(procedure) in self._current_procedures:
                            self._current_procedures[str(procedure)].add_overloaded(procedure)
                        else:
                            self._current_procedures[str(procedure)] = procedure

    def load_schemas_objects(self):
        for schema in self._changed_schemas:
            self._load_tables(schema)
            self._load_procedures(schema)

    def _add_schema_queries(self, schemaName, queries, names):
        if schemaName in self._schemas_diff:
            self._schemas_diff[schemaName]["queries"] += queries
            self._schemas_diff[schemaName]["names"] += names
        else:
            self._schemas_diff[schemaName] = {
                "queries": queries,
                "names": names
            }

    def drop_deleted(self):
        for schemaName in self._changed_schemas:
            schema = self._schemas_objects[schemaName]
            queries, names = [], []

            for fpath in schema["deleted_tables"]:
                table = Table(fpath)
                queries.append(table.drop())
                names.append("drop-table")

            for fpath in self._deleted_procedures:
                sql_file = SqlFile(fpath)
                for header in sql_file.find_procedures_headers():
                    procedure = Procedure(sql_file, header)
                    queries.append(procedure.drop())
                    names.append("drop-procedure")

            self._add_schema_queries(schemaName, queries, names)

    def make_diff(self):
        for schemaName in self._changed_schemas:
            schema = self._schemas_objects[schemaName]
            queries, names = [], []

            for name, table in schema["modify_tables"].iteritems():
                if name in self._current_tables:
                    old = self._current_tables[name]
                    queries.append(old.alter(table))
                    names.append("alter-table")
                else:
                    queries.append(table.create())
                    names.append("create-table")

            for name, procedure in schema["modify_procedures"].iteritems():
                if name in self._current_procedures:
                    old = self._current_procedures[name]
                    queries.append(old.drop())
                    names.append("drop-procedure")
                queries.append(procedure.create())
                names.append("create-procedure")

            self._add_schema_queries(schemaName, queries, names)

    def get_diff(self):
        result = {"queries": [], "names": []}
        for schemaName in self._changed_schemas:
            result["queries"] += self._schemas_diff[schemaName]["queries"]
            result["names"] += self._schemas_diff[schemaName]["names"]
        return result

class DiffMaker(object):
    def _get_diff(self, commit, config):
        """
            Find [A]dded, [D]eleted, [M]odify, [R]enamed files
            from commit
            which started with config.databases names
        """
        regexp = "\\\\|".join(["^[ADMR]\\\\s\\\\+{}".format(db) for db in config.databases])
        cmd = "git diff --name-status {} HEAD".format(self._argv["commit"])
        cmd2 = "grep {}".format(regexp)
        p = Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        p2 = Popen(cmd2, stdin=p.stdout, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        p.stdout.close()
        out, err = p2.communicate()
        if err.strip():
            raise Exception(err)
        print("$ {} | {}".format(cmd, cmd2))
        print(out)
        res = out.strip()
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

    def __init__(self, argv, config):
        self._argv = argv
        self._config = config
        self._diff = self._get_diff(argv["commit"], config)
        self._changes = self._init_changes(config)
        self._logger = logging.getLogger('pgup.diff.DiffMaker')
        self._overview = ""

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
        if len(split) > 2:
            db, schema, path = split[0], split[1], split[2]
        else:
            return

        if path in self._config.tables:
            file_type = "table"
        elif path in self._config.procedures:
            file_type = "procedure"
        else:
            file_type = "unknow"
            self._logger.warning("Unknow file type: {}".format(fpath))
            return

        if action == "D":
            self._changes[db].add_deleted_file(schema, file_type, fpath)
        else:
            self._changes[db].add_modify_file(schema, file_type, fpath)

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

        for db, dbchange in self._changes.iteritems():
            dbchange.find_symlink()
        git("checkout {}".format(self._argv["commit"]))
        for db, dbchange in self._changes.iteritems():
            dbchange.load_schemas_objects()
            dbchange.find_symlink_diff()
        git("checkout {}".format(HEAD))

    def _create_from_structure(self, dbname, schema):
        structure_string = self._argv["{}_structure".format(dbname)]
        if structure_string:
            structure = load_structure(structure_string)
            schema_structure = {"modules": []}
            IN_SCHEMA = False
            for module in structure["modules"]:
                keys = module.keys()
                if len(keys) > 1:
                    raise Exception("Incorrect module object {}".format(module))
                otype = keys[0]
                value = module[otype]

                if otype == "schema" and value == schema:
                    schema_structure["modules"].append(module)
                    IN_SCHEMA = True
                elif otype == "schema" and IN_SCHEMA:
                    break
                elif IN_SCHEMA:
                    schema_structure["modules"].append(module)
            result = parse_structure(schema_structure)
            self._overview += "\n  SYMLINK {}/{}: ".format(dbname, schema) + result["overview"]
            return result["queries"], result["names"]
        else:
            self._logger.warning("Argument not exists: {}".format("{}_structure".format(dbname)))
            return [], []

    def _get_symlinks_queries(self, symlinks):
        queries, names = [], []
        for dbname, db_object in symlinks.iteritems():
            for schema, state in db_object.iteritems():
                if state == "NEW":
                    queries, names = self._create_from_structure(dbname, schema)
                elif (
                    state == "OLD"
                    and dbname in self._changes
                    and schema in self._changes[dbname]._changed_schemas
                ):
                    schemaDiff = self._changes[dbname]._changed_schemas[schema]
                    queries += schemaDiff["queries"]
                    names += schemaDiff["names"]
                elif state == "DEL":
                    queries.append("DROP SCHEMA IF EXISTS {}".format(schema))
                    names.append("drop-schema")
        return queries, names

    def make(self):
        queries = {}
        names = {}
        symlinks = {}
        for db, dbchange in self._changes.iteritems():
            dbchange.make_diff()
            symlinks[db] = dbchange._symlinks

        for db, dbchange in self._changes.iteritems():
            queries[db], names[db] = self._get_symlinks_queries(symlinks[db])
            diff = dbchange.get_diff()
            queries[db] += diff["queries"]
            names[db] += diff["names"]
        return queries, names

    def overview(self):
        overview_list = ["  " + cls.overview() for cls in [Table, Column, Procedure]]
        return self._overview + "\n".join(overview_list) + "\n"
