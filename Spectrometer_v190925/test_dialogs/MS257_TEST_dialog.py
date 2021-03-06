#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
Created on Fri Jan 12 09:06:01 2018

@author: Vedran Furtula
"""

import os, sys, re, serial, time, numpy, configparser
import pyqtgraph as pg

from PyQt5.QtCore import QObject, QThreadPool, QRunnable, pyqtSignal, pyqtSlot
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import (QDialog, QMessageBox, QGridLayout,
														 QLabel, QLineEdit, QComboBox, QTableWidget, QTableWidgetItem,
														 QVBoxLayout, QHBoxLayout, QPushButton)

from instruments import MS257


class WorkerSignals(QObject):
	# Create signals to be used
	update0 = pyqtSignal(object)
	finished = pyqtSignal()
	


class MS257_Worker(QRunnable):
	'''
	Worker thread
	:param args: Arguments to make available to the run code
	:param kwargs: Keywords arguments to make available to the run code
	'''	
	def __init__(self,*argv):
		super(MS257_Worker, self).__init__()
		
		# constants	
		self.ms257 = argv[0].ms257
		self.set_ = argv[0].set_
		self.val = argv[0].val
		
		self.signals = WorkerSignals()
	
	@pyqtSlot()
	def run(self):
		if self.set_=='unit':
			self.ms257.setUNITS(self.val.upper())
			
		elif self.set_=='wl':
			self.ms257.goToWL(self.val)
			X_pos=self.ms257.getCurrentPOS()
			X_wl=self.ms257.getCurrentWL()
			grating=self.ms257.getGRATING()
			self.signals.update0.emit([float(X_pos),float(X_wl),grating])
			
		elif self.set_=='pos':
			self.ms257.goToPOS(self.val)
			X_pos=self.ms257.getCurrentPOS()
			X_wl=self.ms257.getCurrentWL()
			grating=self.ms257.getGRATING()
			self.signals.update0.emit([float(X_pos),float(X_wl),grating])
			
		elif self.set_=='shutter':
			self.ms257.setSHUTTER(self.val)
		
		elif self.set_=='grating':
			self.ms257.setGRATING(self.val)
			
		self.signals.finished.emit()
				
				
				
				
				
				
				
class MS257_TEST_dialog(QDialog):
	
	def __init__(self, parent, inst_list):
		super().__init__(parent)
		
		# constants
		self.inst_list = inst_list
		
		# Initial read of the config file
		self.config = configparser.ConfigParser()
		
		try:
			self.config.read('config.ini')
			self.last_used_scan = self.config.get('LastScan','last_used_scan')
			
			self.grating = self.config.get(self.last_used_scan,'grating')
			self.unit_str = self.config.get(self.last_used_scan,'unit')
			self.shutter_str = self.config.get(self.last_used_scan,'shutter')
			self.ms257inport_str=self.config.get("Instruments",'ms257inport').strip().split(',')[0]
			self.ms257outport_str=self.config.get("Instruments",'ms257outport').strip().split(',')[0]
		except configparser.NoOptionError as e:
			QMessageBox.critical(self, 'Message',''.join(["Main FAULT while reading the config.ini file\n",str(e)]))
			raise
		
		self.setupUi()
		
		# close both MS257 serial ports if open
		if self.inst_list.get("MS257_in"):
			if self.inst_list.get("MS257_in").is_open():
				self.inst_list.get("MS257_in").close()
		self.inst_list.pop('MS257_in', None)
		
		if self.inst_list.get("MS257_out"):
			if self.inst_list.get("MS257_out").is_open():
				self.inst_list.get("MS257_out").close()
		self.inst_list.pop('MS257_out', None)
		
	def setupUi(self):
		self.serialport = QLabel("Serial port (input)",self)
		
		self.combo1 = QComboBox(self)
		mylist1=[self.ms257inport_str ,self.ms257outport_str]
		self.ms257port_str=self.ms257inport_str
		self.combo1.addItems(mylist1)
		self.combo1.setCurrentIndex(mylist1.index(self.ms257inport_str))
		self.combo1.setFixedWidth(70)
		self.combo1.setEditable(True)
		
		grat_lbl = QLabel("Grating",self)
		grat_lbl.setFixedWidth(150)
		self.combo0 = QComboBox(self)
		mylist0=["0","1","2","3","4","home"]
		self.combo0.addItems(mylist0)
		self.combo0.setCurrentIndex(mylist0.index(self.grating))
		self.combo0.setFixedWidth(70)
		
		setUnits_lbl = QLabel("Set unit",self)
		setUnits_lbl.setFixedWidth(150)
		self.combo2 = QComboBox(self)
		self.mylist2=["nm","um","wn"]
		self.combo2.addItems(self.mylist2)
		self.combo2.setCurrentIndex(self.mylist2.index(self.unit_str))
		self.combo2.setFixedWidth(70)
		
		setShutter_lbl = QLabel("Set shutter",self)
		setShutter_lbl.setFixedWidth(150)
		self.combo3 = QComboBox(self)
		self.mylist3=["on","off", " "]
		self.combo3.addItems(self.mylist3)
		self.combo3.setCurrentIndex(self.mylist3.index(" "))
		self.combo3.setFixedWidth(70)
		
		self.goWLButton = QPushButton("Go to wavelength",self)
		self.goWLButton.setFixedWidth(150)
		self.goWLButtonEdit = QLineEdit("",self)
		self.goWLButtonEdit.setFixedWidth(70)
		
		self.goPosButton = QPushButton("Go to position",self)
		self.goPosButton.setFixedWidth(150)
		self.goPosButtonEdit = QLineEdit("",self)
		self.goPosButtonEdit.setFixedWidth(70)
		
		self.clearButton = QPushButton("Clear",self)
		#self.clearButton.setFixedWidth(200)
		##############################################
		
		g0_1 = QGridLayout()
		g0_1.addWidget(self.serialport,0,0)
		g0_1.addWidget(self.combo1,0,1)
		g0_1.addWidget(grat_lbl,1,0)
		g0_1.addWidget(self.combo0,1,1)
		g0_1.addWidget(setUnits_lbl,2,0)
		g0_1.addWidget(self.combo2,2,1)
		g0_1.addWidget(setShutter_lbl,3,0)
		g0_1.addWidget(self.combo3,3,1)
		g0_1.addWidget(self.goWLButton,4,0)
		g0_1.addWidget(self.goWLButtonEdit,4,1)
		g0_1.addWidget(self.goPosButton,5,0)
		g0_1.addWidget(self.goPosButtonEdit,5,1)
		g0_1.addWidget(self.clearButton,6,0,1,2)
		
		##############################################
		
		# set graph  and toolbar to a new vertical group vcan
		self.pw1 = pg.PlotWidget()
		
		##############################################
		
		# create table
		self.tableWidget = self.createTable()

		##############################################
		
		# SET ALL VERTICAL COLUMNS TOGETHER
		hbox = QHBoxLayout()
		hbox.addLayout(g0_1)
		hbox.addWidget(self.tableWidget)
		
		vbox = QVBoxLayout()
		vbox.addLayout(hbox)
		vbox.addWidget(self.pw1)
		
		self.threadpool = QThreadPool()
		print("Multithreading in the MS257 dialog with maximum %d threads" % self.threadpool.maxThreadCount())
		self.isRunning=False
		
		self.setLayout(vbox)
		self.setWindowTitle("Test MS257 monochromator")
		
		# PLOT 2 settings
		# create plot and add it to the figure canvas
		self.p1 = self.pw1.plotItem
		self.curve1=self.p1.plot(pen='w')
		# create plot and add it to the figure
		self.p0_1 = pg.ViewBox()
		self.curve2=pg.PlotCurveItem(pen='r')
		self.p0_1.addItem(self.curve2)
		# connect respective axes to the plot 
		#self.p1.showAxis('left')
		self.p1.getAxis('left').setLabel("Wavelength", units='m', color='yellow')
		self.p1.showAxis('right')
		self.p1.getAxis('right').setLabel("Position", units="", color='red')
		self.p1.scene().addItem(self.p0_1)
		self.p1.getAxis('right').linkToView(self.p0_1)
		self.p0_1.setXLink(self.p1)
		
		self.p1.getAxis('bottom').setLabel("Point no.", units="", color='yellow')
		# Use automatic downsampling and clipping to reduce the drawing load
		self.pw1.setDownsampling(mode='peak')
		self.pw1.setClipToView(True)
		
		# Initialize and set titles and axis names for both plots
		self.clear_vars_graphs()
		self.combo0.activated[str].connect(self.onActivated0)
		self.combo1.activated[str].connect(self.onActivated1)
		self.combo2.activated[str].connect(self.onActivated2)
		self.combo3.activated[str].connect(self.onActivated3)
		
		# run or cancel the main script
		self.clearButton.clicked.connect(self.clear_vars_graphs)
		self.clearButton.setEnabled(False)
		
		self.goPosButton.clicked.connect(self.set_runPosWl)
		self.goWLButton.clicked.connect(self.set_runPosWl)
	
	
	def is_number(self,s):
		try:
			float(s)
			return True
		except ValueError:
			pass

		try:
			import unicodedata
			unicodedata.numeric(s)
			return True
		except (TypeError, ValueError):
			pass

		return False
	
	
	def createTable(self):
		tableWidget = QTableWidget()
 
		# set row count
		#tableWidget.setRowCount(20)
		
		# set column count
		tableWidget.setColumnCount(5)
		
		# hide grid
		tableWidget.setShowGrid(False)
		
		# hide vertical header
		vh = tableWidget.verticalHeader()
		vh.setVisible(False)
		
		# set the font
		font = QFont("Courier New", 9)
		tableWidget.setFont(font)
		tableWidget.setStyleSheet("color: blue")
		
		# place content into individual table fields
		#tableWidget.setItem(0,0, QTableWidgetItem("abe"))
		
		tableWidget.setHorizontalHeaderLabels(["Port","Grat.","Point no.","Position","Wavelength"])
		#tableWidget.setVerticalHeaderLabels(["aa","bb","cc","dd"])
		
		# set horizontal header properties
		hh = tableWidget.horizontalHeader()
		hh.setStretchLastSection(True)
        
		# set column width to fit contents
		tableWidget.resizeColumnsToContents()
		
		# enable sorting
		#tableWidget.setSortingEnabled(True)
		
		return tableWidget
	
	
	def onActivated0(self, text):
		if not hasattr(self, 'MS257'):
			try:
				self.MS257 = MS257.MS257(self.ms257port_str, False)
			except Exception as e:
				reply = QMessageBox.critical(self, 'MS257 TEST MODE', ''.join(["MS257 could not return valid echo signal. Check the port name and check the connection.\n",str(e),"\n\nShould the program proceeds into the TEST MODE?"]), QMessageBox.Yes | QMessageBox.No)
				if reply == QMessageBox.Yes:
					self.MS257 = MS257.MS257(self.ms257port_str, True)
				else:
					self.combo0.setCurrentIndex(self.mylist0.index(self.grating))
					return
			self.MS257.set_timeout(60)
		
		else:
			try:
				if self.MS257.is_open():
					self.MS257.close()
				self.MS257 = MS257.MS257(self.ms257port_str, False)
			except Exception as e:
				reply = QMessageBox.critical(self, 'MS257 TEST MODE', ''.join(["MS257 could not return valid echo signal. Check the port name and check the connection.\n",str(e),"\n\nShould the program proceeds into the TEST MODE?"]), QMessageBox.Yes | QMessageBox.No)
				if reply == QMessageBox.Yes:
					self.MS257 = MS257.MS257(self.ms257port_str, True)
				else:
					self.combo0.setCurrentIndex(self.mylist0.index(self.grating))
					return
			self.MS257.set_timeout(60)
		
		self.grating=str(text)
		self.clearButton.setEnabled(False)
		self.combo0.setEnabled(False)
		self.combo1.setEnabled(False)
		self.combo2.setEnabled(False)
		self.combo3.setEnabled(False)
		
		self.goWLButton.setEnabled(False)
		self.goWLButtonEdit.setEnabled(False)
		self.goPosButton.setEnabled(False)
		self.goPosButtonEdit.setEnabled(False)
		self.isRunning=True
		
		obj=type('obj',(object,),{ 'ms257':self.MS257, 'set_':"grating", 'val':str(text) })
		
		self.worker=MS257_Worker(obj)	
		self.worker.signals.finished.connect(self.finished)
		
		# Execute
		self.threadpool.start(self.worker)
			
			
	def onActivated1(self, text):
		
		self.ms257port_str=str(text)
		if self.ms257port_str=="COM3":
			self.serialport.setText("Serial port (output)")
			QMessageBox.warning(self, "Shutter warning", ''.join(["Shutter not available on port ", self.ms257port_str]))
			self.combo3.setEnabled(False)
		elif self.ms257port_str=="COM4":
			self.serialport.setText("Serial port (input)")
			self.combo3.setEnabled(True)
			
		print("Monochromator serial port changed to", str(text))
	
	
	def onActivated2(self, text):
		if not hasattr(self, 'MS257'):
			try:
				self.MS257 = MS257.MS257(self.ms257port_str, False)
			except Exception as e:
				reply = QMessageBox.critical(self, 'MS257 TEST MODE', ''.join(["MS257 could not return valid echo signal. Check the port name and check the connection.\n",str(e),"\n\nShould the program proceeds into the TEST MODE?"]), QMessageBox.Yes | QMessageBox.No)
				if reply == QMessageBox.Yes:
					self.MS257 = MS257.MS257(self.ms257port_str, True)
				else:
					self.combo2.setCurrentIndex(self.mylist2.index(self.unit_str))
					return
			self.MS257.set_timeout(60)
		
		else:
			try:
				if self.MS257.is_open():
					self.MS257.close()
				self.MS257 = MS257.MS257(self.ms257port_str, False)
			except Exception as e:
				reply = QMessageBox.critical(self, 'MS257 TEST MODE', ''.join(["MS257 could not return valid echo signal. Check the port name and check the connection.\n",str(e),"\n\nShould the program proceeds into the TEST MODE?"]), QMessageBox.Yes | QMessageBox.No)
				if reply == QMessageBox.Yes:
					self.MS257 = MS257.MS257(self.ms257port_str, True)
				else:
					self.combo2.setCurrentIndex(self.mylist2.index(self.unit_str))
					return
			self.MS257.set_timeout(60)
		
		self.unit_str=str(text)
		self.clearButton.setEnabled(False)
		self.combo0.setEnabled(False)
		self.combo1.setEnabled(False)
		self.combo2.setEnabled(False)
		self.combo3.setEnabled(False)
		
		self.goWLButton.setEnabled(False)
		self.goWLButtonEdit.setEnabled(False)
		self.goPosButton.setEnabled(False)
		self.goPosButtonEdit.setEnabled(False)
		self.isRunning=True
		
		obj=type('obj',(object,),{ 'ms257':self.MS257, 'set_':"unit", 'val':str(text) })
		
		self.worker=MS257_Worker(obj)	
		self.worker.signals.finished.connect(self.finished)
		
		# Execute
		self.threadpool.start(self.worker)
		
		
	def onActivated3(self, text):
		if not hasattr(self, 'MS257'):
			try:
				self.MS257 = MS257.MS257(self.ms257port_str, False)
			except Exception as e:
				reply = QMessageBox.critical(self, 'MS257 TEST MODE', ''.join(["MS257 could not return valid echo signal. Check the port name and check the connection.\n",str(e),"\n\nShould the program proceeds into the TEST MODE?"]), QMessageBox.Yes | QMessageBox.No)
				if reply == QMessageBox.Yes:
					self.MS257 = MS257.MS257(self.ms257port_str, True)
				else:
					self.combo3.setCurrentIndex(self.mylist3.index(self.shutter_str))
					return
			self.MS257.set_timeout(60)
		
		else:
			try:
				if self.MS257.is_open():
					self.MS257.close()
				self.MS257 = MS257.MS257(self.ms257port_str, False)
			except Exception as e:
				reply = QMessageBox.critical(self, 'MS257 TEST MODE', ''.join(["MS257 could not return valid echo signal. Check the port name and check the connection.\n",str(e),"\n\nShould the program proceeds into the TEST MODE?"]), QMessageBox.Yes | QMessageBox.No)
				if reply == QMessageBox.Yes:
					self.MS257 = MS257.MS257(self.ms257port_str, True)
				else:
					self.combo3.setCurrentIndex(self.mylist3.index(self.shutter_str))
					return
			self.MS257.set_timeout(60)
		
		if str(text)==" ":
			QMessageBox.warning(self, 'Message',"Set the shutter to position on or position off.")
			self.combo3.setCurrentIndex(self.mylist3.index(self.shutter_str))
			return
		
		self.shutter_str=str(text)
		self.clearButton.setEnabled(False)
		self.combo0.setEnabled(False)
		self.combo1.setEnabled(False)
		self.combo2.setEnabled(False)
		self.combo3.setEnabled(False)
		
		self.goWLButton.setEnabled(False)
		self.goWLButtonEdit.setEnabled(False)
		self.goPosButton.setEnabled(False)
		self.goPosButtonEdit.setEnabled(False)
		self.isRunning=True
		
		obj=type('obj',(object,),{ 'ms257':self.MS257, 'set_':"shutter", 'val':str(text) })
		
		self.worker=MS257_Worker(obj)	
		self.worker.signals.finished.connect(self.finished)
		
		# Execute
		self.threadpool.start(self.worker)
		
		
	def set_runPosWl(self):
		
		if not hasattr(self, 'MS257'):
			try:
				self.MS257 = MS257.MS257(self.ms257port_str, False)
			except Exception as e:
				reply = QMessageBox.critical(self, 'MS257 TEST MODE', ''.join(["MS257 could not return valid echo signal. Check the port name and check the connection.\n",str(e),"\n\nShould the program proceeds into the TEST MODE?"]), QMessageBox.Yes | QMessageBox.No)
				if reply == QMessageBox.Yes:
					self.MS257 = MS257.MS257(self.ms257port_str, True)
				else:
					return
			self.MS257.set_timeout(60)
		
		else:
			try:
				if self.MS257.is_open():
					self.MS257.close()
				self.MS257 = MS257.MS257(self.ms257port_str, False)
			except Exception as e:
				reply = QMessageBox.critical(self, 'MS257 TEST MODE', ''.join(["MS257 could not return valid echo signal. Check the port name and check the connection.\n",str(e),"\n\nShould the program proceeds into the TEST MODE?"]), QMessageBox.Yes | QMessageBox.No)
				if reply == QMessageBox.Yes:
					self.MS257 = MS257.MS257(self.ms257port_str, True)
				else:
					return
			self.MS257.set_timeout(60)
		
		sender=self.sender()
		
		if sender.text()=="Go to wavelength":
			set_ = "wl"
			val = str(self.goWLButtonEdit.text())
			
			if not val or not self.is_number(val):
				QMessageBox.warning(self, 'Message',"MS257 wavelength should be a numeric value")
				return
			if self.unit_str=='nm':
				if float(val)<0 or float(val)>2500:
					QMessageBox.warning(self, 'Message',"MS257 wavelength range is from 0 nm to 2500 nm")
					return
			if self.unit_str=='um':
				if float(val)<0.0 or float(val)>2.500:
					QMessageBox.warning(self, 'Message',"MS257 wavelength range is from 0 um to 2.5 um")
					return
				
		elif sender.text()=="Go to position":
			set_ = "pos"
			val = str(self.goPosButtonEdit.text())
			
			if not val or not self.is_number(val):
				QMessageBox.warning(self, 'Message',"MS257 position should be a numeric value")
				return
			
		self.clearButton.setEnabled(False)
		self.combo0.setEnabled(False)
		self.combo1.setEnabled(False)
		self.combo2.setEnabled(False)
		self.combo3.setEnabled(False)
		
		self.goWLButton.setEnabled(False)
		self.goWLButtonEdit.setEnabled(False)
		self.goPosButton.setEnabled(False)
		self.goPosButtonEdit.setEnabled(False)
		self.isRunning=True
		
		obj=type('obj',(object,),{ 'ms257':self.MS257, 'set_':set_, 'val':val })
		
		self.worker=MS257_Worker(obj)	
		self.worker.signals.update0.connect(self.update0)
		self.worker.signals.finished.connect(self.finished)

		# Execute
		self.threadpool.start(self.worker)
		
		
	def update0(self,my_obj):
		pos, wl, grat = my_obj
		self.tal+=1
		
		# set row height
		self.tableWidget.setRowCount(self.tal+1)
		self.tableWidget.setRowHeight(self.tal, 12)
		
		# add row elements
		self.tableWidget.setItem(self.tal, 0, QTableWidgetItem(self.ms257port_str))
		self.tableWidget.setItem(self.tal, 1, QTableWidgetItem(grat))
		self.tableWidget.setItem(self.tal, 2, QTableWidgetItem(str(self.tal)))
		self.tableWidget.setItem(self.tal, 3, QTableWidgetItem(str(pos)))
		self.tableWidget.setItem(self.tal, 4, QTableWidgetItem(str(wl)))
		
		self.tals.extend([ self.tal ])
		self.plot_pos_tr.extend([ pos ])
		self.plot_wl_tr.extend([ wl ])
		#self.plot_time_tr.extend([ timelist ])
		
		## Handle view resizing 
		def updateViews():
			## view has resized; update auxiliary views to match
			self.p0_1.setGeometry(self.p1.vb.sceneBoundingRect())
			#p3.setGeometry(p1.vb.sceneBoundingRect())

			## need to re-update linked axes since this was called
			## incorrectly while views had different shapes.
			## (probably this should be handled in ViewBox.resizeEvent)
			self.p0_1.linkedViewChanged(self.p1.vb, self.p0_1.XAxis)
			#p3.linkedViewChanged(p1.vb, p3.XAxis)
			
		updateViews()
		self.p1.vb.sigResized.connect(updateViews)
		self.curve1.setData(self.tals, self.plot_wl_tr)
		self.curve2.setData(self.tals, self.plot_pos_tr)
		
		
	def finished(self):
		self.isRunning=False
		self.combo0.setEnabled(True)
		self.combo1.setEnabled(True)
		self.combo2.setEnabled(True)
		self.combo3.setEnabled(True)
		
		self.goWLButton.setEnabled(True)
		self.goWLButtonEdit.setEnabled(True)
		self.goPosButton.setEnabled(True)
		self.goPosButtonEdit.setEnabled(True)
		
		self.clearButton.setEnabled(True)
		self.clearButton.setText("Clear")
		
		
	def clear_vars_graphs(self):
		self.tal=-1
		self.tals=[]
		self.all_time_tr=[]
		self.plot_pos_tr=[]
		self.plot_wl_tr=[]
		#self.plot_time_tr=[]
		self.curve1.clear()
		self.curve2.clear()
		self.tableWidget.clearContents()
		
		self.clearButton.setEnabled(False)
		self.clearButton.setText("Cleared")
		
		
	def closeEvent(self, event):
		reply = QMessageBox.question(self, 'Message', "Quit now? Changes will not be saved!", QMessageBox.Yes | QMessageBox.No)
		if reply == QMessageBox.Yes:
			if hasattr(self, 'MS257'):
				if not hasattr(self, 'worker'):
					if self.MS257.is_open():
						self.MS257.close()
				else:
					if self.isRunning:
						QMessageBox.warning(self, 'Message', "Run in progress. Cancel the scan then quit!")
						event.ignore()
						return None
					else:
						if self.MS257.is_open():
							self.MS257.close()
			event.accept()
		else:
		  event.ignore() 
		  
		  
		  
		  
		  
