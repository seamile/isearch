#!/usr/bin/env python

import os
import sys
from PIL import Image
from filetype import is_image
from heapq import heappush, heappop, heappushpop


def avhash(imgpath: str):
    img = Image.open(imgpath)
    gray_img = img.resize((8, 8), Image.LANCZOS).convert("L")
    img_data = gray_img.getdata()
    avg = sum(img_data) / 64
    bits = [1 if d >= avg else 0 for d in img_data]

    s = 0
    for i, b in enumerate(bits):
        s += b << i

    return s


def hamming(h1, h2):
    h, d = 0, h1 ^ h2
    while d:
        h += 1
        d &= d - 1
    return h


def find_images(dirpath):
    for root, _, files in os.walk(dirpath):
        for f in files:
            if f.startswith('.'):
                continue
            p = os.path.join(root, f)
            if os.path.isfile(p) and is_image(p):
                yield p


def search(source: str, dirpath: str):
    heapq: list[tuple] = []
    heap_height = 3
    s_hash = avhash(source)
    for i, ipath in enumerate(find_images(dirpath), start=1):
        print(f'checking {i}: {ipath}', end='')
        i_hash = avhash(ipath)
        hm = -hamming(s_hash, i_hash)
        print(f' ({-hm})    ', end='\r')

        if hm == 0:
            res = [ipath]
            break
        elif len(heapq) < heap_height:
            heappush(heapq, (hm, ipath))
        else:
            heappushpop(heapq, (hm, ipath))

        if hm > -10:
            print(f'found a very similar image: {ipath} ({-hm})')

    else:
        res = [heappop(heapq)[1] for _ in range(heap_height)]

    print(f'\n\nImages similar to {source}:')
    for i, ipath in enumerate(res[::-1], start=1):
        print(f'{i}. {ipath}')


if __name__ == '__main__':
    source, dirpath = sys.argv[1], sys.argv[2]
    if is_image(source) and os.path.isdir(dirpath):
        search(source, dirpath)
