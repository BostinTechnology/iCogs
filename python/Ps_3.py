#!/usr/bin/env python3

"""
iCogs Ps.3 Reader

For more information see www.BostinTechnology.com

The Ps.3 is based on the MPL3115A2 Absolute Pressure Sensor, but like all iCogs,
comes with an additional EEPROM to provide the capability to store additional information e.g
enviromental specific data.

This module uses 'Repeated Start' (see www.i2c-bus.org/repeated-start-condition) so requires
the following
1. Navigate to /sys/module/i2c_bcm2708/parameters
2. Modify 'combined'
    sudo nano combined
    change N to Y
    Save and Exit

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
## This software is completely new and copied from Ps.2
##
##

#BUG: Need to check all uses of bit setting, ORing bytes is great for gsetting bits
#       but no use for clearing bits!
#           towrite = (byte & mask) | mode

#TODO: Use reg_addr = 0xxx in all registers

# Functions to implement
# Min / Max values
# read and decode registers


import smbus
import logging
import time
import math
import sys
import subprocess

SENSOR_ADDR = 0x60

# The time between a write and subsequent read
WAITTIME = 0.5

#Sensor Modes
STANDBY = 0b0
ACTIVE = 0b1

#Output Modes
NORMAL = 0b0
RAW = 0b01000000

#Altimeter Modes
ALTIMETER = 0b10000000
BAROMETER = 0b00000000

def SetRepeatedStartMode():
    # This function sets the I2C bus to use Repeated Start Mode
    # Command to run as Superuser is
    #   echo -n 1 > /sys/module/i2c_bcm2708/parameters/combined
    logging.info("Setting Repeated Start for I2C comms")
    try:
        response = subprocess.call(["echo -n 1 > /sys/module/i2c_bcm2708/parameters/combined"], shell=True)
        logging.debug("Used subprocess call to set Repeated Start command and got this response %x" % response)
    except:
        e = sys.exc_info()
        logging.critical("Failed to Set Repeated Start mode, program aborted with response %s: %s" % (e[0], e[1]))
        print("Failed to Set Repeated Start mode, program aborted")
        sys.exit()


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
    # Read out and confirm the 'Who Am I' value of 0xC4
    byte = bus.read_byte_data(SENSOR_ADDR,0x0C)
    if byte == 0xC4:
        print("Identified as Correct Device :%x" % byte)
    else:
        print("Check the Device WhoAm I as it is unrecognised")
    logging.info ("Who Am I - Address 0x0C (0xC4):%s" % byte)
    return

def SetSystemMode(mode):
    #Set the System Mode in the System Mode Register 0x11
    # mode can be either STANDBY (0b0) or ACTIVE (0b1)
    reg_addr = 0x26
    mask = 0b00000001
    byte = bus.read_byte_data(SENSOR_ADDR,reg_addr)
    logging.info ("Set System Mode (CTRL_REG1) before setting (%x): %x" % (reg_addr,byte))
    logging.debug("Requested System Mode of operation %x" % mode)
    if (byte & mask) != mode:
        # Modify the register to set bit 0 to the mode
        towrite = (byte & ~mask) | mode
        logging.debug("Byte to write to turn on the requested system Mode: %x" % towrite)
        bus.write_byte_data(SENSOR_ADDR, reg_addr, towrite)
        time.sleep(WAITTIME)
        byte = bus.read_byte_data(SENSOR_ADDR,reg_addr)
        logging.info ("Set System Mode (CTRL_REG1) Register After turning on the required mode: %x" % byte)
        if (byte & mask) == mode:
            print("Sensor Turned in to requested System Mode: %x" % mode)
        else:
            print("Sensor Not in the requested System Mode: %x" % mode)
    else:
        logging.debug("Set System Mode is already set in the required mode")
    return

def SoftwareReset():
    # Perform a Software Reset using CTRL_Register 0x26
    # After the software reset, it automatically clears the bit so no need to check / merge
    reg_addr = 0x26
    value = 0b00000100
    byte = bus.read_byte_data(SENSOR_ADDR,reg_addr)
    logging.info ("Control Register 1 before enabling Software Reset (%x):%x" % (reg_addr,byte))
    # Modify the register to set bit 2 to 0b1
    towrite = byte | value
    logging.debug("Byte to write to perform Software Reset %x" % towrite)
    bus.write_byte_data(SENSOR_ADDR, reg_addr, towrite)
    time.sleep(0.5)
    in_st = 1
    while in_st:
        # Wait while the Software Reset runs
        byte = bus.read_byte_data(SENSOR_ADDR,reg_addr)
        logging.info ("Control Register 1 After enabling Software Reset:%x" % byte)
        in_st = (byte & value) >> 2
        if in_st == 0b1:
            print("Sensor In Software Reset")
    print ("Software Reset Completed")
    logging.debug("Software Reset Completed")
    return

def SetOutputMode(mode):
    #Set the output mode in the CTRL_REG1 Register 0x26
    # mode can be either NORMAL or RAW
    reg_addr = 0x26
    mask = 0b01000000
    byte = bus.read_byte_data(SENSOR_ADDR,reg_addr)
    logging.info ("Set Output Mode (CTRL_REG1) before setting (%x): %x" % (reg_addr,byte))
    logging.debug("Requested Output Mode of operation %x" % mode)
    if (byte & mask) != mode:
        # Modify the register to set bit 0 to the mode
        towrite = (byte & ~mask) | mode
        logging.debug("Byte to write to turn on the requested Output Mode: %x" % towrite)
        bus.write_byte_data(SENSOR_ADDR, reg_addr, towrite)
        time.sleep(WAITTIME)
        byte = bus.read_byte_data(SENSOR_ADDR,reg_addr)
        logging.info ("Set Output Mode (CTRL_REG1) Register After turning on the required mode: %x" % byte)
        if (byte & mask) == mode:
            print("Sensor Turned in to requested Output Mode: %x" % mode)
        else:
            print("Sensor Not in the requested Output Mode: %x" % mode)
    else:
        logging.debug("Set Output Mode is already set in the required mode")
    return

def ReadOutputMode():
    # Read the Output mode bit and return RAW or NORMAL Mode
    reg_addr = 0x26
    byte = bus.read_byte_data(SENSOR_ADDR,reg_addr)
    logging.info ("OUtput Mode Control Register Reading reading (%x):%x" % (reg_addr,byte))
    # Decode the values
    # Output Mode is bit 6
    opm = (byte & 0b01000000)
    logging.debug("Output Mode Reading setting %s" % opm)
    if opm == RAW:
        return RAW
    return NORMAL

def SetAltimeterMode(mode):
    #Set the output mode in the CTRL_REG1 Register 0x26
    # mode can be either ALTIMETER = 0b10000000 or BAROMETER = 0b00000000
    reg_addr = 0x26
    mask = 0b10000000
    byte = bus.read_byte_data(SENSOR_ADDR,reg_addr)
    logging.info ("Set Altimeter - Barometer Mode (CTRL_REG1) before setting (%x): %x" % (reg_addr,byte))
    logging.debug("Requested Output Mode of operation %x" % mode)
    if (byte & mask) != mode:
        # Modify the register to set bit 0 to the mode
        towrite = (byte & ~mask) | mode
        logging.debug("Byte to write to turn on the requested Altimeter - Barometer Mode: %x" % towrite)
        bus.write_byte_data(SENSOR_ADDR, reg_addr, towrite)
        time.sleep(WAITTIME)
        byte = bus.read_byte_data(SENSOR_ADDR,reg_addr)
        logging.info ("Set Altimeter - Barometer Mode (CTRL_REG1) Register After turning on the required mode: %x" % byte)
        if (byte & mask) == mode:
            print("Sensor Turned in to requested Altimeter - Barometer Mode: %x" % mode)
        else:
            print("Sensor Not in the requested Altimeter - Barometer Mode: %x" % mode)
    else:
        logging.debug("Set Altimeter - Barometer Mode is already set in the required mode")
    return

def ReadAltimeterMode():
    # Read the Output mode bit and return mode (either ALTIMETER = 0b10000000 or BAROMETER = 0b00000000)
    reg_addr = 0x26
    byte = bus.read_byte_data(SENSOR_ADDR,reg_addr)
    logging.info ("Altimeter - Barometer Mode Control Register Reading reading (0x%x):%x" % (reg_addr,byte))
    # Decode the values
    # Altimeter - Barometer Mode is bit 7
    opm = (byte & 0b10000000)
    logging.debug("Altimeter - Barometer Mode Reading setting %s" % opm)
    if opm == ALTIMETER:
        logging.info("Altimeter - Barometer Mode Control Register is Altimeter Mode")
        return ALTIMETER
    logging.info("Altimeter - Barometer Mode Control Register is Barometer Mode")
    return BAROMETER

def SetBarometricInput(sealevel):
    # This is used to calibrate the sensor for the difference between current altitude and sea level.
    # input is the equivalent Sea level presure, in 2 Pa units
    # Default value is 1 standard atmosphere (atm) is defined as 101.325 kPa
    data_addr = [0x14, 0x15]
    # The value stored in the register is in 2 Pa units, so divide given value by 2 and remove fraction
    sealevelvalue = int(sealevel / 2)
    logging.info("Requested Sea Level Value and equivalent data to write: %f / %f" % (sealevel, sealevelvalue))
    # Read out current reading first
    data_h = bus.read_byte_data(SENSOR_ADDR,data_addr[0])
    data_l = bus.read_byte_data(SENSOR_ADDR,data_addr[1])
    logging.debug("Barometric Input Equivalent Sea Level current values (%x/%x):%x /%x" % (data_addr[0], data_addr[1], data_h, data_l))
    current_offset = (data_h << 8) + data_l
    logging.info("Current Sea Level offset %f and requried Sea Level Offset %f" % (current_offset, sealevelvalue))
    if current_offset != sealevelvalue:
        # The value required is different to the value currently set
        towrite_h = (sealevelvalue >> 8)
        towrite_l = (sealevelvalue & 0b0000000011111111)
        # towrite_l may be 2 bytes, need to check during testing
        logging.debug("New Sea Levels (high & low bytes) to Write in registers (%x, %x): %x / %x)" % (towrite_h, towrite_l, data_addr[0], data_addr[1]))
        bus.write_byte_data(SENSOR_ADDR, data_addr[0], towrite_h)
        time.sleep(WAITTIME)
        bus.write_byte_data(SENSOR_ADDR, data_addr[1], towrite_l)
        time.sleep(WAITTIME)
        byte_h = bus.read_byte_data(SENSOR_ADDR,data_addr[0])
        byte_l = bus.read_byte_data(SENSOR_ADDR,data_addr[1])
        logging.info ("Set Barometric Input Equivalent Sea Level after writing the required value: %x /  %x" % (byte_h, byte_l))
        byte = (byte_h << 8) + byte_l
        if byte == sealevelvalue:
            print("Barometric Input Equivalent Sea Level set to the requested value: %x" % byte)
        else:
            print("Barometric Input Equivalent Sea Level NOT set to the requested value: %x" % byte)
    else:
        logging.debug("Barometric Input Equivalent Sea Level is already set to the requested value")
    return

def ReadBarometricOffset():
    # This is used to calibrate the sensor for the difference between current altitude and sea level.
    # Value stored is the equivalent Sea level presure, in 2 Pa units
    # Default value is 1 standard atmosphere (atm) is defined as 101.325 kPa
    data_addr = [0x14, 0x15]
    # Read out current reading
    data_h = bus.read_byte_data(SENSOR_ADDR,data_addr[0])
    data_l = bus.read_byte_data(SENSOR_ADDR,data_addr[1])
    logging.debug("Barometric Input Equivalent Sea Level current values (%x/%x):%x /%x" % (data_addr[0], data_addr[1], data_h, data_l))
    current_offset = ((data_h << 8) + data_l) * 2
    logging.info("Current Sea Level offset %f" % current_offset)
    print("Barometric Input Equivalent Sea Level is set to: %d" % current_offset)
    return

def ReadControlRegister1():
    #Read out and decode Control Register 1 0x26
    reg_addr = 0x26
    byte = bus.read_byte_data(SENSOR_ADDR,reg_addr)
    logging.info ("Control Register 1 reading (%x):%x" % (reg_addr,byte))
    # Decode the values
    # SBYB - perodic reading mode
    sbyb = (byte & 0b00000001)
    logging.debug("System Mode %s" % sbyb)
    if sbyb == 0b1:
        print("Ps.3 System Mode is ACTIVE")
    else:
        print("Ps.3 System Mode is in STANDBY")
    # Software Reset
    sr = (byte & 0b00000100) >> 2
    logging.debug("Software Reset Flag %s" % sr)
    if sr == 0b1:
        print("Ps.3 Software Reset  is Enabled")
    else:
        print("Ps.3 Software Reset is Disabled")
    # Raw Mode
    raw = (byte & 0b01000000) >> 6
    logging.debug("Raw Mode  Flag %s" % raw)
    if raw == 0b1:
        print("Ps.3 Raw Mode is Enabled")
    else:
        print("Ps.3 Raw Mode is Disabled")
    # Altitude / Barometric Mode
    aorb = (byte & 0b10000000) >> 7
    logging.debug("Altitude or Barometric Mode Flag %s" % aorb)
    if aorb == 0b1:
        print("Ps.3 Sensor is in Altimeter Mode")
    else:
        print("Ps.3 Sensor is in Barometer Mode")
    return


######## Calculation Routines Used

def TwosCompliment(value):
    # Convert the given 12bit hex value to decimal using 2's compliment
    return -(value & 0b100000000000) | (value & 0b011111111111)

def TwosCompliment20(value):
    # Convert the given 20bit hex value to decimal using 2's compliment
    return -(value & 0b10000000000000000000) | (value & 0b01111111111111111111)

def SignedNumber16(value):
    # Takes the given number and return a signed version of it
    # Assumes the number is 16 bit
    sign = (value & 0b1000000000000000) >> 15
    value = value & 0b0111111111111111
    if sign == 0b1:
        # Sign bit is set, so number is negative
        value = value * -1
    return value


def SignedNumber24(value):
    # Takes the given number and return a signed version of it
    # Assumes the number is 24 bit
    sign = (value & 0b100000000000000000000000) >> 23
    value = value & 0b011111111111111111111111
    if sign == 0b1:
        # Sign bit is set, so number is negative
        value = value * -1
    return value

def SignedNumber32(value):
    # Takes the given number and return a signed version of it
    # Assumes the number is 24 bit
    sign = (value & 0b10000000000000000000000000000000) >> 31
    value = value & 0b01111111111111111111111111111111
    if sign == 0b1:
        # Sign bit is set, so number is negative
        value = value * -1
    return value

def ReadTemperature():
    # Read the data out from the Temperature Registers OUT_T_MSB and OUT_T_LSB data registers
    # Register 0x04 - msb, 0x05 bits 7 - 4 - lsb
    # Number is stored as Q8.4, not Q12.4 as stated in the datasheet
    data_addr = [0x04, 0x05]
    data_h = bus.read_byte_data(SENSOR_ADDR,data_addr[0])
    data_l = bus.read_byte_data(SENSOR_ADDR,data_addr[1])
    logging.debug("OUT_T Data Register values (0x%x/0x%x):%x /%x" % (data_addr[0], data_addr[1], data_h, data_l))
    # value is 8 its from data_h and uppper 4 bits from data_l, but for now just merge them together
    data_out = (data_h << 8) + data_l
    # output is a signed number.
    data_out = SignedNumber16(data_out)
    # Because I merged the numbers together earlier, I now need to divide by 256 to get the right number
    data_out = data_out / 256
    logging.info("OUT_T Registers combined %x" % data_out)
    return data_out

def ReadPressure():
    # Read and retuyrn the pressure value read from the OUT_P_MSB, OUT_P_CSB and OUT_P_LSB registers
    # Registers are 0x01, 0x02, 0x03
    # Value read is dependent on the mode of operation
    data_addr = [0x01, 0x02, 0x03]
    # units is used to return the units of the value
    units = ""
    data_h = bus.read_byte_data(SENSOR_ADDR,data_addr[0])
    data_c = bus.read_byte_data(SENSOR_ADDR,data_addr[1])
    data_l = bus.read_byte_data(SENSOR_ADDR,data_addr[2])
    logging.debug("OUT_P Data Register values (%x/%x/%x):%x / %x / %x" % (data_addr[0], data_addr[1], data_addr[1], data_h, data_c, data_l))
    # The value in the register is dependent on the mode of operation, Altitude or barometer or raw.
    if ReadOutputMode() == RAW:
        # In this mode, the value is all 24 bits and no fraction / sign
        logging.info("Mode is RAW, so the value is retured")
        data_out = (data_h << 16) + (data_c << 8) + data_l
        logging.debug("24 bit number retrieved from the sensor: %x" % data_out)
        units = ""
        return [data_out, units]
    if ReadAltimeterMode() == ALTIMETER:
        # In this mode, the data is a 20 bit signed Q16.4 format number
        # Therefore current value needs signing and dividing by 65536
        data_out = (data_h << 24) + (data_c << 16) + (data_l << 8)
        logging.debug("32 bit number retrieved from the sensor: %x" % data_out)
        data_out = SignedNumber32(data_out)
        logging.debug("Altimeter Pressure Converted using Signed Number %f" % data_out)
        data_out = data_out / 65536
        logging.info("Altimeter Pressure Value being returned %f" % data_out)
        units = "Meters"
    else:
        # In this mode the data is in signed Q18.2
        # Therefore current value needs signing and dividing by 64
        data_out = (data_h << 16) + (data_c << 8) + data_l
        logging.debug("24 bit number retrieved from the sensor: %x" % data_out)
        # pressure is unsigned
        #data_out = SignedNumber(data_out)
        #logging.debug("Barometer Pressure Converted using Signed Number %f" % data_out)
        data_out = data_out / 64
        logging.info("Barometer Pressure Value being returned %f" % data_out)
        units = "Pascals"
    return [data_out, units]

def ReadTemperatureDelta():
    # Read the data out from the Temperature Delta Registers OUT_T_DELTA_MSB and OUT_T_DELTA_LSB data registers
    # Register 0x0A - msb, 0x0B bits 7 - 4 - lsb
    # Number is stored as Q8.4, not Q12.4 as stated in the datasheet as degress C

    #Not sure if this is stored as a 2'c compliment, assumes so at the moment

    data_addr = [0x0A, 0x0B]
    data_h = bus.read_byte_data(SENSOR_ADDR,data_addr[0])
    data_l = bus.read_byte_data(SENSOR_ADDR,data_addr[1])
    logging.debug("OUT_T Delta Data Register values (%x/%x):%x /%x" % (data_addr[0], data_addr[1], data_h, data_l))
    # value is 8 its from data_h and uppper 4 bits from data_l, but for now just merge them together
    data_out = (data_h << 8) + data_l
    # output is a 2's compliment number.
    data_out = TwosCompliment(data_out)
    # Because I merged the numbers together earlier, I now need to divide by 256 to get the right number
    data_out = data_out / 256
    logging.info("OUT_T Delta Registers combined %x" % data_out)
    return data_out

def ReadPressureDelta():
    # Read and return the pressure delta value read from the OUT_P_DELTA_MSB, OUT_P_DELTA_CSB and OUT_P_DELTA_LSB registers
    # Registers are 0x07, 0x08, 0x09
    # Value read is dependent on the mode of operation
    data_addr = [0x07, 0x08, 0x09]
    # units is used to return the units of the value
    units = ""
    data_h = bus.read_byte_data(SENSOR_ADDR,data_addr[0])
    data_c = bus.read_byte_data(SENSOR_ADDR,data_addr[1])
    data_l = bus.read_byte_data(SENSOR_ADDR,data_addr[2])
    logging.debug("OUT_P_DELTA Data Register values (%x/%x/%x):%x / %x / %x" % (data_addr[0], data_addr[1], data_addr[2], data_h, data_c, data_l))
    data_out = (data_h << 16) + (data_c << 8) + data_l
    logging.debug("24 bit number retrieved from the sensor: %x" % data_out)
    # The value in the register is dependent on the mode of operation, Altitude or barometer or raw.
    if ReadOutputMode() == RAW:
        # In this mode, the value is not used
        logging.info("Mode is RAW, no value is retured")
        return [0, units]
    if ReadAltimeterMode() == ALTIMETER:
        # In this mode, the data is a 20 bit 2's compliment number, with 4 decimal places
        # Therefore current value needs 2'c compliment and dividing by 256 as the lowest 8 bits are fractions
        data_out = TwosCompliment20(data_out)
        logging.debug("Altimeter Pressure Delta Converted using 2's Compliment Number %f" % data_out)
        data_out = data_out / 256
        logging.info("Altimeter Pressure Delta Value being returned %f" % data_out)
        units = "Meters"
    else:
        # In this mode the data is a 2'c compliment number with 2 bits being fraction
        # Therefore current value needs 2's compliment and dividing by 64
        data_out = TwosCompliment20(data_out)
        logging.debug("Barometer Pressure Delta Converted using 2's compliment Number %f" % data_out)
        data_out = data_out / 64
        logging.info("Barometer Pressure Delta Value being returned %f" % data_out)
        units = "Pascals"
    return [data_out, units]

def HelpText():
    # show the help text
    print("**************************************************************************\n")
    print("Available commands: -")
    print("\n")
    print("t - Read Temperature")
    print("l - Read Temperature Delta")
    print("w - Who Am I")
    print("A - Read all data blocks")
    print("r - Software Reset")
    print("c - Read Configuration Data")
    print("o - Set Output Mode")
    print("s - Set System Mode")
    print("a - Set Measurement Mode")
    print("p - Read Pressure")
    print("B - Read Current Barometric Offset")
    print("b - Set Barometric Input")
    print("d - Read Pressure Deltas")

    print("e - Exit Program")



# main code loop

print ("Bostin Technology Ltd")
print ("CognIot Products")
print ("")
print ("Press h for help")
print ("")

bus = smbus.SMBus(1)

logging.basicConfig(filename="Ps_3.txt", filemode="w", level=logging.DEBUG, format='%(asctime)s:%(levelname)s:%(message)s')

SetRepeatedStartMode()

while True:
    choice = input ("Select Menu Option:")

    if choice == "H" or choice == "h":
        HelpText()
    elif choice == "A":
        ReadAllData()
    elif choice == "E" or choice == "e":
        sys.exit()
    elif choice == "t":
        temp = ReadTemperature()
        print("Current Temperature %f Deg C" % temp)
    elif choice == "l":
        temp_delta = ReadTemperatureDelta()
        print("Current Temperature Delta %f Deg C" % temp_delta)
    elif choice == "w":
        WhoAmI()
    elif choice == "B":
        ReadBarometricOffset()
    elif choice == "p":
        pres = ReadPressure()
        print("\nCurrent Reading is %f %s" % (pres[0], pres[1]))
    elif choice == "d":
        pres_delta = ReadPressureDelta()
        print("\nCurrent Pressure Delta is %f %s" % (pres_delta[0], pres_delta[1]))
    elif choice == "r":
        SoftwareReset()
    elif choice == "c":
        print("Read configuration data")
        ReadControlRegister1()
    elif choice == "s":
        #Set System Mode()
        print("Select =Mode:-")
        print("1 - STANDBY")
        print("2 - ACTIVE")
        print("0 - return")
        mode = int(input ("Mode:"))
        if mode == 1:
            SetSystemMode(STANDBY)
        elif mode == 2:
            SetSystemMode(ACTIVE)
    elif choice == "o":
        # Set Output Mode()
        print("Select Output Mode:-")
        print("1 - Normal Mode")
        print("2 - Raw Mode")
        print("0 - return")
        full = int(input ("Range:"))
        if full == 1:
            SetOutputMode(NORMAL)
        elif full == 2:
            SetOutputMode(RAW)
    elif choice == "b":
        # Set the required barometric input
        print(" Enter required Barometric Input in Pascals")
        reqd = int(input("Pressure Value:"))
        SetBarometricInput(reqd)
    elif choice == "a":
        #Set Altimeter Mode()
        print("Select =Mode:-")
        print("1 - ALTIMETER")
        print("2 - BAROMETER")
        print("0 - return")
        mode = int(input ("Mode:"))
        if mode == 1:
            SetAltimeterMode(ALTIMETER)
        elif mode == 2:
            SetAltimeterMode(BAROMETER)
    else:
        print("Unknown Option")
        print("")
        print ("Press h for help")

