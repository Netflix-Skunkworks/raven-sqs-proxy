"""
Raven SQS Proxy
===================

A simple SQS poller for proxying Sentry messages in SQS to Sentry
"""
import sys
import os.path

from setuptools import setup, find_packages

ROOT = os.path.realpath(os.path.join(os.path.dirname(__file__)))
sys.path.insert(0, ROOT)

about = {}
with open(os.path.join(ROOT, "raven_sqs_proxy", "__about__.py")) as f:
    exec(f.read(), about)


install_requires = [
    'boto3',
    'requests',
    'click',
    'click_log',
    'retrying'
]

tests_require = [
    'pytest',
    'moto'
]

setup(
    name=about["__title__"],
    version=about["__version__"],
    author=about["__author__"],
    author_email=about["__email__"],
    url=about["__uri__"],
    description=about["__summary__"],
    long_description='See README.md',
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    install_requires=install_requires,
    extras_require={
        'tests': tests_require
    },
    keywords=['aws', 'sentry', 'raven', 'sqs', 'proxy'],
    entry_points={
        "console_scripts": [
            "sqsproxy = raven_sqs_proxy.sqsproxy:cli"
        ]
    },
    classifiers=[
        "Programming Language :: Python",
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
    ],
    license="Apache 2.0",
    maintainer="Mike Grima <GH: mikegrima>"
)
