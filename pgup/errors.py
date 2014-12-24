# -*- coding: utf-8 -*-


class PgupException(Exception):
    pass

class TableException(PgupException):
    pass

class ColumnException(PgupException):
    pass

class ProcedureException(PgupException):
    pass

class ConfigException(PgupException):
    pass
