from typing import Optional
from typing import Tuple
from typing import List

from pathlib import Path
from argparse import ArgumentParser

import requests
import lxml.html

Error = str


BASE_URL = "https://code.visualstudio.com/updates/v1_{version}".format


def get_html(url: str) -> Tuple[Optional[str], Optional[Error]]:
    try:
        res = requests.get(url)
        if res.status_code == 200:
            return res.text, None
        elif res.status_code == 404:
            return None, None
        else:
            return None, f"got status: {res.status_code}"
    except requests.exceptions.BaseHTTPError as e:
        return None, str(e)


def get_h1(html: lxml.html.HtmlElement) -> Optional[str]:
    r = html.xpath('//h1/text()')
    if not r:
        return None
    return r[0]


def exec_xpath(html: lxml.html.HtmlElement, exp: str) -> Optional[list]:
    r = html.xpath(exp)
    if not r:
        return None
    return r


def get_dist_urls(html: lxml.html.HtmlElement) -> Optional[List[str]]:
    # try to find new url syntax
    urls = exec_xpath(html, '//p/a[contains(., "tarball")]')
    if not urls:
        # try to find old url syntax
        urls = exec_xpath(html, '//p/a[contains(., "tar.")]')

    return [u.get('href') for u in urls] or None


def download_version(version: int):
    url = BASE_URL(version=version)
    
    print(f'process: {url}')
    text, err = get_html(url)
    if err is not None:
        raise Exception(err)
    if text is None:
        print(f"version 1.{version} doesn't exist.")
        return
    
    html = lxml.html.fromstring(text)
    h1 = get_h1(html)

    dist_urls = get_dist_urls(html)
    assert dist_urls, "url: {%s}, distro links not found" % url
    dist_url = linux_x64_urls[0] if (linux_x64_urls := [i for i in dist_urls if 'linux-x64/stable' in i]) else None
    assert dist_url, "url: {%s}, main linux-x64 distro link not found" % url

    base_folder = Path('.arch')
    base_folder.mkdir(exist_ok=True)
    version_file_name = f'v1_{version}.tar.gz'

    res = requests.get(dist_url, stream=True) 
    with open(base_folder / version_file_name, 'wb') as f:
        for chunk in res.iter_content(chunk_size=1024): 
            if chunk:
                f.write(chunk)

    with open(base_folder / 'versions.csv', 'a') as f:
        f.write(f'{url}|{h1}\n')


def main():
    parser = ArgumentParser()
    parser.add_argument(
        '-f',
        '--from',
        type=int,
        dest='from_',
        help='version from e.g. 45',
        required=True,
    )
    parser.add_argument(
        '-t',
        '--to',
        type=int,
        help='version to e.g. 47',
        required=True,
    )
    params = parser.parse_args()

    version = params.from_
    while version <= params.to:
        download_version(version)
        version += 1


if __name__ == '__main__':    
    main()
