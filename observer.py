from downloader import chan_dl as downloader
import bs4 as bs
import urllib3
import json
import os
import time
import argparse
import socket
from datetime import date
import traceback

def check_connection():
    try:
        http = urllib3.PoolManager()
        r = http.request(
            'GET',
            f"http://www.4chan.org/"
        )
    except urllib3.exceptions.MaxRetryError as e:
        print(e)
        quit()

def check_board(board):
    http = urllib3.PoolManager()
    r = http.request(
            'GET',
            f"http://boards.4channel.org/{board}/archive"
        )
    if r.status != 200:
        raise ConnectionError("Failed to load the board")

def get_links(board):
    assert type(board)==str
    assert len(board)==1
    http = urllib3.PoolManager()
    r = http.request(
            'GET',
            f"http://boards.4channel.org/{board}/archive"
        )

    soup = bs.BeautifulSoup(r.data, 'lxml')
    soup = soup.find('table',attrs={'id' : 'arc-list'})
    links = [link.get('href') for link in soup.find_all('a')]
    return links

def get_desired_keys():
    with open("keys.json") as keys_json:
        desired_keys = json.load(keys_json)

    desired_keys = {key: set(values) for key, values in desired_keys.items()}
    return desired_keys

def filter_links(links, desired_keys):
    link_keys = [set(link.split('/')[-1].lower().split('-')) for link in links]
    desired_links = []

    for link, keywords in zip(links, link_keys):
        for main_key, keys in desired_keys.items():
            if keywords & keys:
                desired_links.append({"link": link, "dir": main_key})
                break
    return desired_links

def log(filename, message):
    with  open(filename, "a+") as f:
        f.write(message + "\n")

def was_used(link):
    if not os.path.exists("log.txt"): return False
    f = open("log.txt", "r")
    for line in f:
        line=line[:-1]
        if line==link:
            return True
    return False

def observe(board):
    links = get_links(board)
    desired = get_desired_keys()
    filtered = filter_links(links, desired)
    
    for link in filtered:
        if not was_used(link["link"]):
            print(f"downloading {link['link']}")
            log("log.txt", link["link"])
            downloader.run("http://boards.4channel.org" + link["link"], link["dir"])
            print()


if __name__=="__main__":
    try:
        parser = argparse.ArgumentParser(description='Automatic board observation and image scraping')
        parser.add_argument("-b", "--board", help="letter code of the board to be observed", required=True)
        args = parser.parse_args()
        board = args.board
        check_connection()
        check_board(board)
        last_download_day = date.today().day - 1
        print(f"observing {board}...")
        while True:
            if last_download_day != date.today().day:
                try:
                    observe(board)
                    last_download_day = date.today().day
                except urllib3.exceptions.MaxRetryError:
                    pass
            print("sleeping...", end='\r')
            time.sleep(60 * 60)  # sleep for an hour
    except Exception as e:
        tb = "".join(traceback.format_exception(e.__class__, e, e.__traceback__))
        log("error_log.txt", repr(e) + "\n" + tb + "\n")
        raise e




