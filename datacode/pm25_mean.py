# -*- coding: utf-8 -*-
#for gif
#import pandas as pd
#import pymc as mc
import matplotlib.pyplot as plt
from matplotlib import animation

#
import os
import cPickle, gzip, numpy
import matplotlib
from pylab import*
from glob import glob #用到了这个模块
from datetime import *

def search_file(pattern, search_path=os.environ['PATH'], pathsep=os.pathsep):
    for path in search_path.split(os.pathsep):
        for match in glob(os.path.join(path, pattern)):
            yield match

def generate_matchs(i,pm25path):
    matchs=[]
    p=datetime.today()
    p=p.replace(hour=i)
    for d in range(45):#设置求平均的时间长度45days
        p=p-timedelta(days=1)
        match=p.strftime('%Y%m%d%H')
        if int(match)>2015061324:
            match=pm25path+match[0:8]+'/'+match+'.pkl.gz'
        else:
            match=pm25path+match+'.pkl.gz'
        matchs.append(match)
    return matchs

def form_meandata(matchs):
    sumdata = 0#sumdata 的数据类型至少是int，保证不溢出
    num=0
    for match in matchs:
        if os.path.exists(match) and os.path.getsize(match)>0:
            num=num+1
            print match
            f = gzip.open(match, 'rb')
            temp = cPickle.load(f)
            sumdata = sumdata+temp
    mean = sumdata//num
    return mean
    
def savefile(m,path):
    save_file = open(path, 'wb')  # this will overwrite current contents
    cPickle.dump(m, save_file, -1)  # the -1 is for HIGHEST_PROTOCOL
    save_file.close()
    
def showimage(data,title,path):
    cmap = matplotlib.cm.jet #选择colorbar
    #设定每个图的colormap和colorbar所表示范围是一样的，即归一化  
    norm = matplotlib.colors.Normalize(vmin=0, vmax=200)
    im=imshow(data,cmap=cmap,norm=norm)
    plt.colorbar(im) #显示图例
    plt.title(title)
    plt.show() #显示图片
    #savefig(path)
    plt.close() 
        
if __name__ == '__main__':
    searchday=20150315
    for i in range(24):#从0：00开始读到第i点
        #matchs = list(search_file('20150[56]*'+str('%002d'%(i))+'.pkl.gz', search_path='/mnt/storm/nowcasting/pm25/'))#4月和5月的
        matchs=generate_matchs(i,pm25path='/mnt/storm/nowcasting/pm25/')
        print '%d match' % len(matchs)
        #for match in matchs:
        #    print match
        mean=form_meandata(matchs)
        #showimage(mean,title='pm2.5 at '+str(i)+':00',path='/ldata/pm25data/pm25mean/mean0515'+str(i)+'.jpg')
        path='/ldata/pm25data/pm25mean/mean'+datetime.today().strftime('%Y%m%d')
        if not os.path.isdir(path):
            os.mkdir(path)
        savefile(mean,path=path+'/'+'meanfor'+str(i)+'.pkl')
