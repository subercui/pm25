# -*- coding:utf-8 -*-
from __future__ import division
import numpy as np
import gzip
import cPickle
from caiyun_common import gfs2mercator as gfs
from caiyun_common import caiyun
import cv2
import os
import time
from scipy import misc
from scipy.misc import imresize

gfs_key = gfs.get_gfs_key(80,-80,-180,180)

def process(filename):
    try:    
        f = gzip.open(filename)
        tmp = cPickle.load(f)
        rh = cPickle.load(f)
        ugrd = cPickle.load(f)
        vgrd = cPickle.load(f)
        prate = cPickle.load(f)
        tcdc = cPickle.load(f)
        f.close()

        prate = np.array(prate)
        res = gfs.transform(prate,gfs_key)
        res = gfs.trans_rain_dbz(res)
        res_after_blur = cv2.GaussianBlur(res,(13,13),sigmaX=0)
        res_after_blur = res_after_blur.astype('uint8')
        res_after_blur[np.where(res_after_blur>0)] = res_after_blur[np.where(res_after_blur>0)]+2

        matrix = caiyun.replace_color(res_after_blur)
        size = (int(np.round(matrix.shape[0]/5)),int(np.round(matrix.shape[1]/5)))
        matrix = imresize(matrix,size,'bilinear')
        filedir = filename.split('.pkl.gz')[0]+'_rain_world.png'
        misc.imsave(filedir, matrix);

    except Exception as e:
        print e,"No file",filename

def get_key():
    list_key = []
    base_key = "../data/gfs/20150203_18_"
    num = 3
    while num<24*10:
        num_key = base_key+str('%0003d'%(num))+'.pkl.gz'
        list_key.append(num_key)
        num = num+3
    while num<=24*16:
        num_key = base_key+str('%0003d'%(num))+'.pkl.gz'
        list_key.append(num_key)
        num = num+12
    return list_key

if __name__ == '__main__':
    m = get_key() 
    num = 1
    for filepath in m:
        print '-----',num,'-----'
        process(filepath)
        num = num +1
