"""
Maintains the filesystem used by the trainers. MUST BE RUN IN A SEPARATE PROCESS TO MAINTAIN DOWNLOAD INTEGRITY
"""
import io
import json
import random
import zipfile

import fs
import requests


class Downloader:
    BASE_URL = "http://saltie.tk:5000"

    def __init__(self, max_size_mb=100, path='mem://saltie'):
        self.max_size_mb = max_size_mb
        self.filesystem = fs.open_fs(path)

    @staticmethod
    def unzip(in_memory_file: io.BytesIO):
        in_memory_zip_file = zipfile.ZipFile(in_memory_file)
        return [io.BytesIO(in_memory_zip_file.read(name)) for name in in_memory_zip_file.namelist()]

    @staticmethod
    def create_in_memory_file(response: requests.Response) -> io.BytesIO:
        in_memory_file = io.BytesIO()
        for chunk in response.iter_content(chunk_size=1024):
            if chunk:
                in_memory_file.write(chunk)
        return in_memory_file

    def get_random_replay(self):
        js = requests.get(self.BASE_URL + '/replays/list').json()
        filename = random.choice(js)
        return self.get_replay(filename), filename

    def get_replays(self, number=1):
        js = requests.get(self.BASE_URL + '/replays/list').json()
        file_list = []
        for i in range(number):
            filename = random.choice(js)
            file_list.append((self.get_replay(filename), filename))
            print('downloading file:', i)
        return file_list

    def get_replay(self, filename_or_filenames: list or str):
        if isinstance(filename_or_filenames, list):
            r = requests.post(self.BASE_URL + '/replays/download', data={'files': json.dumps(filename_or_filenames)})
            imf = self.create_in_memory_file(r)
            return self.unzip(imf)
        else:
            r = requests.get(self.BASE_URL + '/replays/{}'.format(filename_or_filenames))
            imf = self.create_in_memory_file(r)
            return imf

    def download_replays(self):
        rpl, fn = self.get_random_replay()
        success = self.filesystem.create(fn)
        if success:
            # file has been successfully created
            self.filesystem.setfile(fn, rpl)


if __name__ == '__main__':
    dl = Downloader()
    dl.download_replays()
    print(dl.filesystem.listdir('/'))
