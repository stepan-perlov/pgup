# -*- coding: utf-8 -*-


class Counter(object):
    """
        Max size is 456976 == zzzz
    """
    def __init__(self):
        self._int_value = 0
        self._text_value = [97, 97, 97, 96]

    def next(self):
        self._int_value += 1

        i = len(self._text_value)
        while i > 0:
            i -= 1
            if self._text_value[i] == 122:
                self._text_value[i] = 97
            else:
                self._text_value[i] += 1
                break
        else:
            raise Exception("Max Counter size {}".format(self._int_value - 1))

    def get_intnum(self):
        return self._int_value

    def get_textnum(self):
        return "".join(chr(i) for i in self._text_value)
