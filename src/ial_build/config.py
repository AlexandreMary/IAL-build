#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (c) Météo France (2020)
# This software is governed by the CeCILL-C license under French law.
# http://www.cecill.info
from __future__ import print_function, absolute_import, unicode_literals, division
"""
Configuration parameters.
"""

import os
import re

IAL_OFFICIAL_TAGS_re = re.compile('CY(?P<release>\d{2}([TRH]\d)?)' +
                                  '(_(?P<radical>.+)\.(?P<version>\d{2}))?$')
IAL_OFFICIAL_PACKS_re = re.compile('(?P<prefix>((cy)|(CY))?)(?P<release>\d{2}([TRHtrh]\d)?)' + '_' +
                                   '(?P<radical>.+)\.(?P<version>\d{2})' + '\.' +
                                   '(?P<compiler_label>\w+)\.(?P<compiler_flag>\w+)' +
                                   '(?P<suffix>(\.pack)?)$')
IAL_BRANCHES_re = re.compile('_'.join(['(?P<user>\w+)',
                                       'CY(?P<release>\d{2}([TRH]\d)?)',
                                       '(?P<radical>.+)$']))
IAL_DOC_OUTPUT_DIR = os.path.join(os.environ['HOME'], 'tmp','prep_doc')

DEFAULT_BUNDLE_CACHE_DIR = os.path.join(os.environ['HOME'], 'bundles')

# default repository for IAL
DEFAULT_IAL_REPO = os.environ.get('DEFAULT_IAL_REPO')
if DEFAULT_IAL_REPO in ('', None):
    _git_homepack = os.environ.get('GIT_HOMEPACK', os.path.join(os.environ['HOME'], 'repositories'))
    DEFAULT_IAL_REPO = os.path.join(_git_homepack, 'IAL')
# default repository for IAL-bundle
DEFAULT_IALBUNDLE_REPO = os.environ.get('DEFAULT_IALBUNDLE_REPO')
if DEFAULT_IALBUNDLE_REPO in ('', None):
    DEFAULT_IALBUNDLE_REPO = 'https://github.com/ACCORD-NWP/IAL-bundle.git'
# default gmkpack compiler flag
DEFAULT_PACK_COMPILER_FLAG = os.environ.get('GMK_OPT', 'x')

# hosts recognition
hosts_re = {
    'belenos':re.compile('^belenos(login)?\d+\.belenoshpc\.meteo\.fr$'),
    'taranis':re.compile('^taranis(login)?\d+\.taranishpc\.meteo\.fr$'),
    'lxcnrm':re.compile('^[pls]x[a-z]+\d{1,2}$')
    }
