# -*- coding: utf-8 -*-
#几个bash命令，以及调用的.py文件内的bash命令，访问顺序是什么样的
#用于每日调用，更新model以及依赖文件

import sys
import os
from datetime import datetime

today=datetime.today()
print "begin at "+today.strftime('%Y-%m-%d %H:%M')

#update dataset
os.system('python /home/suber/projects/pm25/datacode/pm25_dataset_maker120h.py')
print "dataset generated"

#update model
os.system('python /home/suber/projects/pm25/model/pm25_mlp120h.py')
print "model trained"

'''
#rsync
os.system('rsync -av /ldata/pm25data/pm25model/MlpModel'+today.strftime('%Y%m%d')+'.pkl.gz caiyun@10.144.246.254:/ldata/pm25data/pm25model/')
os.system('rsync -avr /ldata/pm25data/pm25mean/mean'+today.strftime('%Y%m%d')+' caiyun@10.144.246.254:/ldata/pm25data/pm25mean/')
print "rsync finished"
'''
