import time
from urllib.parse import urlparse, urljoin


def get_now():
    return time.strftime('%Y-%m-%d %H:%M:%S')


def extract_internal_links(soup, url):
    domain = urlparse(url).netloc
    internal_links = set()
    for link in soup.find_all('a', href=True):
        href = link['href']
        if href.startswith('/'):
            internal_links.add(urljoin(url, href))
        elif domain in urlparse(href).netloc:
            internal_links.add(href)
    return list(internal_links)


# TODO: filter ids mailto:
def extract_external_links(soup, url):
    domain = urlparse(url).netloc
    external_links = set()
    for link in soup.find_all('a', href=True):
        href = link['href']
        if not href.startswith('/') and not href.startswith('#') and domain not in urlparse(href).netloc:
            external_links.add(href)
    return list(external_links)
