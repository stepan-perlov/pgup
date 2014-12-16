# -*- coding: utf-8 -*-
import yaml
from errors import TableException


class Table(object):
    _columns = []

    def __init__(self, fpath):
        self._fpath = fpath
        with open(fpath) as fstream:
            table = yaml.load(fstream)

        self.parse(table)

    def parse(self, table):
        if "table" in table:
            self._name = table["table"]
        else:
            raise TableException("table must specified - {}".format(self._fpath))

        if "columns" in table:
            for clm in table["columns"]:
                if len(clm.keys()) == 1:
                    name = clm.keys()[0]

                else:
                    if not "name" in clm:
                        raise TableException("name must specified - {}:{}".format(self._fpath, clm))
                    if not "type" in clm:
                        raise TableException("type must specified - {}:{}".format(self._fpath, clm))
