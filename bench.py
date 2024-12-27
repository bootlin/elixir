#!/usr/bin/env python3

import datetime
import elixir.lib as lib
from elixir.lib import script, scriptLines
import elixir.data as data
from elixir.data import PathList
from find_compatible_dts import FindCompatibleDTS
import elixir.web
import threading
import jinja2
from dataclasses import dataclass

@dataclass
class Config:
    project_dir: str
    version_string: str
    repo_link: str

@dataclass
class Context:
    config: Config
    versions_cache_lock: threading.Lock
    versions_cache: dict
    jinja_env: jinja2.Environment
    dts_comp_cache: dict

@dataclass
class Request:
    context: Context

    is_raw: bool

    def get_param(self, key):
        if key == 'raw':
            return '1' if self.is_raw else '0'
        else:
            raise NotImplementedError

@dataclass
class Response:
    status: int
    location: str
    content_type: str
    text: str
    downloadable_as: str
    cache_control: tuple
    headers: dict


# /linux/v4.5-rc5/source/drivers/scsi/lpfc/lpfc_sli.c
# /linux/v5.11.20/source/drivers/net/ethernet/hisilicon/hns/hnae.c
# /linux/v3.5-rc3/source/mm/percpu-vm.c

config = Config(project_dir='/home/tleb/prog/public/elixir-data',
                version_string='v1.0-fake-version',
                repo_link='https://github.com/bootlin/elixir/')

ctx = Context(config=config,
              versions_cache_lock=threading.Lock(),
              versions_cache={},
              jinja_env=elixir.web.get_jinja_env(),
              dts_comp_cache={"linux": True})

req = Request(context=ctx, is_raw=False)

project = 'linux'
version = 'v3.5-rc3'

path = 'mm/percpu-vm.c'
resp = Response(0, '', '', '', '', ('',), {})

for _ in range(100):
    x = elixir.web.SourceResource()
    x.on_get(req, resp, project, version, path)
