import requests
from requests.exceptions import InvalidSchema
from urllib.parse import urljoin
from bs4 import BeautifulSoup
from PIL import Image, UnidentifiedImageError
from src.database import Database
from src.ftp_connector import FTPConnector
from io import BytesIO
import hashlib
import configparser

SEMANTIC_HTML_LOCATION_ELEMENTS = ['article', 'aside', 'footer', 'header', 'main', 'nav', 'section']


class ImageDataExtractor:
    def __init__(self, soup, base_url):
        self.soup = soup
        self.base_url = base_url
        self.ftp_connector = FTPConnector()
        self.config = configparser.ConfigParser()
        self.config.read("../config.properties")
        self.db = Database(host=self.config['database']['db.host'], username=self.config['database']['db.username'],
                           password=self.config['database']['db.password'], database=self.config['database']['database'],
                           port=self.config['database']['port'])

    def extract_image_data(self):
        images = []
        for image in self.soup.find_all('img', src=True):
            width = image.get('width', 0)
            height = image.get('height', 0)
            src = image['src']
            image_name = src.split('/')[-1]
            image_response = self.get_image_response(src)
            if image_response is None:
                continue
            content_type = image_response.headers.get('Content-Type', '')
            if "image" not in content_type:
                continue
            if 'image/svg+xml' in content_type:
                image_format = 'svg'
                image_size = len(image_response.content)
                image_width = width
                image_height = height
                # TODO
                # dominant_color = self.get_dominant_color_from_svg(image_response.content)
                dominant_color = None
            else:
                try:
                    image_file = Image.open(BytesIO(image_response.content))
                    image_size = int(image_response.headers.get('content-length', 0))
                    image_format = image_file.format.lower()
                    (image_width, image_height) = image_file.size
                    dominant_color = self.get_dominant_color(image_file)
                except UnidentifiedImageError as err:
                    print(f'Unknown image error: {err} at {src}')
                    continue
            img_hash = hashlib.md5(image_response.content).hexdigest()
            if self.ftp_connector.image_exists(img_hash, image_format) or self.db.image_exists(img_hash):
                continue
            images.append({
                'hash': img_hash,
                'image_url': urljoin(self.base_url, src),
                'src': src,
                'file_name': image_name,
                'alt_text': image.get('alt', ''),
                'image_title': image.get('title', ''),
                'image_caption': self.get_image_caption(image),
                'width': image_width,
                'height': image_height,
                'wrapped_element': image.parent.name,
                'semantic_context': self.find_semantic_parent(image),
                'file_size': image_size,
                'file_format': image_format,
                'dominant_color': str(dominant_color)
            })
            self.ftp_connector.upload_to_ftp(img_hash + '.' + image_format, image_response.content)
        return images

    def get_image_response(self, image_src):
        image_url = urljoin(self.base_url, image_src)
        try:
            response = requests.get(image_url)
            response.raise_for_status()
            return response
        except InvalidSchema:
            return None
        except requests.RequestException as e:
            print(f"Request failed for URL: {image_src} with error: {e}")
            return None

    def get_dominant_color(self, image):
        image = image.resize((50, 50))
        result = image.convert('P', palette=Image.ADAPTIVE, colors=1)
        result = result.convert('RGBA')
        dominant_color = result.getcolors(50 * 50)[0][1]
        return dominant_color

    def get_dominant_color_from_svg(self, svg_data):
        png_data = cairo.svg2png(bytestring=svg_data)
        image = Image.open(BytesIO(png_data))
        return self.get_dominant_color(image)

    def find_semantic_parent(self, element):
        parent = element.parent
        while parent:
            if parent.name in SEMANTIC_HTML_LOCATION_ELEMENTS:
                return parent.name
            parent = parent.parent
        return None

    def get_image_caption(self, img):
        figure = img.find_parent('figure')
        if figure:
            figcaption = figure.find('figcaption')
            if figcaption:
                return figcaption.get_text().strip()
