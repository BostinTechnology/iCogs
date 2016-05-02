#!/usr/bin/env python3

"""
iCogs Ls.1 Reader

For more information see www.BostinTechnology.com

The ls.1 is based on the ISL29023 Integrated Digital Light Sensor, but like all iCogs,
comes with an additional EEPROM to provide the capability to store additional information e.g
enviromental specific data.


The code here is experimental, and is not intended to be used in a production environment. It
demonstrates the basics of what is required to get the Raspberry Pi receiving data from the
iCogs range of sensors.

This program is free software; you can redistribute it and / or modify it under the terms of
the GNU General Public licence as published by the Free Foundation version 2 of the licence.

This uses the SMBus functionality of the Raspberry Pi to read and write data for the sensors.

SMBus Commands used

iCog = smbus.SMBus(i2cbus number)

read_byte_data(address, register) - returns a string containing the value in hex
write_byte_data(address, register, value)

"""


import smbus
import logging
import time
import math
import sys

SENSOR_ADDR = 0x60

def ReadAllData():
    # Read out all 255 bytes from the device
    # capture all the readings for printing later
    values = []
    # read each byte of data from 0x00 to 0xff
    for addr in range(0x00,0x100):
        byte = bus.read_byte_data(SENSOR_ADDR,addr)
        logging.debug ("Read All Data Byte %x:%x" % (addr, byte))
        values.append(byte)

    # print out the data, looping in steps of 16 to print the data out in blocks
    for i in range(0x00, 0xff, 0x10):
        print("Addr:%2x "% i, end="")
        for j in range(0x0, 0x10):
            print(" %4x" % values[i+j], end="")
        print(" ")
    return

def ReadCommandReg1():
    #Read out and decode the first command register
    reg_addr = 0x00
    byte = bus.read_byte_data(SENSOR_ADDR,reg_addr)
    logging.info ("Comand Register 1 setting (0x00):%x" % byte)
    # Decode the values
    # Interrupt Persist bits
    ipb = (byte & 0b00000011)
    logging.debug("Interrupt Persist Selection %s" % ipb)
    if ipb == 0b00:
        print("Ls.1 Interrupt Persist Number of Cycles: 1")
    elif ipb == 0b01:
        print("Ls.1 Interrupt Persist Number of Cycles: 4")
    elif ipb == 0b10:
        print("Ls.1 Interrupt Persist Number of Cycles: 8")
    elif ipb == 0b11:
        print("Ls.1 Interrupt Persist Number of Cycles: 16")

    # Interrupt Flag Bit
    ifb = (byte & 0b00000100) >> 2
    logging.debug("Interrupt Flag Bit (1=Interrupt is triggered) %s" % ifb)
    if ifb:
        print("Ls.1 Interrupt Flag Bit: Interrupt is Triggered")
    else:
        print("Ls.1 Interrupt Flag Bit: Interrupt is cleared or not triggered yet")

    # Operation Mode Bits
    omb = (byte & 0b11100000) >> 5
    logging.debug("Operation Mode Bits %s" % omb)
    if omb == 0b000:
        print("Ls.1 Operation Mode: Powered down (Default)")
    elif ipd == 0b001:
        print("Ls.1 Operation Mode: Measuring ALS once every integration cycle")
    elif ipd == 0b010:
        print("Ls.1 Operation Mode: IR Once")
    elif ipd == 0b101:
        print("Ls.1 Operation Mode: Measuring ALS continuously")
    elif ipd == 0b110:
        print("Ls.1 Operation Mode: Measuring IR continuously")
    return

def ReadCommandReg2():
    #Read out and decode the first command register
    reg_addr = 0x01
    byte = bus.read_byte_data(SENSOR_ADDR,reg_addr)
    logging.info ("Comand Register 2 setting (0x01):%x" % byte)
    # Decode the values
    # Full Scale Range bits
    fcr = (byte & 0b00000011)
    logging.debug("Full Scale Range Selection %s" % fcr)
    if fcr == 0b00:
        print("Ls.1 Full Scale Range: 1")
    elif fcr == 0b01:
        print("Ls.1 Full Scale Range: 2")
    elif fcr == 0b10:
        print("Ls.1 Full Scale Range: 3")
    elif fcr == 0b11:
        print("Ls.1 Full Scale Range: 4")

    # ADC Resolution Data
    adc = (byte & 0b00001100) >> 2
    logging.debug("ADC Resolution Bit %s" % adc)
    if adc == 0b00:
        print("Ls.1 ADC Resolution Data: 16")
    elif adc == 0b01:
        print("Ls.1 ADC Resolution Data: 12")
    elif adc == 0b10:
        print("Ls.1 ADC Resolution Data: 8")
    elif adc == 0b11:
        print("Ls.1 ADC Resolution Data: 4")
    return

def TurnOffSensor():
    # set bits 5-7 of the Command Register 0x00 to 0
    reg_addr = 0x00
    byte = bus.read_byte_data(SENSOR_ADDR,reg_addr)
    logging.info ("Command Register Before turning off (0x00):%x" % byte)
    # Modify the register to set bits 7 to 5= 0 000
    towrite = byte & 0b00011111
    logging.debug("Byte to write to turn off %s" % towrite)
    bus.write_byte_data(SENSOR_ADDR, reg_addr, towrite)
    byte = bus.read_byte_data(SENSOR_ADDR,reg_addr)
    logging.info ("Command Register After turning off (0x00):%x" % byte)
    if (byte & 0b11100000) >> 5 > 1:
        print("Sensor Turned on")
    else:
        print("Sensor Turned off")
    return

def SensorALSMode():
    # set bits 5-7 of the Command Register 0x00 to 0b101
    # Sensor will be in ALS mode
    reg_addr = 0x00
    byte = bus.read_byte_data(SENSOR_ADDR,reg_addr)
    logging.info ("Command Register Before turning off (0x00):%x" % byte)
    # Modify the register to set bits 7 to 5 = 101
    towrite = byte | 0b10100000
    logging.debug("Byte to write to turn on ALS mode %x" % towrite)
    bus.write_byte_data(SENSOR_ADDR, reg_addr, towrite)
    byte = bus.read_byte_data(SENSOR_ADDR,reg_addr)
    logging.info ("Command Register After turning on ALS mode (0x00):%x" % byte)
    if (byte & 0b10100000) >> 5 == 0b101:
        print("Sensor Turned on in ALS mode")
    else:
        print("Sensor Not in ALS mode")
    return

def SensorIRMode():
    # set bits 5-7 of the Command Register 0x00 to 0b110
    # Sensor will be IR mode
    reg_addr = 0x00
    byte = bus.read_byte_data(SENSOR_ADDR,reg_addr)
    logging.info ("Command Register Before turning off (0x00):%x" % byte)
    # Modify the register to set bits 7 to 5 = 110
    towrite = byte | 0b11000000
    logging.debug("Byte to write to turn on ALS mode %x" % towrite)
    bus.write_byte_data(SENSOR_ADDR, reg_addr, towrite)
    byte = bus.read_byte_data(SENSOR_ADDR,reg_addr)
    logging.info ("Command Register After turning on ALS mode (0x00):%x" % byte)
    if (byte & 0b10100000) >> 5 == 0b110:
        print("Sensor Turned on in IR mode")
    else:
        print("Sensor Not in IR mode")
    return


#### Calcuation routines

def ReadDataRegisters():
    # Read the data out from the sensor data registers 0x02 - lsb, 0x03 - msb
    data_addr = [0x02, 0x03]
    data_l = bus.read_byte_data(SENSOR_ADDR,data_addr[0])
    data_h = bus.read_byte_data(SENSOR_ADDR,data_addr[1])
    logging.info ("Data Register values (0x03/0x02):%x /%x" % (data_h, data_l))
    data_out = (data_h << 8) + data_l
    logging.debug("Data Register combined %x" % data_out)
    return data_out

def ADCDataResolution():
    # Return the values of the ADC resolution
    reg_addr = 0x01
    byte = bus.read_byte_data(SENSOR_ADDR,reg_addr)
    logging.info ("ADC Data Resolution reading (bits 2 & 3 of 0x01):%x" % byte)
    # Decode the values
    adc = (byte & 0b00001100) >> 2
    logging.debug("ADC Resolution Bit %s" % adc)
    resolution = 00
    if adc == 0b00:
        # 2 ^ 16
        resolution = 65536
    elif adc == 0b01:
        # 2 ^ 12
        resolution = 4096
    elif adc == 0b10:
        # 2 ^ 8
        resolution = 256
    elif adc == 0b11:
        # 2 ^ 4
        resolution = 16
    else:
        print("Unable retrieve ADC Resolution")
    logging.info("ADC Resolution Setting %f" % resolution)
    return resolution

def FullScaleRange(mode):
    # Retrieve data from the full scale range, bits B1 & B0
    # the value returned is based on the mode of operation, "ALS" or "IR"
    # If using IR sensing the value returned is always 65535, else it is based on B1 & B0
    if mode == "IR":
        logging.info("Full Scale Range mode is IR, returning 65535")
        return 65535

    # retrieve data ad decode
    reg_addr = 0x01
    byte = bus.read_byte_data(SENSOR_ADDR,reg_addr)
    logging.info ("Full Scale Range reading:%x" % byte)

    # Full Scale Range bits
    fcr = (byte & 0b00000011)
    logging.debug("Full Scale Range Selection %s" % fcr)
    fullscalerange = 0
    if fcr == 0b00:
        # Range 1
        fullscalerange = 1000
    elif fcr == 0b01:
        # Range 2
        fullscalerange = 4000
    elif fcr == 0b10:
        # Range 3
        fullscalerange = 16000
    elif fcr == 0b11:
        # Range 4
        fullscalerange = 64000
    logging.info("Full Scale Range (in ALS mode) value : %s" % fullscalerange)
    return fullscalerange

def ReadSensorMode():
    # Reads the mode of operation for the sensor and returns "ALS" or "IR"
    reg_addr = 0x00
    byte = bus.read_byte_data(SENSOR_ADDR,reg_addr)
    logging.info ("Sensor Mode Register setting (0x00):%x" % byte)

    # Operation Mode Bits
    omb = (byte & 0b11100000) >> 5
    logging.debug("Operation Mode Bits %s" % omb)
    mode = ""
    if omb == 0b000:
        mode = ""
    elif ipd == 0b001:
        mode = "ALS"
    elif ipd == 0b010:
        mode = "IR"
    elif ipd == 0b101:
        mode = "ALS"
    elif ipd == 0b110:
        mode = "IR"
    logging.info("Sensor Mode of Operation :%s" % mode)
    return mode

def CalculateLux():
    # calculate and return the Lux value
    # formula is:
    #   lux = (full scale range / adc resolution ) * data read back
    #
    lux = 0
    sens_mode = ReadSensorMode()
    full_scale = FullScaleRange(sens_mode)
    adc_resol = ADCDataResolution()
    data_read = ReadDataRegisters()
    lux = (full_scale / adc_resol) * data_read
    logging.info("Calculated LUX value based on (full scale range / adc resolution ) %f" % lux)
    return lux

def HelpText():
    # show the help text
    print("**************************************************************************\n")
    print("Available commands: -")
    print("1 - Read Command Register 1")
    print("2 - Read Command Register 2")
    print("A - Read all data blocks")
    print("L - Calculate lux Reading")
    print("t - Turn on ALS Mode")
    print("i - Turn on IR Mode")
    print("f - Turn off Sensor")
    print("e - Exit Program")



# main code loop

print ("Bostin Technology Ltd")
print ("Cogniot Products")
print ("Ls.1 - Digital Light Sensor")
print ("")
print ("Press h for help")
print ("")

bus = smbus.SMBus(1)

logging.basicConfig(filename="Ls_1.txt", filemode="w", level=logging.DEBUG, format='%(asctime)s:%(levelname)s:%(message)s')


while True:
    choice = input ("Select Menu Option:")


#TODO: sort out the menu options


    if choice == "H" or choice == "h":
        HelpText()
    elif choice == "1":
        ReadCommandReg1()
    elif choice == "2":
        ReadCommandReg2()
    elif choice == "L":
        CalculateLux()
    elif choice == "A":
        ReadAllData()
    elif choice == "t":
        SensorALSMode()
    elif choice == "i":
        SensorIRMode()
    elif choice == "o":
        TurnOffSensor()
    elif choice == "T":
        TemperatureDataAvailable()
        print ("Temperature Reading :%.3f" % CalculateTemperature())
    elif choice == "U":
        HumidityDataAvailable()
        print ("Relative Humidity Reading:%.3f" % CalculateRelativeHumidity())
    elif choice == "q":
        TurnOnHeater()
    elif choice == "E" or choice == "e":
        sys.exit()


