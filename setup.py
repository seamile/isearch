#!/usr/bin/env python3
import setuptools
from isearch import __version__

with open("README.md", "r") as f_readme:
    long_description = f_readme.read()

setuptools.setup(
    name="similar-search",
    version=__version__,
    python_requires=">=3.6",
    author="Seamile",
    author_email="lanhuermao@gmail.com",
    description="An image search tool to find similar images on your disk.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/seamile/isearch",
    install_requires=[
        "filetype >= 1.2.0",
        "numpy >= 1.24.2",
        "Pillow >= 9.4.0",
        "scipy >= 1.10.1",
    ],
    entry_points={
        'console_scripts': ['isearch=isearch:main'],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        'Operating System :: MacOS :: MacOS X',
        'Operating System :: POSIX',
        'Topic :: Internet',
        'Topic :: Utilities',
    ],
)
