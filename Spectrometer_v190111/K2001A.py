import sys, serial, argparse, time, re, random, visa
import numpy as np
import matplotlib.pyplot as plt

class K2001A:
	
	def __init__(self,my_serial,testmode):
		# activate the serial. CHECK the serial port name!
		
		self.testmode = testmode
		if not self.testmode:
			rm = visa.ResourceManager()
			self.ser = rm.open_resource(my_serial)
			time.sleep(0.25)
			#self.ser=serial.Serial(my_serial,baudrate=19200,parity=serial.PARITY_NONE,stopbits=serial.STOPBITS_ONE)
			#print("K2001A serial port:", my_serial)
			#time.sleep(1)

  ############################################################
	# Check input if a number, ie. digits or fractions such as 3.141
	# Source: http://www.pythoncentral.io/how-to-check-if-a-string-is-a-number-in-python-including-unicode/
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
  
  ####################################################################
  # K2001A functions
  ####################################################################
	
	def return_id(self):
		if self.testmode:
			return "TEST MODE Keithley 2001A: return_id"
		elif not self.testmode:
			val = self.ser.query("*idn?")
			return val
	
	def set_dc_voltage(self):
		if self.testmode:
			return "TEST MODE Keithley 2001A: set_dc_voltage"
		elif not self.testmode:
			#read digitized voltage value from the analog port number (dev)
			self.ser.write(":conf:volt:dc")
			self.ser.write(":sense:volt:dc:nplc 1")
			#self.ser.write(":sense:volt:dc:rang:upp 15") #possibly bad resolution
			self.ser.write(":sense:volt:dc:rang:auto 1")
	
	def return_voltage(self):
		if self.testmode:
			time.sleep(0.01)
			return random.uniform(-1,20)
		elif not self.testmode:
			#read digitized voltage value from the analog port number (dev)
			while True:
				val = self.ser.query(":read?")
				val = val.split(',')[0][:-4]
				if self.is_number(val):
					#print("return_reffreq: ", val)
					return float(val)
				else:
					print("Bad value returned from K2001A (read command):", val)
	
	def is_open(self):
		try:
			self.return_id()
			return True
		except Exception as e:
			return False
	
	def close(self):
		if self.testmode:
			print("TEST MODE: Kietheley 2001A: stepper port flushed and closed")
		elif not self.testmode:
			self.ser.close()
			print("Kiethley 2001A stepper port flushed and closed")
				
def main():
  
	# call the sr510 port
	model_510 = K2001A('GPIB0::10::INSTR', False)
	
	for i in range(10):
		print(model_510.return_voltage())
	
if __name__ == "__main__":
	
  main()
  


