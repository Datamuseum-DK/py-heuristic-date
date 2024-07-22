#!/usr/bin/env python3
# -*- encoding: utf-8  -*-
#
# Copyright (c) 2024 Poul-Henning Kamp
# All rights reserved.
#
# Author: Poul-Henning Kamp <phk@phk.freebsd.dk>
#
# SPDX-License-Identifier: BSD-2-Clause
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
# 1. Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions and the following disclaimer in the
#    documentation and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE AUTHOR AND CONTRIBUTORS ``AS IS'' AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED.  IN NO EVENT SHALL AUTHOR OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS
# OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION)
# HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY
# OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF
# SUCH DAMAGE.

'''
    Date heuristics
    ================

    Heuristically attempt to decode a string containing a date.

    Only years in the range [1900…present] are accepted.

    Two digit years are only accepted for [1932…1999]

    Month names are Danish or English (see MONTHS array)

    Where no ambiguity exists, ordering does not matter:
    Both "1983 31 12" and "aug 1923 12" will be accepted.

    Dates containing precisely two '.' or '-' separators are
    assumed to use either DMY or YMD ordering.

    If there D and M are ambiguous, return only the year.

    If multiple years, months or days are present, the first is
    used, providede there is no ambiguity.

    Return None on failure to grok input.

'''

import re
import time

YEAR_LOW = 1900
YEAR_HIGH = time.localtime().tm_year
Y2K_LOW = 32
Y2K_HIGH = 99

assert Y2K_LOW > 31

MONTHS = [
   [re.compile('january|januar|jan', re.IGNORECASE), "…m1"],
   [re.compile('february|februar|feb', re.IGNORECASE), "…m2"],
   [re.compile('march|marts|mar', re.IGNORECASE), "…m3"],
   [re.compile('april|apr', re.IGNORECASE), "…m4"],
   [re.compile('maj|may', re.IGNORECASE), "…m5"],
   [re.compile('june|juni|jun', re.IGNORECASE), "…m6"],
   [re.compile('july|juli|jul', re.IGNORECASE), "…m7"],
   [re.compile('august|aug', re.IGNORECASE), "…m8"],
   [re.compile('september|sept|sep', re.IGNORECASE), "…m9"],
   [re.compile('october|oct|oktober|okt', re.IGNORECASE), "…m10"],
   [re.compile('november|nov', re.IGNORECASE), "…m11"],
   [re.compile('december|dec', re.IGNORECASE), "…m12"],
]

def is_year(x):
    ''' Is x a year '''
    return YEAR_LOW <= int(x) <= YEAR_HIGH

def is_y2k(x):
    ''' Is x a two digit year '''
    return Y2K_LOW <= int(x) <= Y2K_HIGH

def is_month(x):
    ''' Is x a month number '''
    return 1 <= int(x) <= 12

def is_day(x):
    ''' Is x a day number '''
    return 1 <= int(x) <= 31

def interpret(instr):
    '''
    Try to interpret instr as a date, return as much of "YYYY-[MM[-DD]]" as we can.
    '''

    year = None
    month = None
    day = None
    nbrs = []

    # Split into runs of numbers and non-numbers
    l = [instr[0]]
    for i in instr[1:]:
        if i.isdigit() ^ l[-1][-1].isdigit():
            l.append(i)
        else:
            l[-1] += i

    # Classify the numbers we found
    for n, x in list(enumerate(l)):
        if not x.isdigit():
            continue
        v = int(x)

        if len(x) == 8 and is_year(x[:4]) and is_month(x[4:6]) and is_day(x[6:]):
            year = int(x[:4])
            month = int(x[4:6])
            day = int(x[6:])
            break

        if len(x) == 8 and is_day(x[:2]) and is_month(x[2:4]) and is_year(x[4:]):
            year = int(x[4:])
            month = int(x[2:4])
            day = int(x[:2])
            break

        if len(x) == 6 and is_year(x[:4]) and is_month(x[4:]):
            year = int(x[:4])
            month = int(x[4:6])
            day = None
            break

        if len(x) == 6 and is_y2k(x[:2]) and is_month(x[2:4]) and is_day(x[4:]):
            year = int(x[:2]) + 1900
            month = int(x[2:4])
            day = int(x[4:])
            break

        if len(x) == 6 and is_day(x[:2]) and is_month(x[2:4]) and is_y2k(x[4:]):
            year = int(x[4:]) + 1900
            month = int(x[2:4])
            day = int(x[:2])
            break

        if year is None and len(x) == 4 and is_y2k(x[:2]) and is_month(x[2:]):
            year = int(x[:2])
            month = int(x[2:])
            day = None
            break

        if year is None and len(x) == 4 and is_year(v):
            l[n] = "…y" + x
            year = v
        elif year is None and len(x) == 2 and is_y2k(v):
            l[n] = "…y19" + x
            year = 1900 + v
        elif day is None and len(x) == 2 and v > 12 and is_day(v):
            l[n] = "…d" + x
            day = v
        elif len(x) <= 2 and v:
            l[n] = "…n" + x
            nbrs.append(v)

    # Look for month names
    n = 0
    while n < len(l) and month is None:
        first_match = None
        first_mon_id = None
        for regex, mon_id in MONTHS:
            match = regex.search(l[n])
            if match is None:
                continue
            if first_match is None or match.span() < first_match.span():
                first_match = match
                first_mon_id = mon_id
        if first_match is None:
            n += 1
            continue
        x = l.pop(n)
        span = first_match.span()
        if span[0] > 0:
            l.insert(n, x[:span[0]])
            n += 1
        l.insert(n, first_mon_id)
        month = l[n][2:]
        n += 1
        if span[1] < len(x):
            l.insert(n, x[span[1]:])

    if year is None:
        return None

    year = int(year)
    if month is not None:
        month = int(month)
    if day is not None:
        day = int(day)

    if None not in (month, day):
        return "%04d-%02d-%02d" % (year, month, day)

    if month is not None and len(nbrs) == 0:
        return "%04d-%02d" % (year, month)

    if month is not None and len(nbrs) == 1 and is_day(nbrs[0]):
        return "%04d-%02d-%02d" % (year, month, nbrs[0])

    if day is not None and len(nbrs) == 1 and is_month(nbrs[0]):
        return "%04d-%02d-%02d" % (year, nbrs[0], day)

    if month is None and day is None and len(nbrs) == 1 and is_month(nbrs[0]):
        return "%04d-%02d" % (year, nbrs[0])

    if len(nbrs) == 2:
        x = "".join(l)
        if l[-1][:2] == "…y" and is_day(nbrs[0]) and is_month(nbrs[1]):
            for sep in "-.":
                if x.count(sep) == 2:
                    return "%04d-%02d-%02d" % (year, nbrs[1], nbrs[0])
        if l[0][:2] == "…y" and is_day(nbrs[1]) and is_month(nbrs[0]):
            for sep in "-.":
                if x.count(sep) == 2:
                    return "%04d-%02d-%02d" % (year, nbrs[0], nbrs[1])

    if month is not None:
        return "%04d-%02d" % (year, month)

    return "%04d" % year

def main_tty():
    ''' Trivial interactive test function '''
    while True:
        try:
            i = input('--> ')
        except EOFError:
            break
        print("\t", i, "=>", interpret(i))

def main_batch():
    ''' Trivial interactive test function '''
    while True:
        try:
            i = input()
        except EOFError:
            break
        print(interpret(i))

if __name__ == "__main__":
    import sys
    import os
    if os.isatty(sys.stdin.fileno()):
        main_tty()
    else:
        main_batch()
