# -*- coding: utf-8 -*-

import sys
import os
from qiniu import Auth
from multiprocessing import Pool 

access_key = 'CUHjrT-KJB8tT2p3dOtrGINkdpd2CbeAMqMquh-V'
secret_key = 'p5FpEQKCQJbfMyTYa9lLbQnH9lEqlKwsQJoVOnPu'
q = Auth(access_key, secret_key)
bucket = '7u2sgg.com2.z0.glb'

def get_key():
    list_key = []
    base_key = "20150203/18/003"
    for mon in range(5,7):
        base_key=base_key[0:4]+str('%02d'%(mon))+base_key[6:]
        for day in range(1,32):
            base_key=base_key[0:6]+str('%02d'%(day))+base_key[8:]
            for hour in range(0,24,6):
                base_key=base_key[0:9]+str('%02d'%(hour))+base_key[11:]
                for i in [3,6]:
                    base_key=base_key[0:12]+str('%0003d'%(i))
                    list_key.append(base_key)
    return list_key

def get_url(key):
    burl = 'http://%s/%s' % (bucket + '.clouddn.com', key)
    purl = q.private_download_url(burl, expires=3600)
    return purl

def download((url,name)):
    os.system('wget  -T 60 -t 2 -O '+name+' "'+url+'"')

def get_data():
    url_list = []
    filedir = '/ldata/pm25data/gfs/'
    list_key = get_key()
    for key in list_key:
        url = get_url(key)
        keyname = key.split('/')
        name = filedir+keyname[0]+'_'+keyname[1]+'_'+keyname[2]+'.pkl.gz'
        if os.path.isfile(name):
            print name+' has exits'
        else:
            url_list.append((url,name))
    
    for m in url_list:
        download(m)
   # pool = Pool(processes=1)
   # pool.map(download,url_list)

if __name__ == "__main__":
    get_data()
