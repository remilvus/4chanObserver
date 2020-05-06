#!/usr/bin/env python3
import urllib3
import asyncio
import aiohttp
from aiohttp.client_exceptions import ServerDisconnectedError, ClientOSError
import json
import os
import re
from tqdm import tqdm
from observer import log


async def download_post(board, post, output_dir, http, pbar, max_tires=10):
    try_num = 0
    done = False
    while try_num < max_tires and not done:
        try:
            url = 'http://i.4cdn.org/%s/%s%s' % (board, post['tim'], post['ext'])
            async with http.get(url) as r:
                with open('%s/%s%s' % (output_dir, post['tim'], post['ext']), 'wb') as f:
                    data = await r.content.read()
                    f.write(data)
                    pbar.update(1)
                await r.release()
                done = True
        except (TimeoutError, ServerDisconnectedError, ClientOSError, asyncio.TimeoutError) as e:
            try_num += 1
            if try_num < max_tires:
                log("error_log.txt", f"{repr(e)} #{try_num} Retrying to download image...")
            else:
                log("error_log.txt", f"{repr(e)} #{try_num} Download abandoned...")
                print("One download abandoned...\n")



def create_output_dir(output_dir):
    if not os.path.isdir(output_dir):
        os.makedirs(output_dir)


def get_posts(url, board, thrd):
    http = urllib3.PoolManager(num_pools=1)

    r = http.request(
        'GET',
        'http://a.4cdn.org/' + board + '/thread/' + thrd + '.json'
    )    
    posts_list = json.loads(r.data)['posts']
    return [p for p in posts_list if 'tim' in p and 'ext' in p]


async def download_posts(url, output_dir, loop):
    board = re.findall(r'\.org?/.*?/', url)[0][5:-1]
    thrd = re.findall(r'/thread/[0-9]*/', url)[0][8:-1]
    posts = get_posts(url, board, thrd)   
    pbar = tqdm(total=len(posts), position=0)
    async with aiohttp.ClientSession(loop=loop) as http:
        tasks = [download_post(board, post, output_dir, http, pbar) for post in posts]
        await asyncio.gather(*tasks)


def thread_name(url):
    s = url.split('/')
    if len(s) > 1:
        return s[-1]
    else:
        raise ValueError('invalid url')


def main(url, main_dir):
    output_dir = os.path.join(main_dir, thread_name(url))
    create_output_dir(output_dir)
    loop = asyncio.get_event_loop()
    loop.run_until_complete(download_posts(url, output_dir, loop))

def run(url, main_dir):
    main(url, main_dir)
