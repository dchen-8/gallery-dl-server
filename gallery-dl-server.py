# /Library/Frameworks/Python.framework/Versions/3.7/bin/python3

import os
from bottle import route, run, Bottle, request
import gallery_dl
from zipfile import ZipFile

app = Bottle()

DEFAULT_HOST = '0.0.0.0'
DEFAULT_PORT = 8080

GALLERY_PATH = './gallery-dl/'
ZIP_SUFFIX = 'cbz'

@app.route('/')
def gallery_main():
    return {'Main Page'}


@app.route('/gallery-dl', method='POST')
def gallery_post():
    url = request.forms.get('url')

    if not url:
        return {'Missing URL'}

    print('Downloading: ' + url)

    call_gallery_dl(url)


def call_gallery_dl(url):
    download_job = gallery_dl.job.DownloadJob
    download_job(url).run()
    print('Finished downloading!')

@app.route('/gallery-dl/create_zip', method='GET')
def find_directories_and_zip():
    top_dir = os.listdir(GALLERY_PATH)
    for each_dir in top_dir:
        each_dir_path = os.path.join(GALLERY_PATH, each_dir)
        for root_path, dirct, files in os.walk(each_dir_path):

            photos_in_directory = [x for x in files if x.rsplit('.', 1)[1] in ('jpg', 'png')]
            if not photos_in_directory:
                print('No photos in directory: ' + root_path)
                continue
            
            zip_path, zip_file = root_path.rsplit('/', 1)
            zip_file_name = zip_file + '.' + ZIP_SUFFIX
            zip_file_path = os.path.join(zip_path, zip_file_name)
            with ZipFile(zip_file_path, 'w') as myzip:
                for each_photo in photos_in_directory:
                    each_photo_path = os.path.join(root_path, each_photo)
                    myzip.write(each_photo_path)
            print('Finished creating zip for: ' + root_path)


app.run(host=DEFAULT_HOST, port=DEFAULT_PORT, debug=True)