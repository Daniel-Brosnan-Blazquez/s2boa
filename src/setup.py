"""
Setup configuration for the vboa application

Written by DEIMOS Space S.L. (dibb)

module vboa
"""
from setuptools import setup, find_packages

setup(name="s2boa",
      version="0.1.0",
      description="S2 engine and visualization tool for Business Operation Analysis",
      url="https://bitbucket.org/dbrosnan/s2boa/",
      author="Daniel Brosnan",
      author_email="daniel.brosnan@deimos-space.com",
      packages=["s2vboa"],
      python_requires='>=3',
      install_requires=[
          "Flask",
          "Flask-DebugToolbar"
      ],
      tests_require=[
          "nose",
          "before_after",
          "coverage",
          "termcolor"
      ],
      test_suite='nose.collector')
