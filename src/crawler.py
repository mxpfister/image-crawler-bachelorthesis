from urllib.parse import urljoin
from bs4 import BeautifulSoup
from requests import HTTPError
from database import Database
import configparser
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
            print(f"Error: get {response.status_code} as response")
            return
        # soup = BeautifulSoup(response.content, 'html.parser')
        sitemap_pages = self.get_sitemap_pages(url)
        if sitemap_pages is not None:
            print(sitemap_pages)
            print(len(sitemap_pages))
        else:
            print(f'No sitemap found for {url}')

    def parse_sitemap(self, soup):
        urls = []
        if soup.find('sitemapindex'):
            sitemaps = soup.find_all('sitemap')
            for sitemap in sitemaps:
                sitemap_url = sitemap.find('loc').text
                urls.extend(self.parse_sitemap(self.fetch_sitemap(sitemap_url)))
        elif soup.find('urlset'):
            print('elif')
            urls = [url.find('loc').text for url in soup.find_all('url')]
        return urls

    def fetch_sitemap(self, url):
        response = requests.get(url)
        response.raise_for_status()
        return BeautifulSoup(response.content, features='xml')

    def get_sitemap_pages(self, url):
        sitemap_url = urljoin(url, '/sitemap.xml')
        try:
            soup = self.fetch_sitemap(sitemap_url)
        except HTTPError as err:
            print(err)
            return None
        return self.parse_sitemap(soup)
