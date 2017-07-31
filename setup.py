#!/usr/bin/env python

from setuptools import setup

setup(
    name='tap-selligent',
    version='0.0.1',
    description='Singer.io tap for extracting data from the Selligent API',
    author='Stitch',
    url='http://singer.io',
    classifiers=['Programming Language :: Python :: 3 :: Only'],
    py_modules=['tap_selligent'],
    install_requires=[
        'singer-python==1.8.1',
        'backoff==1.3.2',
        'requests==2.12.4',
        'python-dateutil==2.6.0'
    ],
    entry_points='''
    [console_scripts]
    tap-selligent=tap_selligent:main
    ''',
    packages=['tap_selligent']
)
