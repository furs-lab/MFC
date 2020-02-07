#!/usr/bin/env python2
# -*- coding: utf-8 -*-

import numpy as np

import sys  # sys нужен для передачи argv в QApplication
#reload(sys)
#sys.setdefaultencoding('utf-8')
from PyQt5 import QtWidgets
from pyqtgraph.Qt import QtGui, QtCore
import pyqtgraph as pg	# библиотека для отрисовки графиков 
import design  # конвертированный файл дизайна
from PyQt5.QtCore import QBasicTimer
import serial
from port import serial_ports,speeds	#для подключения к последовательному порту
import glob
import units	# модуль для перевода едениц измерения 

class ExampleApp(QtWidgets.QMainWindow, design.Ui_Dialog):
    def __init__(self):
         super(QtWidgets.QMainWindow,self).__init__()
         self.setupUi(self)
         
         # задаем список портов и скоростей для соответствующих выподающих списков
         self.Port.addItems(serial_ports())
         self.Speed.addItems(speeds)
         self.realport = None
         
         # задаем список единиц измерения для расходомера и клапана
         self.fmUnits.addItems(units.unitsfm)
         self.valveUnits.addItems(units.unitsvalve)
                  
         # устанавливаем таймер
         self.delt = 30
         self.timer = QBasicTimer()
         
         # переменные связанные с системой 
         self.realflow = 0	#расход измеренный расходомером
         self.targetflow = 0	#требуемое значение расхода в автоматическом режиме работы
         self.valve = 0		#величина открытия клапана
         
         # инициализируем начальное состояние элементов интерфейса
	 self.targetflowEdit.setText(str(self.targetflow))
         self.valveEdit.setText(str(self.valve))
         self.flowOutLbl.setText(str(self.realflow))
         self.radioManual.setChecked(True)
         self.valveEdit.setDisabled(False)
         self.targetflowEdit.setDisabled(True)
         self.Speed.setCurrentIndex(3)
         
	 # описываем реакцию интерфейса на различные события
         # если нажата кнопка ConnectButton вызываем функцию connect (см.ниже)
         self.ConnectButton.clicked.connect(self.connect)
         
         # если изменены единицы измерения в выпадающих списках
         self.fmUnits.activated.connect(self.unitschanged)
         self.valveUnits.activated.connect(self.unitschanged)
         
         # если изменен требуемый для поддержания расход газа
         self.targetflowEdit.editingFinished.connect(self.changeTargetFlow)
         
         # если изменена величина открытия клапана
         self.valveEdit.editingFinished.connect(self.changeValve)
         
         # если изменен режим работы
         self.radioAuto.toggled.connect(self.changeRegime)
         
         # инициализации для отрисовки графиков
         self.t = []		#массив с порядковым номером вывода
         self.Q = []		#массив с величинами расхода
         self.maxg = 200	#максимальное число точек на графике. по достижении график очищается
         self.w = QtGui.QWidget()
         self.wing = pg.GraphicsWindow()
         self.wing.show()
         self.p1 = self.wing.addPlot(title="A", col=0, row=0)
         #self.p1.setYRange(0, 1024, padding=0)	#установить диапазон оси y. если не указан будет определяться автоматически
             
    
    def connect(self):	# установка соединения с последовательным портом
        self.timer.start(self.delt,self) #!!! TEMP
        try:
            self.realport = serial.Serial(self.Port.currentText(),int(self.Speed.currentText()))
            self.ConnectButton.setStyleSheet("background-color: green")
            self.ConnectButton.setText('On')
            self.timer.start(self.delt, self)
        except Exception as e:
            self.ConnectButton.setStyleSheet("background-color: red")
            self.ConnectButton.setText('Off')
            print(e)
            
    def unitschanged(self):  #если единицы измерения поменялись меняем маски в окнах ввода, пересчитываем в новые единицы и выводим
        self.targetflowEdit.setInputMask(units.maskfm[units.unitsfm.index(self.fmUnits.currentText())])
        self.valveEdit.setInputMask(units.maskvalve[units.unitsvalve.index(self.valveUnits.currentText())])
        self.targetflowEdit.setText(str(units.pwm2unit(self.targetflow,self.fmUnits.currentText(),dev='fm')))
        self.valveEdit.setText(str(units.pwm2unit(self.valve,self.valveUnits.currentText(),dev='valve')))
            
    def changeValve(self):   #если величина открытия клапана была изменена переводим новое значение в единицы 0-1023 и отправляем в порт
        self.valve = units.unit2pwm(float(self.valveEdit.text()),self.valveUnits.currentText(),dev='valve') 
        self.sendvalue(self.valve)	#функция для отправки значения в последовательный порт
    
    def changeTargetFlow(self):   #если величина поддерживаемого расхода изменилась переводим новое значение в единицы 0-1023 и в порт
        self.targetflow = units.unit2pwm(float(self.targetflowEdit.text()),self.fmUnits.currentText(),dev='fm') 
        self.sendvalue(-self.targetflow)   #отправляем отрицательное значение что бы микроконтроллер знал что переходим в авто режим
        
    def changeRegime(self):	#если меняется режим
        if self.radioAuto.isChecked():	#если выбран авто режим
            self.valveEdit.setDisabled(True)	#запрещаем ввод величины открытия клапана
            self.targetflowEdit.setDisabled(False)   #разрешаем ввод требуемого значения расхода
        if self.radioManual.isChecked(): #если выбран ручной режим то делаем все наоборот
            self.valveEdit.setDisabled(False)
            self.targetflowEdit.setDisabled(True)
        
    def sendvalue(self, value):    #функция для отправки значения в последовательный порт
        if self.realport:
            #self.realport.flush()	#это может быть нужно если какие-то задержки обмена или рассинхрон
            #self.realport.flushInput()
            #self.realport.flushOutput()
            self.realport.write(str(value)) #"{0:b}".format(value)
            
    def readvalue(self): #функция для чтения значений из последовательного порта
        line = ''
        if self.realport:
            #self.realport.flush()
            #self.realport.flushInput()
            #self.realport.flushOutput()
            line = self.realport.readline()
            info = line.split(',')
            self.realflow = int(info[0])
            self.valve = int(info[1])
            return int(info[0])
        return -1
#    def readvalue(self):   #эмулятор для тестирования интерфейса если микроконтроллер не подключен
#        return self.valve + np.random.randint(-2,2)
    
    def timerEvent(self, e):    #события происходящие по таймеру с интервалом self.delt
        self.timer.stop()
        try:
            self.realflow = self.readvalue() # считываем данные с расходомера
            realflowinunit = units.pwm2unit(self.realflow,self.fmUnits.currentText(),dev='fm') #переводим в текущие единицы измерения
            self.flowOutLbl.setText('{0:.2f}'.format(realflowinunit)) #выводим
            if self.radioAuto.isChecked():	#если режим автоматический выводим еще значение открытия клапана
                self.valveEdit.setText(str(units.pwm2unit(self.valve,self.valveUnits.currentText(),dev='valve')))
        except:
            self.realflow = self.Q[-1]
        nc = len(self.Q)
        realflowinunit = units.pwm2unit(self.realflow,self.fmUnits.currentText(),dev='fm')
        if nc > self.maxg:    #добавляем считанные значения в массив, а если значений уже больше чем maxg, то очищаем массив
            self.t = [0,1]
            self.Q = [self.Q[-1],realflowinunit]
        else:
            self.t.append(len(self.Q))
            self.Q.append(realflowinunit)
        self.p1.plot(self.t, self.Q, clear=True, pen=(255,0,0))    #отображаем грфик
        
        self.timer.start(self.delt,self)
                

def main():
    app = QtWidgets.QApplication(sys.argv)  # Новый экземпляр QApplication
    window = ExampleApp()  # Создаём объект класса ExampleApp
    window.show()  # Показываем окно
    app.exec_()  # и запускаем приложение
    
if __name__ == '__main__':  # Если мы запускаем файл напрямую, а не импортируем
    main()  # то запускаем функцию main()
