#! /usr/bin/python3

"""
Commands

iCog = smbus.SMBus(i2cbus number)

read_byte_data(address, register)
    returns a string containing the value in hex
write_byte_data(address, register, value)

read_word_data(address, register)
write_word_data(address, register, word to write)

read_block_data(address, register)
write_block_data(address, register, [values])

read_i2c_block_data(address, register)
write_i2c_block_data(address, register, [values])

"""


import smbus
import logging

def ReadAllData():
    #Read out all 255 bytes
    for addr in range(0x00,0xff):
        byte = hex(bus.read_byte_data(0x5f,addr))
        print ("Byte %x:%s" % (addr, byte))
        logging.debug ("Read All Data Byte %x:%s" % (addr, byte))
    #it appears the I2C interface won't let me read a block

def WhoAmI():
    #Read out and confirm the Who Am I data
    byte = hex(bus.read_byte_data(0x5f,0x0F))
    if int(byte,16) == 0xBC:
        print("Identified as Correct Device:%s" % byte)
    else:
        print("Check the Device WhoAm I as it is unrecognised")
    logging.info ("Who Am I (0x0f):%s" % byte)

def ReadAV_Conf():
    #Read out and decode the humidty and temperature mode
    byte = hex(bus.read_byte_data(0x5f,0x10))
    logging.info ("AV_Conf setting (0x10):%s" % byte)
    #TODO: Decode the values

def ReadCtrl_Reg1():
    #Read out and decode the first control register
    byte = hex(bus.read_byte_data(0x5f,0x20))
    logging.info ("Control Register 1 setting (0x20):%s" % byte)
    #TODO: Decode the values

def ReadCtrl_Reg2():
    #Read out and decode the second control register
    byte = hex(bus.read_byte_data(0x5f,0x21))
    logging.info ("Control Register 2 setting (0x21):%s" % byte)
    #TODO: Decode the values

def ReadCtrl_Reg3():
    #Read out and decode the third control register
    byte = hex(bus.read_byte_data(0x5f,0x22))
    logging.info ("Control Register 3 setting (0x22):%s" % byte)
    #TODO: Decode the values

def ReadStatus_Reg():
    #Read out and decode the status register
    byte = hex(bus.read_byte_data(0x5f,0x27))
    logging.info ("Status Register setting (0x27):%s" % byte)
    #TODO: Decode the values

def ReadHumidity():
    #Read out and decode the 2 bytes of humidity readings
    humidity_out_l = hex(bus.read_byte_data(0x5f,0x28))
    humidity_out_h = hex(bus.read_byte_data(0x5f,0x29))
    logging.info ("Humidity Out Reading (0x29/0x28):%s/%s" % (humidity_out_h, humidity_out_l))
    #TODO: Merge the values into a signel reading

def ReadTemperature():
    #Read out and decode the 2 bytes of temperature readings
    temp_out_l = hex(bus.read_byte_data(0x5f,0x2a))
    temp_out_h = hex(bus.read_byte_data(0x5f,0x2b))
    logging.info ("Temperture Out Reading (0x2b/0x2a):%s/%s" % (temp_out_h, temp_out_l))
    #TODO: Merge the values into a signel reading




#main

bus = smbus.SMBus(1)

logging.basicConfig(filename="Ts_1.txt", filemode="w", level=logging.DEBUG, format='%(asctime)s:%(levelname)s:%(message)s')

WhoAmI()
ReadAV_Conf()
ReadCtrl_Reg1()
ReadCtrl_Reg2()
ReadCtrl_Reg3()
ReadStatus_Reg()
ReadHumidity()
ReadTemperature()
