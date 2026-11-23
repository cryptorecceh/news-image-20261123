#!/usr/bin/env python3
"""Monday 23 November 2026 world news, summed up in one 1024x1024 image.

Standard library only (Python 3.13): no third-party imports, no
network, no clock, no randomness. All artwork (text, map, charts) is
drawn procedurally from the data tables in this file, and the PNG
encoder is written here too, on top of stdlib zlib.

Run:  python3 main.py [--output entry.png] [--check]
The default output is /output/entry.png (or $MAKEFUN_OUTPUT_DIR/entry.png).
Two runs write byte-identical output.
"""

import argparse
import base64
import math
import os
import struct
import sys
import zlib

# ---------------------------------------------------------------- fonts
# 1-bit bitmap fonts, rasterised from Liberation fonts at build time.
# Blob layout: glyphs in codepoint order; each glyph starts with one
# width byte, then ceil(width/8)*height bitmap bytes (MSB-first,
# row-major).
# CHARS is ASCII 32-126 plus middle dot, em dash, right quote, euro.
CHARS = [chr(c) for c in range(32, 127)] + ["\u00b7", "\u2014", "\u2019", "\u20ac"]
# The masthead serif only renders "Sunday 22 November 2026", so its
# blob holds just those characters, in codepoint order.
SERIF_CHARS = " 0126NSabdemnortuvy"

F_SANS10 = "AwAAAAAAAAAAAAAAAAADAAAAQEBAQEAAQAAAAAQAAACgIAAAAAAAAAAABgAAAAgI/ED4EBAAAAAGAAAAeIBgMAgIeAAAAAkAAAAAAABiAIQAgABrABQAFAAjAAAAAAAAAAcAAAA4CDBklIh0AAAAAgAAAAAAAAAAAAAAAAAEAAAAIEBAQEBAQEAgAAQAAACAQAAgICAAQIAABAAAAADgYCAAAAAAAAAGAAAAAAAAeAAAAAAAAAMAAAAAAAAAAABAQAAABAAAAAAAAABgAAAAAAADAAAAAAAAAAAAQAAAAAMAAAAgAEBAQICAAAAABgAAAHBIiIiISHAAAAAGAAAAIGAgICAgeAAAAAYAAABwSAgQIEB4AAAABgAAAHAICDAICHAAAAAGAAAAEDAwUBD4EAAAAAYAAAB4QHAICAhwAAAABgAAADBAcEhISDAAAAAGAAAAeAgQICAgIAAAAAYAAABwSEhwSEhwAAAABgAAAHBICEh4CHAAAAADAAAAAABAAAAAQAAAAAMAAAAAAEAAAABAQAAABgAAAAAIMMAwCAAAAAAGAAAAAAB4AHgAAAAAAAYAAAAAQDAIMEAAAAAABgAAAHBICBAgACAAAAALAAAAAAAAHwAggE4AUgASgFsAQAAeAAAAAAAHAAAAECAoSHxEggAAAAcAAAB4RER4RER4AAAACAAAADxCQEBAQjwAAAAIAAAAeERCQkJEeAAAAAcAAAB8QEB8QEB8AAAABwAAAHxAQHhAQEAAAAAIAAAAPEJADkJCPAAAAAgAAABERER8REREAAAAAwAAAEBAQEBAQEAAAAAFAAAAMBAQEBCQcAAAAAcAAABESFBwUEhEAAAABgAAAEBAQEBAQHgAAAAJAAAAAAAAQwBjAGUARQBRAFkASQAAAAAAAAAIAAAAYmJSUkpGQgAAAAgAAAA8QkKCQkI8AAAABwAAAHhERER4QEAAAAAIAAAAPEJCgkJCPAgMAAgAAAB8RER4SEREAAAABwAAADhEQDgERHgAAAAHAAAA/BAQEBAQEAAAAAgAAABEREREREQ4AAAABwAAAIREREgoMBAAAAAKAAAAAAAAiICMgESAVQBRADMAIwAAAAAAAAAHAAAARAgwEChIRAAAAAcAAABESCgwEBAQAAAABwAAAHwIECAgQPwAAAADAAAAQEBAQEBAQEBAAAMAAACAgABAQAAgAAAAAwAAAMBAQEBAQEBAwAAFAAAAIFAQgAAAAAAAAAYAAAAAAAAAAAAAAPgABAAAQAAAAAAAAAAAAAAGAAAAAABwCHiIaAAAAAYAAABAQHBISEhwAAAABQAAAAAAcECAQHAAAAAGAAAACAh4SIhIeAAAAAYAAAAAAHBI+EBwAAAAAwAAAGBA4EBAQEAAAAAGAAAAAAB4CIgIaAhwAAYAAABAQHBISEhIAAAAAwAAAAAAQEBAQEAAAAADAAAAAABAQEBAQECAAAUAAABAQFBgYFBIAAAAAwAAAEBAQEBAQEAAAAAJAAAAAAAAAAAAAHYASQBJAEkASQAAAAAAAAAGAAAAAABwSEhISAAAAAYAAAAAAHBIiEhwAAAABgAAAAAAcEhISHBAQAAGAAAAAAB4SIhIeAgIAAQAAAAAAGBAQEBAAAAABQAAAAAAcEAwCHAAAAADAAAAAEDAQEBAQAAAAAYAAAAAAEhISEhoAAAABQAAAAAAiFBQUCAAAAAIAAAAAACSmmhsZAAAAAUAAAAAAFBQIFCIAAAABQAAAAAAiFBQMCAgQAAFAAAAAABwECBA8AAAAAQAAAAgQEBAwEBAQCAAAwAAAEBAQEBAQEBAQAAEAAAAwEBAQCBAQEDAAAYAAAAAAGAYAAAAAAAABAAAAAAAAEAAAAAAAAAKAAAAAAAAAAAAAAAAAAD/wAAAAAAAAAAAAAADAAAAQAAAAAAAAAAAAAYAAAA4QPBA8EA4AAAA"
F_SANS12 = "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"
F_SANSB10 = "AwAAAAAAAAAAAAAAAAAEAAAAQEBAQEAAQAAAAAUAAABQUFAAAAAAAAAABgAAACgIeFD4UBAAAAAGAAAAeMBgeAgIeAAAAAkAAAAAAABiAJQAlABrABSAFIAjAAAAAAAAAAgAAAA4KDh0XEx+AAAAAwAAAEBAQAAAAAAAAAAEAAAAIEBAQEBAQEAgAAQAAADAQGBgYGBgQMAABAAAAEDwYCAAAAAAAAAGAAAAACAg+DAgAAAAAAMAAAAAAAAAAABAQEAABAAAAAAAAADgAAAAAAADAAAAAAAAAAAAQAAAAAMAAABgQEBAQMCAAAAABgAAAHBYyMjIWHAAAAAGAAAAcHAwMDAweAAAAAYAAABwWBgQIED4AAAABgAAAHBYGDAYyHAAAAAGAAAAGDg4WNj8GAAAAAYAAAB4QHBYCNhwAAAABgAAADBYwPjISHAAAAAGAAAA+BgQMCAgIAAAAAYAAABwSFhwyMhwAAAABgAAAHDYyHgIWHAAAAAEAAAAAABAAAAAQAAAAAQAAAAAAEAAAABAAEAABgAAAAAIcMBwCAAAAAAGAAAAAAD4APgAAAAAAAYAAAAAwDgIOMAAAAAABwAAAHhICBgwADAAAAAKAAAAAAAAHgAhgE6AUoACgAaAWwBAAD4AAAAIAAAAGDgoLHxExgAAAAgAAAB8RER8RkZ8AAAACAAAADxmQMBAZjwAAAAIAAAAeExGRkZMeAAAAAcAAAB8QEB8QEB8AAAABwAAAHxAQHxAQEAAAAAIAAAAPGZAzkJmPAAAAAgAAABGRkZ+RkZGAAAAAwAAAEBAQEBAQEAAAAAGAAAAOBgYGBjYcAAAAAgAAABESFBwSExGAAAABwAAAEBAQEBAQHwAAAAJAAAAAAAAYwBnAGcAVwBbAFsASwAAAAAAAAAIAAAAZmZ2Vl5ORgAAAAgAAAA8ZkLCQmY8AAAABwAAAHhMREx4QEAAAAAIAAAAPGZCwkJmPAgOAAgAAAB8RkZ8TERGAAAABwAAAHhMYDwERHgAAAAHAAAA/DAwMDAwMAAAAAgAAABGRkZGRmQ4AAAABwAAAMRETGgoODAAAAAKAAAAAAAAzIDMgF2AVYB3AHMAMwAAAAAAAAAHAAAARGg4MDhsxAAAAAcAAADEbCgwEBAQAAAABwAAAHwIEDBgQPwAAAAEAAAAYEBAQEBAQEBgAAMAAACAwEBAQEBgAAAABAAAAOBgYGBgYGBg4AAGAAAAMHBIyAAAAAAAAAYAAAAAAAAAAAAAAPgABAAAQCAAAAAAAAAAAAAGAAAAAABwGHjYbAAAAAcAAABAQHhMTEx4AAAABgAAAAAAcEjASHAAAAAHAAAACAh4SMhIeAAAAAYAAAAAAHBI+EB4AAAABAAAAGBA4EBAQEAAAAAHAAAAAAB4SMhIeAh4AAcAAABAQHhISEhIAAAAAwAAAEAAQEBAQEAAAAADAAAAQABAQEBAQEDAAAYAAABAQFhQcFhIAAAAAwAAAEBAQEBAQEAAAAAJAAAAAAAAAAAAAFsASQBJAEkASQAAAAAAAAAHAAAAAABYSEhISAAAAAcAAAAAAHhMzEh4AAAABwAAAAAAeExMTHhAQAAHAAAAAAB4SMhIeAgIAAQAAAAAAHBAQEBAAAAABgAAAAAAcEB4CHgAAAAEAAAAAEDgQEBAYAAAAAcAAAAAAEhISEh4AAAABgAAAAAAyEhYcDAAAAAIAAAAAACb2mpmZgAAAAYAAAAAAEhwMHDIAAAABgAAAAAAyEhYMDAgYAAFAAAAAABwMCBA+AAAAAQAAAAwYGBgwGBgYDAAAwAAAEBAQEBAQEBAQAAEAAAAwGBgYDBgYGDAAAYAAAAAAGAYAAAAAAAABAAAAAAAAEAAAAAAAAAKAAAAAAAAAAAAAAAAAAD/wAAAAAAAAAAAAAADAAAAQEBAAAAAAAAAAAYAAAA4QOBA4EA4AAAA"
F_SANSB15 = "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"
F_SANSB22 = "BwAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAIAAAAAAA4ODg4ODg4ODg4AAA4ODgAAAAAAAsAAAAAAAAAAAAAc4AzgDOAM4AzgAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA0AAAAAAAAAAAAADGAMYAhACEB/8H/wGMAQgDGA/+B/4DGAIQBjAGMAAAAAAAAAAAAAAA0AAAAAAAAAAAIAH4A/4HLgcmByAH4AP4AfwAfgAnBicHJwfvA/4B+AAgACAAAAAAAAABQAAAAAAAAAAAAAAAAAAAA8BwB+BgBjDABjHABjGABjMABjd4B+b8A8zOAB3GABnGADHGAHDOAGD8AMB4AAAAAAAAAAAAAAAAAAAAAQAAAAAAAAAAAAAAPAD+AMcAxwDOAPwA+AHwg7HHOYcfhw8Hj4P/4fjgAAAAAAAAAAAAAGAAAAAABwcHBwcAAAAAAAAAAAAAAAAAAAAAgAAAAADhwcODg4OHBwcHBwcHA4ODg4HBwOCAAAAADgcHA4OBwcHBwcHBwcHBwcODhwcOAJAAAAAAAAAAAAABgAGABbAP8APAA+AHcAIgAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAANAAAAAAAAAAAAAAAAAAAHAAcABwAHAH/wf/AHAAcABwAHAAcAAAAAAAAAAAAAAAAAAAAHAAAAAAAAAAAAAAAAAAAAAAA4ODgYMDAAAAgAAAAAAAAAAAAAAAAAfHx8AAAAAAAAAAAABwAAAAAAAAAAAAAAAAAAAAAAeHh4AAAAAAAHAAAAABwcGBg4ODgwMHBwcGBgYOAAAAAAAA0AAAAAAAAAAAAADwA/wDnAcOBw4HDgcOBw4HDgcOBw4HDgOcAfwA8AAAAAAAAAAAAAAA0AAAAAAAAAAAAABwAfAD8AdwAHAAcABwAHAAcABwAHAAcABwB/8H/wAAAAAAAAAAAAAA0AAAAAAAAAAAAAH4A/wHngcOAA4ADgAcADwAeAHgA8ADgAeAB/4H/gAAAAAAAAAAAAAA0AAAAAAAAAAAAAH4A/wHngcOAA4AHgD4APgAPgAOAA4HDgf+A/wB+AAAAAAAAAAAAAAA0AAAAAAAAAAAAAA8ADwAfAD8ANwB3AGcAxwHHAYcD/8P/wAcABwAHAAAAAAAAAAAAAAA0AAAAAAAAAAAAAP+A/4HgAcABwAHeAf8B/4ADgAPAA8HDgeeA/wB+AAAAAAAAAAAAAAA0AAAAAAAAAAAAAD4AfwD3gcOBwAHeAf8B54HDgcOBw4HDgPeAfwA+AAAAAAAAAAAAAAA0AAAAAAAAAAAAAf+B/4ADgAOABwAOAA4AHAAcADgAOAA4AHgAcABwAAAAAAAAAAAAAAA0AAAAAAAAAAAAAH4A/wHngcOBw4DjgH8AfwHjgcOBw8HDgeOA/wB+AAAAAAAAAAAAAAA0AAAAAAAAAAAAAHwA/wHnAcOBw4HDgcOB54D/gHuAA4HDge8A/wB8AAAAAAAAAAAAAAAgAAAAAAAAAADg4OAAAAAAAADg4OAAAAAAACAAAAAAAAAAAODg4AAAAAAAAODg4GBgwAAANAAAAAAAAAAAAAAAAAAAAEADwB/AfgH4AcABwAH4AH4AD8ADwABAAAAAAAAAAAAAAAAANAAAAAAAAAAAAAAAAAAAAAAAAf/B/8AAAAAAAAH/wf/AAAAAAAAAAAAAAAAAAAAAAAAANAAAAAAAAAAAAAAAAAABAAHgAfgAPwAPwAHAAcAPwD8B+AHgAQAAAAAAAAAAAAAAAAAAOAAAAAAAAAAAAAA/AH+A98HhwcHAAcAHgA8AHAAcAAAAAAAcABwAHAAAAAAAAAAAAAAAWAAAAAAAAAAAAAAAAAAAAAP4AA/+ABgDADABgGHswMP8wMYYwIwYQYwYwYgYwYgwwYwxgI/fAMeOAGAAAHAEAB/8AAfwAAAAAAAAAEAAAAAAAAAAAAAADwAPAB+AH4A5gDnAOcBw4HDgf+D/8OBx4HHAOcA4AAAAAAAAAAAAAEAAAAAAAAAAAAAB/8H/4eHx4HHgceDx/+H/4eDx4HngOeB54PH/8f/AAAAAAAAAAAAAAEAAAAAAAAAAAAAAH4B/4P/w8HngMcABwAHAAcABwAHgMPB4//A/4B+AAAAAAAAAAAAAAEAAAAAAAAAAAAAB/wH/wefh4PHgeeA54DngOeA54HngceDx4+H/wf8AAAAAAAAAAAAAADwAAAAAAAAAAAAB/+H/4eAB4AHgAeAB/+H/4eAB4AHgAeAB4AH/8f/wAAAAAAAAAAAAADgAAAAAAAAAAAAB/+H/4eAB4AHgAeAB/8H/weAB4AHgAeAB4AHgAeAAAAAAAAAAAAAAAEgAAAAAAAAAAAAAAAAAAAAfwAB/8AD/+ADweAHgMAHAAAHAAAHB/AHB/AHAHAHgHADwPAD//AB/8AAfwAAAAAAAAAAAAAAAAAAAAABAAAAAAAAAAAAAAeBx4HHgceBx4HHgcf/x//H/8eBx4HHgceBx4HHgcAAAAAAAAAAAAAAcAAAAAAHh4eHh4eHh4eHh4eHh4eAAAAAAADQAAAAAAAAAAAAAH4AfgAeAA4ADgAOAA4ADgAOAA4HDgceB/wD/AHwAAAAAAAAAAAAAAEAAAAAAAAAAAAAB4Hng8eHh48Hnge8B/gH/AfcB44HjweHh4PHgceA4AAAAAAAAAAAAADgAAAAAAAAAAAAB4AHgAeAB4AHgAeAB4AHgAeAB4AHgAeAB4AH/4f/gAAAAAAAAAAAAAEwAAAAAAAAAAAAAAAAAAAHwPgHwPgH4PgH4PgH4fgHYbgHcbgHM7gHMzgHOzgHHzgHHjgHHjgHDjgHDDgAAAAAAAAAAAAAAAAAAAABAAAAAAAAAAAAAAeAx8DH4Mfgx3DHcMc4xzjHHMcOxw7HB8cHxwPHA8AAAAAAAAAAAAABIAAAAAAAAAAAAAAAAAAAAH8AAP/AA//gA8HgB4DwBwBwBwBwBwBwBwBwBwBwB4DwA8HgAf/AAP+AAH4AAAAAAAAAAAAAAAAAAAAAAPAAAAAAAAAAAAAH/gf/h4+Hg8eBx4HHg8ePh/8H/geAB4AHgAeAB4AAAAAAAAAAAAAAASAAAAAAAAAAAAAAAAAAAAB/AAD/gAP/4APB4AeA8AcAcAcAcAcAcAcAcAcAcAeA8APA4APj4AH/wAB/AAAOAAAPAAAH4AAD4AAAAAEAAAAAAAAAAAAAB/8H/8eHx4HngeeBx4fH/4f/B4cHh4eDh4PHgeeA4AAAAAAAAAAAAADwAAAAAAAAAAAAAP4D/wPHh4OHgAPAA/wA/wAfgAPHAccDx8eD/4D+AAAAAAAAAAAAAADgAAAAAAAAAAAAD/+P/4B4AHAAcABwAHAAcABwAHAAcABwAHAAcABwAAAAAAAAAAAAAAEAAAAAAAAAAAAABwHnAecB5wHnAecB5wHnAecB54HngcODw//B/4B+AAAAAAAAAAAAAADwAAAAAAAAAAAADwHHAccDx4ODg4OHAccBxwHOAO4A7gD8AHwAfAA4AAAAAAAAAAAAAAFQAAAAAAAAAAAAAAAAAAAOBwePD4cHD4cHD4cHDYcHHc4Dnc4Dmc4DmM4DuNwB+PwB+PwB8PgA8HgA8HgAAAAAAAAAAAAAAAAAAAAA8AAAAAAAAAAAAAcDw4ODxwHPAO4A/AB8AHwAfADuAc8BxwODhwPHAcAAAAAAAAAAAAAA8AAAAAAAAAAAAAcBx4ODh4PHAc8A7gD8AHwAeAA4ADgAOAA4ADgAOAAAAAAAAAAAAAAA4AAAAAAAAAAAAAf/B/8ADwAOAB4APAA4AHAA4AHgA8ADgAeAB/+H/4AAAAAAAAAAAAAAgAAAAAfn5wcHBwcHBwcHBwcHBwcHBwcH5+BwAAAADgYGBgcHBwMDA4ODgYGBwcAAAAAAAIAAAAAPz8HBwcHBwcHBwcHBwcHBwcHBz8/A0AAAAAAAAAAAAADwAPgA2AHcAYwDjAMOAwYHBwYDAAAAAAAAAAAAAAAAAAAAAAAAAAAA0AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAP/wAAAAAAgAAAAAcDgMAAAAAAAAAAAAAAAAAAAAAAAADQAAAAAAAAAAAAAAAAAAAAAPgD/AOcAw4ADgH+B/4HDgceBz4H7wPHAAAAAAAAAAAAAADgAAAAAAAAAAOAA4ADgAOAA7wD/gPPA4cDhwOHg4eDhwOHA88D/gc8AAAAAAAAAAAAAADQAAAAAAAAAAAAAAAAAAAAAPgD/AOOBw4HAAcABwAHAAcOA44D/AD4AAAAAAAAAAAAAADgAAAAAAAAAAAHAAcABwAHAecD/wOPBw8HBwcHBwcHBwcPA48D/wHnAAAAAAAAAAAAAADQAAAAAAAAAAAAAAAAAAAAAPgD/AOOBw4HDgf+B/4HAAcAA44D/AD4AAAAAAAAAAAAAACAAAAAAePjg4/v44ODg4ODg4ODg4AAAAAAAOAAAAAAAAAAAAAAAAAAAAAB5wP/A48HDwcHBwcHBwcHBw8DjwP/AecABwAHA44D/gD4AOAAAAAAAAAAA4ADgAOAA4ADvAP+A88DhwOHA4cDhwOHA4cDhwOHA4cAAAAAAAAAAAAAAHAAAAADg4AAA4ODg4ODg4ODg4ODgAAAAAAAcAAAAAODgAADg4ODg4ODg4ODg4ODg4cPDgDQAAAAAAAAAAOAA4ADgAOAA48DngOcA7gD8APwA/gDvAOcA44DjgOHAAAAAAAAAAAAAABwAAAAA4ODg4ODg4ODg4ODg4ODg4AAAAAAAUAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAc8eAN++APfvAOPHAOPHAOOHAOOHAOOHAOOHAOOHAOOHAOOHAAAAAAAAAAAAAAAAAAAAADgAAAAAAAAAAAAAAAAAAAABzwDfgPPA4cDhwOHA4cDhwOHA4cDhwOHAAAAAAAAAAAAAADgAAAAAAAAAAAAAAAAAAAAAPgB/gOPB4cHBwcHhweHBweHA48B/gD4AAAAAAAAAAAAAADgAAAAAAAAAAAAAAAAAAAABzwD/gPPA4cDhwOHg4eDhwOHA88D/gO8A4ADgAOAA4ADgADgAAAAAAAAAAAAAAAAAAAAAecD/wOPBw8HBwcHBwcHBwcPA48D/wHnAAcABwAHAAcABwCQAAAAAAAAAAAAAAAAAAAABzADcAPwA4ADgAOAA4ADgAOAA4ADgAOAAAAAAAAAAAAAAADQAAAAAAAAAAAAAAAAAAAAAfgD/AcOBwwHwAP4AP4AHgcOBw4D/gH4AAAAAAAAAAAAAACAAAAAAAGDg4/v44ODg4ODg4OD4eAAAAAAAOAAAAAAAAAAAAAAAAAAAAAHBwcHBwcHBwcHBwcHBwcHB48D3wP3AecAAAAAAAAAAAAAANAAAAAAAAAAAAAAAAAAAAAOBwcHBw4HDgOOA5wDnAHYAfgB+ADwAPAAAAAAAAAAAAAAASAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA4cOA4eOAY+OAY2MAc2cAc3cANzcANjYAPj4APj4AHhwAHBwAAAAAAAAAAAAAAAAAAAAADQAAAAAAAAAAAAAAAAAAAABw4HjgOcAfgB+ADwAPAB+AHcA5wHDg8PAAAAAAAAAAAAAADQAAAAAAAAAAAAAAAAAAAADwcHBwcOAw4DjAOcAZwB2AH4APgA8ABwAHAA4AHgB8AHgACwAAAAAAAAAAAAAAAAAAAAB/wH/AA4AHgAcADgAeABwAOAB4AH/Af8AAAAAAAAAAAAAACQAAAAAAAAAADwAfABwAHAAcABwAHAAcADgA8ADwADgAHAAcABwAHAAcABwAHAAfAA8ABwAAAAAwMDAwMDAwMDAwMDAwMDAwMDAwMDAJAAAAAAAAAADwAPgAPAAcABwAHAAcABwAHgAPAA8AHgAcABwAHAAcABwAHAA8APgA8AANAAAAAAAAAAAAAAAAAAAAAAAAAAA8AH8wR/AB4AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAIAAAAAAAAAAAAAAA4ODgAAAAAAAAAAAAAABYAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAD///z///wAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAHAAAAAAA4ODgQEDAAAAAAAAAAAAAAAAAAAA0AAAAAAAAAAAAAD4Af4DzgOHA4AP8AfgB4AP8AfwA4ADhwPOAf4AeAAAAAAAAAAAAAAA=="
F_SERIFB48 = "DAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAABgAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAfgAB/4AD78AHw+APw/APg/Afgfgfgfgfgfg/gfw/gfw/gfw/gfw/gfw/gfw/gfw/gfw/gfw/gfw/gfw/gfw/gfwfgfgfgfgfgfgPg/APw/AHw+AD78AB/4AAfgAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAYAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA8AAD8AAP8AAf8AB/8AD/8ACH8AAH8AAH8AAH8AAH8AAH8AAH8AAH8AAH8AAH8AAH8AAH8AAH8AAH8AAH8AAH8AAH8AAH8AAH8AAH8AAH8AAH8AAH+AD//8D//8AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAGAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAP+AB//wB+f4BwH8BwD+BwD+BgD+BgB+AAB+AAD+AAD+AAD+AAD8AAH8AAH4AAPwAAPgAAfAAA+AAB8AAD4AAHwAAPAAAeAAA8AAB4AAD///D///D///D///D///AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAABgAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAP8AA//gB+fgD8HgH4DgPwDgPwDgfgBgfgAA/gAA/gAA/gAA/v4A//+A///A/g/g/gfw/gfw/gfw/gPw/gP4/gP4/gPwfgPwfgPwPwfwPwfgH4fgD9/AB/+AAfwAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAjAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAf/AB/8B/+AH/wAf8ABwAB/wAHAAH/gAcAAf/ABwAB/+AHAAHf8AcAAc/wBwABz/gHAAHH/AcAAcP+BwABwf4HAAHA/wcAAcD/hwABwH/HAAHAP+cAAcAf5wABwB/3AAHAD/8AAcAH/wABwAP/AAHAAf8AAcAB/wABwAD/AAHAAH8AAcAAPwABwAAfAAHAAB8AH/wADwAf/AAHAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAGwAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAB/4AAB//4AB/n+AA+APgAPAB4AHwAOAB8ADgAfAA4AH4AAAB/AAAAf8AAAH/4AAA//gAAP//AAB//4AAH//AAAf/4AAB//AAAD/wAAAH8AAAA/gBgAH4AYAB+AGAAfABgAHwAcAB8AHAAeAB8APgAf4fwAH//wAAH/wAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAABgAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAD/4AP/+APj/AOA/gMA/gMA/gAA/gAA/gAA/gB//gP//gfw/g/g/g/g/g/A/g/A/g/A/g/g/g/g/gf//gf/f4H4f4AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAbAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAH/AAAB/wAAAH8AAAB/AAAAfwAAAH8AAAB/AAAAfwAAAH8AAAB/AAAAfwAAAH4/gAB//+AAf//wAH8D+AB/AfwAfwH8AH8A/AB/AP4AfwD+AH8A/gB/AP4AfwD+AH8A/gB/APwAfwD8AH8B/AB/AfgAfwH4AH8D8AB/7+AAf//AAAH/AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAGwAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAf8AAAH/AAAAfwAAAH8AAAB/AAAAfwAAAH8AAAB/AAAAfwAAAH8AAAB/AAD/fwAD//8AB/n/AA/gfwAfwH8AH8B/AB+AfwA/gH8AP4B/AD+AfwA/gH8AP4B/AD+AfwA/gH8AP4B/AD+AfwAfwH8AH8B/AA/gfwAH//8AA///wAD+P8AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAABYAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA/gAD/4AP78APh+Afh+Afg/A/g/A/g/A/g/A///A///A/gAA/gAA/gAA/gAA/gAAfgAAfwAAP4AAH//AD/+AA/wAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAoAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAf8HwD8A/z/x/4B///v/wH/H/j/gfwP4H+B/AfwP4H8B/A/gfwH8D+B/AfwP4H8B/A/gfwH8D+B/AfwP4H8B/A/gfwH8D+B/AfwP4H8B/A/gfwH8D+B/AfwP4H8B/A/gfwH8D+D/x/8/+f/H/z/4AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAGwAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAPwf4AH/n+AD//+AB/x/gAfwP4AH8D+AB/A/gAfwP4AH8D+AB/A/gAfwP4AH8D+AB/A/gAfwP4AH8D+AB/A/gAfwP4AH8D+AB/A/gAfwP4Af8H+AH/D/gAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAABgAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA/wAD/8AH5+APw/Afgfgfgfg/gfw/gfw/gfw/gfw/gfw/gfw/gfw/gfw/gfw/gfwfgfgfgfgPw/AH5+AD/8AA/wAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAWAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAf+BwP+HwD+PwD+fwD+/wD/4wD/AwD+AQD+AAD+AAD+AAD+AAD+AAD+AAD+AAD+AAD+AAD+AAD+AAD+AAP/wAf/wAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAEAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAcADwAPAB8APwD/+f/4f4A/AD8APwA/AD8APwA/AD8APwA/AD8APwA/AD8AP4A/gD/8H/wH8AAAAAAAAAAAAAAAAAAAAAAAAAAAAABsAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAB/w/4Af8H+AB/A/gAfwP4AH8D+AB/A/gAfwP4AH8D+AB/A/gAfwP4AH8D+AB/A/gAfwP4AH8D+AB/A/gAfwP4AH8D+AB/A/gAf8f4AD//+AAf+f4AD8H+AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAYAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA/+B//+B/P4AcP4AcH8A4H8A4D+AwD+BwB/BwB/DgB/jgA/nAA/3AAf2AAf+AAP8AAP8AAH8AAH4AAD4AADwAABwAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAGAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAP/w/3/gfj+AHB/AOB/AOB/gOA/gcA/gcAfw4Afw4AP4wAP5wAP9wAH9gAH/gAD/AAD/AAB/AAB+AAB+AAA8AAA8AAAcAAA4AAA4AABwAGBwAGDgAGHgAH/AAH+AAH4AAAAAAA=="

# Decoded-size expectations (integrity check on every font blob).
_FONT_SPECS = [
    {"name": "sans10", "chars": CHARS, "height": 13, "blob": F_SANS10, "size": 1464},
    {"name": "sans12", "chars": CHARS, "height": 14, "blob": F_SANS12, "size": 1709},
    {"name": "sansb10", "chars": CHARS, "height": 13, "blob": F_SANSB10, "size": 1464},
    {"name": "sansb15", "chars": CHARS, "height": 18, "blob": F_SANSB15, "size": 3123},
    {"name": "sansb22", "chars": CHARS, "height": 25, "blob": F_SANSB22, "size": 4699},
    {"name": "serif48", "chars": SERIF_CHARS, "height": 54, "blob": F_SERIFB48, "size": 3475},
]


def _decode_fonts():
    """Decode the bitmap blobs into {name: (height, {char: (w, bytes)})}."""
    decoded = {}
    for spec in _FONT_SPECS:
        name = spec["name"]
        raw = base64.b64decode(spec["blob"])
        if len(raw) != spec["size"]:
            raise ValueError("font %s decoded to %d bytes, expected %d"
                             % (name, len(raw), spec["size"]))
        glyphs = {}
        off = 0
        for ch in spec["chars"]:
            w = raw[off]
            off += 1
            stride = (w + 7) // 8
            glyphs[ch] = (w, raw[off:off + stride * spec["height"]])
            off += stride * spec["height"]
        if off != len(raw):
            raise ValueError("font %s parse ended at %d of %d"
                             % (name, off, len(raw)))
        decoded[name] = (spec["height"], glyphs)
    return decoded


# ---------------------------------------------------------------- colours
W, H = 1024, 1024
_PALETTE = {
    "paper": (247, 243, 235),
    "ink": (24, 24, 24),
    "red": (166, 38, 38),
    "navy": (15, 28, 46),
    "gold": (212, 164, 65),
    "grey": (96, 90, 74),
    "ocean": (214, 228, 232),
    "land": (232, 220, 190),
    "dusk": (38, 52, 74),
    "cream": (239, 231, 214),
    "burst": (205, 72, 25),
    "white": (255, 255, 255),
    "skyline": (13, 22, 38),
}
(PAPER, INK, RED, NAVY, GOLD, GREY, OCEAN, LAND, DUSK, CREAM, BURST,
 WHITE, SKYLINE) = (_PALETTE[k] for k in
                    ("paper", "ink", "red", "navy", "gold", "grey",
                     "ocean", "land", "dusk", "cream", "burst", "white",
                     "skyline"))


class Surface:
    """Plain RGB bytearray canvas with tiny drawing primitives."""

    def __init__(self, w, h, bg):
        self.w = w
        self.h = h
        self.px = bytearray(bytes(bg) * (w * h))

    def set(self, x, y, c):
        if 0 <= x < self.w and 0 <= y < self.h:
            o = (y * self.w + x) * 3
            self.px[o:o + 3] = bytes(c)

    def rect(self, x, y, w, h, c):
        ax = max(0, x)
        ay = max(0, y)
        bx = min(self.w, x + w)
        by = min(self.h, y + h)
        if bx <= ax or by <= ay:
            return
        row = bytes(c) * (bx - ax)
        for yy in range(ay, by):
            o = (yy * self.w + ax) * 3
            self.px[o:o + len(row)] = row

    def hline(self, x0, x1, y, c, thick=1):
        for t in range(thick):
            self.rect(x0, y + t, x1 - x0, 1, c)

    def vline(self, x, y0, y1, c, thick=1):
        for t in range(thick):
            self.rect(x + t, y0, 1, y1 - y0, c)

    def line(self, ax, ay, bx, by, c):
        dx = abs(bx - ax)
        dy = -abs(by - ay)
        sx = 1 if ax < bx else -1
        sy = 1 if ay < by else -1
        err = dx + dy
        while True:
            self.set(ax, ay, c)
            if ax == bx and ay == by:
                return
            e2 = 2 * err
            if e2 >= dy:
                err += dy
                ax += sx
            if e2 <= dx:
                err += dx
                ay += sy

    def circle(self, cx, cy, r, c):
        r2 = r * r
        for yy in range(cy - r, cy + r + 1):
            dy = yy - cy
            for xx in range(cx - r, cx + r + 1):
                dx = xx - cx
                if dx * dx + dy * dy <= r2:
                    self.set(xx, yy, c)

    def ring(self, cx, cy, r, c):
        steps = max(24, 6 * r)
        for i in range(steps):
            a = 2 * math.pi * i / steps
            self.set(int(cx + r * math.cos(a)), int(cy + r * math.sin(a)), c)

    def poly(self, pts, c):
        """Scanline fill of a simple polygon (list of (x, y))."""
        if len(pts) < 3:
            return
        ys = [p[1] for p in pts]
        top = max(0, int(min(ys)))
        bot = min(self.h - 1, int(max(ys)))
        n = len(pts)
        for y in range(top, bot + 1):
            xs = []
            for i in range(n):
                x0, y0 = pts[i]
                x1, y1 = pts[(i + 1) % n]
                if (y0 <= y < y1) or (y1 <= y < y0):
                    t = (y - y0) / (y1 - y0)
                    xs.append(x0 + t * (x1 - x0))
            xs.sort()
            for k in range(0, len(xs) - 1, 2):
                xa = max(0, int(xs[k]))
                xb = min(self.w - 1, int(xs[k + 1]))
                if xb >= xa:
                    self.rect(xa, y, xb - xa + 1, 1, c)


class Typer:
    """Bitmap text using the decoded fonts."""

    def __init__(self, fonts):
        self.fonts = fonts

    def width(self, name, s):
        _, glyphs = self.fonts[name]
        blank = glyphs[" "][0]
        total = 0
        for ch in s:
            g = glyphs.get(ch)
            total += g[0] if g else blank
        return total

    def draw(self, pg, name, x, y, s, color):
        height, glyphs = self.fonts[name]
        blank = glyphs[" "][0]
        cx = x
        for ch in s:
            g = glyphs.get(ch)
            if g is None:
                cx += blank
                continue
            w, bits = g
            rb = (w + 7) // 8
            for yy in range(height):
                row = bits[yy * rb:(yy + 1) * rb]
                for xx in range(w):
                    if row[xx // 8] & (0x80 >> (xx % 8)):
                        pg.set(cx + xx, y + yy, color)
            cx += w
        return cx

    def draw2x(self, pg, name, x, y, s, color):
        """Draw text at 2x scale (each bitmap pixel becomes a 2x2 block).

        Used for the masthead: the serif masthead font only holds the
        characters of the previous day's date, so the masthead is set in
        the bold sans at double size instead.
        """
        height, glyphs = self.fonts[name]
        blank = glyphs[" "][0]
        cx = x
        for ch in s:
            g = glyphs.get(ch)
            if g is None:
                cx += blank * 2
                continue
            w, bits = g
            rb = (w + 7) // 8
            for yy in range(height):
                row = bits[yy * rb:(yy + 1) * rb]
                for xx in range(w):
                    if row[xx // 8] & (0x80 >> (xx % 8)):
                        pg.rect(cx + xx * 2, y + yy * 2, 2, 2, color)
            cx += w * 2
        return cx

    def wrap(self, name, s, maxw):
        """Greedy word wrap; returns a list of lines (never empty)."""
        space = self.width(name, " ")
        lines = []
        cur_words = []
        cur_w = 0
        for word in s.split(" "):
            ww = self.width(name, word)
            add = ww if not cur_words else space + ww
            if cur_w + add <= maxw:
                cur_words.append(word)
                cur_w += add
                continue
            if cur_words:
                lines.append(" ".join(cur_words))
                cur_words = []
                cur_w = 0
            while ww > maxw and len(word) > 1:
                # hard-split an over-long word
                n = len(word)
                while n > 1 and self.width(name, word[:n]) > maxw:
                    n -= 1
                lines.append(word[:n])
                word = word[n:]
                ww = self.width(name, word)
            cur_words = [word]
            cur_w = ww
        if cur_words or not lines:
            lines.append(" ".join(cur_words))
        return lines

# ---------------------------------------------------------------- PNG out
def _paeth_pick(a, b, c):
    p = a + b - c
    pa = abs(p - a)
    pb = abs(p - b)
    pc = abs(p - c)
    if pa <= pb and pa <= pc:
        return a
    if pb <= pc:
        return b
    return c


def _filter_scanline(kind, row, prev):
    n = len(row)
    out = bytearray(n)
    if kind == 0:
        out[:] = row
    elif kind == 1:
        out[:3] = row[:3]
        for i in range(3, n):
            out[i] = (row[i] - row[i - 3]) & 0xFF
    elif kind == 2:
        if prev is None:
            out[:] = row
        else:
            for i in range(n):
                out[i] = (row[i] - prev[i]) & 0xFF
    elif kind == 3:
        for i in range(n):
            left = row[i - 3] if i >= 3 else 0
            up = prev[i] if prev is not None else 0
            out[i] = (row[i] - ((left + up) // 2)) & 0xFF
    else:
        for i in range(n):
            a = row[i - 3] if i >= 3 else 0
            b = prev[i] if prev is not None else 0
            cc = prev[i - 3] if (prev is not None and i >= 3) else 0
            out[i] = (row[i] - _paeth_pick(a, b, cc)) & 0xFF
    return bytes(out)


def _png_chunk(tag, data):
    blob = struct.pack(">I", len(data)) + tag + data
    return blob + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)


def encode_png_bytes(pg):
    """Encode the surface as PNG bytes; per-row greedy filter choice."""
    w, h = pg.w, pg.h
    raw = bytes(pg.px)
    stride = w * 3
    comp = zlib.compressobj(9)
    stream = bytearray()
    prev = None
    for y in range(h):
        row = raw[y * stride:(y + 1) * stride]
        best = None
        best_score = None
        best_kind = 0
        for kind in range(5):
            trial = _filter_scanline(kind, row, prev)
            score = 0
            for byte in trial:
                score += byte if byte < 128 else 256 - byte
            if best_score is None or score < best_score:
                best = trial
                best_score = score
                best_kind = kind
        stream.append(best_kind)
        stream += best
        prev = row
    body = comp.compress(bytes(stream)) + comp.flush()

    ihdr = struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0)
    return (b"\x89PNG\r\n\x1a\n" + _png_chunk(b"IHDR", ihdr)
            + _png_chunk(b"IDAT", bytes(body)) + _png_chunk(b"IEND", b""))


# ---------------------------------------------------------------- data
# Stories are stored as dicts with named fields. Kicker = section label
# shown in red; body/detail = one or two short sentences condensed to
# fit the layout; source = attribution.
LEADS = [
    {"kicker": "CLIMATE \u00b7 COP31",
     "headline": "COP31 collapses, no deal",
     "body": "190+ nations fail to agree the Antalya Pact after 44 hours overtime; fossil fuels dropped.",
     "source": "Sources: CNN, AFP, Le Monde"},
    {"kicker": "MARKETS \u00b7 ASIA",
     "headline": "Asian markets plunge on AI rout",
     "body": "KOSPI falls ~4% as Wall Street's AI sell-off spreads; S&P in correction, Nasdaq in bear territory.",
     "source": "Sources: Reuters, CNBC"},
    {"kicker": "BAHRAIN \u00b7 GULF",
     "headline": "Iran hits US bases in Bahrain",
     "body": "IRGC missiles and drones hit al-Riffa and Awali; two hurt and a factory burns.",
     "source": "Sources: Reuters, AP, AFP"},
]

MEDIUM = [
    {"kicker": "NATO", "headline": "NATO meets Monday over Poland",
     "detail": "Council meets in Brussels over 3 Kh-101 missiles.",
     "source": "Reuters", "icon": "summit"},
    {"kicker": "MEXICO", "headline": "Mexico seizes 'El Chapo Isidro'",
     "detail": "FBI Top 10 fugitive caught in Guasave; 11 killed.",
     "source": "CNN", "icon": "gavel"},
    {"kicker": "UKRAINE", "headline": "Russian drone kills 4 near Kyiv",
     "detail": "4 killed in Dymer; 10-14 missing under rubble.",
     "source": "Reuters", "icon": "burst"},
    {"kicker": "LIBYA", "headline": "Russian warship sunk off Libya",
     "detail": "Sea drones sink corvette off Benghazi base.",
     "source": "AP", "icon": "missile"},
    {"kicker": "SAUDI ARABIA", "headline": "Houthis claim Rabigh hit",
     "detail": "Houthis claim direct hit on Red Sea refinery.",
     "source": "Reuters", "icon": "flame"},
    {"kicker": "SUDAN", "headline": "Sudan drones kill 4 in Khartoum",
     "detail": "UN premises damaged with staff inside.",
     "source": "AFP", "icon": "tank"},
    {"kicker": "CRICKET", "headline": "India posts record 720/9 in Test",
     "detail": "Rahul 136, Pant 128; NZ 157/4 at lunch Day 5.",
     "source": "Reuters", "icon": "pin"},
    {"kicker": "FOOTBALL", "headline": "Liverpool hammer Man Utd 4-0",
     "detail": "Pochettino's first game; Yoro off after 8 mins.",
     "source": "Reuters", "icon": "flags"},
    {"kicker": "SPACE", "headline": "BepiColombo enters Mercury orbit",
     "detail": "8-year, 10-billion-km trip ends at Mercury.",
     "source": "ESA", "icon": "globe"},
    {"kicker": "SPACE", "headline": "Voyager 1 reaches one light-day",
     "detail": "First object one light-day out; signal: 24 hrs.",
     "source": "NASA", "icon": "chip"},
    {"kicker": "INDONESIA", "headline": "Factory fire: dozens missing",
     "detail": "3 dead, 24 body bags found; 36-50 missing.",
     "source": "Reuters", "icon": "flame"},
    {"kicker": "GOLD", "headline": "Gold rebounds above $3,600",
     "detail": "Up ~2% after five straight daily losses.",
     "source": "Reuters", "icon": "crown"},
]

# List stories as dicts. Two columns: items 1-18, then 19-39.
LIST_A = [
    {"text": "Two injured in Bahrain attack", "source": "AFP"},
    {"text": "Iran readies 14 tankers at Kharg", "source": "Gulf News"},
    {"text": "Saudi intercepts Houthi missile", "source": "SPA"},
    {"text": "Second ship hit off Benghazi", "source": "Reuters"},
    {"text": "South Sudan: 24 civilians killed", "source": "AFP"},
    {"text": "Nigeria: 35 killed in revenge attacks", "source": "AFP"},
    {"text": "WHO pleads for peace in Ebola Congo", "source": "WHO"},
    {"text": "Israel coalition talks fail again", "source": "AFP"},
    {"text": "Bolsonaro stable in intensive care", "source": "Reuters"},
    {"text": "Trump hosts meme-coin gala", "source": "Reuters"},
    {"text": "ICE detain father, daughter at Seattle", "source": "AP"},
    {"text": "US Army to detonate Iowa explosives", "source": "Reuters"},
    {"text": "GTA 6 smashes $3.79bn day one", "source": "Take-Two"},
    {"text": "NASA seeks new astronauts", "source": "AP"},
    {"text": "Kansas City win first NWSL title", "source": "AP"},
    {"text": "Wembanyama scores 50 in Spurs win", "source": "AP"},
    {"text": "Amazon nears $7.5bn Decart deal", "source": "FT"},
    {"text": "Nvidia spy scandal deepens", "source": "NYT"},
]
LIST_B = [
    {"text": "Albanese: COP31 shows difficult times", "source": "AFP"},
    {"text": "$120bn adaptation finance target dropped", "source": "IPS"},
    {"text": "90+ nations sign electrification pledge", "source": "CNN"},
    {"text": "Russia launches 186 drones overnight", "source": "Reuters"},
    {"text": "Zelenskiy: 165 missiles in one week", "source": "Reuters"},
    {"text": "Russian ship still burning off Finland", "source": "Reuters"},
    {"text": "Kim: security, not supremacy", "source": "KCNA"},
    {"text": "Myanmar slams ASEAN as unfair", "source": "Reuters"},
    {"text": "Nepal PM meets Modi in Delhi", "source": "IANS"},
    {"text": "Korea minister quits over AI cheating", "source": "Reuters"},
    {"text": "Verstappen wins Las Vegas GP thriller", "source": "F1"},
    {"text": "Sindarov gets White in Game 1", "source": "FIDE"},
    {"text": "Earth gets temporary mini-moon", "source": "CNN"},
    {"text": "Hera inspects DART asteroid crater", "source": "ESA"},
    {"text": "S&P enters correction, Nasdaq bear", "source": "Reuters"},
    {"text": "China injects 499.5bn yuan liquidity", "source": "PBoC"},
    {"text": "Korea readies market stabilisation fund", "source": "Reuters"},
    {"text": "Lisbon marches over living costs", "source": "Reuters"},
    {"text": "UN killer-robot talks end, no rules", "source": "AP"},
    {"text": "India MP Wadkute dies at 72", "source": "PTI"},
    {"text": "WeRide plans 1,000 robotaxis in Europe", "source": "Reuters"},
]

TIMELINE = [
    {"time": "00:00", "event": "Sudan drones hit Khartoum"},
    {"time": "01:00", "event": "Asian markets plunge"},
    {"time": "02:00", "event": "Gold rebounds past $3,600"},
    {"time": "03:30", "event": "UN robot talks end"},
    {"time": "10:00", "event": "Cikande fire: dozens missing"},
    {"time": "16:30", "event": "Liverpool 4-0 Man Utd"},
]

DATECHECK = [
    {"text": "COP31 final text REJECTED \u2014 no deal, 22 Nov"},
    {"text": "Merkury corvette SUNK at Benghazi \u2014 22 Nov"},
    {"text": "Sparta II hit 21 Nov, still smouldering"},
    {"text": "Chapo Isidro CAPTURED 20 Nov, in custody"},
    {"text": "BepiColombo ENTERED Mercury orbit 21 Nov"},
    {"text": "Voyager 1 CROSSED one light-day 18 Nov"},
    {"text": "GTA 6 $3.79bn day-one CONFIRMED 20 Nov"},
    {"text": "FIDE Game 1 NOT played \u2014 starts Tue 24 Nov"},
    {"text": "India-NZ Test NOT finished \u2014 NZ 157/4, Day 5"},
    {"text": "Not yet: NATO Poland decision, due Mon 23 Nov."},
]

FOOTER = "Stories leading Monday 23 November 2026, as reported that morning; claims are attributed. Sources: Reuters, AP, AFP, BBC, IANS, UN and others."

# Map dots: dx/dy nudge the drawn dot away from its true position (a
# leader line links them) so crowded dots do not overlap. Numbers match
# the legend under the map.
MAP_DOTS = [
    {"n": 1, "place": "Manama", "lon": 50.6, "lat": 26.2, "dx": -14, "dy": -10},
    {"n": 2, "place": "Tehran", "lon": 51.4, "lat": 35.7, "dx": 16, "dy": -12},
    {"n": 3, "place": "Hormuz", "lon": 56.5, "lat": 26.6, "dx": 14, "dy": 10},
    {"n": 4, "place": "Antalya", "lon": 30.7, "lat": 36.9, "dx": -14, "dy": -10},
    {"n": 5, "place": "Brussels", "lon": 4.4, "lat": 50.9, "dx": -12, "dy": -8},
    {"n": 6, "place": "Guasave", "lon": -108.5, "lat": 25.6, "dx": -10, "dy": 10},
    {"n": 7, "place": "Dymer", "lon": 30.3, "lat": 50.8, "dx": 0, "dy": -12},
    {"n": 8, "place": "Helsinki", "lon": 25.0, "lat": 60.2, "dx": 12, "dy": -10},
    {"n": 9, "place": "Benghazi", "lon": 20.1, "lat": 32.1, "dx": -12, "dy": 10},
    {"n": 10, "place": "Khartoum", "lon": 32.5, "lat": 15.6, "dx": 12, "dy": 8},
    {"n": 11, "place": "Wellington", "lon": 174.8, "lat": -41.3, "dx": 0, "dy": 0},
    {"n": 12, "place": "Las Vegas", "lon": -115.1, "lat": 36.2, "dx": -12, "dy": -10},
    {"n": 13, "place": "Geneva", "lon": 6.1, "lat": 46.2, "dx": 12, "dy": 8},
    {"n": 14, "place": "Cikande", "lon": 106.1, "lat": -6.2, "dx": 0, "dy": 0},
    {"n": 15, "place": "Seoul", "lon": 127.0, "lat": 37.5, "dx": 12, "dy": -10},
]
MAP_LEGEND = ("1 Manama  2 Tehran  3 Hormuz  4 Antalya\n"
              "5 Brussels  6 Guasave  7 Dymer  8 Helsinki\n"
              "9 Benghazi  10 Khartoum  11 Wellington\n"
              "12 Las Vegas  13 Geneva  14 Cikande  15 Seoul")

# Coarse equirectangular continent outlines (lon, lat), stylised.
NORTH_AMERICA = [(-168, 66), (-150, 70), (-135, 69), (-125, 71), (-115, 73),
    (-100, 73), (-90, 74), (-80, 73), (-75, 70), (-65, 62), (-60, 55),
    (-55, 50), (-60, 46), (-65, 44), (-70, 42), (-74, 39), (-76, 35),
    (-80, 32), (-81, 27), (-84, 30), (-89, 29), (-91, 19), (-96, 19),
    (-97, 26), (-97, 16), (-92, 15), (-87, 13), (-83, 9), (-79, 9),
    (-80, 7), (-83, 8), (-86, 12), (-90, 14), (-92, 15), (-95, 16),
    (-97, 19), (-102, 18), (-106, 22), (-110, 24), (-114, 28), (-117, 32),
    (-120, 34), (-124, 40), (-124, 46), (-126, 50), (-130, 54), (-135, 58),
    (-142, 60), (-150, 61), (-158, 58), (-162, 55), (-165, 60), (-168, 66)]
GREENLAND = [(-58, 64), (-52, 60), (-43, 60), (-40, 64), (-32, 68),
    (-25, 70), (-22, 74), (-30, 76), (-45, 76), (-58, 74), (-58, 64)]
ICELAND = [(-22, 64), (-18, 63), (-14, 64), (-15, 66), (-20, 66),
    (-23, 65), (-22, 64)]
SOUTH_AMERICA = [(-79, 9), (-77, 4), (-80, -3), (-81, -6), (-77, -12),
    (-72, -18), (-70, -24), (-70, -30), (-72, -37), (-73, -44),
    (-74, -50), (-70, -54), (-66, -55), (-65, -48), (-62, -41),
    (-57, -34), (-52, -32), (-48, -27), (-41, -23), (-39, -17),
    (-35, -9), (-35, -6), (-40, -3), (-44, -2), (-50, 0), (-53, 4),
    (-58, 6), (-62, 9), (-68, 11), (-72, 12), (-76, 10), (-79, 9)]
AFRICA = [(-6, 35), (-10, 31), (-15, 27), (-17, 21), (-17, 15), (-15, 11),
    (-12, 8), (-8, 5), (-4, 5), (0, 6), (6, 4), (9, 4), (9, -1), (12, -6),
    (13, -11), (12, -17), (14, -22), (16, -28), (20, -35), (26, -34),
    (32, -29), (35, -24), (39, -18), (40, -11), (42, -4), (46, -1),
    (51, 2), (51, 10), (48, 11), (44, 11), (40, 15), (38, 18), (37, 22),
    (35, 28), (34, 31), (32, 31), (30, 32), (27, 33), (22, 33), (19, 33),
    (15, 32), (11, 34), (10, 37), (5, 37), (0, 36), (-6, 35)]
EURASIA = [(-9, 37), (-9, 44), (-4, 48), (-1, 50), (3, 52), (7, 54),
    (8, 57), (11, 59), (7, 62), (13, 66), (19, 69), (26, 71), (33, 70),
    (40, 68), (47, 68), (54, 69), (61, 69), (68, 72), (75, 73), (82, 73),
    (89, 75), (96, 76), (103, 77), (110, 74), (117, 73), (124, 73),
    (131, 72), (138, 72), (145, 72), (152, 70), (159, 70), (166, 69),
    (173, 67), (178, 65), (178, 62), (172, 60), (166, 60), (162, 58),
    (158, 52), (156, 51), (158, 56), (156, 59), (150, 59), (144, 59),
    (142, 55), (140, 50), (136, 46), (132, 43), (128, 39), (126, 38),
    (122, 37), (120, 33), (117, 29), (112, 24), (109, 20), (106, 18),
    (103, 13), (100, 9), (99, 12), (97, 14), (94, 16), (91, 22), (88, 22),
    (85, 19), (82, 16), (80, 13), (77, 8), (75, 12), (73, 16), (70, 20),
    (67, 23), (63, 25), (59, 25), (57, 26), (55, 26), (53, 25), (51, 24),
    (49, 21), (47, 18), (45, 14), (43, 13), (41, 15), (39, 20), (37, 24),
    (35, 28), (34, 28), (33, 31), (35, 33), (33, 36), (30, 36), (27, 37),
    (24, 36), (22, 37), (21, 39), (19, 40), (17, 40), (16, 38), (15, 40),
    (13, 41), (11, 43), (9, 44), (7, 44), (5, 43), (3, 42), (1, 39),
    (0, 38), (-2, 37), (-5, 36), (-6, 36), (-9, 37)]
UK = [(-5, 50), (-4, 53), (-6, 55), (-4, 58), (-2, 57), (0, 54), (1, 51),
    (-2, 50), (-5, 50)]
JAPAN = [(130, 31), (133, 34), (137, 35), (140, 37), (141, 41), (142, 44),
    (141, 42), (140, 38), (137, 35), (134, 33), (131, 31), (130, 31)]
SUMATRA = [(95, 5), (98, 3), (101, 0), (104, -3), (106, -6), (104, -5),
    (101, -1), (98, 2), (95, 5)]
BORNEO = [(109, 1), (112, 4), (116, 6), (118, 2), (117, -2), (114, -3),
    (110, -2), (109, 1)]
JAVA = [(105, -6), (108, -7), (112, -7), (114, -8), (114, -9), (110, -8),
    (106, -7), (105, -6)]
NEW_GUINEA = [(131, -1), (136, -2), (141, -3), (146, -6), (150, -8),
    (147, -8), (142, -8), (137, -6), (132, -3), (131, -1)]
AUSTRALIA = [(113, -22), (114, -30), (115, -35), (118, -35), (124, -33),
    (129, -32), (132, -32), (135, -35), (138, -35), (140, -38),
    (145, -38), (150, -37), (153, -32), (153, -27), (150, -22),
    (146, -19), (142, -15), (142, -11), (141, -13), (137, -12),
    (135, -12), (132, -12), (130, -13), (126, -14), (122, -17),
    (118, -20), (113, -22)]
NEW_ZEALAND = [(167, -45), (170, -42), (173, -40), (175, -38), (177, -38),
    (175, -40), (172, -42), (169, -44), (167, -45)]
MADAGASCAR = [(44, -16), (47, -15), (50, -16), (49, -20), (47, -24),
    (45, -25), (44, -22), (43, -18), (44, -16)]
CONTINENTS = [NORTH_AMERICA, GREENLAND, ICELAND, SOUTH_AMERICA, AFRICA,
    EURASIA, UK, JAPAN, SUMATRA, BORNEO, JAVA, NEW_GUINEA, AUSTRALIA,
    NEW_ZEALAND, MADAGASCAR]

# ---------------------------------------------------------------- drawing
def draw_frame(pg, x, y, w, h, c):
    pg.rect(x, y, w, 1, c)
    pg.rect(x, y + h - 1, w, 1, c)
    pg.rect(x, y, 1, h, c)
    pg.rect(x + w - 1, y, 1, h, c)


def burst(pg, cx, cy, r, c):
    for i in range(8):
        a = math.pi * i / 4
        pg.line(cx, cy, int(cx + r * math.cos(a)), int(cy + r * math.sin(a)), c)
    pg.circle(cx, cy, max(2, r // 4), c)


def quad_curve(pg, p0, p1, p2, c, steps=24):
    prev = p0
    for i in range(1, steps + 1):
        t = i / steps
        x = (1 - t) * (1 - t) * p0[0] + 2 * (1 - t) * t * p1[0] + t * t * p2[0]
        y = (1 - t) * (1 - t) * p0[1] + 2 * (1 - t) * t * p1[1] + t * t * p2[1]
        cur = (int(x), int(y))
        pg.line(prev[0], prev[1], cur[0], cur[1], c)
        prev = cur


def pictogram(pg, kind, ox, oy):
    """Small geometric pictogram in a 28x28 box at (ox, oy)."""
    if kind == "flame":
        pg.poly([(14 + ox, 2 + oy), (22 + ox, 14 + oy), (18 + ox, 26 + oy),
                 (10 + ox, 26 + oy), (6 + ox, 14 + oy)], BURST)
        pg.poly([(14 + ox, 12 + oy), (18 + ox, 20 + oy), (14 + ox, 25 + oy),
                 (10 + ox, 20 + oy)], GOLD)
    elif kind == "missile":
        pg.line(ox + 4, oy + 24, ox + 22, oy + 6, INK)
        pg.poly([(ox + 22, oy + 6), (ox + 26, oy + 10), (ox + 18, oy + 12)], RED)
        pg.line(ox + 8, oy + 20, ox + 4, oy + 26, INK)
        pg.line(ox + 12, oy + 22, ox + 6, oy + 22, INK)
    elif kind == "burst":
        burst(pg, ox + 14, oy + 14, 12, BURST)
        pg.circle(ox + 14, oy + 14, 3, GOLD)
    elif kind == "globe":
        pg.ring(ox + 14, oy + 14, 11, NAVY)
        pg.line(ox + 3, oy + 14, ox + 25, oy + 14, NAVY)
        pg.line(ox + 14, oy + 3, ox + 14, oy + 25, NAVY)
        pg.rect(ox + 8, oy + 8, 12, 1, NAVY)
        pg.rect(ox + 8, oy + 19, 12, 1, NAVY)
    elif kind == "flags":
        pg.line(ox + 7, oy + 4, ox + 7, oy + 26, INK)
        pg.line(ox + 19, oy + 4, ox + 19, oy + 26, INK)
        pg.poly([(ox + 7, oy + 4), (ox + 17, oy + 7), (ox + 7, oy + 11)], RED)
        pg.poly([(ox + 19, oy + 4), (ox + 27, oy + 7), (ox + 19, oy + 11)], NAVY)
    elif kind == "summit":
        pg.circle(ox + 7, oy + 20, 3, NAVY)
        pg.circle(ox + 14, oy + 8, 3, RED)
        pg.circle(ox + 21, oy + 20, 3, NAVY)
        pg.line(ox + 7, oy + 20, ox + 14, oy + 8, INK)
        pg.line(ox + 14, oy + 8, ox + 21, oy + 20, INK)
        pg.line(ox + 7, oy + 20, ox + 21, oy + 20, INK)
    elif kind == "pin":
        pg.circle(ox + 14, oy + 10, 8, RED)
        pg.poly([(ox + 8, oy + 14), (ox + 20, oy + 14), (ox + 14, oy + 26)], RED)
        pg.circle(ox + 14, oy + 10, 3, WHITE)
    elif kind == "chip":
        pg.rect(ox + 7, oy + 7, 14, 14, NAVY)
        pg.rect(ox + 11, oy + 11, 6, 6, GOLD)
        for dx in (9, 14, 19):
            pg.rect(ox + dx, oy + 3, 2, 4, INK)
            pg.rect(ox + dx, oy + 21, 2, 4, INK)
        for dy in (9, 14, 19):
            pg.rect(ox + 3, oy + dy, 4, 2, INK)
            pg.rect(ox + 21, oy + dy, 4, 2, INK)
    elif kind == "bars":
        pg.rect(ox + 4, oy + 18, 5, 8, NAVY)
        pg.rect(ox + 12, oy + 12, 5, 14, RED)
        pg.rect(ox + 20, oy + 5, 5, 21, GOLD)
    elif kind == "tank":
        pg.rect(ox + 4, oy + 12, 18, 8, NAVY)
        pg.line(ox + 20, oy + 15, ox + 27, oy + 15, INK)
        pg.circle(ox + 8, oy + 22, 2, INK)
        pg.circle(ox + 14, oy + 22, 2, INK)
        pg.circle(ox + 20, oy + 22, 2, INK)
    elif kind == "gavel":
        pg.line(ox + 6, oy + 24, ox + 20, oy + 10, INK)
        pg.rect(ox + 16, oy + 4, 10, 6, NAVY)
        pg.rect(ox + 4, oy + 24, 8, 2, INK)
    elif kind == "crown":
        pg.poly([(ox + 5, oy + 22), (ox + 5, oy + 10), (ox + 10, oy + 15),
                 (ox + 14, oy + 6), (ox + 18, oy + 15), (ox + 23, oy + 10),
                 (ox + 23, oy + 22)], GOLD)
        pg.rect(ox + 5, oy + 22, 18, 3, GOLD)


def art_gulf(pg, ox, oy, w, h):
    pg.rect(ox, oy, w, h, NAVY)
    pg.poly([(ox + 30, oy + 30), (ox + 120, oy + 14), (ox + 210, oy + 28),
             (ox + 290, oy + 20), (ox + 305, oy + 55), (ox + 260, oy + 88),
             (ox + 170, oy + 98), (ox + 80, oy + 92), (ox + 25, oy + 62)], LAND)
    quad_curve(pg, (ox + 300, oy + 30), (ox + 210, oy + 5), (ox + 120, oy + 55), RED)
    quad_curve(pg, (ox + 310, oy + 70), (ox + 235, oy + 40), (ox + 150, oy + 75), RED)
    pg.circle(ox + 120, oy + 55, 3, WHITE)
    pg.circle(ox + 150, oy + 75, 3, WHITE)
    burst(pg, ox + 120, oy + 55, 12, BURST)
    burst(pg, ox + 150, oy + 75, 10, GOLD)


def art_climate(pg, ox, oy, w, h):
    pg.rect(ox, oy, w, h, DUSK)
    bars = [34, 52, 44, 66, 58, 74, 48, 62, 40, 56, 70, 46]
    bw = w // len(bars)
    for i, bh in enumerate(bars):
        pg.rect(ox + i * bw, oy + h - bh, bw - 2, bh, SKYLINE)
    quad_curve(pg, (ox + 20, oy + h - 30), (ox + 162, oy + h - 78),
               (ox + 304, oy + h - 30), GOLD)
    for vx in range(50, 300, 42):
        pg.line(ox + vx, oy + h - 30, ox + vx, oy + h - 52, GOLD)
    burst(pg, ox + 90, oy + 42, 13, BURST)
    burst(pg, ox + 225, oy + 58, 11, GOLD)
    pg.circle(ox + 78, oy + 30, 4, GREY)
    pg.circle(ox + 238, oy + 46, 4, GREY)


def art_cartel(pg, tp, ox, oy, w, h):
    pg.rect(ox, oy, w, h, CREAM)
    for gx in range(ox + 40, ox + w, 40):
        pg.vline(gx, oy, oy + h, (224, 214, 190))
    for gy in range(oy + 28, oy + h, 28):
        pg.hline(ox, ox + w, gy, (224, 214, 190))
    # Guasave at night: road, burning barricades, buildings
    pg.rect(ox, oy + 78, w, 34, (52, 52, 52))
    pg.rect(ox, oy + 92, w, 2, GOLD)
    for bx in (18, 78, 138, 198, 258):
        pg.rect(ox + bx, oy + 34, 44, 44, NAVY)
        pg.rect(ox + bx + 8, oy + 46, 10, 10, GOLD)
        pg.rect(ox + bx + 26, oy + 46, 10, 10, GOLD)
    for fx in (60, 160, 260):
        burst(pg, ox + fx, oy + 88, 11, BURST)
    tp.draw(pg, "sansb10", ox + 8, oy + 6, "GUASAVE, SINALOA", RED)
    pg.circle(ox + 252, oy + 88, 13, GOLD)
    pg.circle(ox + 288, oy + 70, 13, GOLD)
    for cx, cy, ch in ((ox + 252, oy + 88, "$"), (ox + 288, oy + 70, "5")):
        ww = tp.width("sansb15", ch)
        tp.draw(pg, "sansb15", cx - ww // 2, cy - 8, ch, INK)


def art_markets(pg, ox, oy, w, h):
    """Asian markets plunge: a falling gold line over red bars."""
    pg.rect(ox, oy, w, h, NAVY)
    for i in range(12):
        bx = ox + 12 + i * 25
        top = oy + 22 + i * 6
        pg.rect(bx, top, 14, oy + h - top - 6, (150, 45, 45))
    pg.line(ox + 12, oy + 18, ox + 306, oy + 92, GOLD)
    pg.line(ox + 12, oy + 21, ox + 306, oy + 95, GOLD)
    for i in range(7):
        px = ox + 18 + i * 46
        py = oy + 20 + i * 12
        pg.circle(px, py, 3, WHITE)
    burst(pg, ox + 292, oy + 88, 10, BURST)
    burst(pg, ox + 40, oy + 30, 8, GOLD)


LEAD_COLS = [12, 350, 688]
MED_COLS = [12, 180, 348, 516, 684, 852]
TICK_X = [170, 323, 476, 629, 782, 935]
MAP_X, MAP_Y, MAP_W, MAP_H = 12, 628, 330, 166
LAT_TOP, LAT_BOT = 84, -58


def project(lon, lat):
    px = MAP_X + int((lon + 180) * MAP_W / 360)
    py = MAP_Y + int((LAT_TOP - lat) * MAP_H / (LAT_TOP - LAT_BOT))
    return px, py


def render_page(pg, tp):
    assert len(LEADS) == 3 and len(MEDIUM) == 12
    assert len(LIST_A) + len(LIST_B) == 39
    total = 3 + 12 + 39

    # ---- kicker line
    tp.draw(pg, "sansb10", 12, 2, "THE WORLD'S NEWS OF ONE DAY", RED)
    kick_r = "54 STORIES \u00b7 9 REGIONS \u00b7 ALL FROM THIS MONDAY"
    tp.draw(pg, "sans10", 1012 - tp.width("sans10", kick_r), 2, kick_r, INK)

    # ---- masthead (bold sans at 2x: the serif blob only holds the
    # characters of the previous day's date)
    mast = "Monday 23 November 2026"
    tp.draw2x(pg, "sansb22", (W - 2 * tp.width("sansb22", mast)) // 2, 16,
              mast, INK)
    pg.hline(12, 1012, 72, INK, 2)
    pg.hline(12, 1012, 75, INK, 1)

    # ---- timeline
    tp.draw(pg, "sansb10", 12, 80, "THE DAY IN UTC", RED)
    pg.hline(140, 980, 99, INK, 1)
    for slot, tick in zip(TIMELINE, TICK_X):
        pg.vline(tick, 95, 103, INK, 1)
        tp.draw(pg, "sansb10", tick - tp.width("sansb10", slot["time"]) // 2, 82,
                slot["time"], INK)
        tp.draw(pg, "sans10", tick - tp.width("sans10", slot["event"]) // 2, 102,
                slot["event"], INK)

    # ---- leads
    art_fns = [art_climate, art_markets, art_gulf]
    for i, lead in enumerate(LEADS):
        lx = LEAD_COLS[i]
        art_fns[i](pg, lx, 118, 324, 112)
        draw_frame(pg, lx, 118, 324, 112, INK)
        tp.draw(pg, "sansb10", lx, 236, lead["kicker"], RED)
        wrapped = tp.wrap("sansb22", lead["headline"], 324)[:3]
        for j, txt in enumerate(wrapped):
            tp.draw(pg, "sansb22", lx, 252 + j * 26, txt, INK)
        for j, txt in enumerate(tp.wrap("sans12", lead["body"], 324)[:2]):
            tp.draw(pg, "sans12", lx, 332 + j * 15, txt, INK)
        tp.draw(pg, "sans10", lx, 364, lead["source"], GREY)
    pg.hline(12, 1012, 382, INK, 1)

    # ---- medium stories: 6 columns, 2 rows
    for k, item in enumerate(MEDIUM):
        col, row = k % 6, k // 6
        mx = MED_COLS[col]
        ry = 388 + row * 110
        pictogram(pg, item["icon"], mx, ry)
        tp.draw(pg, "sansb10", mx + 34, ry + 8, item["kicker"], RED)
        for j, txt in enumerate(tp.wrap("sansb15", item["headline"], 160)[:2]):
            tp.draw(pg, "sansb15", mx, ry + 32 + j * 17, txt, INK)
        for j, txt in enumerate(tp.wrap("sans10", item["detail"], 160)[:2]):
            tp.draw(pg, "sans10", mx, ry + 68 + j * 12, txt, INK)
        tp.draw(pg, "sans10", mx, ry + 92, item["source"], GREY)
    pg.hline(12, 1012, 606, INK, 1)

    # ---- bottom section headers
    tp.draw(pg, "sansb10", 12, 612, "WHERE IT HAPPENED", RED)
    tp.draw(pg, "sansb10", 354, 612, "AMERICAS \u00b7 AFRICA \u00b7 MIDDLE EAST",
            RED)
    tp.draw(pg, "sansb10", 676, 612, "EUROPE \u00b7 ASIA \u00b7 MARKETS", RED)
    pg.vline(348, 612, 1000, GREY, 1)
    pg.vline(672, 612, 1000, GREY, 1)

    # ---- world map
    pg.rect(MAP_X, MAP_Y, MAP_W, MAP_H, OCEAN)
    grid_c = (198, 216, 222)
    for lon in range(-150, 181, 30):
        gx, _ = project(lon, 0)
        pg.vline(gx, MAP_Y, MAP_Y + MAP_H, grid_c, 1)
    for lat in (60, 30, 0, -30):
        _, gy = project(0, lat)
        pg.hline(MAP_X, MAP_X + MAP_W, gy, grid_c, 1)
    for poly_lonlat in CONTINENTS:
        pg.poly([project(lon, lat) for lon, lat in poly_lonlat], LAND)
    draw_frame(pg, MAP_X, MAP_Y, MAP_W, MAP_H, INK)
    for dot in MAP_DOTS:
        sx, sy = project(dot["lon"], dot["lat"])
        dotx, doty = sx + dot["dx"], sy + dot["dy"]
        if dot["dx"] or dot["dy"]:
            pg.line(sx, sy, dotx, doty, INK)
            pg.circle(sx, sy, 2, RED)
        pg.circle(dotx, doty, 7, RED)
        tag = str(dot["n"])
        tp.draw(pg, "sansb10", dotx - tp.width("sansb10", tag) // 2,
                doty - 6, tag, WHITE)
    for j, txt in enumerate(MAP_LEGEND.split("\n")):
        tp.draw(pg, "sans10", 12, 798 + j * 12, txt, INK)

    # ---- date check box
    draw_frame(pg, 12, 850, 330, 150, INK)
    tp.draw(pg, "sansb10", 20, 856, "DATE CHECK \u2014 LEFT OUT AS OLDER NEWS",
            RED)
    for j, item in enumerate(DATECHECK):
        tp.draw(pg, "sans10", 20, 872 + j * 12, item["text"], INK)

    # ---- list columns
    for colx, items in ((354, LIST_A), (676, LIST_B)):
        for j, item in enumerate(items):
            y = 634 + j * 17
            pg.rect(colx, y + 4, 9, 3, RED)
            pg.rect(colx, y + 7, 9, 3, NAVY)
            after = tp.draw(pg, "sans12", colx + 13, y, item["text"], INK)
            tp.draw(pg, "sans12", after, y, " [" + item["source"] + "]", GREY)

    # ---- footer
    pg.hline(12, 1012, 1006, GREY, 1)
    tp.draw(pg, "sans10", (W - tp.width("sans10", FOOTER)) // 2, 1010,
            FOOTER, GREY)
    return total


# ---------------------------------------------------------------- main
def render_entry():
    fonts = _decode_fonts()
    pg = Surface(W, H, PAPER)
    tp = Typer(fonts)
    total = render_page(pg, tp)
    return encode_png_bytes(pg), total


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--output", "-o", default=None)
    ap.add_argument("--check", action="store_true",
                    help="render and validate without writing a file")
    args = ap.parse_args(argv)
    png, total = render_entry()
    if len(png) > 1024 * 1024:
        print("FAIL: PNG is %d bytes, over the 1 MiB limit" % len(png),
              file=sys.stderr)
        return 1
    if args.check:
        print("CHECK OK: %d stories (3 leads + 12 medium + 39 list), "
              "1024x1024, PNG %d bytes (%.1f KB)"
              % (total, len(png), len(png) / 1024))
        return 0
    out = args.output
    if out is None:
        outdir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
        out = os.path.join(outdir, "entry.png")
    parent = os.path.dirname(os.path.abspath(out))
    if parent:
        os.makedirs(parent, exist_ok=True)
    with open(out, "wb") as f:
        f.write(png)
    print("wrote %s (%d bytes, %.1f KB, %d stories)"
          % (out, len(png), len(png) / 1024, total))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
