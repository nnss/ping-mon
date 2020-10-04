
import urllib.request
import re
import os

#####
# prepare environment
# the python in the VENV should exist, if not, create it as:
# python -m venv path_to_dir
# example:
# python -m venv D:\venv-pingmon
# python -n venv $HOME/venv-pingmon
#
# Be sure to activate the environment a
# $VENV_BIN_PATH/pip install -r requirements.txt
#
# this script will download all the JS files (static folder)
#
##########
urls = ['https://code.highcharts.com/8.2.0/highcharts.js',
        'https://code.highcharts.com/8.2.0/highcharts-more.js',
        'https://code.highcharts.com/8.2.0/modules/exporting.js',
        'https://code.highcharts.com/8.2.0/modules/data.js',
        'https://code.highcharts.com/8.2.0/modules/export-data.js',
        'https://code.jquery.com/jquery-1.12.4.min.js']

for url in urls:
    print(url)
    with urllib.request.urlopen(url) as response:
        html = response.read()
    file = re.sub(r'.*\/([^\/]+)$', r"\1", url)
    print(file)
    if not os.path.exists("./static"):
        os.mkdir("./static")
    with open("./static/" + file, "wb") as fd:
        fd.write(html)
print("done")
