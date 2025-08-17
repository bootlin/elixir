import random
from locust import HttpUser, between, task
from bs4 import BeautifulSoup

# To run: python3 -m locust -f utils/crawl-locust.py
# Dynamically querying projects and versions is not implemented, remember to replace
# data in `projects` key with a subset of data from the tested instance.

class ElixirUser(HttpUser):
    wait_time = between(1, 10)
    projects = (
        ("linux", (
            "v6.9.4",
            "v6.8",
            "v6.2",
            "v5.14.15",
            "v5.9",
            "v5.4",
            "v4.17",
            "v4.10.11",
            "v4.6",
            "v3.15",
            "v3.5.6",
            "v3.1"
        )),
        ("musl",(
            "v1.2.5" ,
        )),
        ("zephyr",(
            "v3.7.0",
            "v3.4.0",
            "v3.0.0",
            "v2.7.0",
            "v2.5.0",
            "v2.3.0",
            "v1.12.0",
            "v1.5.0",
        )),
    )

    def on_start(self):
        self.wait()
        self.index_page()

    def parse_tree(self, phtml):
        links = phtml.find_all('a', class_='tree-icon')

        for link in links:
            link_url = f"{self.host}{link['href']}"
            self.urls.append(link_url)

    def parse_html(self, r):
        phtml = BeautifulSoup(r.content, 'html.parser')
        tree = phtml.find(class_='lxrtree')
        if tree is not None:
            self.parse_tree(phtml)
        else:
            idents = phtml.find_all(class_='ident')
            for i in idents:
                self.urls.append(f"{self.host}{i['href']}")

    @task(1)
    def index_page(self):
        project, versions = random.choice(self.projects)
        version = random.choice(versions)
        r = self.client.get(f"{project}/{version}/source")
        self.urls = []
        self.parse_html(r)

    @task(100)
    def load_random_source_page(self):
        url = random.choice(self.urls)
        r = self.client.get(url)
        self.parse_html(r)

