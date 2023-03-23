#!/usr/bin/env python

import os
from argparse import ArgumentParser
from heapq import heappush, heappop, heappushpop

from filetype import is_image
from PIL import Image
from scipy.fft import dct
import numpy as np


def ahash(imgpath: str) -> int:
    '''平均哈希算法'''
    # 将图片转换为 8x8 大小的灰度图片
    gray_img = Image.open(imgpath).resize((8, 8), Image.NEAREST).convert("L")
    # 计算平均值
    img_data = gray_img.getdata()
    avg = sum(img_data) / 64

    _hash = 0
    for value in img_data:
        bit = 0 if value < avg else 1
        _hash = _hash << 1 | bit
    return _hash


def dhash(imgpath: str) -> int:
    '''差异哈希算法'''
    # 将图片转换为 9x8 大小的灰度图片
    gray_img = Image.open(imgpath).resize((9, 8), Image.NEAREST).convert("L")
    # 逐行比较相邻两值的大小
    _hash = 0
    img_data = gray_img.getdata()
    for idx in range(64):
        i = idx + idx // 8
        _hash = (_hash << 1) | (img_data[i] < img_data[i + 1])
    return _hash


def phash(imgpath: str) -> int:
    image = Image.open(imgpath).resize((32, 32), Image.NEAREST).convert('L')
    pixels = np.asarray(image)
    dct_data = dct(dct(pixels, axis=0), axis=1)
    dctlowfreq = dct_data[:8, :8]  # type: ignore
    med = np.median(dctlowfreq)
    diff = dctlowfreq < med
    _hash = 0
    for v in diff.flat:
        bit = 0 if v else 1
        _hash = _hash << 1 | bit
    return _hash


def hamming_distance(h1, h2):
    v = (h1 ^ h2)
    v -= (v >> 1) & 0x5555555555555555
    v = (v & 0x3333333333333333) + ((v >> 2) & 0x3333333333333333)
    v = (v + (v >> 4)) & 0x0f0f0f0f0f0f0f0f
    v += v >> 8
    v += v >> 16
    v += v >> 32
    return v & 0xff


def find_images(gallery):
    for item in gallery:
        if os.path.isdir(item):
            for root, _, files in os.walk(item):
                for f in files:
                    if f.startswith('.'):
                        continue
                    p = os.path.join(root, f)
                    if os.path.isfile(p) and is_image(p):
                        yield p
        elif is_image(item):
            yield item
        else:
            continue


def search(baseimg: str, gallery, hash_func):
    heapq: list[tuple] = []
    heap_height = 3
    s_hash = hash_func(baseimg)
    for num, ipath in enumerate(find_images(gallery), start=1):
        print(f'checking {num}: {ipath}', end='')
        i_hash = hash_func(ipath)
        hm = hamming_distance(s_hash, i_hash)
        print(f' ({hm})    ', end='\r')

        if hm > 10:
            continue
        elif hm == 0:
            heapq = [(hm, ipath)]
            break
        elif len(heapq) < heap_height:
            heappush(heapq, (-hm, ipath))
        else:
            heappushpop(heapq, (-hm, ipath))

    res = [heappop(heapq) for _ in range(len(heapq))]

    if len(res) == 0:
        print('\n\nnot found any image that similar to xxx.')
    else:
        print(f'\n\nImages similar to {baseimg}:')
        for i, (hm, ipath) in enumerate(res[::-1], start=1):
            print(f'{i}. {ipath} ({(64+hm) / 64 * 100:.1f}%)')


if __name__ == '__main__':
    parser = ArgumentParser('isearch')
    parser.add_argument('-a', dest='algorithm', default='dhash',
                        choices=['ahash', 'dhash', 'phash'],
                        help='the image similarity recognition algorithm (default=%(default)s)')

    parser.add_argument('baseimg', type=str, help='the image to search')
    parser.add_argument('gallery', nargs='+', help='the gallery for searching sources')
    args = parser.parse_args()

    hash_func = {'ahash': ahash, 'dhash': dhash, 'phash': phash}[args.algorithm]

    if os.path.isfile(args.baseimg) and is_image(args.baseimg):
        search(args.baseimg, args.gallery, hash_func)
    else:
        print(f'{args.baseimg} is not a image')
        exit(1)
