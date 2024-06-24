import time
from urllib.parse import urlparse, urljoin, urlunparse


def get_now():
    return time.strftime('%Y-%m-%d %H:%M:%S')


def extract_internal_links(soup, url):
    domain = urlparse(url).netloc
    internal_links = set()
    for link in soup.find_all('a', href=True):
        href = link['href']
        if href.startswith('#'):
            continue
        parsed_href = urlparse(href)
        cleaned_href = urlunparse((parsed_href.scheme, parsed_href.netloc, parsed_href.path, parsed_href.params, '', ''))
        if cleaned_href.startswith('/'):
            internal_links.add(urljoin(url, cleaned_href))
        elif domain in urlparse(cleaned_href).netloc:
            internal_links.add(cleaned_href)
    return list(internal_links)


def extract_external_links(soup, url):
    domain = urlparse(url).netloc
    external_links = set()
    for link in soup.find_all('a', href=True):
        href = link['href']
        if not href.startswith('/') and not href.startswith('#') and not href.startswith(
                'mailto') and domain not in urlparse(href).netloc:
            external_links.add(href)
    return list(external_links)
