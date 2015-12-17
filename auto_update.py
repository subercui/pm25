# -*- coding: utf-8 -*-
#几个bash命令，以及调用的.py文件内的bash命令，访问顺序是什么样的
#用于每日调用，更新model以及依赖文件

import sys
import os
from datetime import datetime

today=datetime.today()
print "begin at "+today.strftime('%Y-%m-%d %H:%M')

#prepare data
#gfs
os.system('python /home/suber/projects/pm25/datacode/download_gfs.py')
print "gfs downloading finished"
gfsdir='/ldata/pm25data/gfs/'
os.system('find '+gfsdir+' -type f -size 0 -exec rm -f {} \;')
print "empty gfs files deleted"
#pm25 mean
os.system('python /home/suber/projects/pm25/datacode/pm25_mean.py')
print "pm25 mean generated"

#update dataset
#os.system('python /home/suber/projects/pm25/datacode/pm25_dataset_maker0605.py')
#print "48h dataset generated"
os.system('python /home/suber/projects/RNN_pm25/datacode/RNNPm25DataMaker.py')
print "RNN dataset generated"
if not os.path.exists('/ldata/pm25data/pm25dataset/RNNPm25Dataset'+today.strftime('%Y%m%d')+'_t100p100shuffled.pkl.gz'):
        os.system('echo "Pm25 RNN Dataset file generating error!" | mail -s "caiyun pm25 alarm" "subercui@sina.com"')

#update model
os.system('python /home/suber/projects/RNN_pm25/model/Pm25RNN_MINIBATCH.py')
print "RNN model trained"

#rsync
#os.system('rsync -av /ldata/pm25data/pm25model/MlpModel'+today.strftime('%Y%m%d')+'.pkl.gz caiyun@10.144.246.254:/ldata/pm25data/pm25model/')
os.system('rsync -av /ldata/pm25data/pm25model/RNNModel'+today.strftime('%Y%m%d')+'.pkl.gz caiyun@10.144.246.254:/ldata/pm25data/pm25model/')
os.system('rsync -avr /ldata/pm25data/pm25mean/mean'+today.strftime('%Y%m%d')+' caiyun@10.144.246.254:/ldata/pm25data/pm25mean/')
os.system('rsync -av /ldata/pm25data/pm25model/RNNModel'+today.strftime('%Y%m%d')+'.pkl.gz caiyun@inner.wrapper2.api.caiyunapp.com:/ldata/pm25data/pm25model/')
os.system('rsync -avr /ldata/pm25data/pm25mean/mean'+today.strftime('%Y%m%d')+' caiyun@inner.wrapper2.api.caiyunapp.com:/ldata/pm25data/pm25mean/')
print "rsync finished"

#check
if not(os.path.exists('/ldata/pm25data/pm25model/RNNModel'+today.strftime('%Y%m%d')+'.pkl.gz') and os.path.exists('/ldata/pm25data/pm25mean/mean'+today.strftime('%Y%m%d'))):
    os.system('echo "Pm25 file generating error!" | mail -s "caiyun pm25 alarm" "subercui@sina.com"')

if today.day==20:
    monthago=today.replace(month=today.month-1)
    os.system('rm /ldata/pm25data/pm25dataset/120hPm25Dataset'+monthago.strftime('%Y%m')+'*')
    os.system('rm /ldata/pm25data/pm25dataset/RNNPm25Dataset'+monthago.strftime('%Y%m')+'*')
