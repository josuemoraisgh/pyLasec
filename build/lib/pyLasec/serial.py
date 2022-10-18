import io
import asyncio
import ipywidgets
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

class commSerial():
  serialBuf = "" 
  serialBufOld = ""
         
  def __init__(self, socketPort = 4466, ip='127.0.0.1'):
    self.ip, self.socketPort = ip, socketPort

  def __del__(self):
    self.closeSerial()

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
    self.commSerialRegister(self.ip,self.socketPort)    
    eval_js("commSerial('open',{'port':'"+serialPort+"','baudrate':"+str(baudrate)+",'bytesize':"+str(bytesize)+",'parity':"+str(parity)+",'stopbits':"+str(stopbits)+"})")

  def flushSerial(self):
    self.commSerialRegister(self.ip,self.socketPort)    
    eval_js("commSerial('flush')")

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
      return([int(item.replace('\r','')) for item in self.serialBuf.split("\n") if item.replace('\r','') != ''])
    return([])

  def writeSerial(self,data):
    self.commSerialRegister(self.ip,self.socketPort)    
    writeBuffer = [ord(x) for x in str(data)+'\r\n']
    return(eval_js("commSerial('write',{'write':"+str(writeBuffer)+"})"))

class plotSerial():
  out = ipywidgets.Output()

  def __init__(self, maxSizeWin=9000, timeStep=0.001):
    self.timeStep, self.time, self.readValue, self.writeValue = timeStep, [x*timeStep for x in range(maxSizeWin)], clt.deque(iterable=np.zeros(maxSizeWin),maxlen=maxSizeWin), clt.deque(iterable=np.zeros(maxSizeWin),maxlen=maxSizeWin) # start collections with zeros
    #plt.ion()
    self.fig, self.ax = plt.subplots(figsize=(18,6), facecolor='#DEDEDE') # define and adjust figure
    self.fig.suptitle('Leitura e Escrita na porta Serial', fontsize=16)
    self.lines = self.ax.plot(self.time, self.readValue, 'r',self.time, self.writeValue,'b')
    self.lines[0].set_label('Serial Read')
    self.lines[1].set_label('Serial Write')
    plt.xlabel('Tempo')
    plt.ylabel('Amplitude')
    self.ax.legend()
    plt.grid()
    plt.close()

  def redraw(self,writeBuffer,readBuffer):
    if readBuffer != []:
      for i in range(len(readBuffer)):
        self.readValue.append(readBuffer[i])
        self.writeValue.append(writeBuffer)
      self.time = [x+self.timeStep*len(readBuffer) for x in self.time]
      self.lines[0].set_data(self.time,self.readValue)
      self.lines[1].set_data(self.time,self.writeValue)
      minx, maxx = min(self.time), max(self.time)
      self.ax.set_xlim(minx*0.99 if minx>=0 else minx*1.01, maxx*1.01 if maxx>=0 else maxx*0.99)
      miny, maxy = min([min(self.readValue), min(self.writeValue)]), max([max(self.readValue),max(self.writeValue)])
      self.ax.set_ylim(miny*0.99 if miny>=0 else miny*1.01,maxy*1.01 if maxy>=0 else maxy*0.99)
      #self.fig.canvas.draw()
      #self.fig.canvas.flush_events()

class SerialGui():
  run = True
  valueRun ="""<script>var b=setTimeout(a=>{document.querySelector('#output-body button')?.click()},1);</script>"""  
  valueStop="""<script>clearInterval(b)</script>"""  
  box_layout1 = widgets.Layout(flex_flow='row', display='flex', justify_content = 'center')
  box_layout2 = widgets.Layout(flex_flow='col', display='flex', justify_content = 'center')   
  valorSend = widgets.IntText(value=84,description= "Serial Write: ")
  button = ipywidgets.Button(description='Resume:',tooltip='Continua a animação do gráfico')
  buttonPause = ipywidgets.Button(description='Pause:',tooltip='Pausa a animação do gráfico')
  out = ipywidgets.Output()

  def __init__(self, socketPort = 4466, serialPort="COM7", baudrate=9600, bytesize=8, parity=0, stopbits=1, ip='127.0.0.1',maxSizeWin=9000, timeStep=0.001):
    self.serialPort, self.baudrate, self.bytesize, self.parity, self.stopbits = serialPort, baudrate, bytesize, parity, stopbits
    self.valorSend.observe(self.printSerial,'value')
    self.buttonPause.on_click(self.pause)
    self.button.on_click(self.resume)
    self.a=ipywidgets.HTML(value="image here")
    self.out.append_display_data(widgets.Box(children=[self.valorSend, self.button, self.buttonPause],layout=self.box_layout1))
    self.out.append_display_data(widgets.Box(children=[self.a],layout=self.box_layout2))
    self.serialcomm = commSerial(socketPort, ip)
    self.serialplot = plotSerial(maxSizeWin, timeStep)
    self.serialcomm.openSerial(self.serialPort, self.baudrate, self.bytesize, self.parity, self.stopbits)
    display(self.out)
    self.resume({})

  def __del__(self):
    del self.serialplot
    del self.serialcomm

  def pltToImg(self, plotFig):
    s = io.BytesIO()
    plotFig.savefig(s, format='png', bbox_inches="tight")
    s = b64encode(s.getvalue()).decode("utf-8").replace("\n", "")
    return '<img align="middle" src="data:image/png;base64,%s"> </br>' % s 

  def printSerial(self,b):
    self.serialcomm.writeSerial(self.valorSend.value)

  def resume(self,b):
    self.serialplot.redraw(self.valorSend.value,self.serialcomm.readSerial())
    self.a.value=(self.pltToImg(self.serialplot.fig))
    if self.run == True: self.out.append_display_data(ipywidgets.HTML(self.valueRun))
    else: self.run = True
  
  def pause(self,b):
    self.run = False