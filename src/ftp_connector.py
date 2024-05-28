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
        self.chdir(self.config['ftp']['img-directory'])

    def chdir(self, dir):
        if self.directory_exists(dir) is False:
            self.ftp.mkd(dir)
        self.ftp.cwd(dir)

    def directory_exists(self, dir):
        filelist = []
        self.ftp.retrlines('LIST', filelist.append)
        for f in filelist:
            if f.split()[-1] == dir and f.upper().startswith('D'):
                return True
        return False

    def upload_to_ftp(self, file_name, file_content):
        with BytesIO(file_content) as file:
            self.ftp.storbinary(f'STOR {file_name}', file)
