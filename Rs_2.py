#!/usr/bin/env python3

"""
iCogs Rs.2 Reader

For more information see www.BostinTechnology.com

The Rs.2 is based on the MMA8652FC 3-Axis, 12-bit Digital Accelerometer, but like all iCogs,
comes with an additional EEPROM to provide the capability to store additional information e.g
enviromental specific data.

Note: The operating modes can only be changed when in standby.


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


##
##
## This software is ready for testing
##
##


import smbus
import logging
import time
import math
import sys

SENSOR_ADDR = 0x1d

#Sensor Modes
STANDBY = 0b00
WAKE = 0b01
SLEEP = 0b10

#Full Scale Ranges
TWOG = 0b00
FOURG = 0b01
EIGHTG = 0b10

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

def WhoAmI():
    # Read out and confirm the 'Who Am I' value of 0x4a
    byte = bus.read_byte_data(SENSOR_ADDR,0x0F)
    if byte == 0x4A:
        print("Identified as Correct Device :%x" % byte)
    else:
        print("Check the Device WhoAm I as it is unrecognised")
    logging.info ("Who Am I (0x0f):%s" % byte)
    return

def ReadF_Setup():
    #Read out and decode the F_Setup Register 0x09
    reg_addr = 0x09
    byte = bus.read_byte_data(SENSOR_ADDR,reg_addr)
    logging.info ("F_Setup Register reading (%x):%x" % (reg_addr,byte))
    # Decode the values
    # FIFO Buffer Overflow mode
    fbom = (byte & 0b11000000) >> 6
    logging.debug("FIFO Buffer Overflow bits %s" % fbom)
    if fbom == 0b00:
        print("Rs.2 FIFO is disabled")
    elif fbom == 0b01:
        print("Rs.2 FIFO contains the most recent samples when overflowed")
    elif fbom == 0b10:
        print("Rs.2 FIFO stops accepting new samples when overflowed")
    elif fbom == 0b11:
        print("Rs.2 FIFO is in Trigger mode")
    # FIFO Event Sample Count Watermark
    fescw = (byte & 0b00111111)
    logging.debug("FIFO Event Sample Count Watermark %s" % fescw)
    print ("FIFO Event Sample Count Watermark %s" % fescw)
    return

def ReadSystemMode():
    #Read out and decode the SYSMOD Register 0x0B
    reg_addr = 0x0B
    byte = bus.read_byte_data(SENSOR_ADDR,reg_addr)
    logging.info ("SYSMOD Register reading (%x):%x" % (reg_addr,byte))
    # Decode the values
    # FIFO Gate Error flag
    fge = (byte & 0b10000000) >> 7
    logging.debug("FIFO Gate Error Flag %s" % fge)
    if fge == 0b1:
        print("Rs.2 FIFO Gate Error has been detected")
    else:
        print("Rs.2 FIFO Gate Error has NOT been detected")
    # Number of ODR time units since FIFO Gate Error
    fgerr = (byte & 0b01111100)
    logging.debug("Number of ODR time units since FIFO Gate Error %s" % fgerr)
    print ("Number of ODR time units since FIFO Gate Error %s" % fgerr)
    # System Mode
    sysmod = (byte & 0b00000011)
    logging.debug("System Modebits %s" % sysmod)
    if sysmod == 0b00:
        print("Rs.2 In Standby Mode")
    elif sysmod == 0b01:
        print("Rs.2 In Wake Mode")
    elif sysmod == 0b10:
        print("Rs.2 In Sleep Mode")
    return

def SetSystemMode(mode):
    #Set the System Mode in the SYSMOD Register 0x0B
    # mode can be either STANDBY, WAKE, SLEEP
    reg_addr = 0x0B
    byte = bus.read_byte_data(SENSOR_ADDR,reg_addr)
    logging.info ("SYSMOD Register before setting (%x):%x" % (reg_addr,byte))
    logging.debug("Requested mode of operation %x" % mode)
    # Modify the register to set bits 1 - 0 to the mode
    towrite = byte | mode
    logging.debug("Byte to write to turn on the reqeusted mode %x" % towrite)
    bus.write_byte_data(SENSOR_ADDR, reg_addr, towrite)
    time.sleep(0.5)
    byte = bus.read_byte_data(SENSOR_ADDR,reg_addr)
    logging.info ("SYSMOD Register After turning on the required mode:%x" % byte)
    if (byte & 0b00000011) == mode:
        print("Sensor Turned in to requested mode")
    else:
        print("Sensor Not in the requested mode")
    return

def ReadXYZ_Data_Cfg():
    #Read out and decode the XYZ_DATA_CFG Register 0x0E
    reg_addr = 0x0E
    byte = bus.read_byte_data(SENSOR_ADDR,reg_addr)
    logging.info ("XYZ_DATA_CFG Register reading (%x):%x" % (reg_addr,byte))
    # Decode the values
    # High Pass Filter Out setting
    hpf = (byte & 0b00010000) >> 4
    logging.debug("High Pass Filter Out Flag %s" % hpf)
    if hpf == 0b1:
        print("Rs.2 High Pass Filter Output Enabled")
    else:
        print("Rs.2 Output data is NOT High Pass Filtered")
    # Full Scale Range setting
    fsr = (byte & 0b00000011)
    logging.debug("Full Scale Range setting %s" % fsr)
    if fsr == 0b00:
        print("Rs.2 Full Scale Range : +/- 2g")
    elif fsr == 0b01:
        print("Rs.2 Full Scale Range : +/- 4g")
    elif fsr == 0b10:
        print("Rs.2 Full Scale Range : +/- 8g")
    return

def SetFullScaleMode(mode):
    #Set the Full Scale Mode in the XYZ_DATA_CFG Register 0x0E
    # mode can be either TWOG, FOURG, EIGHTG
    reg_addr = 0x0e
    byte = bus.read_byte_data(SENSOR_ADDR,reg_addr)
    logging.info ("XYZ_DATA_CFG Register before setting (%x):%x" % (reg_addr,byte))
    logging.debug("Requested Full Scale mode of operation %x" % mode)
    # Modify the register to set bits 1 - 0 to the mode
    towrite = byte | mode
    logging.debug("Byte to write to turn on the Full Scale mode %x" % towrite)
    bus.write_byte_data(SENSOR_ADDR, reg_addr, towrite)
    time.sleep(0.5)
    byte = bus.read_byte_data(SENSOR_ADDR,reg_addr)
    logging.info ("XYZ_DATA_CFG Register After turning on the Full Scale mode:%x" % byte)
    if (byte & 0b00000011) == mode:
        print("Sensor Turned in to Full Scale mode")
    else:
        print("Sensor Not in the Full Scale mode")
    return

def ReadControlRegister2():
    #Read out and decode Control Register 2 0x2b
    reg_addr = 0x2B
    byte = bus.read_byte_data(SENSOR_ADDR,reg_addr)
    logging.info ("Control Register 2 reading (%x):%x" % (reg_addr,byte))
    # Decode the values
    # Self Test Enabled
    ste = (byte & 0b10000000) >> 7
    logging.debug("Self Test  Flag %s" % ste)
    if ste == 0b1:
        print("Rs.2 Self Test is Enabled")
    else:
        print("Rs.2 Self Test is Disabled")
    # Software Reset
    sr = (byte & 0b01000000) >> 6
    logging.debug("Self Test  Flag %s" % sr)
    if sr == 0b1:
        print("Rs.2 Software Reset  is Enabled")
    else:
        print("Rs.2 Software Reset is Disabled")
    # Sleep Mode power Scheme
    smps = (byte & 0b00011000)
    logging.debug("Sleep Mode Power Scheme bits %s" % smps)
    if smps == 0b00:
        print("Rs.2 Sleep Mode Power Mode: Normal")
    elif smps == 0b01:
        print("Rs.2 Sleep Mode Power Mode: Low Noise Low Power")
    elif smps == 0b10:
        print("Rs.2 Sleep Mode Power Mode: High Resolution")
    elif smps == 0b11:
        print("Rs.2 Sleep Mode Power Mode: Low Power")
    # Auto Sleep Mode flag
    sr = (byte & 0b00000100) >> 2
    logging.debug("Auto Sleep Mode Flag %s" % sr)
    if sr == 0b1:
        print("Rs.2 Auto Sleep Mode Flag is Enabled")
    else:
        print("Rs.2 Auto Sleep Mode Flag is Disabled")
    # Active Mode power Scheme
    amps = (byte & 0b00011000)
    logging.debug("Active Mode Power Scheme bits %s" % amps)
    if amps == 0b00:
        print("Rs.2 Active Mode Power Mode: Normal")
    elif amps == 0b01:
        print("Rs.2 Active Mode Power Mode: Low Noise Low Power")
    elif amps == 0b10:
        print("Rs.2 Active Mode Power Mode: High Resolution")
    elif amps == 0b11:
        print("Rs.2 Active Mode Power Mode: Low Power")
    return

def EnableSelfTest():
    # Enable the Self Test using CTRL_Register 0x2b
    reg_addr = 0x0e
    byte = bus.read_byte_data(SENSOR_ADDR,reg_addr)
    logging.info ("Control Register 2 before enabling Self Test (%x):%x" % (reg_addr,byte))
    # Modify the register to set bit 7 to 0b1
    towrite = byte | 0b10000000
    logging.debug("Byte to write to turn on the Self Test %x" % towrite)
    bus.write_byte_data(SENSOR_ADDR, reg_addr, towrite)
    time.sleep(0.5)
    in_st = 1
    while in_st:
        # Wait while the self test runs
        byte = bus.read_byte_data(SENSOR_ADDR,reg_addr)
        logging.info ("Control Register 2 After turning on the Self Test:%x" % byte)
        in_st = (byte & 0b10000000) >> 7
        if in_st == 0b1:
            print("Sensor In Self Test")
    print ("Self Test Completed")
    return

def SoftwareReset():
    # Perform a Software Reset using CTRL_Register 0x2b
    reg_addr = 0x0e
    byte = bus.read_byte_data(SENSOR_ADDR,reg_addr)
    logging.info ("Control Register 2 before enabling Software Reset (%x):%x" % (reg_addr,byte))
    # Modify the register to set bit 6 to 0b1
    towrite = byte | 0b01000000
    logging.debug("Byte to write to perform Software Reset %x" % towrite)
    bus.write_byte_data(SENSOR_ADDR, reg_addr, towrite)
    time.sleep(0.5)
    in_st = 1
    while in_st:
        # Wait while the Software Reset runs
        byte = bus.read_byte_data(SENSOR_ADDR,reg_addr)
        logging.info ("Control Register 2 After enabling Software Reset:%x" % byte)
        in_st = (byte & 0b01000000) >> 6
        if in_st == 0b1:
            print("Sensor In Software Reset")
    print ("Software Reset Completed")
    return


######### Calculation Routines

def ReadFullScaleMode():
    #Read out and decode the XYZ_DATA_CFG Register 0x0E for Full Scale Mode
    # Returns the multiplication factor to convert the reading to g values
    reg_addr = 0x0E
    byte = bus.read_byte_data(SENSOR_ADDR,reg_addr)
    logging.info ("Full Scale Mode Reading XYZ_DATA_CFG Register reading (%x):%x" % (reg_addr,byte))
    # Decode the values
    # Full Scale Range setting
    fsr = (byte & 0b00000011)
    logging.debug("Full Scale Mode Reading  setting %s" % fgerr)
    if fsr == 0b00:
        fsr_multiplier = 1/1024
    elif fsr == 0b01:
        fsr_multiplier = 1/512
    elif fsr == 0b10:
        fsr_multiplier = 1/256
    return fsr_multiplier
    
def ReadXAxisDataRegisters():
    # Read the data out from the X Axis data registers 0x01 - msb, 0x02 bits 7 - 4 - lsb
    data_addr = [0x02, 0x01]
    data_l = bus.read_byte_data(SENSOR_ADDR,data_addr[0])
    data_h = bus.read_byte_data(SENSOR_ADDR,data_addr[1])
    logging.debug("X Axis Data Register values (%x/%x):%x /%x" % (data_addr[0], data_addr[1], data_h, data_l))
    data_out = (data_h << 4) + (data_l >> 4)
    logging.info("X Axis Data Register combined %x" % data_out)
    return data_out

def ReadYAxisDataRegisters():
    # Read the data out from the Y Axis data registers 0x03 - msb, 0x04 bits 7 - 4 - lsb
    data_addr = [0x04, 0x03]
    data_l = bus.read_byte_data(SENSOR_ADDR,data_addr[0])
    data_h = bus.read_byte_data(SENSOR_ADDR,data_addr[1])
    logging.debug("Y Axis Data Register values (%x/%x):%x /%x" % (data_addr[0], data_addr[1], data_h, data_l))
    data_out = (data_h << 4) + (data_l >> 4)
    logging.info("Y Axis Data Register combined %x" % data_out)
    return data_out

def ReadZAxisDataRegisters():
    # Read the data out from the Z Axis data registers 0x05 - msb, 0x06 bits 7 - 4 - lsb
    data_addr = [0x06, 0x05]
    data_l = bus.read_byte_data(SENSOR_ADDR,data_addr[0])
    data_h = bus.read_byte_data(SENSOR_ADDR,data_addr[1])
    logging.debug("Z Axis Data Register values (%x/%x):%x /%x" % (data_addr[0], data_addr[1], data_h, data_l))
    data_out = (data_h << 4) + (data_l >> 4)
    logging.info("Z Axis Data Register combined %x" % data_out)
    return data_out

def CalculateValues():
    # Takes the readings and returns the x, y, z values
    fsr = ReadFullScaleMode()
    x = ReadXAxisDataRegisters()
    x = TwosCompliment(x)
    x = x * fsr
    y = ReadYAxisDataRegisters()
    y = TwosCompliment(y)
    y = y * fsr
    z = ReadZAxisDataRegisters ()
    z = TwosCompliment(z)
    z = z * fsr
    return [x, y, z]

def TwosCompliment(value):
    # Convert the given 12bit hex value to decimal using 2's compliment
    return -(value & 0b100000000000) | (value & 0b011111111111)
    
def HelpText():
    # show the help text
    print("**************************************************************************\n")
    print("Available commands: -")
    print("\n")
    print("T - Self Test")
    print("w - Who Am I")
    print("A - Read all data blocks")
    print("x - Read Axis Values")
    print("r - Software Reset")
    print("c - Read Configuration Data")
    print("s - Set System Mode")
    print("f - Set Full Scale Mode")
    print("e - Exit Program")



# main code loop

print ("Bostin Technology Ltd")
print ("Cogniot Products")
print ("Rs.2 - 3 Axis Rate Sensor")
print ("")
print ("Press h for help")
print ("")

bus = smbus.SMBus(1)

logging.basicConfig(filename="Rs_2.txt", filemode="w", level=logging.DEBUG, format='%(asctime)s:%(levelname)s:%(message)s')


while True:
    choice = input ("Select Menu Option:")

    if choice == "H" or choice == "h":
        HelpText()
    elif choice == "A":
        ReadAllData()
    elif choice == "E" or choice == "e":
        sys.exit()
    elif choice == "T":
        EnableSelfTest()
    elif choice == "w":
        WhoAmI()
    elif choice == "x":
        g_force = CalculateValues()
        print(" Y |             :%f" % g_force[1])
        print("   |")
        print("   |   Z         :%f" % g_force[2])
        print("   |  / ")
        print("   | /")
        print("   |_________ X  :%f" % g_force[0])
        print("/n")
    elif choice == "r":
        SoftwareReset()
    elif choice == "c":
        ReadF_Setup()
        ReadSystemMode()
        ReadXYZ_Data_Cfg()
        ReadControlRegister2()
    elif choice == "s":
        #Set System Mode()
        print("Select =Mode:-")
        print("1 - STANDBY")
        print("2 - WAKE")
        print("3 - SLEEP")
        print("0 - return")
        mode = int(input ("Mode:"))
        if mode == 1:
            SetSystemMode(STANDBY)
        elif mode == 2:
            SetSystemMode(WAKE)
        elif mode == 3:
            SetSystemMode(SLEEP)
    elif choice == "f":
        # Set Full Scale Mode()
        print("Select Full Scale Range:-")
        print("2 - 2 G")
        print("4 - 4 G")
        print("8 - 8 G")
        print("0 - return")
        full = int(input ("Range:"))
        if full == 2:
            SetFullScaleMode(TWOG)
        elif full == 2:
            SetFullScaleMode(FOURG)
        elif full == 3:
            SetFullScaleMode(EIGHTG)
    else:
        print("Unknown Option")
        print("")
        print ("Press h for help")

