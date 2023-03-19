#!/usr/bin/env python

import os
import sys
from PIL import Image
# from scipy.fft import dct, idct
from filetype import is_image
from heapq import heappush, heappop, heappushpop


def ahash(imgpath: str) -> int:
    '''平均哈希'''
    # 将图片转换为 8x8 大小的灰度图片
    gray_img = Image.open(imgpath).resize((8, 8), Image.NEAREST).convert("L")
    # 计算平均值
    img_data = gray_img.getdata()
    avg = sum(img_data) / 64

    _hash = 0
    for offset, value in enumerate(img_data):
        bit = 0 if value < avg else 1
        _hash |= bit << offset

    return _hash


def dhash(imgpath: str) -> int:
    # 将图片转换为 8x8 大小的灰度图片
    gray_img = Image.open(imgpath).resize((9, 8), Image.NEAREST).convert("L")
    # 逐行比较相邻两值的大小
    _hash = 0
    img_data = gray_img.getdata()
    for idx in range(64):
        i = idx + idx // 8
        _hash |= (img_data[i] >= img_data[i + 1]) << i
    return _hash


def phash(imgpath: str) -> int:
    return 0


def hamming_distance(h1, h2):
    v = (h1 ^ h2)
    v -= (v >> 1) & 0x5555555555555555
    v = (v & 0x3333333333333333) + ((v >> 2) & 0x3333333333333333)
    v = (v + (v >> 4)) & 0x0f0f0f0f0f0f0f0f
    v += v >> 8
    v += v >> 16
    v += v >> 32
    return v & 0xff


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
    s_hash = ahash(source)
    for num, ipath in enumerate(find_images(dirpath), start=1):
        print(f'checking {num}: {ipath}', end='')
        i_hash = ahash(ipath)
        hm = hamming_distance(s_hash, i_hash)
        print(f' ({hm})    ', end='\r')

        if hm == 0:
            res = [ipath]
            break
        elif len(heapq) < heap_height:
            heappush(heapq, (-hm, ipath))
        else:
            heappushpop(heapq, (-hm, ipath))

    height = min(num, heap_height)  # type: ignore
    res = [heappop(heapq)[1] for _ in range(height)]

    print(f'\n\nImages similar to {source}:')
    for i, ipath in enumerate(res[::-1], start=1):
        print(f'{i}. {ipath}')


if __name__ == '__main__':
    source, dirpath = sys.argv[1], sys.argv[2]
    if is_image(source) and os.path.isdir(dirpath):
        search(source, dirpath)
