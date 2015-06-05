#-*- coding: utf-8 -*-
#生成pm25 dataset向量数据集，并存入pkl文件
#input的格式，每一行是一个trainning example；example有120维前96维是以预测点为
#中心的前后两天的天气6要素（6×16），后24维是预测点之前一天每小时的相对pm25数据（24）
#output的格式，每一行是一个trainning example的预测结果,24维表示预测点之后一天每
#小时的pm2.5的变化量

#'Pm25Dataset0521_timerange0401-0510'是第一步，加入了时区变换的
import os
from glob import glob
import cPickle, gzip
import numpy as np
import datetime 
#from profilehooks import profile

gfsdir='/ldata/pm25data/gfsinmercator/'
pm25dir='/mnt/storm/nowcasting/pm25/'
pm25meandir='/ldata/pm25data/pm25mean/mean0515/'
savedir='/ldata/pm25data/pm25dataset/'

class Pm25Dataset(object):
    '''
    给出预测点的位置和数据集的时间范围，利用gfs和pm25原始
    数据文件，构建这一时间和地点内的pm25 dataset
    '''
    def __init__(self,cord_x=np.hstack((np.array([230,280,320,380,300,279,255,264,285,269]),np.random.randint(220,310,90))),cord_y=np.hstack((np.array([480,470,435,375,465,476,485,460,455,485]),np.random.randint(430,490,90))),start='2015040108',stop='2015051008',d_in=120,d_out=24):
        '''Initialize the parameters
        
        :cord_x: x coordinate in mercator coordinate, scalar or vector like
        :cord_y: y coordinate in mercator coordinate, scalar or vector like
        :start: time the dataset forecast point starts, e.g.'2015022800'
                better be 3 hours counted(00,03,06), since the gfs data
                are divided into 3 hours. Beijing time
        :stop: time the dataset forecast point stops, e.g.'2015022818' 
               better be 3 hours counted(00,03,06), since the gfs data
               are divided into 3 hours.
        :d_in: dimention of input
        :d_out: dimention of output.
        '''
        self.cord_x=cord_x
        self.cord_y=cord_y
        self.d_in=d_in
        self.d_out=d_out
        self.starttime=datetime.datetime(int(start[0:4]),int(start[4:6]),int(start[6:8]),int(start[8:10]))
        self.stoptime=datetime.datetime(int(stop[0:4]),int(stop[4:6]),int(stop[6:8]),int(stop[8:10]))
        self.n_points=len(self.cord_x)#从地图上取了n_points个试验点
        self.n_perpoint=int((self.stoptime-self.starttime).days*8+(self.stoptime-self.starttime).seconds/10800+1)
        self.n_exp=self.n_points * self.n_perpoint#总样本数
        #n_exp按照每隔3小时一组training example来计算
        
        self.input_data=self.generateinput()#这里新版本input包括了之后的target24维
        
    def generateinput(self):
        '''generate input vector'''
        inputs=np.zeros((self.n_exp,self.d_in+self.d_out))
        '''gfs,96 dimentions'''
        for h in range(-24,24,3):#在starttime前后两天的时间点,这个循环填上第一个example的前96个数据
            name=(self.starttime+datetime.timedelta(hours=h)-datetime.timedelta(hours=8)).strftime('%Y%m%d%H')#做时区变换，转回GMT
            cnt=0
            for entry in ['tmp','rh','ugrd','vgrd','prate','tcdc']:#填6个数据
                if os.path.exists(gfsdir+name+entry+'.pkl.gz'):#判断文件是否存在
                    f = gzip.open(gfsdir+name+entry+'.pkl.gz', 'rb')
                    temp=cPickle.load(f)
                    f.close()
                    for k in range(self.n_points):
                        inputs[(0+k*self.n_perpoint,(h+24)*2+cnt)]=temp[(self.cord_x[k],self.cord_y[k])]
                    #(h+24)*2+cnt是用来找对应的格位置，（h+24）*2是对应小时的6格开始位置，再加上cnt作为偏置
                else:#用3小时之前的替换
                    for k in range(self.n_points):
                        print(gfsdir+name+entry+'.pkl.gz')
                        inputs[(0+k*self.n_perpoint,(h+24)*2+cnt)]=inputs[(0+k*self.n_perpoint,(h+24)*2+cnt-6)]                
                cnt=cnt+1
   
        for i in range(1,self.n_perpoint):#填上矩阵中，剩余trainning example的数据
            current=self.starttime+datetime.timedelta(hours=3*i)-datetime.timedelta(hours=8)#做时区变换，转回GMT
            #对于当前current所指的这一行，前90维的数据可以从上一行获得
            for k in range(self.n_points):
                inputs[i+k*self.n_perpoint,0:90]=inputs[i+k*self.n_perpoint-1,6:96]
            #对于当前current所指的这一行，最后小时的六个数据需要以下重新读文件获得
            name=(current+datetime.timedelta(hours=21)).strftime('%Y%m%d%H')
            cnt=0
            for entry in ['tmp','rh','ugrd','vgrd','prate','tcdc']:#填6个数据
                if os.path.exists(gfsdir+name+entry+'.pkl.gz'):#判断文件是否存在
                    f = gzip.open(gfsdir+name+entry+'.pkl.gz', 'rb')
                    temp=cPickle.load(f)
                    f.close()
                    for k in range(self.n_points):
                        inputs[(i+k*self.n_perpoint,90+cnt)]=temp[(self.cord_x[k],self.cord_y[k])]
                    #(h+24)*2+cnt是用来找对应的格位置，（h+24）*2是对应小时的6格开始位置，再加上cnt作为偏置
                else:#用左边即前3个小时的数据填充（暂定可能的补偿方法）
                    for k in range(self.n_points):
                        inputs[(i+k*self.n_perpoint,90+cnt)]=inputs[(i+k*self.n_perpoint,84+cnt)]                
                cnt=cnt+1
                
        '''pm25,24 dimentions'''
        pm25mean=[None]*24
        for h in range(24):#取出各个小时的pm25mean备用
            f = open(pm25meandir+'meanfor'+str(h)+'.pkl', 'rb')
            pm25mean[h]=cPickle.load(f)
            f.close()
        #生成第一行
        for h in range(48):#在starttime前后两天的时间点,这个循环填上第一个example的后48个数据
            name=(self.starttime+datetime.timedelta(hours=h-23)).strftime('%Y%m%d%H')
            cnt=0
            if os.path.exists(pm25dir+name+'.pkl.gz'):#判断文件是否存在
                f = gzip.open(pm25dir+name+'.pkl.gz', 'rb')
                temp=cPickle.load(f)
                f.close()
                for k in range(self.n_points):
                    inputs[(0+k*self.n_perpoint,96+h)]=temp[(self.cord_x[k],self.cord_y[k])]-pm25mean[int(name[8:10])][self.cord_x[k],self.cord_y[k]]
                #(h+24)*2+cnt是用来找对应的格位置，（h+24）*2是对应小时的6格开始位置，再加上cnt作为偏置
            else:#用3小时之前的替换
                for k in range(self.n_points):
                    inputs[(0+k*self.n_perpoint,96+h)]=inputs[(0+k*self.n_perpoint,96+h)]                
            cnt=cnt+1
            
        for i in range(1,self.n_perpoint):#for 全部行,生成后24维数据
            current=self.starttime+datetime.timedelta(hours=3*i)
            #对于当前current所指的这一行，前90维的数据可以从上一行获得
            for k in range(self.n_points):
                inputs[i+k*self.n_perpoint,96:96+45]=inputs[i+k*self.n_perpoint-1,96+3:96+48]
            for h in range(3):#最后新的3位数据要读文件
                #每一行从左向右的时间顺序,这里直接生成48维数据，前24维作为input（包括当前时刻）
                #后24维作为output,从当前时刻之后的一小时开始
                #name=(current-datetime.timedelta(hours=h)).strftime('%Y%m%d%H')
                name=(current+datetime.timedelta(hours=h+22)).strftime('%Y%m%d%H')#未来22，23，24小时
                if os.path.exists(pm25dir+name+'.pkl.gz') and os.path.getsize(pm25dir+name+'.pkl.gz')>0:#判断文件是否存在
                    f = gzip.open(pm25dir+name+'.pkl.gz', 'rb')
                    print(name+'.pkl.gz')
                    temp=cPickle.load(f)
                    f.close()
                    for k in range(self.n_points):
                        inputs[i+k*self.n_perpoint,141+h]=temp[self.cord_x[k],self.cord_y[k]]-pm25mean[int(name[8:10])][self.cord_x[k],self.cord_y[k]]
                else:#用右边后一个小时的数据填充（暂定可能的补偿方法）
                    for k in range(self.n_points):
                        inputs[i+k*self.n_perpoint,141+h]=inputs[i+k*self.n_perpoint,141+h-1]
        
        '''send out'''
        return inputs
                                 
    def save():
        '''save files'''
        
#从时间计算推算前后两天的时间节点
def draw_period(time):
    period=[None]*49#period[0]代表起始时间，period[1]代表截止时间
    year=int(time[0:4])
    month=int(time[4:6])
    date=int(time[6:8])
    hour=int(time[8:10])
    date=datetime.datetime(year,month,date,hour)-datetime.timedelta(days=1)
    for i in range(49):
        period[i]=date.strftime('%Y%m%d%H')
        date=date+datetime.timedelta(hours=1)
    return period
    
def search_file(pattern, search_path=os.environ['PATH'], pathsep=os.pathsep):
    matchs=[]
    for path in search_path.split(os.pathsep):
        for match in glob(os.path.join(path, pattern)):
            matchs.append(match)
    return matchs
            
def filesinroot(dir,wildcard,recursion):
    matchs=[]
    exts=wildcard.split()
    for root,subdirs,files in os.walk(dir):
        for name in files:
            for ext in exts:
                if(name.endswith(ext)):
                    matchs.append(name)
                    break
        if(not recursion):
            break
    return matchs
    
def savefile(m,path):
    save_file = gzip.open(path, 'wb')  # this will overwrite current contents
    cPickle.dump(m, save_file, -1)  # the -1 is for HIGHEST_PROTOCOL
    save_file.close()
    
if __name__ == '__main__':
    obj=Pm25Dataset()
    savefile(obj.input_data,savedir+'Pm25Dataset0521_timerange0401-0510.pkl.gz')
    np.savetxt(savedir+"Pm25Dataset0521_timerange0401-0510.txt", obj.input_data, fmt='%.2f')
    np.random.shuffle(obj.input_data)
    savefile(obj.input_data,savedir+'Pm25Dataset0521_timerange0401-0510shuffled.pkl.gz')
