# -*- coding: utf-8 -*-
import codecs
import os
import re
from setuptools import setup


VER_RE = "__version__ = [\"'](?P<Version>(?:(?![\"']).)*)"

here = os.path.abspath(os.path.dirname(__file__))

with open(os.path.join(os.getcwd(), 'flask_cuttlepool.py'), 'r') as f:
    init_file = f.read()
    version = re.search(VER_RE, init_file).group('Version')

with codecs.open(os.path.join(here, 'README.rst'), encoding='utf-8') as f:
    long_description = f.read()


setup(
    name='Flask-CuttlePool',
    version=version,
    description='A Flask extension for CuttlePool',
    long_description=long_description,
    url='http://github.com/smitchell556/flask-cuttlepool',
    license='BSD 3-Clause',
    author='Spencer Mitchell',
    py_modules=['flask_cuttlepool'],
    include_package_data=True,
    platforms='any',
    install_requires=[
        'cuttlepool>=0.6.0',
        'flask'
    ],
    extras_require={
        'dev': ['pytest']
    },
    classifiers=[
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        'Topic :: Software Development :: Libraries :: Python Modules'
    ]
)
