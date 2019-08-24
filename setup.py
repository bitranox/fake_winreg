"""Setuptools entry point."""
import codecs
import os
import subprocess
import sys


def install_requirements_when_using_setup_py():
    proc = subprocess.Popen([sys.executable, "-m", "pip", "install", '-r', './requirements_setup.txt'],
                            stdin=subprocess.PIPE,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE)
    stdout, stderr = proc.communicate()
    encoding = sys.getdefaultencoding()
    print(stdout.decode(encoding))
    print(stderr.decode(encoding))

    if proc.returncode != 0:
        raise RuntimeError('Error installing requirements_setup.txt')


try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup


CLASSIFIERS = [
    'Development Status :: 5 - Production/Stable',
    'Intended Audience :: Developers',
    'License :: OSI Approved :: MIT License',
    'Natural Language :: English',
    'Operating System :: OS Independent',
    'Programming Language :: Python',
    'Topic :: Software Development :: Libraries :: Python Modules'
]

description = 'Windows Registry related'

dirname = os.path.dirname(__file__)
readme_filename = os.path.join(dirname, 'README.rst')

long_description = description
if os.path.exists(readme_filename):
    try:
        readme_content = codecs.open(readme_filename, encoding='utf-8').read()
        long_description = readme_content
    except Exception:
        pass

install_requirements_when_using_setup_py()

setup(name='lib_registry',
      version='1.0.3',
      description=description,
      long_description=long_description,
      long_description_content_type='text/x-rst',
      author='Robert Nowotny',
      author_email='rnowotny1966@gmail.com',
      url='https://github.com/bitranox/lib_registry',
      packages=['lib_registry'],
      classifiers=CLASSIFIERS,
      install_requires=['typing'],        # we need typing for python 2.7
      setup_requires=['typing', 'pytest-runner'],
      tests_require=['typing', 'pytest']  # we need typing for python 2.7
      )
