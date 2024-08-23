import time
import logging
import sys
import random
from bs4 import BeautifulSoup
import requests

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print(f"usage: {sys.argv[0]} url project version")
        exit(1)

    base_url = sys.argv[1]
    project = sys.argv[2]
    version = sys.argv[3]

    first_url = f"{base_url}/{project}/{version}/source"
    urls_set = set([first_url])
    urls_list = [first_url]

    while True:
        url_index = random.randint(0, len(urls_list)-1)
        url = urls_list.pop(url_index)

        try:
            req = requests.get(url, timeout=30)
        except Exception as e:
            logging.exception("request failed!")
            time.sleep(1)
            continue

        if req.status_code != 200:
            print("===== ERROR", url, req.status_code)

        phtml = BeautifulSoup(req.text, 'html.parser')

        tree = phtml.find(class_='lxrtree')
        if tree is not None:
            links = phtml.find_all('a', class_='tree-icon')

            for link in links:
                link_url = f"{base_url}{link['href']}"
                if link_url not in urls_set:
                    urls_set.add(link_url)
                    urls_list.append(link_url)

            urls_set.remove(url)

        duration = req.elapsed.total_seconds()
        print(url, req.status_code, duration, '' if duration < 1 else 'LONG')


