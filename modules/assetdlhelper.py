import os
import requests
from urllib.parse import urljoin

from requests.adapters import HTTPAdapter

import botconfig
from modules.config import proxies

__UNIPJSK__VIEWER_BASEURL__ = 'https://assets.unipjsk.com/'
__BOT_ASSET_CACHE_PATH__ = botconfig.ASSET_CACHE_PATH

# 从unipjsk下载asset，若本地有cache则直接返回
def load_asset_from_unipjsk(asset_path: str) -> str:
    if os.path.exists(os.path.join(__BOT_ASSET_CACHE_PATH__, asset_path)):
        return os.path.join(__BOT_ASSET_CACHE_PATH__, asset_path)
    asset_url = urljoin(__UNIPJSK__VIEWER_BASEURL__, asset_path)
    session = requests.Session()
    session.mount(asset_url, HTTPAdapter(max_retries=10))
    resp = session.get(asset_url, proxies=proxies)
    if resp.status_code != 200:
        raise RuntimeError(f"Failed to load asset from {asset_url}")
    dir_splits = asset_path.split(os.path.sep)
    father_dirs = dir_splits[:-1]
    if not os.path.exists(os.path.join(__BOT_ASSET_CACHE_PATH__, *father_dirs)):
        try:
            os.makedirs(os.path.join(__BOT_ASSET_CACHE_PATH__, *father_dirs))
        except Exception as e:
            print(e)
            raise RuntimeError(f"创建asset cache目录失败。")
    try:
        with open(os.path.join(__BOT_ASSET_CACHE_PATH__, asset_path), 'wb') as f:
            f.write(resp.content)
            return os.path.join(__BOT_ASSET_CACHE_PATH__, asset_path)
    except Exception:
        raise RuntimeError("保存asset cache失败")
