#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
riprova
=======
Small and versatile library to retry failed operations
using different backoff strategies.

:copyright: (c) Tomas Aparicio
:license: MIT
"""

import os
import sys
import codecs
from setuptools import setup, find_packages
from setuptools.command.test import test as TestCommand

# Publish command
if sys.argv[-1] == 'publish':
    os.system('python setup.py sdist upload')
    sys.exit()


setup_requires = []
if 'test' in sys.argv:
    setup_requires.append('pytest')


def read_version(package):
    with open(os.path.join(package, '__init__.py'), 'r') as fd:
        for line in fd:
            if line.startswith('__version__ = '):
                return line.split()[-1].strip().strip("'")


# Get package current version
version = read_version('riprova')


class PyTest(TestCommand):
    def finalize_options(self):
        TestCommand.finalize_options(self)
        self.test_args = ['tests/']
        self.test_suite = True

    def run_tests(self):
        # import here, cause outside the eggs aren't loaded
        import pytest
        errno = pytest.main(self.test_args)
        sys.exit(errno)


with codecs.open('requirements-dev.txt', encoding='utf-8') as f:
    tests_require = f.read().splitlines()
with codecs.open('requirements.txt', encoding='utf-8') as f:
    install_requires = f.read().splitlines()
with codecs.open('README.rst', encoding='utf-8') as f:
    readme = f.read()
with codecs.open('History.rst', encoding='utf-8') as f:
    history = f.read()


setup(
    name='riprova',
    version=version,
    author='Tomas Aparicio',
    author_email='tomas+python@aparicio.me',
    description=(
        'Small and versatile library to retry failed operations using '
        'different backoff strategies'
    ),
    url='https://github.com/h2non/riprova',
    license='MIT',
    long_description=readme + '\n\n' + history,
    py_modules=['riprova'],
    zip_safe=False,
    install_requires=install_requires,
    tests_require=tests_require,
    packages=find_packages(exclude=['tests']),
    package_data={'': ['README.rst', 'LICENSE', 'History.rst',
                       'requirements.txt', 'requirements-dev.txt']},
    package_dir={'riprova': 'riprova'},
    include_package_data=True,
    cmdclass={'test': PyTest},
    classifiers=[
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        'Operating System :: OS Independent',
        'Development Status :: 5 - Production/Stable',
        'Natural Language :: English',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Topic :: Software Development',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Programming Language :: Python :: Implementation :: CPython',
        'Programming Language :: Python :: Implementation :: PyPy',
        'Programming Language :: Python :: Implementation :: Jython'
    ],
)
