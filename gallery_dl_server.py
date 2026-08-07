import argparse
import os
import time
import uuid
from collections import OrderedDict
import gallery_dl

from bottle import route, run, Bottle, request, static_file
from queue import Queue
from threading import Thread
from zipfile import ZipFile
from concurrent.futures import ThreadPoolExecutor

parser = argparse.ArgumentParser()
parser.add_argument("--zip_downloads", 
                    nargs='?',
                    const=1,
                    default='False', 
                    choices=['False', 'True'], 
                    help="Zip files into CBZ after download")
args, _ = parser.parse_known_args()

app = Bottle()
DL_THREAD = ThreadPoolExecutor(max_workers=2)

DEFAULT_HOST = '0.0.0.0'
DEFAULT_PORT = 8080

GALLERY_PATH = './gallery-dl/'
ZIP_SUFFIX = 'cbz'
QUEUE_TXT_PATH = 'queue.txt'

JOBS = OrderedDict()


def log_url_to_file(url, timestamp):
    try:
        with open(QUEUE_TXT_PATH, 'a', encoding='utf-8') as f:
            f.write(f"[{timestamp}] {url}\n")
    except Exception as e:
        print(f"Error writing to {QUEUE_TXT_PATH}: {e}")


class NoPathExists(Exception):
    pass

@app.route('/')
def gallery_main():
    return static_file('index.html', root='./')


@app.route('/gallery-dl', method='POST')
def gallery_post():
    url = request.forms.get('url')
    zip_opt = request.forms.get('zip') or request.forms.get('zip_downloads')

    if not url:
        return {'Missing URL'}

    job_id = uuid.uuid4().hex[:8]
    timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
    job_info = {
        'id': job_id,
        'url': url,
        'status': 'queued',
        'timestamp': timestamp,
        'error': None,
        'directory': None
    }
    JOBS[job_id] = job_info

    # Append to flat text file
    log_url_to_file(url, timestamp)

    DL_THREAD.submit(call_gallery_dl, job_id, url, zip_downloads=zip_opt)

    return {"successfully_added_to_queue": True, "job_id": job_id, "job": job_info}


@app.route('/gallery-dl/queue', method='GET')
@app.route('/gallery-dl/status', method='GET')
def get_queue_status():
    return {"jobs": list(JOBS.values())}


@app.route('/gallery-dl/clear_queue', method='POST')
@app.route('/gallery-dl/clear_queue', method='GET')
def clear_queue():
    to_delete = [jid for jid, j in JOBS.items() if j['status'] in ('finished', 'zipped', 'failed')]
    for jid in to_delete:
        del JOBS[jid]
    return {"success": True, "remaining": len(JOBS)}


def call_gallery_dl(job_id, url, zip_downloads=None):
    job = JOBS.get(job_id)
    if job:
        job['status'] = 'downloading'

    try:
        download_job = gallery_dl.job.DownloadJob
        downloader = download_job(url)
        downloader.run()

        download_path = getattr(downloader.pathfmt, 'directory', None)
        if job:
            job['directory'] = download_path

        should_zip = (str(zip_downloads).lower() in ('true', '1')) if zip_downloads is not None else (args.zip_downloads == 'True')

        final_status = 'finished'
        if should_zip and download_path:
            zip_directories(download_path)
            final_status = 'zipped'

        if job:
            job['status'] = final_status

        print('Finished downloading!')
    except Exception as gd:
        print(gd)
        if job:
            job['status'] = 'failed'
            job['error'] = str(gd)

@app.route('/gallery-dl/create_zip', method='GET')
def find_directories_and_zip():
    if not os.path.exists(GALLERY_PATH):
        return {'error': 'GALLERY PATH does not exist; Download something and try again', 'successful_created_zips': False}

    top_dir = os.listdir(GALLERY_PATH)
    for each_dir in top_dir:
        each_dir_path = os.path.join(GALLERY_PATH, each_dir)
        zip_directories(each_dir_path)

    return {'successful_created_zips': True}


def zip_directories(path_to_zip):
    for root_path, dirct, files in os.walk(path_to_zip):

        # Check if there are photos in the files, if not skip directory
        photos_in_directory = [x for x in files if x.rsplit('.', 1)[1] in ('jpg', 'png')]
        if not photos_in_directory:
            print('No photos in directory: ' + root_path)
            continue

        # Remove trailing / if it exists
        zip_path, zip_file = root_path.rstrip('/').rsplit('/', 1)
        zip_file_name = zip_file + '.' + ZIP_SUFFIX
        zip_file_path = os.path.join(zip_path, zip_file_name)

        # Check if zip file has already been created and skip if already created
        # TODO: Allow ability to ignore check and re-zip folders.
        if os.path.exists(zip_file_path):
            existing_zip = ZipFile(zip_file_path)
            items_in_zip = existing_zip.namelist()

            # If the photos in the directory is less than or equal to items in zip; skip
            if len(photos_in_directory) <= len(items_in_zip):
                print('Files have already been zipped.')
                print('Skipping')
                continue

        print('Creating file: ' + zip_file_path)
        with ZipFile(zip_file_path, 'w') as myzip:
            for each_photo in photos_in_directory:
                each_photo_path = os.path.join(root_path, each_photo)
                myzip.write(each_photo_path)
        print('Finished creating zip for: ' + root_path)


if __name__ == '__main__':

    app.run(host=DEFAULT_HOST, port=DEFAULT_PORT, debug=True)