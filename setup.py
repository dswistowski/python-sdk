#!/usr/bin/env python
# -*- coding: utf-8 -*-
from distutils.core import setup
 
setup(
    name='facebook-python-sdk',
    version='0.1',
    description='This is fork of client library is designed to support the Facebook Graph API and the official Facebook JavaScript SDK, which is the canonical way to implement Facebook authentication. Fork is to make connection with django framework',
    author='Facebook',
    url='http://github.com/dswistowski/python-sdk',
    package_dir={'': 'src'},
    py_modules=[
        'facebook', 'facebookdj'
    ],
)
