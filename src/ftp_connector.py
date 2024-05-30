from ftplib import FTP
import configparser
from io import BytesIO


class FTPConnector:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(FTPConnector, cls).__new__(cls, *args, **kwargs)
        return cls._instance

    def __init__(self):
        self.config = configparser.ConfigParser()
        self.config.read("../config.properties")
        self.ftp = FTP(self.config['ftp']['server'])
        self.ftp.login(self.config['ftp']['username'], self.config['ftp']['password'])
        self.chdir(self.config['ftp']['img-path'])

    def chdir(self, dir_path):
        directories = dir_path.split('/')
        for i in range(len(directories)):
            current_dir = '/'.join(directories[:i + 1])
            if not self.directory_exists(current_dir):
                self.ftp.mkd(current_dir)
            self.ftp.cwd(current_dir)

    def directory_exists(self, dir_path):
        try:
            self.ftp.cwd(dir_path)
            return True
        except:
            return False

    def upload_to_ftp(self, file_name, file_content):
        with BytesIO(file_content) as file:
            self.ftp.storbinary(f'STOR {file_name}', file)

    def image_exists(self, img_hash, img_format):
        return f'{img_hash}.{img_format}' in self.ftp.nlst()

