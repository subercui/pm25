# -*- coding: utf-8 -*-
#几个bash命令，以及调用的.py文件内的bash命令，访问顺序是什么样的
#用于每日调用，更新model以及依赖文件

import sys
import os
#prepare data
#gfs
os.system('python ./datacode/download_gfs.py')
print "gfs downloading finished"
gfsdir='/ldata/pm25data/gfs/'
os.system('find '+gfsdir+' -type f -size 0 -exec rm -f {} \;')
print "empty gfs files deleted"
#pm25 mean
os.system('python ./datacode/pm25_mean.py')
print "pm25 mean generated"

#update dataset
#os.system('python ./datacode/pm25_dataset_maker0518.py')
os.system('python ./datacode/pm25_dataset_maker0605.py')
print "dataset generated"

#update model
#os.system('python ./model/pm25_mlp.py')
os.system('python ./model/pm25_mlp0605.py')
print "model trained"