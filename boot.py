# coding=utf-8
# (C) Copyright 2019 Josef Kolar (xkolar71)
# Licenced under MIT.
# Part of bachelor thesis.
try:
    from fis.core import Core
    c = Core()
except Exception as e:
    print('ERROR: ', e)
