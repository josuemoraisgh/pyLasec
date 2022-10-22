import io
import time
import asyncio
import matplotlib.pyplot as plt
import numpy as np
import ipywidgets as widgets
import collections as clt
from multiprocessing import Process
from IPython.display import display, HTML, Javascript
try:
  from google.colab.output import eval_js
except:
  from js2py import eval_js
from base64 import b64decode, b64encode

class SerialComm():
  itemwrite = 0
  itemOld = 0
  itemOldOld = 0
  serialBuf = "" 
  serialBufOld = ""
         
  def __init__(self, socketPort = 4466, ip='127.0.0.1'):
    self.ip, self.socketPort = ip, socketPort

  def __del__(self):
    self.exitSerial()

  def commSerialRegister(self, ip, socketPort):
    display(Javascript("""
      async function commSerial(command = 'read', data = {}, socketPort = '"""+str(socketPort)+"""', ip ='"""+ip+"""'){
        var response = await fetch("http://"+ip+":"+socketPort+"/"+command, {
          method: 'POST',
          mode: 'cors', 
          headers: {'Content-Type' : 'application/json', 'Accept' : 'application/json'},
          body: JSON.stringify(data)
          }
        );
        var data = await response.json();
        return(data);
      }
    """))

  def openSerial(self, serialPort="COM7", baudrate=9600, bytesize=8, parity=0, stopbits=1):
    try:
      eval_js("""window.location.href = 'serialcommproto:"""+str(self.socketPort)+"""'""")
      time.sleep(3)   
    finally:
      try:
        self.commSerialRegister(self.ip,self.socketPort)
        eval_js("commSerial('open',{'port':'"+serialPort+"','baudrate':"+str(baudrate)+",'bytesize':"+str(bytesize)+",'parity':"+str(parity)+",'stopbits':"+str(stopbits)+"})")
      except:
        return False
      else:
        return True

  def exitSerial(self):
    try:
      self.commSerialRegister(self.ip,self.socketPort)    
      eval_js("commSerial('exit')")
    except:
      pass

  def closeSerial(self):
    self.commSerialRegister(self.ip,self.socketPort)    
    eval_js("commSerial('close')")

  def readSerial(self):
    self.commSerialRegister(self.ip,self.socketPort)   
    data = eval_js("commSerial()")
    if data['status'] == 'SUCESS' and data['data'] != []: self.serialBuf = self.serialBufOld + ''.join(chr(int(i)) for i in data['data'] if int(i)) # i.isdigit())
    else: self.serialBuf = self.serialBufOld
    if self.serialBuf != "":
      self.serialBufOld = self.serialBuf[self.serialBuf.rfind("\n")+1:]#Extrai do ultimo '\n' ate o fim sem o '\n'.
      self.serialBuf = self.serialBuf[:(-1*len(self.serialBufOld))-1]#Extrai do Inicio ate o ultimo '\n' sem ele.
      return(self.filterSerial([int(item.replace('\r','')) for item in self.serialBuf.split("\n") if item.replace('\r','') != '']))
    return([])
  
  def filterSerial(self, data):
    result = []
    for item in data:
      if not((item == 0 and self.itemOld == self.itemwrite) or (item == self.itemwrite and self.itemOld != self.itemwrite)): 
        if (item != 0 and self.itemOld == self.itemwrite):
          result.append(self.itemOld)
        result.append(item)
      self.itemOld,self.itemOldOld = item, self.itemOld
    return(result)

  def writeSerial(self,data):
    itemwrite = data
    self.commSerialRegister(self.ip,self.socketPort)    
    writeBuffer = [ord(x) for x in str(data)+'\r\n']
    return(eval_js("commSerial('write',{'write':"+str(writeBuffer)+"})"))

class SerialChart():

  def __init__(self, maxSizeWin=9000, timeStep=0.001):
    self.timeStep, self.time, self.readValue, self.writeValue = timeStep, [x*timeStep for x in range(maxSizeWin)], clt.deque(iterable=np.zeros(maxSizeWin),maxlen=maxSizeWin), clt.deque(iterable=np.zeros(maxSizeWin),maxlen=maxSizeWin) # start collections with zeros
    #plt.ion()
    self.fig, self.ax = plt.subplots(figsize=(18,8), facecolor='#DEDEDE') # define and adjust figure
    self.fig.suptitle('Leitura e Escrita na porta Serial', fontsize=16)
    self.lines = self.ax.plot(self.time, self.readValue, 'r',self.time, self.writeValue,'b')
    self.lines[0].set_label('Serial Read')
    self.lines[1].set_label('Serial Write')
    plt.xlabel('Tempo')
    plt.ylabel('Amplitude')
    self.ax.legend()
    plt.grid()
    plt.close()

  def redraw(self,writeBuffer,readBuffer,multMinX,multMaxX,multMinY,multMaxY):
    if readBuffer != []:
      for i in range(len(readBuffer)):
        self.readValue.append(readBuffer[i])
        self.writeValue.append(writeBuffer)
      self.time = [x+self.timeStep*len(readBuffer) for x in self.time]
      self.lines[0].set_data(self.time,self.readValue)
      self.lines[1].set_data(self.time,self.writeValue)
    maxX, minX = max(self.time), min(self.time)
    self.ax.set_xlim(((maxX-minX)*multMinX/100)+minX, ((maxX-minX)*multMaxX/100)+minX)
    minY, maxY = min([min(self.readValue), min(self.writeValue)]), max([max(self.readValue),max(self.writeValue)])
    self.ax.set_ylim(((maxY-minY)*multMinY/100)+minY, ((maxY-minY)*multMaxY/100)+minY)
    
class SerialPlot():
  box_layout1 = widgets.Layout(flex_flow='row', display='flex', justify_content = 'center')
  box_layout2 = widgets.Layout(flex_flow='col', display='flex', justify_content = 'center')
  sliderPosx = widgets.FloatRangeSlider(value=[-1.0, 101.0],min=-50.0,max=150.0,step=0.1,description='time:',disabled=False,continuous_update=False,orientation='horizontal',readout=True,readout_format='.1f',layout=widgets.Layout(width='10000px', height='auto'))
  sliderPosy = widgets.FloatRangeSlider(value=[-1.0, 101.0],min=-50.0,max=150.0,step=0.1,description='ampl.:',disabled=False,continuous_update=False,orientation='horizontal',readout=True,readout_format='.1f',layout=widgets.Layout(width='10000px', height='auto'))
  valorSend = widgets.IntText(value=0,description= "Serial Write: ")
  button = widgets.Button(description='Updating!!',tooltip='Continua a animação do gráfico')
  buttonResume = widgets.Button(description='Resume:',tooltip='Continua a animação do gráfico')
  buttonPause = widgets.Button(description='Pause:',tooltip='Pausa a animação do gráfico')
  buttonStop = widgets.Button(description='Stop:',tooltip='Para a animação do gráfico')
  out = widgets.Output()

  def __init__(self, socketPort = 4466, serialPort="COM7", baudrate=9600, bytesize=8, parity=0, stopbits=1, ip='127.0.0.1',maxSizeWin=9000, timeStep=0.001):
    self.serialPort, self.baudrate, self.bytesize, self.parity, self.stopbits = serialPort, baudrate, bytesize, parity, stopbits
    self.valorSend.observe(self.printSerial, names='value')
    self.sliderPosx.observe(self.sliderChange, names='value')
    self.sliderPosy.observe(self.sliderChange, names='value')
    self.buttonPause.on_click(self.pause)
    self.buttonStop.on_click(self.stop)
    self.buttonResume.on_click(self.resume)
    self.button.on_click(self.redraw)
    self.a=widgets.HTML(value="graphic here")
    self.out.append_display_data(widgets.Box(children=[self.button, self.buttonResume, self.buttonPause, self.valorSend, self.buttonStop],layout=self.box_layout1))
    self.out.append_display_data(widgets.Box(children=[self.sliderPosx, self.sliderPosy],layout=self.box_layout1))
    self.out.append_display_data(widgets.Box(children=[self.a],layout=self.box_layout2))
    self.serialcomm = SerialComm(socketPort, ip)
    self.serialchart = SerialChart(maxSizeWin, timeStep)
    if self.serialcomm.openSerial(self.serialPort, self.baudrate, self.bytesize, self.parity, self.stopbits) == True:
      display(self.out)
      self.resume({})
    else:
      self.a.value="ERROR: SOCKET PORT NOT OPEN!!!"

  def __del__(self):
    del self.serialplot
    del self.serialcomm

  def pltToImg(self, plotFig):
    bytesIO = io.BytesIO() 
    plotFig.savefig(bytesIO, format='png', bbox_inches="tight")
    str = b64encode(bytesIO.getvalue()).decode("utf-8").replace("\n", "")
    return '<img align="middle" src="data:image/png;base64,'+str+'"></br>'
  
  def sliderChange(self,b):
    if self.isStop == True or self.run == False:
      self.serialchart.redraw(self.valorSend.value,[],self.sliderPosx.value[0],self.sliderPosx.value[1],self.sliderPosy.value[0],self.sliderPosy.value[1])
      self.a.value=(self.pltToImg(self.serialplot.fig))

  def printSerial(self,b):
    self.serialcomm.writeSerial(self.valorSend.value)

  def stop(self,b):
    self.pause({})
    self.isStop = True
    time.sleep(3)
    self.buttonResume.disabled = True
    self.serialcomm.exitSerial()

  def redraw(self,b):
    if self.isStop == False:
      self.serialchart.redraw(self.valorSend.value,self.serialcomm.readSerial(),self.sliderPosx.value[0],self.sliderPosx.value[1],self.sliderPosy.value[0],self.sliderPosy.value[1])
      if self.run == True:
        self.a.value=(self.pltToImg(self.serialchart.fig))
      eval_js("document.querySelector('#output-body button')?.click()")

  def resume(self,b):
    self.isStop = False
    self.run = True
    self.button.disabled = False
    self.valorSend.disabled = False
    self.buttonPause.disabled = False
    self.buttonResume.disabled = True
    self.redraw({})
  
  def pause(self,b):
    self.run = False
    self.button.disabled = True
    self.buttonPause.disabled = True
    self.valorSend.disabled = True
    self.buttonResume.disabled = False