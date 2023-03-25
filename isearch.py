#!/usr/bin/env python

import os
from argparse import ArgumentParser
from functools import reduce
from heapq import heappush, heappop, heappushpop
from queue import Queue, Empty
from threading import Thread
from typing import Callable, Generator, Iterable

import numpy as np
from filetype import is_image
from PIL import Image
from scipy.fft import dct

__version__ = '0.1.1'


def ahash(imgpath: str) -> int:
    '''平均哈希算法'''
    # 将图片转换为 8x8 大小的灰度图片
    gray_img = Image.open(imgpath).resize((8, 8), Image.NEAREST).convert("L")
    # 计算平均值
    pixels = gray_img.getdata()
    avg = sum(pixels) / 64
    bits = (pix < avg for pix in pixels)

    return reduce(lambda h, b: int(h) << 1 | int(b), bits)


def dhash(imgpath: str) -> int:
    '''差异哈希算法'''
    # 将图片转换为 9x8 大小的灰度图片
    gray_img = Image.open(imgpath).resize((9, 8), Image.NEAREST).convert("L")
    pixels = np.asarray(gray_img)
    # 逐行比较相邻两值的大小
    bits = (pixels[:, :-1] < pixels[:, 1:]).astype(int).flat

    return reduce(lambda h, b: int(h) << 1 | int(b), bits)


def phash(imgpath: str) -> int:
    '''感知哈希算法'''
    gray_img = Image.open(imgpath).resize((32, 32), Image.NEAREST).convert('L')
    pixels = np.asarray(gray_img).astype(float)
    dct_low = dct(dct(pixels, axis=0), axis=1)[:8, :8]  # type: ignore
    avg = np.mean(dct_low)
    # 逐一与平均值比较大小
    bits = (dct_low < avg).astype(int).flat

    return reduce(lambda h, b: int(h) << 1 | int(b), bits)


def hamming_distance(h1: int, h2: int) -> int:
    '''汉明距离'''
    v = (h1 ^ h2)
    v -= (v >> 1) & 0x5555555555555555
    v = (v & 0x3333333333333333) + ((v >> 2) & 0x3333333333333333)
    v = (v + (v >> 4)) & 0x0f0f0f0f0f0f0f0f
    v += v >> 8
    v += v >> 16
    v += v >> 32
    return v & 0xff


def find_images(gallery: Iterable[str]) -> Generator[str, None, None]:
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


def search(baseimg: str, gallery: Iterable[str], hash_fn: Callable, level: int):
    heapq: list[tuple] = []
    heap_height = 3
    b_hash = hash_fn(baseimg)
    for num, ipath in enumerate(find_images(gallery), start=1):
        i_hash = hash_fn(ipath)
        hm = hamming_distance(b_hash, i_hash)
        msg = f'  checking {num}: {ipath} ({hm})  '
        print(msg, end='\r')

        if hm > level:
            continue
        elif hm == 0:
            heapq = [(hm, ipath)]
            break
        elif len(heapq) < heap_height:
            heappush(heapq, (-hm, ipath))
        else:
            heappushpop(heapq, (-hm, ipath))

    # 清空前面打印的内容
    print(' ' * (len(msg) + 4), end='\r')  # type: ignore

    res = [heappop(heapq) for _ in range(len(heapq))]

    if len(res) == 0:
        print(f'not found any image that similar to "{baseimg}".')
    else:
        print(f'Images similar to "{baseimg}":')
        for i, (hm, ipath) in enumerate(res[::-1], start=1):
            print(f'{i}. {ipath} ({(64+hm) / 64 * 100:.1f}%)')


class Worker(Thread):
    def __init__(self, task_q: Queue, result_q: Queue,
                 hash_fn: Callable, base_hash: int, level: int):
        super().__init__(daemon=True)
        self.task_q = task_q
        self.result_q = result_q
        self.hash_fn = hash_fn
        self.base_hash = base_hash
        self.level = level

    def run(self):
        while True:
            img_path = self.task_q.get()
            img_hash = self.hash_fn(img_path)
            hm = hamming_distance(self.base_hash, img_hash)
            print(f' > {img_path[-30:]} {(1-hm/64)*100:4.1f}%', end='      \r')
            if hm <= self.level:
                self.result_q.put((hm, img_path))
            self.task_q.task_done()


def put_img_to_queue(gallery: Iterable[str], task_q: Queue):
    for p in find_images(gallery):
        task_q.put(p)


def parallel_search(baseimg: str, gallery: Iterable[str], hash_fn: Callable, level: int):
    heapq: list[tuple] = []
    heap_height = 3
    b_hash = hash_fn(baseimg)
    task_q: Queue[str] = Queue()
    result_q: Queue[tuple[int, str]] = Queue()

    # 创建并启动工作线程
    workers = [Worker(task_q, result_q, hash_fn, b_hash, level)
               for _ in range(os.cpu_count() or 4)]
    for w in workers:
        w.start()

    finder = Thread(target=put_img_to_queue, args=(gallery, task_q))
    finder.start()

    while finder.is_alive() or task_q.unfinished_tasks or not result_q.empty():
        try:
            hm, ipath = result_q.get(timeout=0.5)
        except Empty:
            continue

        if hm == 0:
            heapq = [(hm, ipath)]
            break
        elif len(heapq) < heap_height:
            heappush(heapq, (-hm, ipath))
        else:
            heappushpop(heapq, (-hm, ipath))
    print(' ' * 50, end='\r')

    res = [heappop(heapq) for _ in range(len(heapq))]

    if len(res) == 0:
        print(f'not found any image that similar to "{baseimg}".')
    else:
        print(f'Images similar to "{baseimg}":')
        for i, (hm, ipath) in enumerate(res[::-1], start=1):
            print(f'{i}. {ipath} ({(64+hm) / 64 * 100:.1f}%)')


def main():
    parser = ArgumentParser('isearch')
    parser.add_argument('-a', dest='algorithm', default='phash',
                        choices=['ahash', 'dhash', 'phash'], metavar='ahash/dhash/phash',
                        help='image similarity recognition algorithm (default: "%(default)s")')

    parser.add_argument('-l', dest='level', type=int, default=10,
                        choices=range(1, 11), metavar='1-10',
                        help='tolerance level of the similarity algorithm (default: %(default)s)')

    parser.add_argument('-v', dest='version', action='version', version=__version__,
                        help="show isearch's version")

    parser.add_argument('baseimg', type=str, help='the image to search')
    parser.add_argument('gallery', nargs='+', help='the gallery for searching sources')
    args = parser.parse_args()

    hash_fn = {'ahash': ahash, 'dhash': dhash, 'phash': phash}[args.algorithm]

    if os.path.isfile(args.baseimg) and is_image(args.baseimg):
        parallel_search(args.baseimg, args.gallery, hash_fn, args.level)
    else:
        print(f'{args.baseimg} is not a image')
        exit(1)


if __name__ == '__main__':
    main()
