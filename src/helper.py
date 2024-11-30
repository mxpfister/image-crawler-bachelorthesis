from urllib.parse import urlparse, urljoin, urlunparse
import re


def extract_internal_links(soup, url):
    domain = urlparse(url).netloc
    internal_links = set()
    for link in soup.find_all('a', href=True):
        href = link['href']
        if href.startswith('#'):
            continue
        parsed_href = urlparse(href)
        cleaned_href = urlunparse(
            (parsed_href.scheme, parsed_href.netloc, parsed_href.path, parsed_href.params, '', ''))
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


def normalize_url(url):
    parsed_url = urlparse(url)
    normalized_url = urlunparse(parsed_url._replace(path=parsed_url.path.rstrip('/')))
    return normalized_url


def custom_urljoin(base, path):
    if re.search(r"/[a-z]{2}/?$", base):
        if not base.endswith('/'):
            base += '/'
        return base + path.lstrip('/')
    else:
        return urljoin(base, path)
