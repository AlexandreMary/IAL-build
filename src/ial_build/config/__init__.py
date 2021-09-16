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

DEFAULT_IA4H_REPO = os.environ.get('DEFAULT_IA4H_REPO')
if DEFAULT_IA4H_REPO in ('', None):
    GIT_HOMEPACK = os.environ.get('GIT_HOMEPACK', os.path.join(os.environ['HOME'], 'repositories'))
    DEFAULT_IA4H_REPO = os.path.join(GIT_HOMEPACK, 'IA4H')

# temporary => UNTIL USE OF BUNDLE
_ecSDK_dir = {'belenos':'/home/gmap/mrpe/mary/public/ecSDK',
              'taranis':'/home/gmap/mrpe/mary/public/ecSDK',
              'lxcnrm':'/home/common/epygram/public/ecSDK',
              }
GMKPACK_HUB_PACKAGES = {'eckit':{'CY48':'1.4.4',
                                 'CY48T1':'1.4.4',
                                 'CY46T1':'1.4.4',
                                 'project':'ecSDK'},
                        'fckit':{'CY48':'0.6.4',
                                 'CY48T1':'0.6.4',
                                 'CY46T1':'0.6.4',
                                 'project':'ecSDK'},
                        'ecbuild':{'CY48':'3.1.0',
                                   'CY48T1':'3.1.0',
                                   'CY46T1':'3.1.0',
                                   'project':'ecSDK'}
                        }
for p in GMKPACK_HUB_PACKAGES.keys():
    GMKPACK_HUB_PACKAGES[p].update(**_ecSDK_dir)
hosts_re = {
    'belenos':re.compile('^belenos(login)?\d+\.belenoshpc\.meteo\.fr$'),
    'taranis':re.compile('^taranis(login)?\d+\.taranishpc\.meteo\.fr$'),
    'lxcnrm':re.compile('^[pls]x[a-z]+\d{1,2}$')
    }
