# -*- coding: utf-8 -*-


class PgupException(Exception):
    pass

class TableException(PgupException):
    pass

class ConfigException(PgupException):
    pass