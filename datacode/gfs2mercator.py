# -*- coding:utf-8 -*-

from __future__ import division
import numpy as np
import gzip
import cPickle
from pyproj import Proj

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

def trans_rain_dbz(value):
    dBZ = np.zeros(value.shape)
    value = value*3600
    no_zero = np.where(value!=0)
    is_zero = np.where(value==0)
    dBZ[no_zero] = 10*np.log10(200*np.power(value[no_zero],1.6))
    dBZ[is_zero] = 0
    dBZ = np.round(dBZ/5)
    dBZ[np.where(dBZ<0)]=0
    return dBZ

