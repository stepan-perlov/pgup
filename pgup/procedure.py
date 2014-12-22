# -*- coding: utf-8 -*-
from pyparsing import CaselessKeyword, Word, Literal, Suppress, cStyleComment
from pyparsing import ZeroOrMore, OneOrMore, Optional, restOfLine, CharsNotIn
from pyparsing import alphas, nums, alphanums, Regex, SkipTo


def parse_header(header):
    CREATE = CaselessKeyword("CREATE")
    OR = CaselessKeyword("OR")
    REPLACE = CaselessKeyword("REPLACE")
    FUNCTION = CaselessKeyword("FUNCTION")
    IN = CaselessKeyword("IN")
    OUT = CaselessKeyword("OUT")
    NAME = (Word(alphas + "_."))("name")
    ALIAS = Word(alphas, alphas + "_")
    TYPE = (
        Word(alphas, alphanums + "[] ", ) + Suppress(Optional(Literal("(") + Word(nums) + Literal(")")))
    )
    PRM = (
        Optional( Suppress(IN) + Suppress(ALIAS) ) +
        Optional( OUT + Suppress(ALIAS) ) +
        TYPE
    ).setParseAction(lambda res: "" if res[0].startswith("OUT") else res[0].strip())
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
    ).setParseAction(lambda res: {"name": res.name, "input": [t for t in res.input if t]})

    parse_header = OneOrMore(HEADER | Suppress(SkipTo(HEADER)))
    parse_header.ignore(COMMENT)
    parse_header.ignore(cStyleComment)
    return parse_header.parseString(header)


class Procedure(object):

    _drop = 0
    _create = 0

    def __init__(self, fpath):
        self._fpath = fpath
        with open(fpath) as fstream:
            self._procedure = fstream.read()

        self._parse(self._procedure)

    @classmethod
    def overview(cls):
        return u"PROCEDURE: CREATE {} / DROP {}".format(
            cls._create, cls._drop
        )

    def _parse(self, procedure):
        try:
            self._header = parse_header(procedure)
        except Exception as error:
            print self._fpath
            raise error

    def drop(self):
        for h in self._header:
            Procedure._drop += 1
            return "DROP FUNCTION {name}({input});".format(
                name=h["name"],
                input=", ".join(h["input"])
            )

    def create(self):
        Procedure._create += 1
        return self._procedure
