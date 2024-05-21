from urllib.parse import urljoin
from bs4 import BeautifulSoup
from requests import HTTPError
from database import Database
import configparser
from src.image_data_extractor import ImageDataExtractor
from src.page_data_extractor import PageDataExtractor
import requests

config = configparser.ConfigParser()
config.read("../config.properties")


class Crawler:
    def __init__(self):
        self.db = Database(host=config['database']['db.host'], username=config['database']['db.username'],
                           password=config['database']['db.password'], database=config['database']['db.database'])

    def crawl(self, url):
        response = requests.get(url)
        if response.status_code != 200:
            print(f"Error: get {response.status_code} as response for {url}")
            return
        sitemap_pages = self.get_sitemap_pages(url)
        if sitemap_pages is not None:
            for page in sitemap_pages:
                print(page)
                soup = self.fetch_url(page)
                self.crawl_pages(soup, urls=url)
                self.crawl_images(soup, url)
        else:
            print(f'No sitemap found for {url}')

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

    def fetch_url(self, url, xml=False):
        response = requests.get(url)
        response.raise_for_status()
        if xml:
            return BeautifulSoup(response.content, features='xml')
        return BeautifulSoup(response.content, features='html.parser')

    def get_sitemap_pages(self, url):
        sitemap_url = urljoin(url, '/sitemap.xml')
        try:
            soup = self.fetch_url(sitemap_url, xml=True)
        except HTTPError as err:
            print(err)
            return None
        return self.parse_sitemap(soup)
