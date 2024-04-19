#!/usr/bin/env python3
# usage: repo_setup.py [source_repo_url] [local_repo_dir]
# example: repo_setup.py http://www.apps4av.org/new/ /usr/share/nginx/mirrors.nw.ci/public/avare

import requests
import subprocess
from bs4 import BeautifulSoup
import os,sys
import datetime
from yarl import URL

# wget --mirror --no-directories --no-verbose --directory-prefix=. http://www.apps4av.org/new/2101/databases.zip

def generate_input_file(url, zipfiles, version):
    with open('/tmp/'+version, 'w') as output_file:
        for zipfile in zipfiles:
            fileurl = url / zipfile
            output_file.write(str(fileurl))
            output_file.write('\n')


def create_ver_dir(dir_path, version):
    dir_path = os.path.join(dir_path, version)
    try:
        os.chdir(dir_path)
    except:
        os.mkdir(dir_path)
        os.chdir(dir_path)


def update_php(version):
    with open('version.php', 'w') as php_file:
        php_file.write(version)


def parse_web(response):
    zipfiles = []
    soup = BeautifulSoup(response.text, 'html.parser')
    for link in soup.find_all('a', href=True):
        if '.txt' and '.zip' in link.attrs['href']:
            zipfiles.append(link.attrs['href'])
    return zipfiles


def get_new_version(url):
    response = requests.get(url / 'version.php')
    return response.text.strip('\n')


def get_existing_version(path):
    v = 0
    vphp = os.path.join(path, "version.php")
    try:
        f = open(vphp)
        new_v = int(f.readline())
        if new_v > 0: v = new_v
        f.close()
    except:
       return -1
    return v

def main():
    url = URL(sys.argv[1])
    new_version = get_new_version(url)
    dir_path = sys.argv[2]
    existing_version = get_existing_version(dir_path)
    if existing_version >= int(new_version):
        print("existing cycle is current")
        return
    create_ver_dir(dir_path, new_version)
    os.chdir("../")
    new_version_dir = new_version #+ '/'
    response = requests.get(url / new_version_dir)
    zipfiles = parse_web(response)
    generate_input_file(url / new_version_dir, zipfiles, new_version)
    aria2c_cmd = "aria2c --file-allocation=none --allow-overwrite -c -x 32 -s 8 -d " \
                 + os.path.join(dir_path,new_version_dir) + " -i /tmp/" + new_version
    aria2c_ret = subprocess.run(aria2c_cmd.split())
    if aria2c_ret.returncode == 0:
        update_php(new_version)
        print("new cycle {} now active".format(new_version))

if __name__ == '__main__':
    main()

