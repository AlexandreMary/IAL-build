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

DEFAULT_IA4H_REPO = os.environ.get('DEFAULT_IA4H_REPO')
if DEFAULT_IA4H_REPO in ('', None):
    GIT_HOMEPACK = os.environ.get('GIT_HOMEPACK', os.path.join(os.environ['HOME'], 'repositories'))
    DEFAULT_IA4H_REPO = os.path.join(GIT_HOMEPACK, 'IA4H')

# temporary => UNTIL USE OF BUNDLE
_ecSDK_dir = '/home/gmap/mrpe/mary/public/ecSDK'
GMKPACK_HUB_PACKAGES = {'eckit':{'CY48':'1.4.4',
                                 'belenos':_ecSDK_dir,
                                 'beaufix':_ecSDK_dir,
                                 'project':'ecSDK'},
                        'fckit':{'CY48':'0.6.4',
                                 'belenos':_ecSDK_dir,
                                 'beaufix':_ecSDK_dir,
                                 'project':'ecSDK'},
                        'ecbuild':{'CY48':'3.1.0',
                                   'belenos':_ecSDK_dir,
                                   'beaufix':_ecSDK_dir,
                                   'project':'ecSDK'}
                        }
HPCs = ('beaufix', 'belenos')
