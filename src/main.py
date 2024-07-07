from src.crawler import Crawler
from src.database import Database
import configparser

config = configparser.ConfigParser()
config.read("../config.properties")

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
    crawler = Crawler()
    crawler.crawl(domain, page_count=config['crawler']['page-count'])
    print(f"Finished crawling {domain}")
