from urllib.parse import urljoin
from bs4 import BeautifulSoup
from requests import HTTPError
from database import Database
import configparser
from src.image_data_extractor import ImageDataExtractor
from src.page_data_extractor import PageDataExtractor
import requests
import src.helper as helper
import random

config = configparser.ConfigParser()
config.read("../config.properties")

NOT_ALLOWED_PAGES = ["impressum", "sitemap", "datenschutz", "category", "tag"]


class Crawler:
    def __init__(self, params):
        self.db = Database(host=config['database']['db.host'], username=config['database']['db.username'],
                           password=config['database']['db.password'], database=config['database']['database'],
                           port=config['database']['port'])
        self.visited_urls = set()
        self.to_visit = []
        self.params = params

    def crawl(self, url):
        page_count = self.params.get('page_count', False)
        # sitemap_pages = self.get_sitemap_pages(url)
        # if sitemap_pages:
        #     print("Crawling website through sitemap...")
        #     for page in sitemap_pages:
        #         if page_count and len(self.visited_urls) >= page_count:
        #             break
        #         self.visit_url(page)
        # else:
        #     print(f'No sitemap found for {url}. Crawling internal links...')

        self.to_visit.append(url)
        while self.to_visit and (not page_count or len(self.visited_urls) < int(page_count)):
            next_index = random.randint(0, len(self.to_visit) - 1)
            next_url = self.to_visit.pop(next_index)
            if any(substring in next_url for substring in NOT_ALLOWED_PAGES):
                continue
            if next_url not in self.visited_urls:
                self.visit_url(next_url)

    def visit_url(self, url):
        normalized_url = helper.normalize_url(url)
        if normalized_url in self.visited_urls:
            return
        print(f"Visiting: {normalized_url}")
        self.visited_urls.add(normalized_url)
        try:
            soup = self.fetch_url(normalized_url)
            if soup is None:
                return
        except HTTPError as err:
            print(f"Error: {err} for URL: {normalized_url}")
            return

        page_data = self.crawl_page(soup, normalized_url)
        print(page_data)
        image_data = self.crawl_images(soup, normalized_url)
        if image_data:
            page_id = self.db.insert_page(page_data)
            for image in image_data:
                image['page_id'] = page_id
                self.db.insert_image(image)
            print("Data saved")

        internal_links = helper.extract_internal_links(soup, normalized_url)
        for link in internal_links:
            normalized_link = helper.normalize_url(link)
            if normalized_link not in self.visited_urls and normalized_link not in self.to_visit:
                self.to_visit.append(normalized_link)

    def crawl_page(self, soup, url):
        page_data_extractor = PageDataExtractor(soup, url)
        return page_data_extractor.extract_page_data()

    def crawl_images(self, soup, url):
        max_images = self.params.get('max_images_page', False)
        img_data_extractor = ImageDataExtractor(soup, url)
        return img_data_extractor.extract_image_data(max_images)

    def fetch_url(self, url, xml=False):
        request_timeout = self.params.get('timeout', 10)
        try:
            response = requests.get(url, timeout=request_timeout)
        except requests.exceptions.RequestException as e:
            print(f"Request failed: {e}")
            return None
        response.raise_for_status()
        content_type = response.headers.get('Content-Type', '')
        if 'html' not in content_type and 'xml' not in content_type:
            return None
        if xml:
            return BeautifulSoup(response.content, features='xml')
        return BeautifulSoup(response.content, features='html.parser')

    def parse_sitemap(self, soup):
        urls = []
        if soup.find('sitemapindex'):
            sitemaps = soup.find_all('sitemap')
            for sitemap in sitemaps:
                sitemap_url = sitemap.find('loc').text
                urls.extend(self.parse_sitemap(self.fetch_url(sitemap_url, xml=True)))
        elif soup.find('urlset'):
            urls = [url.find('loc').text for url in soup.find_all('url')]
        return urls

    def get_sitemap_pages(self, url):
        sitemap_url = urljoin(url, '/sitemap.xml')
        try:
            soup = self.fetch_url(sitemap_url, xml=True)
        except HTTPError as err:
            print(err)
            return None
        return self.parse_sitemap(soup)
