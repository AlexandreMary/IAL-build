#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (c) Météo France (2020)
# This software is governed by the CeCILL-C license under French law.
# http://www.cecill.info

from __future__ import print_function, absolute_import, unicode_literals, division

USUAL_BINARIES = ['masterodb', 'bator',
                  'ioassign', 'lfitools',
                  'pgd', 'prep',
                  'oovar', 'ootestvar',
                  ]

class PackError(Exception):
    pass


from .gmkpack import GmkpackTool
from .pack import Pack
