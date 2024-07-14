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
from cairosvg import svg2png

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

    def extract_image_data(self, max_images):
        images = []
        for image in self.soup.find_all('img', src=True):
            if max_images and len(images) >= max_images:
                break
            width = image.get('width', 100)
            height = image.get('height', 100)
            src = image['src']
            image_name = src.split('/')[-1]
            image_response = self.get_image_response(src)
            if image_response is None:
                continue
            content_type = image_response.headers.get('Content-Type', '')
            if "image" not in content_type:
                continue
            converted_svg = None
            if 'image/svg+xml' in content_type:
                image_format = 'svg'
                svg = image_response.content
                converted_svg = svg2png(bytestring=svg)
                image_file = Image.open(BytesIO(converted_svg))
                image_width = width
                image_height = height
            else:
                try:
                    image_file = Image.open(BytesIO(image_response.content))
                    image_format = image_file.format.lower()
                    (image_width, image_height) = image_file.size
                except UnidentifiedImageError as err:
                    print(f'Unknown image error: {err} at {src}')
                    continue
            img_hash = hashlib.md5(image_response.content).hexdigest()
            images.append({
                'hash': img_hash,
                'image_url': urljoin(self.base_url, src),
                'src': src,
                'file_name': image_name,
                'alt_text': image.get('alt', ''),
                'image_title': image.get('title', ''),
                'image_caption': self.get_image_caption(image),
                'headline_above_image': self.get_headline_above_image(image),
                'width': image_width,
                'height': image_height,
                'contains_transparency': self.has_transparency(image_file),
                'wrapped_element': image.parent.name,
                'semantic_context': self.find_semantic_parent(image),
                'file_format': image_format
            })
            image_content = converted_svg if image_format == 'svg' else image_response.content
            image_format = 'png' if image_format == 'svg' else image_format
            if not self.ftp_connector.image_exists(img_hash, image_format):
                self.ftp_connector.upload_to_ftp(img_hash + '.' + image_format, image_content)
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

    def find_semantic_parent(self, element):
        parent = element.parent
        while parent:
            if parent.name in SEMANTIC_HTML_LOCATION_ELEMENTS:
                return parent.name
            parent = parent.parent
        return None

    def get_headline_above_image(self, img_element):
        headline = img_element.find_previous(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
        if headline is not None:
            return headline.get_text()
        return None

    def has_transparency(self, image):
        if image.info.get("transparency", None) is not None:
            return True
        if image.mode == "P":
            transparent = image.info.get("transparency", -1)
            for _, index in image.getcolors():
                if index == transparent:
                    return True
        elif image.mode == "RGBA":
            extrema = image.getextrema()
            if extrema[3][0] < 255:
                return True
        return False

    def get_image_caption(self, img):
        figure = img.find_parent('figure')
        if figure:
            figcaption = figure.find('figcaption')
            if figcaption:
                return figcaption.get_text().strip()
