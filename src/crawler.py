from urllib.parse import urljoin
from bs4 import BeautifulSoup
from requests import HTTPError
from database import Database
import configparser
from src.image_data_extractor import ImageDataExtractor
from src.page_data_extractor import PageDataExtractor
import requests
import src.helper as helper
from collections import Counter

config = configparser.ConfigParser()
config.read("../config.properties")


class Crawler:
    def __init__(self):
        self.db = Database(host=config['database']['db.host'], username=config['database']['db.username'],
                           password=config['database']['db.password'], database=config['database']['database'],
                           port=config['database']['port'])
        self.visited_urls = set()
        self.to_visit = []
        self.image_freq = Counter()

    def crawl(self, url):
        sitemap_pages = self.get_sitemap_pages(url)
        if sitemap_pages:
            print("Crawling website through sitemap...")
            for page in sitemap_pages:
                self.visit_url(page)
        else:
            print(f'No sitemap found for {url}. Crawling internal links...')
            self.to_visit.append(url)
            while self.to_visit:
                next_url = self.to_visit.pop(0)
                if next_url not in self.visited_urls:
                    self.visit_url(next_url)

    def visit_url(self, url):
        if url in self.visited_urls:
            return
        print(f"Visiting: {url}")
        self.visited_urls.add(url)
        try:
            soup = self.fetch_url(url)
        except HTTPError as err:
            print(f"Error: {err} for URL: {url}")
            return
        # TODO save image frequence only when its the last page
        self.image_freq.update([img['src'] for img in soup.find_all('img', src=True)])

        page_data = self.crawl_page(soup, url)
        image_data = self.crawl_images(soup, url)
        if image_data:
            page_id = self.db.insert_page(page_data)
            for image in image_data:
                image['page_id'] = page_id
                # TODO
                image['frequency_on_website'] = 0
                self.db.insert_image(image)
            print("Data saved")

        internal_links = helper.extract_internal_links(soup, url)
        for link in internal_links:
            if link not in self.visited_urls and link not in self.to_visit:
                self.to_visit.append(link)

    def crawl_pages(self, soup, urls):
        page_data_extractor = PageDataExtractor(soup, urls)
        data = page_data_extractor.extract_page_data()
        print('PAGE DATA')
        print(data)
        print(len(data))

    def crawl_images(self, soup, url):
        img_data_extractor = ImageDataExtractor(soup, url)
        data = img_data_extractor.extract_image_data()
        print('IMAGE DATA')
        print(data)
        print(len(data))

    def fetch_url(self, url, xml=False):
        response = requests.get(url)
        response.raise_for_status()
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
