# -*- coding: utf-8 -*-
import io
from pyparsing import CaselessKeyword, Word, Literal, Suppress, cStyleComment
from pyparsing import ZeroOrMore, OneOrMore, Optional, restOfLine
from pyparsing import alphas, nums, alphanums, SkipTo


def parse_header(header):
    CREATE = CaselessKeyword("CREATE")
    OR = CaselessKeyword("OR")
    REPLACE = CaselessKeyword("REPLACE")
    FUNCTION = CaselessKeyword("FUNCTION")
    IN = CaselessKeyword("IN")
    OUT = CaselessKeyword("OUT")
    INOUT = CaselessKeyword("INOUT")
    VARIADIC = CaselessKeyword("VARIADIC")
    NAME = (Word(alphas + "_."))("name")
    ALIAS = Word(alphas, alphas + "_")
    TYPE = (
        Word(alphas, alphanums + "[] ", ) + Suppress(Optional(Literal("(") + Word(nums) + Literal(")")))
    )
    PRM = (
        Optional(IN | OUT | INOUT | VARIADIC | (OUT + VARIADIC)) +
        Optional(ALIAS) +
        TYPE
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
    return parse_header.parseString(header)


class Procedure(object):

    _drop = 0
    _create = 0

    def __init__(self, fpath):
        self._fpath = fpath
        self._overloaded = []
        with io.open(fpath, encoding="utf-8") as fstream:
            self._procedure = fstream.read()

        try:
            self._header = parse_header(self._procedure)
        except Exception as error:
            print self._fpath
            raise error

    def __str__(self):
        return self._header[0]["name"]

    @classmethod
    def overview(cls):
        return u"PROCEDURE: CREATE {} / DROP {}".format(
            cls._create, cls._drop
        )

    def add_overloaded(self, procedure):
        self._overloaded.append(procedure)

    def drop(self):
        queries = []
        for h in self._header:
            Procedure._drop += 1
            queries.append(
                u"DROP FUNCTION {name}({input});".format(
                    name=h["name"],
                    input=u", ".join(h["input"])
                )
            )
        return "\n".join(queries)

    def create(self):
        Procedure._create += 1
        return self._procedure
