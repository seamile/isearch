# isearch

![PyPI - Downloads](https://img.shields.io/pypi/dm/similar-search?label=Install&color=green)
![PyPI](https://img.shields.io/pypi/v/similar-search?color=9cf)

An image search tool to find similar images on your disk.

## Install

`pip install similar-search`

## Usage

`isearch [-h] [-a ahash/dhash/phash] [-l 1-10] baseimg gallery...`

### Arguments

- positional arguments:
    - baseimg: the image to search
    - gallery: the gallery for searching sources

- options:
  - `-h, --help`: show this help message and exit
  - `-a ahash/dhash/phash`: image similarity recognition algorithm (default: "phash")
  - `-l 1-10`: tolerance level of the similarity algorithm (default: 10)
  - `-v`: show isearch's version
