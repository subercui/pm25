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
   
#load data
if os.path.exists(datadir) and os.path.getsize(datadir)>0:
    f = gzip.open(datadir)
    pm25_mat=cPickle.load(f)
else:
    raise Exception,'No such data file: '+datadir
                       
                
#数据分析
#1.全数据逐小时准确性分析：
error=[]
for h in range(1,25):#针对之后第h小时的预测值的准确性
    error.append(np.mean(np.abs(pm25_mat[:-h,h+1]-pm25_mat[h:,1])))
print error
