#!/usr/bin/python

import os
import os.path
from distutils.core import setup
try:
	import tornado
except ImportError:
	print "rbalancer will still be installed, but you need to install tornado in order to run rbalancer" 

datafiles = [('', ['README.rst'])]
homedir = os.path.expanduser('~')

if os.access('/etc', os.W_OK) and not os.path.exists(os.path.join('/etc', 'rbalancer.conf.default')):
    datafiles.append(('/etc', ['conf/rbalancer.conf.default']))
datafiles.append(('/etc/init.d', ['init/rbalancer']))

with open('README.rst') as file:
	long_description = file.read()

setup(
    data_files = datafiles,
    name = 'rbalancer',
    version = '0.1.0',
    url = 'https://github.com/whatvn/rbalancer',
    description = 'HTTP Load Balancer using redirect response.',
    long_description = long_description,
    author = 'Hung Nguyen Van',
    author_email = 'hungnv@opensource.com.vn',
    license = 'gpl',
    platforms = 'any',
    scripts=['sbin/rbalancer'],
    py_modules = [
        'rbalancer'
    ],
    classifiers = [
        'Development Status :: 2 - Beta',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        'License :: OSI Approved :: GNU General Public License (GPL)',
        'License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Topic :: Internet',
        'Topic :: System :: Systems Administration',
        'Topic :: Communications',
    ],
)
