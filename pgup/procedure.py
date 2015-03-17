# -*- coding: utf-8 -*-
import os
import io
from pyparsing import CaselessKeyword, Word, Literal, Suppress, cStyleComment
from pyparsing import ZeroOrMore, OneOrMore, Optional, restOfLine
from pyparsing import alphas, nums, alphanums, SkipTo
from errors import ProcedureException


class SqlFile(object):

    def __init__(self, fpath):
        self._fpath = fpath
        self._get_called = False

        if os.path.exists(fpath):
            with io.open(fpath, encoding="utf-8") as fstream:
                self._sql = fstream.read()
        else:
            raise ProcedureException("File not found {}".format(fpath))

    def get(self):
        if self._get_called:
            return ""
        else:
            self._get_called = True
            return self._sql

    def find_procedures_headers(self):
        CREATE = CaselessKeyword("CREATE")
        OR = CaselessKeyword("OR")
        REPLACE = CaselessKeyword("REPLACE")
        FUNCTION = CaselessKeyword("FUNCTION")
        IN = CaselessKeyword("IN")
        OUT = CaselessKeyword("OUT")
        INOUT = CaselessKeyword("INOUT")
        VARIADIC = CaselessKeyword("VARIADIC")
        NAME = (Word(alphas, alphanums + "_."))("name")
        ALIAS = Word(alphas, alphanums + "_")
        TYPE = (
            Word(alphas, alphanums + "[]_. ", ) + Suppress(Optional(Literal("(") + Word(nums) + Literal(")")))
        )
        PRM = (
            (Optional(IN | OUT | INOUT | VARIADIC | (OUT + VARIADIC)) +
            Optional(ALIAS) +
            TYPE) | TYPE
        ).setParseAction(lambda res: " ".join([w.strip() for w in res]))
        COMMENT = "--" + restOfLine
        COMMA = Suppress(",")
        PARAMS = ZeroOrMore(
            PRM +
            Optional(COMMA)
        )("input")
        PARAMS.ignore(COMMENT)
        HEADER = (
            CREATE + Optional(OR) + Optional(REPLACE) + FUNCTION + NAME +
            Suppress("(") + PARAMS  + Suppress(")")
        ).setParseAction(lambda res: {"name": res.name, "input": res.input})

        parse_header = OneOrMore(HEADER | Suppress(SkipTo(HEADER)))
        parse_header.ignore(COMMENT)
        parse_header.ignore(cStyleComment)
        try:
            headers = parse_header.parseString(self._sql)
        except Exception as error:
            print self._fpath
            raise error
        return headers


class Procedure(object):

    _drop = 0
    _create = 0

    def __init__(self, sql_file, header):
        self._sql_file = sql_file
        self._header = header
        self._overloaded = []

    def __str__(self):
        return self._header["name"]

    @classmethod
    def overview(cls):
        return u"PROCEDURE: CREATE {} / DROP {}".format(
            cls._create, cls._drop
        )

    def add_overloaded(self, procedure):
        self._overloaded.append(procedure)

    def drop(self):
        queries = []
        queries.append(
            u"DROP FUNCTION {name}({input});".format(
                name=self._header["name"],
                input=u", ".join(self._header["input"])
            )
        )
        for proc in self._overloaded:
            queries.append(proc.drop())
        Procedure._drop += 1
        return "\n".join(queries) + "\n"

    def create(self):
        queries = []
        queries.append(self._sql_file.get())
        for proc in self._overloaded:
            queries.append(proc.create())
        Procedure._create += 1
        return "\n".join(queries) + "\n"
