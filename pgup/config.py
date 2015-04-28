# -*- coding: utf-8 -*-
import os
import json
import yaml
from errors import ConfigException


class Config(object):
    _cache = {}

    def __init__(self, config_string="/etc/pgup.yaml"):
        if config_string.endswith(".yaml"):
            fpath = config_string
            if os.path.exists(fpath):
                with open(fpath) as fstream:
                    config = yaml.load(fstream)
            else:
                raise ConfigException("Config not exists: {}".format(fpath))
        else:
            config = json.loads(config_string)

        if type(config) == dict:
            self.__dict__ = config
        else:
            raise ConfigException("Config type must be dict: {}".format(type(config)))

    @classmethod
    def get(cls, fpath):
        if not fpath in cls._cache:
            cls._cache[fpath] = Config(fpath)
        return cls._cache[fpath]
