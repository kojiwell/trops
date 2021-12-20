import os
from setuptools import setup

def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

setup(
    name = "Trops",
    version = "0.0.1",
    author = "Koji Tanaka",
    author_email = "kojiwelly@gmail.com",
    description = ("Track operations"),
    license = "MIT",
    keywords = "linux system administration",
    url = "http://github.com/kojiwell/trops",
    packages=['trops'],
    long_description=read('README.md'),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Topic :: Utilities",
        "License :: MIT License",
    ],
    entry_points={
        'console_scripts': ['trops=trops.trops:main',
                             'trgit=trops.trops:trgit',
                             'trlog=trops.trlog:main',
                             'tredit=trops.tredit:tredit'],
    },

)
