from setuptools import setup, find_packages
import sys, os

version = "0.1"

setup(
    name="alain",
    version=version,
    description="Alain",
    long_description="""\
AFPy's IRC bot""",
    classifiers=[],  # Get strings from http://pypi.python.org/pypi?%3Aaction=list_classifiers
    keywords="irc afpy",
    author="Gael Pasgrimaud",
    author_email="gawel@afpy.org",
    url="https://hg.afpy.org/gawel/alain/index.html",
    license="MIT",
    packages=find_packages("src/"),
    package_dir={"": "src/"},
    include_package_data=True,
    zip_safe=False,
    install_requires=["irc3", "chut", "feedparser", "requests", "twitter", "aiocron"],
    extras_require={
        "dev": [
            "flake8",
            "pylint==2.0.0.dev",  # Don't work on py37 without v2
            "astroid==2.0.0.dev",  # Don't work on py37 without v2
            "pytest",
            "pytest-cov",
            "detox",
            "bandit",
            "black",
            "mypy",
        ]
    },
)
