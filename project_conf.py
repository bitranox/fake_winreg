# single point for all configuration of the project

# stdlib
from setuptools import find_packages  # type: ignore
from typing import List, Dict

package_name = 'lib_registry'  # type: str
version = '0.1.0'
# codeclimate_link_hash - get it under https://codeclimate.com/github/<user>/<project>/badges
codeclimate_link_hash = 'affaa3b099c55c69950c'  # for lib_registry

# cc_test_reporter_id - get it under https://codeclimate.com/github/<user>/<project> and press "test coverage"
cc_test_reporter_id = 'tba'    # for lib_registry

# pypi_password
# to create the secret :
# cd /<repository>
# travis encrypt -r bitranox/lib_parameter pypi_password=*****
# copy and paste the encrypted password here
# replace with:
# travis_pypi_secure_code = '<code>'     # pypi secure password, without '"'
travis_pypi_secure_code = 'F6REHdAOCTEicl8s9aiTNNJ5S6xLAoOyLF7qL3m1LkV5c46+FNyiOg8XsUOO1DocO6oT9nhsKnjp8KkSZa2gO83IRGsfwt+2TfzPm+ISiwpfb7Vqznlt91R0hqN'\
                          'jXUe96Sno4CZSVnCg/wNyaHmI8qP16axojgYIsWy1Nh5UXQOYMN4L+dkBbzGTmh8HR/imhmLMbSZXnRZ2TcY9UftIBLMCqkqOOit8q+C8K5cFbonqxSvLaVX+Dt'\
                          'aU2Llbro4MgJB6rIT5bqIFoSEWFi8X8cJDiRSsi9ugsblhB5BTjE/CBLQKStao2kpJ3FvNnrFozO/b7rZLbHyysv8+JAuk3t8zTz1CJyN2Md+takZr7mvMKkECi'\
                          'BgRCP4HDjDCwhsIkgiHr58e9LYJif4cI7Ph9eYuMdcZFVG5H7oIsde5XJBde+MKRGPfe9c/4j8tpduwpSrUq1VI3E/DbMT+yBuW76yIEP6fn39jqZwskLm1Zu4A'\
                          'QKNfXqXJ8FYCUlfrbso6cp+kjX8Qop1LKLC7wWD8Q6SaSV/iXAXKN2MC7L3rkvtMQKydG++LWpH+wiAyynhyKghF638VjGDVXw6Wbx07iiO2hgcv87tlXUTnRvu'\
                          'APznPoMkwFIkGBkloyzQr5/2dWu99vHKA8O3L6iIj8cDPuiyFEguOnotiOXjO003xLjY='

# include package data files
# package_data = {package_name: ['some_file_to_include.txt']}
package_data = dict()       # type: Dict[str, List[str]]

author = 'Robert Nowotny'
author_email = 'rnowotny1966@gmail.com'
github_account = 'bitranox'

linux_tests = False
osx_tests = False
pypy_tests = False
windows_tests = True
wine_tests = False
badges_with_jupiter = False

# a short description of the Package - especially if You deploy on PyPi !
description = 'some convenience functions to access the windows registry - to be extended'

# #############################################################################################################################################################
# DEFAULT SETTINGS - no need to change usually, but can be adopted
# #############################################################################################################################################################

shell_command = package_name
src_dir = package_name
module_name = package_name
init_config_title = description
init_config_name = package_name

# we ned to have a function main_commandline in module module_name - see examples
entry_points = {'console_scripts': ['{shell_command} = {src_dir}.{module_name}:main_commandline'
                .format(shell_command=shell_command, src_dir=src_dir, module_name=module_name)]}  # type: Dict[str, List[str]]

long_description = package_name  # will be overwritten with the content of README.rst if exists

packages = [package_name]

url = 'https://github.com/{github_account}/{package_name}'.format(github_account=github_account, package_name=package_name)
github_master = 'git+https://github.com/{github_account}/{package_name}.git'.format(github_account=github_account, package_name=package_name)
travis_repo_slug = github_account + '/' + package_name

CLASSIFIERS = ['Development Status :: 5 - Production/Stable',
               'Intended Audience :: Developers',
               'License :: OSI Approved :: MIT License',
               'Natural Language :: English',
               'Operating System :: OS Independent',
               'Programming Language :: Python',
               'Topic :: Software Development :: Libraries :: Python Modules']
