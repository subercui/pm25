# -*- coding: utf-8 -*-
#预测模型，presict模式
import numpy as np
import gzip
import cPickle, requests, time, datetime
from pyproj import Proj

import caiyun.platform.config as cfg

cfg = cfg.load_config("pm25.cfg")

now = time.time()
yesterday = datetime.datetime.fromtimestamp(now - now % 3600 - 3600 * 24).strftime('%Y%m%d')

pm25mean_path=cfg.get('pm25', 'mean', raw=True) % {'yesterday': yesterday}
pm25mean=[None]*24
for h in range(24):#取出各个小时的pm25mean备用
    f = open(pm25mean_path+'meanfor'+str(h)+'.pkl', 'rb')
    pm25mean[h]=cPickle.load(f)
    f.close()

#load mlp48 model
mlp48_model_path=cfg.get('pm25', 'mlp48', raw=True) % {'yesterday': yesterday}
f = gzip.open(mlp48_model_path, 'rb')
hidden_w48= cPickle.load(f).get_value()
hidden_b48= cPickle.load(f).get_value()
out_w48= cPickle.load(f).get_value()
out_b48= cPickle.load(f).get_value()
para_min48= cPickle.load(f)
para_max48= cPickle.load(f)
f.close()

#load mlp120 model
mlp120_model_path=cfg.get('pm25', 'mlp48', raw=True) % {'yesterday': yesterday}
f = gzip.open(mlp120_model_path, 'rb')
hidden_w120= cPickle.load(f).get_value()
hidden_b120= cPickle.load(f).get_value()
out_w120= cPickle.load(f).get_value()
out_b120= cPickle.load(f).get_value()
para_min120= cPickle.load(f)
para_max120= cPickle.load(f)
f.close()


def mlp_predict48(inputs):
    #inputs scaling
    #风速绝对化，实验试试看是否提高预测精度
    for i in range(24):
        wind=np.sqrt(inputs[(i*6+2)]**2+inputs[(i*6+3)]**2)
        drct=inputs[(i*6+2)]/inputs[(i*6+3)]
        inputs[(i*6+2)]=wind
        #inputs[(i*6+3)]=drct
    #风速绝对值化
    inputs[0:144]=np.abs(inputs[0:144])
    inputs[0:144]=(inputs[0:144]-para_min48[0:144])/(para_max48[0:144]-para_min48[0:144])
    inputs[144:168]=inputs[144:168]/100

    #predict
    hidden_out48=np.tanh(np.dot(inputs,hidden_w48)+hidden_b48)
    output=np.dot(hidden_out48,out_w48)+out_b48

    #output scaling back
    output=output*100
    return output
    
def mlp_predict120(inputs,t_predict):
    #inputs scaling
    #风速绝对化，实验试试看是否提高预测精度
    for i in range(8*(t_predict/24+1)):
        wind=np.sqrt(inputs[(i*6+2)]**2+inputs[(i*6+3)]**2)
        drct=inputs[(i*6+2)]/inputs[(i*6+3)]
        inputs[(i*6+2)]=wind
        #inputs[(i*6+3)]=drct
    #风速绝对值化
    inputs[0:2*t_predict+48]=np.abs(inputs[0:2*t_predict+48])
    inputs[0:2*t_predict+48]=(inputs[0:2*t_predict+48]-para_min120[0:2*t_predict+48])/(para_max120[0:2*t_predict+48]-para_min120[0:2*t_predict+48])
    inputs[2*t_predict+48:]=inputs[2*t_predict+48:]/100

    #predict
    hidden_out120=np.tanh(np.dot(inputs,hidden_w120)+hidden_b120)
    output=np.dot(hidden_out120,out_w120)+out_b120

    #output scaling back
    output=output*100
    return output


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


def predictor48(lon,lat):
    #paras
    pos=lonlat2mercator(lon,lat)#在中国地图中的坐标
    hour=time.localtime().tm_hour#当前小时
    start=time.time()
    start=int(start-start%3600-24*3600)#24小时之前的时刻
    #get gfs data
    r=requests.get('http://api.dev2.caiyunapp.com/?lonlat='+str(lon)+','+str(lat)+'&time='+str(start)+',72')
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
    inputs=np.zeros(168)
    for i in range(0,72,3):#第i小时,注意根据现在的输入格式，每隔3小时取一个tmp值
        inputs[0+i*2]=tmp[i]+273.0#绝对温度
        inputs[1+i*2]=rh[i]
        inputs[2+i*2]=ugrd[i]
        inputs[3+i*2]=vgrd[i]
        inputs[4+i*2]=prate[i]
        inputs[5+i*2]=tcdc[i]

    for i in range(24):#生成后24维的pm25数据，时间从之前24小时到当前
        inputs[144+i]=pm25[23-i]+80.0-pm25mean[(hour-23+i)%24][pos[0],pos[1]]

    #predict
    #predict=linear_predict(inputs)
    predict=mlp_predict48(inputs)
    for i in range(48):
        predict[i]=predict[i]+pm25mean[(i+1+hour)%24][pos[0],pos[1]]-80
        #减80是因为，原始数据来自中国地图pm25数据，是在真实值上增加了80的
    #print predict

    return {
            "model": "MLP",
            "length": "48h",
            "pm_25": predict.tolist()
            }


def predict_online(provider):
    if 17 < provider.lat < 72 and 54 < provider.lng < 135:
        pos = lonlat2mercator(provider.lng, provider.lat) #在中国地图中的坐标

        #generate inputs
        inputs = np.zeros(168)
        #第i小时,注意根据现在的输入格式，每隔3小时取一个tmp值
        for i in range(0,72,3):
            inputs[0+i*2] = provider.tmp[i] + 273.0 #绝对温度
            inputs[1+i*2] = provider.rh[i]
            inputs[2+i*2] = provider.ugrd[i]
            inputs[3+i*2] = provider.vgrd[i]
            inputs[4+i*2] = provider.prate[i]
            inputs[5+i*2] = provider.tcdc[i]

        hour = time.localtime().tm_hour #当前小时
        for i in range(24): #生成后24维的pm25数据，时间从之前24小时到当前
            inputs[144 + i] = provider.pm25data[23 - i] + 80.0 - pm25mean[(hour-23+i)%24][pos[0], pos[1]]

        predict = mlp_predict48(inputs)
        for i in range(48):
            #减80是因为，原始数据来自中国地图pm25数据，是在真实值上增加了80的
            predict[i] = predict[i] + pm25mean[(i + 1 + hour) % 24][pos[0], pos[1]] - 80
        predict = np.concatenate(([provider.pm25data[0]], predict))[:48]

        return predict
    else:
        return []

def predict_online120h(provider,t_predict=120):
    if 17 < provider.lat < 72 and 54 < provider.lng < 135:
        pos = lonlat2mercator(provider.lng, provider.lat) #在中国地图中的坐标

        #generate inputs
        inputs = np.zeros(t_predict*2+48+24)
        #第i小时,注意根据现在的输入格式，每隔3小时取一个tmp值
        for i in range(0,24+t_predict,3):
            inputs[0+i*2] = provider.tmp[i] + 273.0 #绝对温度
            inputs[1+i*2] = provider.rh[i]
            inputs[2+i*2] = provider.ugrd[i]
            inputs[3+i*2] = provider.vgrd[i]
            inputs[4+i*2] = provider.prate[i]
            inputs[5+i*2] = provider.tcdc[i]

        hour = time.localtime().tm_hour #当前小时
        for i in range(24): #生成后24维的pm25数据，时间从之前24小时到当前
            inputs[t_predict*2+48 + i] = provider.pm25data[23 - i] + 80.0 - pm25mean[(hour-23+i)%24][pos[0], pos[1]]

        predict = mlp_predict120(inputs,t_predict)
        for i in range(t_predict):
            #减80是因为，原始数据来自中国地图pm25数据，是在真实值上增加了80的
            predict[i] = predict[i] + pm25mean[(i + 1 + hour) % 24][pos[0], pos[1]] - 80
        predict = np.concatenate(([provider.pm25data[0]], predict))[:t_predict]

        return predict
    else:
        return []

def aqi_online(provider):
    return provider.pm25predict + np.array(provider.tmp[24:144])
