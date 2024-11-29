from bluepy import btle
import time
import sys
import binascii
import struct
import csv


class arduino:
    def __init__(self):
        self.mac_ad = "0E:DF:9A:B2:12:94"
        self.SERVICE_UUID = "181A"
        self.CHARACTERISTIC_UUID = "2B44"
        self.CHARACTERISTIC_UUID_2 = "2B9B"
        self.CHARACTERISTIC_UUID_3 = "2A2C"

    def byte_array_to_int(self, value):
        value = bytearray(value)
        value = int.from_bytes(value, byteorder="little", signed=True)
        return value

    def read_floatpack(self, service):
        #pack_gyro_char = service.getCharacteristics(CHARACTERISTIC_UUID)[0]
        pack_acc_char = service.getCharacteristics(self.CHARACTERISTIC_UUID_2)[0]
        #pack_mag_char = service.getCharacteristics(CHARACTERISTIC_UUID_3)[0]
        
        #pack_gyro = pack_gyro_char.read()
        pack_acc = pack_acc_char.read()
        #pack_mag = pack_mag_char.read()
        try:
            data = []
            #data_gyro = struct.unpack_from('<fff', pack_gyro)
            data_acc = struct.unpack_from('<fff', pack_acc)
            #data_mag = struct.unpack_from('<fff', pack_mag)
            
            #data.append(data_gyro)
            data.append(data_acc)
            #data.append(data_mag)
            item_length = len(data[0])
            
            # with open('labTest0912.csv', 'a') as test_file:
                # file_writer = csv.writer(test_file)
                # for i in range(item_length):
                    # file_writer.writerow([x[i] for x in data])
                
                # file_writer.writerow([' '])
            
            #print(data_gyro)
            #print()
            print(data_acc)
            #print()
            #print(data_mag)
            data.clear()
        except:
            print("Something went wrong")
        
    def parseFloatData(data):
        data = binascii.b2a_hex(data)
        return data
        
    def main_run(self):
        print("Connecting...")
        pls = True
        while(pls):
            try:
                nano_ble = btle.Peripheral(self.mac_ad, addrType=btle.ADDR_TYPE_PUBLIC)
                pls = False
            except:
                print("Didn't work")

        print("Discovering Services...")
        _ = nano_ble.services
        bleService = nano_ble.getServiceByUUID(self.SERVICE_UUID)

        print("Discovering Characteristics...")
        _ = bleService.getCharacteristics()

        while True:
            print("\n")
            read_floatpack(bleService)
            time.sleep(0.250)

