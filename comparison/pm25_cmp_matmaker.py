# -*- coding: utf-8 -*-
#实现长期的预测值与真实值监测对比，
#将记录的数据构成数据矩阵，按如下格式
'''
 考察时间   当前真实值 预测后1小时值 预测后2小时值  ...    预测后24小时
[2015052914, 17       , 10(预测15点), 29(预测16点), ...    , ...    , ]
[2015052915, 9        , 29          , 35          , ...    , ...    , ]
[2015052916，30       , 35          , 33          , ...    , ...    , ]
[...       , ...      ,                    ...                        ]
[...       , ...      ,                    ...                        ]
[...       , ...      ,                    ...                        ]
shape:(n,26)
'''
#这样就可以方便的在数据矩阵中按需要取值，进行准确度比对

import os
import cPickle, gzip
import numpy as np
import requests,time

datadir='/ldata/pm25data/pm25compare/Pm25ComparingMat.pkl.gz'
txtdir='/ldata/pm25data/pm25compare/Pm25ComparingMat.txt'
  
#生成一组数据
def generate_line(lon,lat):
    line=[]
    #get time
    line.append(int(time.strftime('%Y%m%d%H')))
    #get pm25 actual data
    r=requests.get('http://dev2.rain.swarma.net/fcgi-bin/v1/pm25.py?lonlat='+str(lon)+','+str(lat))
    line.append(r.json()["pm_25"])
    #get pm25 predict data
    r=requests.get('http://api.caiyunapp.com/v2/pm25/'+str(lon)+','+str(lat))
    line=line+r.json()["pm_25"]
    return np.array(line)
   
#定时触发，数据生成组合
#拿到原有数据
if os.path.exists(datadir) and os.path.getsize(datadir)>0:
    f = gzip.open(datadir)
    pm25_mat=cPickle.load(f)
    pm25_mat=np.vstack([pm25_mat,generate_line(lon=116.3883,lat=39.3289)])
else:
    pm25_mat=generate_line(lon=116.3883,lat=39.3289)
        
#存储        
save_file = gzip.open(datadir, 'wb')
cPickle.dump(pm25_mat, save_file, -1)
save_file.close()
np.savetxt(txtdir,pm25_mat, fmt='%.2f')
