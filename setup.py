#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# This file is part of thr library released under the MIT license.
# See the LICENSE file for more information.

from setuptools import setup, find_packages

DESCRIPTION = ("Asynchronous HTTP router, traffic shaper " +
               "and proxy based on Tornado and Redis")

try:
    with open('PIP.rst') as f:
        LONG_DESCRIPTION = f.read()
except IOError:
    LONG_DESCRIPTION = DESCRIPTION

with open('pip-requirements.txt') as reqs:
    install_requires = [
        line for line in reqs.read().split('\n')
        if (line and not line.startswith('--'))
    ]
setup(
    name='thr',
    version="0.0.1",
    author="Fabien MARTY",
    author_email="fabien.marty@gmail.com",
    url="https://github.com/thefab/thr",
    packages=find_packages(),
    license='MIT',
    download_url='https://github.com/thefab/thr',
    description=DESCRIPTION,
    long_description=LONG_DESCRIPTION,
    install_requires=install_requires,
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        'License :: OSI Approved :: MIT License',
        'Operating System :: MacOS :: MacOS X',
        'Operating System :: POSIX',
        'Operating System :: Unix',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Topic :: Utilities',
        'Topic :: System :: Distributed Computing',
        'Topic :: Software Development',
    ],
    entry_points="""
    [console_scripts]
    http2redis = thr.http2redis.app:main
    redis2http = thr.redis2http.app:main
    """,
)
