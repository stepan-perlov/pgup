# -*- coding: utf-8 -*-
import os
import yaml
from errors import ConfigException


class Config(object):
    _cache = {}

    def __init__(self, fpath="/etc/pgup.yaml"):
        if os.path.exists(fpath):
            with open(fpath) as fstream:
                config = yaml.load(fstream)
        else:
            raise ConfigException("Config not found: {}".format(fpath))

        if type(config) == dict:
            self.__dict__ = config
        else:
            raise ConfigException("Config type must be dict: {}".format(type(config)))

    @classmethod
    def get(cls, fpath):
        if not fpath in cls._cache:
            cls._cache[fpath] = Config(fpath)
        return cls._cache[fpath]
