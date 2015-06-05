# -*- coding: utf-8 -*-
#预测模型，presict模式
import numpy as np
import gzip
import cPickle,requests,time
from pyproj import Proj

linear_model_path='/ldata/pm25data/pm25model/LinearModel0515.pkl.gz'
pm25mean_path='/ldata/pm25data/pm25mean/mean0515/'

def linear_predict(inputs):
    #load model
    f = gzip.open(linear_model_path, 'rb')
    w= cPickle.load(f).get_value()
    b= cPickle.load(f).get_value()
    f.close()
    
    #predict
    output=np.dot(inputs,w)+b
    return output
    
def load_mean(path):
    pm25mean=[None]*24
    for h in range(24):#取出各个小时的pm25mean备用
        f = open(path+'meanfor'+str(h)+'.pkl', 'rb')
        pm25mean[h]=cPickle.load(f)
        f.close()
    return pm25mean
    
def lonlat2mercator(lon=116.3883,lat=39.3289):
    p = Proj('+proj=merc')

    radius=[17,72,54,135]
    res=10000
    longitude,latitude = p(lon,lat)
    latlng = np.array([latitude,longitude])
    y,x = np.round(np.array(p(radius[1],radius[0]))/res)
    y1,x1 = np.round(np.array(p(radius[3],radius[2]))/res)
    latlng = np.abs(np.round(latlng/res)-np.array([x1,y]))
    return latlng

if __name__ == '__main__':
    
    #paras
    lon=116.3883
    lat=39.9289
    pos=lonlat2mercator(lon,lat)#在中国地图中的坐标
    hour=time.localtime().tm_hour#当前小时
    start=int(time.time()-time.time()%3600-24*3600)#48小时之前的时刻
    #get gfs data
    r=requests.get('http://api.dev2.caiyunapp.com/?lonlat='+str(lon)+','+str(lat)+'&time='+str(start)+',48')
    tmp=r.json()["gfs_value"]["tmp"]#摄氏度
    prate=r.json()["gfs_value"]["prate"]
    tcdc=r.json()["gfs_value"]["tcdc"]
    ugrd=r.json()["gfs_value"]["ugrd"]
    vgrd=r.json()["gfs_value"]["vgrd"]
    rh=r.json()["gfs_value"]["rh"]
    
    #get pm25 data
    r=requests.get('http://dev2.rain.swarma.net/fcgi-bin/v1/pm25_history.py?lonlat='+str(lon)+','+str(lat))
    pm25=r.json()["pm_25"]#从当前倒推24小时,真实数据没有加80
    
    #generate inputs
    inputs=np.zeros(120)
    for i in range(0,48,3):#第i小时,注意根据现在的输入格式，每隔3小时取一个tmp值
        inputs[0+i*2]=tmp[i]+273.0#绝对温度
        inputs[1+i*2]=rh[i]
        inputs[2+i*2]=ugrd[i]
        inputs[3+i*2]=vgrd[i]
        inputs[4+i*2]=prate[i]
        inputs[5+i*2]=tcdc[i]
        
    pm25mean=load_mean(pm25mean_path)
    for i in range(24):#生成后24维的pm25数据，时间从之前24小时到当前
        inputs[96+i]=pm25[23-i]+80.0-pm25mean[(hour-23+i)%24][pos[0],pos[1]]
    
    #predict  
    predict=linear_predict(inputs)
    for i in range(24):
        predict[i]=predict[i]+pm25mean[(i+1+hour)%24][pos[0],pos[1]]-80
        #减80是因为，原始数据来自中国地图pm25数据，是在真实值上增加了80的
    print predict
