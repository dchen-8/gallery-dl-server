# /Library/Frameworks/Python.framework/Versions/3.7/bin/python3

from bottle import route, run, Bottle, request
import gallery_dl

app = Bottle()

DEFAULT_HOST = '0.0.0.0'
DEFAULT_PORT = 8080

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
    global_config = gallery_dl.config
    print(global_config._config)
    global_config.set(url, 'dest', '/gallery-dl',)

    download_job = gallery_dl.job.DownloadJob
    download_job(url).run()
    print('Finished downloading!')


app.run(host=DEFAULT_HOST, port=DEFAULT_PORT, debug=True)