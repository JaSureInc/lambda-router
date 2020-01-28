import codecs
import os
import re

from setuptools import find_packages, setup


INSTALL_REQUIRES = ["attrs>=19.1.0"]

EXTRAS_REQUIRE = {"docs": ["sphinx"], "tests": ["coverage", "pytest"]}


HERE = os.path.abspath(os.path.dirname(__file__))


def read(*parts):
    with codecs.open(os.path.join(HERE, *parts), "rb", "utf-8") as f:
        return f.read()


def get_version(package):
    ver_file = read(os.path.join("src", package, "__init__.py"))
    return re.search("__version__ = ['\"]([^'\"]+)['\"]", ver_file).group(1)


version = get_version("lambda_router")


setup(
    name="lambda_router",
    version=version,
    url="https://github.com/jasureinc/lambda-router",
    license="BSD 3 Clause",
    description="AWS Lambda Routing Utility",
    long_description=read("README.md"),
    author="Jason Paidoussi",
    author_email="jason@paidoussi.net",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    include_package_data=True,
    install_requires=INSTALL_REQUIRES,
    extras_require=EXTRAS_REQUIRE,
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "License :: OSI Approved :: BSD License",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
)
