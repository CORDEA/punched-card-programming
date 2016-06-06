#!/usr/bin/env python
# encoding:utf-8
#
# Copyright 2016 Yoshihiro Tanaka
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

__Author__  = "Yoshihiro Tanaka <contact@cordea.jp>"
__date__    = "2016-06-04"
__version__ = "0.1"

from PIL import Image
from error import DefNotFoundError
import sys
from optparse import OptionParser

THRESHOLD = 40

def setOptions():
    usage = "%prog [options] [definition tsv file] [target image file]"
    version = __version__
    parser = OptionParser(usage=usage, version=version)

    parser.add_option(
            "-c", "--column",
            action = "store",
            type = "int",
            dest = "column",
            default = 80,
            help = "Number of columns per marksheet."
            )

    return parser.parse_args()

def isAcceptableColorRange(pixel):
    for p in pixel:
        if p > THRESHOLD:
            return False
    return True

def isAcceptableRange(c, region):
    for r in region:
        if c >= r[0] and c <= r[1]:
            return True
    return False

def getCurrentPos(c, region):
    for i in range(len(region)):
        r = region[i]
        if c >= r[0] and c <= r[1]:
            return i
    return -1

def toPunchCardPos(pos):
    if   pos == 0:
        return 12
    elif pos == 1:
        return 11
    return pos - 2

def getYRegion(rgb, w, h):
    cols = []
    for x in range(w):
        region = []
        for y in range(h):
            p = rgb.getpixel((x, y))
            if x > 0:
                befP = rgb.getpixel((x - 1, y))
            if isAcceptableColorRange(p):
                if x > 0 and isAcceptableColorRange(befP):
                    continue
                region.append(y)
            else:
                if len(region) > 0:
                    cols.append(region)
                    region = []
        if len(cols) == 12:
            break
        else:
            cols = []
    res = []
    for c in cols:
        res.append((min(c), max(c)))
    return tuple(res)

def getXRegion(rgb, w, h, defCols):
    rows = []
    for y in reversed(range(h)):
        region = []
        for x in range(w):
            p = rgb.getpixel((x, y))
            if y > 0:
                befP = rgb.getpixel((x, y - 1))
            if isAcceptableColorRange(p):
                if y > 0 and isAcceptableColorRange(befP):
                    continue
                region.append(x)
            else:
                if len(region) > 0:
                    rows.append(region)
                    region = []
        if len(rows) == (defCols + 1):
            break
        else:
            rows = []
    res = []
    for r in rows[1:]:
        res.append((min(r), max(r)))
    return tuple(res)

def process(rgb, w, h, xReg, yReg):
    cols = []
    line = -1
    for x in range(w):
        rows = []
        isConn = False
        befX = x - 1
        for y in range(h):
            p = rgb.getpixel((x, y))
            if x > 0:
                befP = rgb.getpixel((x - 1, y))
            if isAcceptableColorRange(p):
                if x > 0 and isAcceptableColorRange(befP):
                    continue
                if not isConn:
                    l = getCurrentPos(y, yReg)
                    if l != -1:
                        rows.append(toPunchCardPos(l))
                    isConn = True
            else:
                isConn = False
        l = getCurrentPos(x, xReg)
        if l != -1:
            if line == l:
                if len(cols) > l:
                    if len(cols[l]) == 0 and len(rows) > 0:
                        cols[l] = rows
            else:
                cols.append(rows)
                line = l
    return cols

def readDef(name):
    defMap = {}
    with open(name) as f:
        for line in f.readlines():
            ts = line.split("\t")
            ds = tuple([int(r) for r in (ts[0].split(",") if "," in ts[0] else [ts[0]])])
            if len(ds) not in defMap:
                defMap[len(ds)] = []
            defMap[len(ds)].append((ds, ts[1].rstrip()))
    return defMap

def toChar(n, defMap):
    if len(n) == 0:
        return " "
    ds = defMap[len(n)]
    for d in ds:
        de = d[0]
        correct = True
        for i in range(len(de)):
            if de[i] != n[i]:
                correct = False
        if correct:
            return d[1]
    return None

if __name__=='__main__':
    options, args = setOptions()

    if len(args) != 2:
        print "Argument is missing."
        exit()

    defFile,imgFile = args

    img = Image.open(imgFile)
    rgb = img.convert("RGB")
    w, h = img.size

    defCols = options.column

    cols = getYRegion(rgb, w, h)
    assert len(cols) == 12

    rows = getXRegion(rgb, w, h, defCols)
    assert len(rows) == defCols

    res = process(rgb, w, h, rows, cols)
    assert len(res) == defCols

    d = readDef(defFile)
    line = ""
    for r in res:
        c = toChar(r, d)
        if c == None:
            raise DefNotFoundError(r)
        else:
            line = line + c
    print line
