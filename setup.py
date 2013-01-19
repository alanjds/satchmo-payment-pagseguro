import setuptools
from setuptools import find_packages
from distutils.core import setup

import os

# Utility function to read the README file.
def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

import re

def parse_requirements(file_name):
    requirements = []
    for line in open(file_name, 'r').read().split('\n'):
        if re.match(r'(\s*#)|(\s*$)', line):
            continue
        if re.match(r'\s*-e\s+', line):
            requirements.append(re.sub(r'\s*-e\s+.*#egg=(.*)$', r'\1', line))
        elif re.match(r'\s*-f\s+', line):
            pass
        else:
            requirements.append(line)

    return requirements

def parse_dependency_links(file_name):
    dependency_links = []
    for line in open(file_name, 'r').read().split('\n'):
        if re.match(r'\s*-[ef]\s+', line):
            dependency_links.append(re.sub(r'\s*-[ef]\s+', '', line))

    return dependency_links

print parse_requirements('requirements.txt')
print parse_dependency_links('requirements.txt')

template_patterns = [
    'pagseguro/templates/shop/checkout/pagseguro/*.html'
]

packages = find_packages(exclude=["tests"]) #['satchmo_pagseguro']

setup(
    name = "satchmo-payment-pagseguro",
    version = "0.1-dev",
    packages = packages,
    package_data=dict( [(package_name, template_patterns) for package_name in packages] ),
    test_suite='tests.suite',
    zip_safe = False,
    author = "Alan Justino da Silva",
    author_email = "alan.justino[at]yahoo.com.br",
    description = """Satchmo's custom payment module for PagSeguro platform. 
    Unofficial fork of code from https://bitbucket.org/williambr/satchmo/src/e250ab0977f1/satchmo/apps/payment/modules/pagseguro?at=lojalivre
    """,
    long_description = read('README'),    
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: Web Environment",
        "Programming Language :: Python :: 2 :: Only",
        "Framework :: Django",
        "Intended Audience :: Developers",
    ],
    url = "https://github.com/alanjds/satchmo-payment-pagseguro",
    download_url = "https://github.com/alanjds/satchmo-payment-pagseguro/archive/master.zip",
    install_requires = parse_requirements('requirements.txt'),
    #tests_require = parse_requirements('tests_requirements.txt'),
    dependency_links = parse_dependency_links('requirements.txt'), # + parse_dependency_links('test_requirements.txt'),
)
