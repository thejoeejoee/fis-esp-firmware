# coding=utf-8
# (C) Copyright 2019 Josef Kolar (xkolar71)
# Licenced under MIT.
# Part of bachelor thesis.
import machine

try:
    # 'c' is available from boot.py
    c.start()
except Exception as e:
    machine.reset()
