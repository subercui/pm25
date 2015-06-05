# -*- coding: utf-8 -*-
#load data
import os
import numpy as np
import cPickle, gzip
from pyproj import Proj
import datetime

#========================
# Mercator Projection
#========================

p = Proj('+proj=merc')

def get_gfs_key(n=60,s=4,w=70,e=140,r=10000):

    # Transform gfs_data to mercator projection
    # North latitude:  0   ~ 88
    # South latitude: -88  ~ 0
    # West longitude: -180 ~ 0
    # Eest longitude:  0   ~ 180
    # Accuracy: r (default:10000 metres)

    x,y = np.round(np.array(p(w,s))/r)
    x1,y1 = np.round(np.array(p(e,n))/r)
    lng = np.arange(np.abs(x1-x))+x
    lat = np.arange(np.abs(y1-y))+y
    lng,lat = np.meshgrid(lng*r,lat*r)
    lngs,lats = p(lng,lat,inverse=True)
    lngs = np.round(lngs*4)
    lats = np.flipud((90-np.round(lats*4)/4)*4)
    gfs_key = (lats.astype(int),lngs.astype(int))
    return gfs_key
    
def transform(gfs_data,gfs_key):
    gfs_data = gfs_data.reshape((180*4+1,360*4))
    res = gfs_data[gfs_key[0],gfs_key[1]]
    return res
    
def filesinroot(dir,wildcard,recursion):#目录中的文件
    matchs=[]
    exts=wildcard.split()
    for root,subdirs,files in os.walk(dir):
        for name in files:
            for ext in exts:
                if(name.endswith(ext)):
                    matchs.append(name)
                    break
        if(not recursion):
            break
    return matchs
    
def savefile(m,path):
    save_file = gzip.open(path, 'wb')  # this will overwrite current contents
    cPickle.dump(m, save_file, -1)  # the -1 is for HIGHEST_PROTOCOL
    save_file.close()
        
def decode_gfs(readdir,savedir):
    wildcard=".gz"
    matchs=filesinroot(readdir,wildcard,0);
    #解析某一时刻的gfs文档，生成六要素的新文档
    for match in matchs:
        print(match)
        #generate file name
        year=int(match[0:4])
        month=int(match[4:6])
        date=int(match[6:8])
        hour=int(match[9:11])
        hour_offset=int(match[12:15])
        date=datetime.datetime(year,month,date,hour)+datetime.timedelta(hours=hour_offset)
        if os.path.exists(savedir+date.strftime('%Y%m%d%H')+'tmp'+'.pkl.gz'):
            print('file already exists')
        else:
            #open
            f = gzip.open(readdir+match, 'rb')
            tmp = transform(cPickle.load(f),get_gfs_key(n=54,s=17,w=72,e=135,r=10000))#温度
            rh = transform(cPickle.load(f),get_gfs_key(n=54,s=17,w=72,e=135,r=10000))#相对湿度
            ugrd = transform(cPickle.load(f),get_gfs_key(n=54,s=17,w=72,e=135,r=10000))#横向风速
            vgrd = transform(cPickle.load(f),get_gfs_key(n=54,s=17,w=72,e=135,r=10000))#径向风速
            prate = transform(cPickle.load(f),get_gfs_key(n=54,s=17,w=72,e=135,r=10000))#降雨量
            tcdc = transform(cPickle.load(f),get_gfs_key(n=54,s=17,w=72,e=135,r=10000))#云量
            f.close()
            #save
            savefile(tmp,savedir+date.strftime('%Y%m%d%H')+'tmp'+'.pkl.gz')
            savefile(rh,savedir+date.strftime('%Y%m%d%H')+'rh'+'.pkl.gz')
            savefile(ugrd,savedir+date.strftime('%Y%m%d%H')+'ugrd'+'.pkl.gz')
            savefile(vgrd,savedir+date.strftime('%Y%m%d%H')+'vgrd'+'.pkl.gz')
            savefile(prate,savedir+date.strftime('%Y%m%d%H')+'prate'+'.pkl.gz')
            savefile(tcdc,savedir+date.strftime('%Y%m%d%H')+'tcdc'+'.pkl.gz')
    
if __name__ == '__main__':
    readdir='/ldata/pm25data/gfs/'
    savedir='/ldata/pm25data/gfsinmercator/'
    decode_gfs(readdir,savedir)  

