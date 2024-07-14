from src.crawler import Crawler
from src.database import Database
import configparser

config = configparser.ConfigParser()
config.read("../config.properties")

params = {
    'page_count': 10,
    'max_images_page': 7,
    'timeout': 5
}

db = Database(host=config['database']['db.host'], username=config['database']['db.username'],
              password=config['database']['db.password'], database=config['database']['database'],
              port=config['database']['port'])
db.connect()
db.create_tables()

domains_query = """
SELECT url FROM google_results;
"""
domains_result = db.execute_query(domains_query, None, 'all')
domains = [d[0] for d in domains_result]
print(domains)

for domain in domains:
    crawler = Crawler(params)
    crawler.crawl(domain)
    print(f"Finished crawling {domain}")
