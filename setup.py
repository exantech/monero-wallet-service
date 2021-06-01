# Always prefer setuptools over distutils
from setuptools import setup, find_packages
# To use a consistent encoding
from codecs import open
from os import path

here = path.abspath(path.dirname(__file__))

setup(
    name='monero-wallet-service',

    # Versions should comply with PEP440.  For a discussion on single-sourcing
    # the version across setup.py and the project code, see
    # https://packaging.python.org/en/latest/single_source_version.html
    version='0.0.1',
    zip_safe=False,

    description='Monero Wallet Service backend',
    #    long_description=long_description,

    # Author details
    author='Denis Voskvitsov',
    author_email='dv@exante.eu',

    # Choose your license
    license='EULA',

    # You can just specify the packages manually here if your project is
    # simple. Or you can use find_packages().
    packages=find_packages(exclude=['contrib', 'docs', 'tests']),

    package_index='http://ci2-pypi.ghcg.com/simple/',
    # List run-time dependencies here.  These will be installed by pip when
    # your project is installed. For an analysis of "install_requires" vs pip's
    # requirements files see:
    # https://packaging.python.org/en/latest/requirements.html
    install_requires=[
        'aiohttp==3.0.9',
        'aiohttp-swagger==1.0.5',
        'aioredis==1.1.0',
        'async-timeout==2.0.1',
        'attrs==17.4.0',
        'boto3==1.9.90',
        'chardet==3.0.4',
        'hiredis==0.2.0',
        'idna==2.6',
        'idna-ssl==1.0.1',
        'Jinja2==2.10',
        'MarkupSafe==1.0',
        'multidict==4.1.0',
        'PyYAML==3.12',
        'yarl==1.1.1',
        'peewee==2.10.2',
        'peewee-async==0.5.12',
        'peewee-db-evolve==0.6.8',
        'psycopg2==2.7.4',
        'psycopg2-binary==2.7.4',
        'aiopg==0.13.2',
        'python-slugify==1.2.5',
        'urllib3==1.26.5',
        'ujson==1.35',
        'Flask==0.12.2',
        'flask-peewee==3.0.0',
        'flask-swagger-ui==3.6.0',
        'uwsgi==2.0.17',
        'redis==2.10.6',
        'cryptonote==0.1',
    ],

    include_package_data=True,

    # List additional groups of dependencies here (e.g. development
    # dependencies). You can install these using the following syntax,
    # for example:
    # $ pip install -e .[dev,test]
    extras_require={
        'dev': ['check-manifest'],
        'test': ['coverage'],
    },
)
