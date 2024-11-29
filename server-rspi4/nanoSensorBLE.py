from bluepy import btle
import struct
import time
from secondTermAcc import arduino
import csv
import sys


class connector():
	def __init__(self):
		self.MAC_ADDRESS = "0E:DF:9A:B2:12:94"
		self.SERVICE_UUID = "180C"
		self.CHAR_UUID = "2A56"
		self.nano = None
		self.service = None
		self.time= []
		self.acc_x = [] 
		self.acc_y = []
		self.acc_z = []
		self.bpm = []

	def read_data(self, run_flag):
		if not run_flag: return False
		try:
			characteristic = self.service.getCharacteristics(self.CHAR_UUID)[0]
			
			data = characteristic.read()
			
			time, accX, accY, accZ, bpm = struct.unpack('<Ihhhh', data)
			# gyroX, gyroY, gyroZ, magX, magY, magZ = struct.unpack('<hhhhhhhhh', data)

			time, accX, accY, accZ = time / 1000, accX / 1000, accY / 1000, accZ / 1000
			# gyroX, gyroY, gyroZ = gyroX / 1000, gyroY / 1000, gyroZ / 1000
			# magX, magY, magZ = magX / 1000, magY / 1000, magZ / 1000
			
			#print(accX, accY, accZ, "|", gyroX, gyroY, gyroZ, "|", magX, magY, magZ) 
			# print(time, accX, accY, accZ)
			self.time.append(time)
			self.acc_x.append(accX)
			self.acc_y.append(accY)
			self.acc_z.append(accZ)
			self.bpm.append(bpm)
			
			return True
		except:
			print("Lost connection.")
			
			return False
	
	def connect_arduino(self):		
		while self.nano is None:
			print("Connecting...")
			
			try:
				self.nano = btle.Peripheral(self.MAC_ADDRESS, addrType=btle.ADDR_TYPE_PUBLIC)
				print("Connected to Arduino Nano")
				break

			except Exception as e:
				print("Failed to Connect", e)		
			
		if self.nano is not None:
			print("Discovering Services...")
			self.service = self.nano.getServiceByUUID(self.SERVICE_UUID)

			print("Discovering Characteristics...")
			self.service.getCharacteristics()
			
		return self.nano
	
	def main(self, run_flag):
		
		while True:
			#print("\n")
			if self.read_data(run_flag[0]) is False:
				break
		
			time.sleep(0.050)
								
		with open("IMU_data.csv", mode = "w", newline= "") as file:
			writer = csv.writer(file)
			writer.writerow(["time", "x acc", "y acc", "z acc", "bpm"])
			for i in range(0, len(self.time)):
				writer.writerow([self.time[i], self.acc_x[i], self.acc_y[i], self.acc_z[i], self.bpm[i]])
		file.close()
		
		self.nano.disconnect()
