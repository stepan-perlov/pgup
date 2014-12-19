# -*- coding: utf-8 -*-
import yaml


class Procedure(object):

    def __init__(self, fpath):
        self._fpath = fpath
        with open(fpath) as fstream:
            procedure = yaml.load(fstream)
        self._parse(procedure)

    def _parse(self, procedure):
        pass

from pyparsing import Word, WordStart, WordEnd, Optional, Suppress, alphas, nums, CaselessKeyword, ZeroOrMore, alphanums, Literal, Forward, Group

CREATE = CaselessKeyword("CREATE")
OR = CaselessKeyword("OR")
REPLACE = CaselessKeyword("REPLACE")
FUNCTION = CaselessKeyword("FUNCTION")
NAME = (Word(alphas + "_."))("name")
COMMA = Literal(",")
#TYPE = Forward()
#TYPE << (WordStart(alphas) + Word(alphanums + "[]()"))("type")
TYPE = (WordStart(alphas) + Word(alphanums) + Optional(WordEnd("[]")) + Optional(Literal("(") + Word(nums) + WordEnd(")")) )("type")
ARG = Forward()
ARG << Suppress("(") + ZeroOrMore(TYPE + Optional(COMMA)) + Suppress(")")

parse_header = (CREATE + OR + REPLACE + FUNCTION + NAME + ARG).setParseAction(lambda t: {"name": t})
print parse_header.parseString("CREATE OR REPLACE FUNCTION um.add_user(str, text, int)")
