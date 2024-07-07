import src.helper as helper
import json


class PageDataExtractor:
    def __init__(self, soup, url):
        self.soup = soup
        self.url = url

    def extract_page_data(self):
        return {
            'title': str(self.soup.title.string) if self.soup.title else '',
            'top_headline': self.soup.find('h1').get_text() if self.soup.find('h1') else '',
            'url': self.url,
            'meta_description': self.extract_meta_description(),
            # 'html_raw': self.soup.prettify(),
            'language': self.soup.html.get('lang') if self.soup.html else '',
            'word_count': self.extract_word_count(),
            'image_count': len(self.soup.find_all('img')),
            'external_link_count': len(helper.extract_external_links(self.soup, self.url)),
            'internal_link_count': len(helper.extract_internal_links(self.soup, self.url))
        }
        
    def extract_meta_description(self):
        meta_description = ""
        if self.soup.find('meta', attrs={'name': 'description'}):
            meta_description = self.soup.find('meta', attrs={'name': 'description'}).get('content', '')
        return meta_description

    def extract_word_count(self):
        content = ' '.join([p.get_text() for p in self.soup.find_all('p')])
        return len(content.split())
