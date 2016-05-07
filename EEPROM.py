#!/usr/bin/env python3

"""
iCogs Ts.1 Reader

For more information see www.BostinTechnology.com

Supplied with all iCogs is an additional EEPROM that can contains default information about
the associated iCog and an area where data can be written and retrieved. This software
provides the links into this software.


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

#TODO: Update for the LS.1 and other iCogs.

#TODO: Make production ready so Paul could use it, or Liz for that matter.


import smbus
import logging
import sys
import time
import random

EEPROM_ADDR = 0x50


def CalculateChecksum():
    # Calculate the EEPROM checksum to go into bytes 0x0e and 0x0f
    calc_sum = 0
    print("Calculating Checksum")
    # read each byte of data from 0x00 to 0xff
    for addr in range(0x00,0x80):
        byte = bus.read_byte_data(EEPROM_ADDR,addr)
        logging.debug ("Read Checksum Data Byte %x:%x" % (addr, byte))
        if addr == 0x0e or addr == 0x0f:
            # ignore the checksum bytes
            byte = 0x00
        calc_sum = calc_sum + byte
    logging.debug("Sum of all bytes %x" % calc_sum)
    checksum_h = ((calc_sum & 0xff00) >> 16)
    checksum_l = (calc_sum & 0xff)
    logging.info("Calculated Checksum %x/%x" % (checksum_h, checksum_l))
    return checksum_h, checksum_l

def WriteChecksum(chk):
    # write the given checksum to the EEPROM
    logging.debug("Writing data bytes %x/%x to the checksum" % (chk[0], chk[1]))
    bus.write_byte_data(EEPROM_ADDR, 0x0e, chk[0])
    time.sleep(0.5)
    bus.write_byte_data(EEPROM_ADDR, 0x0f, chk[1])
    time.sleep(0.5)
    logging.info("Checksum Written")
    print("Written Checksum")
    return

def VerifyChecksum(chk):
    #Check the checksum matches the calculated value
    logging.info("Verifying the checksum")
    chk_read_h = bus.read_byte_data(EEPROM_ADDR, 0x0e)
    time.sleep(0.5)
    chk_read_l = bus.read_byte_data(EEPROM_ADDR, 0x0f)
    logging.debug("Checksum Values read from EEPROM %x/%x" % (chk[0], chk[1]))
    if (chk_read_h == chk[0]) and (chk_read_l == chk[1]):
        print("Checksum matches")
        logging.debug("Checksum matches calculated value")
    else:
        print("Checksum Error")
        logging.critical("Checksum Error")
    return



def WriteMapVersion():
    # Write the EEPROM Memory Map Version, currently 0.2
    # Writes 0x00 to the upper byte and 0x02 to the lower byte
    logging.info("Writing Map Version 0.2")
    bus.write_byte_data(EEPROM_ADDR, 0x00, 0x00)
    time.sleep(0.5)
    byte_h = bus.read_byte_data(EEPROM_ADDR, 0x00)
    bus.write_byte_data(EEPROM_ADDR, 0x01, 0x02)
    time.sleep(0.5)
    byte_l = bus.read_byte_data(EEPROM_ADDR, 0x01)
    logging.debug("Writing Map Version Response %x/%x" % (byte_h, byte_l))
    if byte_h == 0x00 and byte_l == 0x02:
        print("Map Version written successfully")
        logging.info("Map Version written successfully")
    else:
        print("Failed to write MAP Version")
        logging.info("Map Version written FAILED")
    return

def WriteDeviceBus():
    # Write the EEPROM Device Bus with 0b00000001 as this device is I2C
    logging.info("Writing Device Bus 0b00000001")
    bus.write_byte_data(EEPROM_ADDR, 0x10, 0x01)
    time.sleep(0.5)
    byte = bus.read_byte_data(EEPROM_ADDR, 0x10)
    logging.debug("Writing Device Bus Response %x" % byte)
    if byte == 0x01:
        print("Device Bus written successfully")
        logging.info("Device Bus written successfully")
    else:
        print("Failed to write MAP Version")
        logging.info("Device Bus written FAILED")
    return

def WriteSensorI2CAddress():
    # Write the EEPROM Device Bus with 0x5f as this is the I2C address of the sensor
    logging.info("Writing I2C Address 0x5f")
    bus.write_byte_data(EEPROM_ADDR, 0x11, 0x5f)
    time.sleep(0.5)
    byte = bus.read_byte_data(EEPROM_ADDR, 0x11)
    logging.debug("Writing I2C Address Response %x" % byte)
    if byte == 0x5f:
        print("I2C Address written successfully")
        logging.info("I2C Address written successfully")
    else:
        print("Failed to write I2C Address")
        logging.info("Device Bus written FAILED")
    return

def WriteBlanks():
    #Write 0x00 to the values that need to be blank.
    add_list = []
    add_list = [0x12, 0x13, 0x14, 0x17, 0x18, 0x19, 0x1A, 0x1B, 0x1C, 0x1D, 0x1E, 0x1F]
    success = True
    for x in add_list:
        bus.write_byte_data(EEPROM_ADDR, x, 0x00)
        logging.debug("Writing memory address %x with 0x00" % x)
        time.sleep(0.5)
        byte = bus.read_byte_data(EEPROM_ADDR, x)
        logging.debug("Writing memory address response %x with 0x00" % byte)
        if byte != 0x00:
            # flay that a byte failed to clear
            success = False
        print(".", end="", flush=True)
    print("\n")
    if success:
        print("Remainder of Data Written successfully")
        logging.info("Blank Values written successfully")
    else:
        print("Failed to write Remainder of data")
        logging.info("Remainder of Data Written FAILED")
    return

def WriteSensorType():
    # Each sensor has unique values to identify it, for the Ts.1 write 0x03, 0x01
    logging.info("Writing Sensor Type 0x03, 0x01")
    bus.write_byte_data(EEPROM_ADDR, 0x15, 0x03)
    time.sleep(0.5)
    byte_h = bus.read_byte_data(EEPROM_ADDR, 0x15)
    bus.write_byte_data(EEPROM_ADDR, 0x16, 0x01)
    time.sleep(0.5)
    byte_h = bus.read_byte_data(EEPROM_ADDR, 0x15)
    byte_l = bus.read_byte_data(EEPROM_ADDR, 0x16)
    logging.debug("Writing Sensor type Response %x/%x" % (byte_h, byte_l))
    if byte_h == 0x03 and byte_l == 0x01:
        print("Sensor type written successfully")
        logging.info("Sensor type written successfully")
    else:
        print("Failed to write Sensor type")
        logging.info("Sensor type written FAILED")
    return

def ClearCalibrationData():
    # Write 0x00 to all the calibration values to effectivily clear it
    clear_list = []
    clear_list = [0x20, 0x30, 0x40, 0x50, 0x60, 0x70]
    success = True
    for x in clear_list:
        for y in range (0x00, 0x0f):
            bus.write_byte_data(EEPROM_ADDR, x+y, 0x00)
            logging.debug("Writing memory address %x" % (x+y))
            time.sleep(0.5)
            byte = bus.read_byte_data(EEPROM_ADDR, x+y)
            logging.debug("Writing memory address response %x" % byte)
            if byte != 0x00:
                success = False
                logging.info("Writing memory address failed")
            print(".", end="", flush=True)
    print("\n")
    if success:
        print("Calibration Data cleared successfully")
        logging.info("Calibration Data cleared successfully")
    else:
        print("Failed to clear Calibration Data cleared")
        logging.info("Clearing of Calibration Data FAILED")
    return

def WriteDefaults():
    # Write all default values back into the EEPROM
    WriteMapVersion()
    WriteDeviceBus()
    WriteSensorI2CAddress()
    WriteBlanks()
    WriteSensorType()
    ClearCalibrationData()
    print("Write Default Values completed")

def ReadUUID():
    # Read out the sensor unique value
    logging.info("Reading the UUID Bytes")
    uuid = 0
    for addr in range (0xFC, 0x100):
        byte = bus.read_byte_data(EEPROM_ADDR, addr)
        logging.debug("UUID Byte %x Read value %x" % (addr, byte))
        uuid = (uuid << 8) + byte
    logging.info("uuid value %8x" % uuid)
    print("UUID :%8x" % uuid)
    return

def ReadEEPROMManufacturer():
    # Read the EEPROM manufacturer ID
    logging.info("Reading EEPROM Manufacturer ID")
    byte = bus.read_byte_data(EEPROM_ADDR, 0xFA)
    logging.debug("EEPROMT Manufacturer ID Response %x" % byte)
    print("EEPROM Manufacture : %x" % byte)
    logging.info("EEPROM Manufacturer Response %x" % byte)
    return

def ReadEEPROMDeviceID():
    # Read the EEPROM manufacturer Device ID
    logging.info("Reading EEPROM Device Manufacturer ID")
    byte = bus.read_byte_data(EEPROM_ADDR, 0xFB)
    logging.debug("EEPROMT Manufacturer Device ID Response %x" % byte)
    print("EEPROM Manufacture Device: %x" % byte)
    logging.info("EEPROM Manufacturer DeviceResponse %x" % byte)
    return

def ReadEEPROMData():
    # Read the EEPROM manufacuters data
    ReadUUID()
    ReadEEPROMManufacturer()
    ReadEEPROMDeviceID()
    return

def WriteExampleData():
    # Write some data into a user defined area for storage
    # Writes 4 random bytes into local 0x36
    success = True
    written = []
    for addr in range(0x36, 0x3A):
        value = random.randint(0x00, 0xFF)
        written.append(hex(value))
        bus.write_byte_data(EEPROM_ADDR, addr, value)
        logging.debug("Writing Example data at address %x with %x" % (addr, value))
        time.sleep(0.5)
        byte = bus.read_byte_data(EEPROM_ADDR, addr)
        logging.debug("Writing Example data at address response %x" % byte)
        if byte != value:
            success = False
            logging.info("Writing Example data at address failed")
        print(".", end="", flush=True)
    print ("\n")
    if success:
        print("Example data written successfully %s" % written)
        logging.info("Example data written successfully")
    else:
        print("Failed to write example data")
        logging.info("Writing of example Data FAILED")
    return

def ReadExampleData():
    # Read the data from the user defined area
    # Read the example data from a user defined area for storage
    values = []
    for addr in range(0x36, 0x3A):
        byte = bus.read_byte_data(EEPROM_ADDR, addr)
        logging.debug("Reading Example data from address response %x" % byte)
        values.append(hex(byte))
        print(".", end="", flush=True)
    print ("\n")
    print("Example data read from the EEPROM %s" % values)
    logging.info("Example data read from the eeprom %s" % values)
    return

def ReadAllData():
    # Read out all 255 bytes from the device
    # capture all the readings for printing later
    values = []
    # read each byte of data from 0x00 to 0xff
    for addr in range(0x00,0x100):
        byte = bus.read_byte_data(EEPROM_ADDR,addr)
        logging.debug ("Read All Data Byte %x:%x" % (addr, byte))
        values.append(byte)

    # print out the data, looping in steps of 16 to print the data out in blocks
    for i in range(0x00, 0xf1, 0x10):
        print("Addr:%2x "% i, end="")
        for j in range(0x0, 0x10):
            print(" %4x" % values[i+j], end="")
        print(" ")
    return




def HelpText():
    # show the help text
    print("**************************************************************************\n")
    print("Available commands: -")
    print("W - Write map defaults")
    print("U - Read EEPROM Manufactureres data")
    print("X - write eXample data")
    print("R - Read example data")
    print("A - read All data")
    print("C - write Checksum")
    print("v - Verify Checksum")
    print("e - Exit Program")



# main code loop

print ("Bostin Technology Ltd")
print ("Cogniot Products")
print ("iCogs EEPROM program")
print ("")
print ("Press h for help")
print ("")

bus = smbus.SMBus(1)

logging.basicConfig(filename="eeprom.txt", filemode="w", level=logging.DEBUG, format='%(asctime)s:%(levelname)s:%(message)s')


while True:
    choice = input ("Select Menu Option:")

    if choice == "H" or choice == "h":
        HelpText()
    elif choice == "W":
        WriteDefaults()
    elif choice == "X":
        WriteExampleData()
    elif choice == "R":
        ReadExampleData()
    elif choice == "U":
        ReadEEPROMData()
    elif choice == "A":
        ReadAllData()
    elif choice =="C":
        csum = CalculateChecksum()
        WriteChecksum(csum)
        VerifyChecksum(csum)
    elif choice == "v":
        VerifyChecksum(CalculateChecksum())
    elif choice == "E" or choice == "e":
        sys.exit()


