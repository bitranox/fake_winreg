"""Setuptools entry point."""
import codecs
import os
from typing import Dict, List

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

package_name = 'lib_registry'
required = list()         # type: List
entry_points = dict()     # type: Dict


def get_version(dist_directory):
    # type: (str) -> str
    path_version_file = os.path.join(os.path.dirname(__file__), [dist_directory, 'version.txt'])
    with open(path_version_file, mode='r') as version_file:
        version = version_file.readline()
    return version


CLASSIFIERS = [
    'Development Status :: 5 - Production/Stable',
    'Intended Audience :: Developers',
    'License :: OSI Approved :: MIT License',
    'Natural Language :: English',
    'Operating System :: OS Independent',
    'Programming Language :: Python',
    'Topic :: Software Development :: Libraries :: Python Modules'
]


long_description = package_name
path_readme = os.path.join(os.path.dirname(__file__), 'README.rst')
if os.path.exists(path_readme):
    # noinspection PyBroadException
    try:
        readme_content = codecs.open(path_readme, encoding='utf-8').read()
        long_description = readme_content
    except Exception:
        pass


setup(name=package_name,
      version=get_version(package_name),
      url='https://github.com/bitranox/{package_name}'.format(package_name=package_name),
      packages=[package_name],
      description=package_name,
      long_description=long_description,
      long_description_content_type='text/x-rst',
      author='Robert Nowotny',
      author_email='rnowotny1966@gmail.com',
      classifiers=CLASSIFIERS,
      entry_points=entry_points,
      # minimally needs to run tests - no project requirements here
      tests_require=['typing',
                     'pathlib',
                     'mypy ; platform_python_implementation != "PyPy" and python_version >= "3.5"',
                     'pytest',
                     'pytest-pep8 ; python_version < "3.5"',
                     'pytest-codestyle ; python_version >= "3.5"',
                     'pytest-mypy ; platform_python_implementation != "PyPy" and python_version >= "3.5"'
                     ],

      # specify what a project minimally needs to run correctly
      install_requires=['typing'] + required,
      # minimally needs to run the setup script, dependencies needs also to put here for setup.py install test
      setup_requires=['typing',
                      'pathlib',
                      'pytest-runner'] + required
      )
