from urllib.parse import urlparse, urljoin


class PageDataExtractor:
    def __init__(self, soup, url):
        self.soup = soup
        self.url = url

    def extract_page_data(self):
        return {
            'title': self.soup.title.string if self.soup.title else '',
            'meta_description': self.extract_meta_description(),
            # 'html_raw': self.soup.prettify(),
            'language': self.soup.html.get('lang') if self.soup.html else '',
            'word_count': self.extract_word_count(),
            'image_count': len(self.soup.find_all('img')),
            'page_structure': self.extract_page_structure(),
            'external_links': self.extract_external_links(),
            'internal_links': self.extract_internal_links()
        }
        
    def extract_meta_description(self):
        meta_description = ""
        if self.soup.find('meta', attrs={'name': 'description'}):
            meta_description = self.soup.find('meta', attrs={'name': 'description'}).get('content', '')
        return meta_description

    # TODO extend structure
    def extract_page_structure(self):
        structure = {
            'headings': {f'h{i}': len(self.soup.find_all(f'h{i}')) for i in range(1, 7)},
            'paragraphs': len(self.soup.find_all('p')),
            'lists': len(self.soup.find_all(['ul', 'ol'])),
            'tables': len(self.soup.find_all('table'))
        }
        return structure

    def extract_internal_links(self):
        domain = urlparse(self.url).netloc
        internal_links = []
        for link in self.soup.find_all('a', href=True):
            href = link['href']
            if href.startswith('/'):
                internal_links.append(urljoin(self.url, href))
            elif domain in urlparse(href).netloc:
                internal_links.append(href)
        return len(internal_links)

    def extract_external_links(self):
        domain = urlparse(self.url).netloc
        external_links = []
        for link in self.soup.find_all('a', href=True):
            href = link['href']
            if not href.startswith('/') and domain not in urlparse(href).netloc:
                external_links.append(href)
        return len(external_links)

    def extract_word_count(self):
        content = ' '.join([p.get_text() for p in self.soup.find_all('p')])
        return len(content.split())
