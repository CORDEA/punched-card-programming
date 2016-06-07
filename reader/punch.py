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
            help = "number of columns per marksheet"
            )

    return parser.parse_args()

class Reader:
    def __init__(self):
        pass

    def read(self, defFile, imgFile, defCols):
        img = Image.open(imgFile)
        self.rgb = img.convert("RGB")
        self.w, self.h = img.size

        cols = self.getYRegion()
        assert len(cols) == 12

        rows = self.getXRegion(defCols)
        assert len(rows) == defCols

        res = self.process(rows, cols)
        assert len(res) == defCols

        d = self.readDef(defFile)
        line = ""
        for r in res:
            c = self.toChar(r, d)
            if c == None:
                raise DefNotFoundError(r)
            else:
                line = line + c
        print line

    def isAcceptableColorRange(self, pixel):
        for p in pixel:
            if p > THRESHOLD:
                return False
        return True

    def isAcceptableRange(self, c, region):
        for r in region:
            if c >= r[0] and c <= r[1]:
                return True
        return False

    def getCurrentPos(self, c, region):
        for i in range(len(region)):
            r = region[i]
            if c >= r[0] and c <= r[1]:
                return i
        return -1

    def toPunchCardPos(self, pos):
        if   pos == 0:
            return 12
        elif pos == 1:
            return 11
        return pos - 2

    def getYRegion(self):
        rgb = self.rgb
        cols = []
        for x in range(self.w):
            region = []
            for y in range(self.h):
                p = rgb.getpixel((x, y))
                if x > 0:
                    befP = rgb.getpixel((x - 1, y))
                if self.isAcceptableColorRange(p):
                    if x > 0 and self.isAcceptableColorRange(befP):
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

    def getXRegion(self, defCols):
        rgb = self.rgb
        rows = []
        for y in reversed(range(self.h)):
            region = []
            for x in range(self.w):
                p = rgb.getpixel((x, y))
                if y > 0:
                    befP = rgb.getpixel((x, y - 1))
                if self.isAcceptableColorRange(p):
                    if y > 0 and self.isAcceptableColorRange(befP):
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

    def process(self, xReg, yReg):
        rgb = self.rgb
        cols = []
        line = -1
        for x in range(self.w):
            rows = []
            isConn = False
            befX = x - 1
            for y in range(self.h):
                p = rgb.getpixel((x, y))
                if x > 0:
                    befP = rgb.getpixel((x - 1, y))
                if self.isAcceptableColorRange(p):
                    if x > 0 and self.isAcceptableColorRange(befP):
                        continue
                    if not isConn:
                        l = self.getCurrentPos(y, yReg)
                        if l != -1:
                            rows.append(self.toPunchCardPos(l))
                        isConn = True
                else:
                    isConn = False
            l = self.getCurrentPos(x, xReg)
            if l != -1:
                if line == l:
                    if len(cols) > l:
                        if len(cols[l]) == 0 and len(rows) > 0:
                            cols[l] = rows
                else:
                    cols.append(rows)
                    line = l
        return cols

    def readDef(self, name):
        defMap = {}
        with open(name) as f:
            for line in f.readlines():
                ts = line.split("\t")
                ds = tuple([int(r) for r in (ts[0].split(",") if "," in ts[0] else [ts[0]])])
                if len(ds) not in defMap:
                    defMap[len(ds)] = []
                defMap[len(ds)].append((ds, ts[1].rstrip()))
        return defMap

    def toChar(self, n, defMap):
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
        sys.exit("Argument is missing, or too many.")

    rd = Reader()
    rd.read(args[0], args[1], options.column)
