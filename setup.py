"""Build and installation script for FlashKit."""

# standard libraries
import re
from setuptools import setup, find_packages

# get long description from README.rst
with open('README.rst', mode='r') as readme:
    long_description = readme.read()

# get package metadata by parsing __meta__ module
with open('flashkit/__meta__.py', mode='r') as source:
    content = source.read().strip()
    metadata = {key: re.search(key + r'\s*=\s*[\'"]([^\'"]*)[\'"]', content).group(1)
                for key in ['__pkgname__', '__version__', '__authors__', '__contact__',
                            '__license__', '__website__', '__description__']}

# core dependancies
DEPENDANCIES = ['cmdkit>=2.1.2', 'toml>=0.10.2', 'alive_progress>=1.6.2',
                'h5py>=3.1.0']

setup(
    name                 = metadata['__pkgname__'],
    version              = metadata['__version__'],
    author               = metadata['__authors__'],
    author_email         = metadata['__contact__'],
    description          = metadata['__description__'],
    license              = metadata['__license__'],
    keywords             = 'flash code skd and cli',
    url                  = metadata['__website__'],
    packages             = find_packages(),
    include_package_data = True,
    long_description     = long_description,
    classifiers          = ['Development Status :: 2 - Pre-Alpha',
                            'Topic :: Utilities',
                            'Programming Language :: Python :: 3',
                            'Programming Language :: Python :: 3.7',
                            'Programming Language :: Python :: 3.8',
                            'Programming Language :: Python :: 3.9',
                            'License :: OSI Approved :: MIT License', ],
    entry_points         = {'console_scripts': ['flashkit=flashkit.cli:main', ]},
    install_requires     = DEPENDANCIES,
)
