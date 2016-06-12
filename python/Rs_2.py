#!/usr/bin/env python3

"""
iCogs Rs.2 Reader

For more information see www.BostinTechnology.com

The Rs.2 is based on the MMA8652FC 3-Axis, 12-bit Digital Accelerometer, but like all iCogs,
comes with an additional EEPROM to provide the capability to store additional information e.g
enviromental specific data.

This module uses 'Repeated Start' (see www.i2c-bus.org/repeated-start-condition) so requires
the following which is done programmatically
1. Open a terminal window
2. Run the following comamnds
    sudo su -
    echo -n 1 > /sys/module/i2c_bcm2708/parameters/combined
    exit

This changes the contents of combined to 'Y' in /sys/module/i2c_bcm2708/parameters, default is 'N'

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

Explanation of the use of masking
mode = the required values of the bits
mask = 0b00001100                                   # mask bits set to 1 are the ones to change
shift = 2                                           # How many bits to shift the mode to match the mask
byte = bus.read_byte_data(SENSOR_ADDR,reg_addr)     # Read the register from the sensor
# Modify the register to set bits 1 - 0 to the mode
towrite = (byte & ~mask) | (mode << shift)          # by ANDing the byte with the inverse of the mask, any bit
                                                    # that is not required is unchanged, but the bits required by the mask
                                                    # are set to zero
                                                    # When ORed with the required mode, the bits are set accordingly
bus.write_byte_data(SENSOR_ADDR, reg_addr, towrite)
time.sleep(WAITTIME)                                # Allow the sensor to complete the write before reading
byte = bus.read_byte_data(SENSOR_ADDR,reg_addr)
if (byte & mask) == (mode << shift):                # by ANDing the register value with the mask, we can compare it
                                                    # to the required values and check they match

NOTE: For some functions need to also shift the bits

"""

import smbus
import logging
import time
import math
import sys
import subprocess

SENSOR_ADDR = 0x1d

# The time between a write and subsequent read
WAITTIME = 0.5

#Full Scale Ranges
TWOG = 0b00
FOURG = 0b01
EIGHTG = 0b10

#Operating Modes
STANDBY = 0b0
ACTIVE = 0b1

#Tap Detection Modes
OFF = 0b00000000
SINGLE = 0b00010101
DOUBLE = 0b00101010


def SetRepeatedStartMode():
    # This function sets the I2C bus to use Repeated Start Mode
    # Command to run as Superuser is
    #   echo -n 1 > /sys/module/i2c_bcm2708/parameters/combined
    logging.info("Setting Repeated Start for I2C comms")
    try:
        response = subprocess.call("echo -n 1 > /sys/module/i2c_bcm2708/parameters/combined", shell=True)
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
    # Read out and confirm the 'Who Am I' value of 0x4a
    reg_addr = 0x0d
    byte = bus.read_byte_data(SENSOR_ADDR,reg_addr)
    if byte == 0x4A:
        print("Identified as Correct Device :%x" % byte)
    else:
        print("Check the Device WhoAm I as it is unrecognised")
    logging.info ("Who Am I value expected 0x4a from address 0x0d received:%s" % byte)
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
    print ("Rs.2 FIFO Event Sample Count Watermark %s" % fescw)
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
    fgerr = (byte & 0b01111100) >> 2
    logging.debug("Number of ODR time units since FIFO Gate Error %s" % fgerr)
    print ("Rs.2 Number of ODR time units since FIFO Gate Error %s" % fgerr)
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
    logging.debug("Software Reset Flag %s" % sr)
    if sr == 0b1:
        print("Rs.2 Software Reset  is Enabled")
    else:
        print("Rs.2 Software Reset is Disabled")
    # Sleep Mode power Scheme
    smps = (byte & 0b00011000) >> 3
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
    amps = (byte & 0b00000011)
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

def ReadFullScaleMode():
    #Read out and decode the XYZ_DATA_CFG Register 0x0E for Full Scale Mode
    # Returns the multiplication factor to convert the reading to g values
    reg_addr = 0x0E
    byte = bus.read_byte_data(SENSOR_ADDR,reg_addr)
    logging.info ("Full Scale Mode Reading XYZ_DATA_CFG Register reading (%x):%x" % (reg_addr,byte))
    # Decode the values
    # Full Scale Range setting
    fsr = (byte & 0b00000011)
    logging.debug("Full Scale Mode Reading setting %s" % fsr)
    fsr_multiplier = 1
    if fsr == 0b00:
        fsr_multiplier = 1/1024
    elif fsr == 0b01:
        fsr_multiplier = 1/512
    elif fsr == 0b10:
        fsr_multiplier = 1/256
    logging.info("Full Scale Mode setting %f" % fsr_multiplier)
    return fsr_multiplier

def SetFullScaleMode(mode):
    #Set the Full Scale Mode in the XYZ_DATA_CFG Register 0x0E
    # mode can be either TWOG, FOURG, EIGHTG
    reg_addr = 0x0e
    mask = 0b00000011
    byte = bus.read_byte_data(SENSOR_ADDR,reg_addr)
    logging.info ("XYZ_DATA_CFG Register before setting Full Scale Mode(%x):%x" % (reg_addr,byte))
    logging.debug("Requested Full Scale mode of operation %x" % mode)
    # check if the bits are not already set
    if (byte & mask) != mode:
        # Modify the register to set bits 1 - 0 to the mode
        towrite = (byte & ~mask) | mode
        logging.debug("Byte to write to turn on the Full Scale mode %x" % towrite)
        bus.write_byte_data(SENSOR_ADDR, reg_addr, towrite)
        time.sleep(WAITTIME)
        byte = bus.read_byte_data(SENSOR_ADDR,reg_addr)
        logging.info ("XYZ_DATA_CFG Register After turning on the Full Scale mode:%x" % byte)
        if (byte & mask) == mode:
            print("Sensor Turned in to Full Scale mode")
        else:
            print("Sensor Not in the Full Scale mode")
    else:
        logging.debug("Sensor already in required Full Scale mode")
    return

def SetSystemMode(mode):
    # Set the System Mode in the SYSMOD Register 0x2A, it can be read from 0x0B
    # mode can be either STANDBY (0b0) or ACTIVE (0b1)
    reg_addr = 0x2A
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

def SetSelfTest(onoff):
    # To activate the self-test by setting the ST bit in the CTRL_REG2 register (0x2B).
    # Enable the Self Test using CTRL_Register 0x2b
    reg_addr = 0x2b
    mask = 0b10000000
    shift = 7
    byte = bus.read_byte_data(SENSOR_ADDR,reg_addr)
    logging.info ("Self Test byte before setting Self Test bit (%x):%x" % (reg_addr,byte))
    if (byte & mask) != (onoff << shift):
        # Modify the register to set bit 7 to on or off
        towrite = (byte & ~mask) | (onoff << shift)
        logging.debug("Self Test Byte to write to turn on the Self Test %x" % towrite)
        bus.write_byte_data(SENSOR_ADDR, reg_addr, towrite)
        time.sleep(WAITTIME)
        byte = bus.read_byte_data(SENSOR_ADDR,reg_addr)
        logging.info ("Self Test After turning on the required mode:%x" % byte)
        if (byte & mask) == (onoff << shift):
            print("Sensor Turned in to required Self Test mode")
        else:
            print("Sensor Not in the required Self Test mode")
    else:
        logging.debug("Sensor already in required Self Test mode")
    return

def SetPulseConfig(mode):
    # Set the Pulse Configuration used for sensing tap detection
    # mode can be either OFF, SINGLE or DOUBLE
    reg_addr = 0x21
    mask = 0b00111111
    byte = bus.read_byte_data(SENSOR_ADDR,reg_addr)
    logging.info ("Set Pulse Configuration Mode (PULSE_CFG) before setting (%x): %x" % (reg_addr,byte))
    logging.debug("Requested Pulse Configuration Mode of operation %x" % mode)
    if (byte & mask) != mode:
        # Modify the register to set bits5 - 0 to the mode
        towrite = (byte & ~mask) | mode
        logging.debug("Byte to write to turn on the requested Pulse Configuration Mode: %x" % towrite)
        bus.write_byte_data(SENSOR_ADDR, reg_addr, towrite)
        time.sleep(WAITTIME)
        byte = bus.read_byte_data(SENSOR_ADDR,reg_addr)
        logging.info ("Set Pulse Configuration Mode (PULSE_CFG) Register After turning on the required mode: %x" % byte)
        if (byte & mask) == mode:
            print("Sensor Turned in to requested Pulse Configuration Mode: %x" % mode)
        else:
            print("Sensor Not in the requested Pulse Configuration Mode: %x" % mode)
    else:
        logging.debug("Sensor already in required Pulse Configuration mode")
    return

def SetPulseThreshold(axis, value):
    # Set the Pulse Threshold for either of the 3 axis' used for sensing tap detection
    # axis can be either X, Y or Z, value is to be written
    if axis.upper() == "X":
        reg_addr = 0x23
    elif axis.upper() == "Y":
        reg_addr = 0x24
    elif axis.upper() == "Z":
        reg_addr = 0x25
    else:
        logging.error("Unable to axis to set threshold for, assuming X")
        reg_addr = 0x23

    mask = 0b01111111
    byte = bus.read_byte_data(SENSOR_ADDR,reg_addr)
    logging.info ("Set Pulse Threshold %s (PULSE_THSx) before setting (%x): %x" % (axis,reg_addr,byte))
    logging.debug("Requested Pulse Threshold value %x for axis %s" % (value, axis))
    if (byte & mask) != value:
        # Modify the register to set bits6 - 0 to the mode
        towrite = (byte & ~mask) | value
        logging.debug("Byte to write to turn on the requested Pulse Threshold for axis %s Mode: %x" % (axis,towrite))
        bus.write_byte_data(SENSOR_ADDR, reg_addr, towrite)
        time.sleep(WAITTIME)
        byte = bus.read_byte_data(SENSOR_ADDR,reg_addr)
        logging.info ("Set Pulse Threshold (PULSE_THSx) Register After turning on the required mode: %x for axis %s" % (byte, axis))
        if (byte & mask) == value:
            print("Sensor Pulse Threshold set for axis: %s" % axis)
        else:
            print("Sensor Pulse Threshold set for axis: %s" % axis)
    else:
        logging.debug("Sensor Pulse Threshold already set for axis: %s" % axis)
    return

def SetPulseTimeWindow(limit):
    # Set the Pulse Time Limit used for sensing tap detection
    # limit is the value to be written in mS
    # AS this uses all bits, no need for a mask
    reg_addr = 0x26
    byte = bus.read_byte_data(SENSOR_ADDR,reg_addr)
    logging.info ("Set Pulse Time Window (PULSE_TMLT) before setting (%x): %x" % (reg_addr,byte))
    logging.debug("Requested Pulse Time Window in mS %x" % limit)
    if byte != limit:
        # Modify the register to set bits7 - 0 to the mode
        towrite = limit
        logging.debug("Byte to write to turn on the requested Pulse Time Window: %x" % towrite)
        bus.write_byte_data(SENSOR_ADDR, reg_addr, towrite)
        time.sleep(WAITTIME)
        byte = bus.read_byte_data(SENSOR_ADDR,reg_addr)
        logging.info ("Set Pulse Time Window (PULSE_TMLY) Register After turning on the required mode: %x" % byte)
        if byte == limit:
            print("Sensor set to requested Pulse Time Window: %x" % limit)
        else:
            print("Sensor set to requested Pulse Time Window: %x" % limit)
    else:
        logging.debug("Sensor already set to requested Pulse Time Window")
    return

def SetPulseLatency(interval):
    # Set the Pulse Latency Time Limit used for sensing tap detection
    # limit is the value to be written in mS
    # AS this uses all bits, no need for a mask
    reg_addr = 0x27
    byte = bus.read_byte_data(SENSOR_ADDR,reg_addr)
    logging.info ("Set Pulse Latency Time Window (PULSE_TMLT) before setting (%x): %x" % (reg_addr,byte))
    logging.debug("Requested Pulse Latency Time Window in mS %x" % interval)
    if byte != interval:
        # Modify the register to set bits7 - 0 to the mode
        towrite = interval
        logging.debug("Byte to write to turn on the requested Pulse Latency Time Window: %x" % towrite)
        bus.write_byte_data(SENSOR_ADDR, reg_addr, towrite)
        time.sleep(WAITTIME)
        byte = bus.read_byte_data(SENSOR_ADDR,reg_addr)
        logging.info ("Set Pulse Latency Time Window (PULSE_TMLY) Register After turning on the required mode: %x" % byte)
        if byte == interval:
            print("Sensor set to requested Pulse Latency Time Window: %x" % interval)
        else:
            print("Sensor set to requested Pulse Latency Time Window: %x" % interval)
    else:
        logging.debug("Sensor already set to requested Pulse Latency Time Window")
    return

def SetPulseDetection():
    # Set the Ctrl_Reg4 (0x2D) to Pulse Detection
    # no additional value is required as function sets bit 3 on only
    reg_addr = 0x2D
    mask = 0b00000100
    value = 0b00000100
    byte = bus.read_byte_data(SENSOR_ADDR,reg_addr)
    logging.info ("Set Pulse Detection mode (CTRL_REG4) before setting (%x): %x" % (reg_addr,byte))
    logging.debug("Requested Pulse Detection Mode of operation %x" % value)
    if (byte & mask) != value:
        # Modify the register to set bit 3 to 1
        towrite = (byte & ~mask) | value
        logging.debug("Byte to write to turn on the requested Pulse Detection Mode: %x" % towrite)
        bus.write_byte_data(SENSOR_ADDR, reg_addr, towrite)
        time.sleep(WAITTIME)
        byte = bus.read_byte_data(SENSOR_ADDR,reg_addr)
        logging.info ("Set Pulse Configuration Detection Mode (CTRL_REG4) Register After turning on the required mode: %x" % byte)
        if (byte & mask) == value:
            print("Sensor Turned in to requested Pulse Detection Mode: %x" % value)
        else:
            print("Sensor Not in the requested Pulse Detection Mode: %x" % value)
    else:
        logging.debug("Sensor already in the requested Pulse Detection Mode")
    return

def MonitorForTap():
    # Monitor the PULSE_SRC register for a tap being detected and identify on which axis
    reg_addr = 0x22
    byte = 0x00
    print("Waiting for Tap")
    while byte == 0x00:
        byte = bus.read_byte_data(SENSOR_ADDR,reg_addr)
    logging.debug("Value returned from tap being detected :%x" % byte)


    # Due to the nature of the detection, this can be unreliable and is provided here for information only.

    # decode the pulse that has been detected, first the axis
    if (byte & 0b01000000) >> 6 == 1:
        axis_event = "Z"
    elif (byte & 0b00100000) >> 5 == 1:
        axis_event = "Y"
    elif (byte & 0b00010000) >> 4 == 1:
        axis_event = "X"
    else:
        axis_event = "Multiple"

    # decode the direction
    if (byte & 0b00000111) == 0:
        axis_direction = "positive"
    else:
        axis_direction = "negative"

    print ("Tap Detected on %s axis in a %s direction" % (axis_event, axis_direction))
    logging.info("Tap Detected on %s axis in a %s direction" % (axis_event, axis_direction))

    return

def SoftwareReset():
    # Perform a Software Reset using CTRL_Register 0x2b
    # After the software reset, it automatically clears the bit so no need to check / merge
    reg_addr = 0x0e
    value = 0b01000000
    byte = bus.read_byte_data(SENSOR_ADDR,reg_addr)
    logging.info ("Control Register 2 before enabling Software Reset (%x):%x" % (reg_addr,byte))
    # Modify the register to set bit 6 to 0b1
    towrite = byte | value
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
    logging.debug("Software Reset Completed")
    return

def SelfTest():
    """
    Run the self test routine and capture the results. Steps required
    Set the sensor in Standby by clearing the ACTIVE bit in CTRL_REG1 register (0x2A)
    Set the Full Scale mode to 2g
    Set the sensor into Self Test by setting the ST bit in CTRL_REG2 (0x2B)
    Set the Sensor back into ACTIVE mode by setting the ACTIVE bit in CTRL_REG1 register (0x2A)
    Measure the values from the 3 axis (take multiple samples)
    Set the sensor in Standby by clearing the ACTIVE bit in CTRL_REG1 register (0x2A)
    End the Self Test by clearing the ST bit in CTRL_REG2 (0x2B)
    Set the Sensor back into ACTIVE mode by setting the ACTIVE bit in CTRL_REG1 register (0x2A)
    Measure the values from the 3 axis (take multiple samples)

    Then simply compute the difference between the acceleration output of all axes with self-test enabled
    (ST = 1) and disabled (ST = 0) as follows:

    XST = XST_ON − XST_OFF
    YST = YST_ON − YST_OFF
    ZST = ZST_ON − ZST_OFF

    The difference is based on a full scale mode of 2g although the values are not calculated
    range   x       y       z
    2g      +90     +104    +782

    """
    # Need to get the full scale mode for later use
    fullscalerange = ReadFullScaleMode()
    SetFullScaleMode(TWOG)

    SetSystemMode(STANDBY)
    SetSelfTest(False)
    SetSystemMode(ACTIVE)
    print ("Capturing Values")
    out_selftest = CalculateAvgValues(fullscalerange)
    print ("Set into STANDBY mode")
    SetSystemMode(STANDBY)
    print ("Enable Self Test mode")
    SetSelfTest(True)
    print ("Set into ACTIVE mode")
    SetSystemMode(ACTIVE)
    print ("Capturing Values")
    in_selftest = CalculateAvgValues(fullscalerange)
    print ("Set into STANDBY mode")
    SetSystemMode(STANDBY)
    print ("DISable Self Test mode")
    SetSelfTest(False)

    print("\nValues Before / During Self Test (Non Calibrated Values)")
    print(" Y |             :%f / %f" % (out_selftest[1],in_selftest[1]))
    print("   |")
    print("   |   Z         :%f / %f" % (out_selftest[2],in_selftest[2]))
    print("   |  / ")
    print("   | /")
    print("   |_________ X  :%f / %f" % (out_selftest[0],in_selftest[0]))
    print("\n")

    # Check for Self Test Pass
    # X increase of 90, y increase of 104, z increase of 782 (these are non calibrated!)
    if (in_selftest[0] - out_selftest[0]) > (90 * 0.75):
        print("X - PASS")
    else:
        print("X - FAIL")
    if (in_selftest[1] - out_selftest[1]) > (104 * 0.75):
        print("Y - PASS")
    else:
        print("Y - FAIL")
    if (in_selftest[2] - out_selftest[2]) > (782 * 0.75):
        print("Z - PASS")
    else:
        print("Z - FAIL")

    return

def TapDetection():
    """
    For a single tap event, the PULSE_TMLT, PULSE_THSX/Y/Z and PULSE_LTCY registers are key parameters to consider.

    sample code from nxp website

        unsigned char reg_val = 0, CTRL_REG1_val = 0;

       I2C_WriteRegister(MMA845x_I2C_ADDRESS, CTRL_REG2, 0x40);             // Reset all registers to POR values

            do            // Wait for the RST bit to clear
       {
              reg_val = I2C_ReadRegister(MMA845x_I2C_ADDRESS, CTRL_REG2) & 0x40;
       }      while (reg_val);

       I2C_WriteRegister(MMA845x_I2C_ADDRESS, CTRL_REG1, 0x0C);             // ODR = 400Hz, Reduced noise, Standby mode
       I2C_WriteRegister(MMA845x_I2C_ADDRESS, XYZ_DATA_CFG_REG, 0x00);      // +/-2g range -> 1g = 16384/4 = 4096 counts
       I2C_WriteRegister(MMA845x_I2C_ADDRESS, CTRL_REG2, 0x02);             // High Resolution mode

       I2C_WriteRegister(MMA845x_I2C_ADDRESS, PULSE_CFG_REG, 0x15);         //Enable X, Y and Z Single Pulse
       I2C_WriteRegister(MMA845x_I2C_ADDRESS, PULSE_THSX_REG, 0x20);        //Set X Threshold to 2.016g
       I2C_WriteRegister(MMA845x_I2C_ADDRESS, PULSE_THSY_REG, 0x20);        //Set Y Threshold to 2.016g
       I2C_WriteRegister(MMA845x_I2C_ADDRESS, PULSE_THSZ_REG, 0x2A);        //Set Z Threshold to 2.646g
       I2C_WriteRegister(MMA845x_I2C_ADDRESS, PULSE_TMLT_REG, 0x28);        //Set Time Limit for Tap Detection to 25 ms
       I2C_WriteRegister(MMA845x_I2C_ADDRESS, PULSE_LTCY_REG, 0x28);        //Set Latency Time to 50 ms

       I2C_WriteRegister(MMA845x_I2C_ADDRESS, CTRL_REG4, 0x08);             //Pulse detection interrupt enabled
       I2C_WriteRegister(MMA845x_I2C_ADDRESS, CTRL_REG5, 0x08);             //Route INT1 to system interrupt

       CTRL_REG1_val = I2C_ReadRegister(MMA845x_I2C_ADDRESS, CTRL_REG1);   //Active Mode
       CTRL_REG1_val |= 0x01;
       I2C_WriteRegister(MMA845x_I2C_ADDRESS, CTRL_REG1, CTRL_REG1_val);

        Handle the Interrupt
        The PULSE_SRC register indicates a double or single pulse event has occurred and also which direction.
        In this case the value of the register mentioned is passed to the PULSE_SRC_val variable and evaluated.
        Reading the PULSE_SRC register clears all bits. Reading the source register will clear the interrupt.

         void PORTA_IRQHandler()
         {
           PORTA_PCR14 |= PORT_PCR_ISF_MASK;               // Clear the interrupt flag
           PULSE_SRC_val = I2C_ReadRegister(MMA845x_I2C_ADDRESS, PULSE_SRC_REG); //Read Pulse Source Register
         }

    For more info https://community.nxp.com/docs/DOC-329888
    """
    SetFullScaleMode(TWOG)
    SetPulseConfig(DOUBLE)
    SetPulseThreshold("X",0x20)
    SetPulseThreshold("Y",0x20)
    SetPulseThreshold("Z",0x20)
    SetPulseTimeWindow(0x28)
    SetPulseLatency(0x28)
    SetPulseDetection()
    SetSystemMode(ACTIVE)

    MonitorForTap()

    return


######### Calculation Routines

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

def CalculateValues(fsr):
    # Takes the readings and returns the x, y, z values
    # Given the current Full Scale Range
    x = ReadXAxisDataRegisters()
    y = ReadYAxisDataRegisters()
    z = ReadZAxisDataRegisters()

    x = TwosCompliment(x)
    x = x * fsr
    y = TwosCompliment(y)
    y = y * fsr
    z = TwosCompliment(z)
    z = z * fsr
    return [x, y, z]

def CalculateAvgValues(fsr):
    # Takes 10 sets of readings and returns the averaged x, y, z values
    # Given the current Full Scale Range
    avg_x = 0
    avg_y = 0
    avg_z = 0
    for n in range(0,10):
        x = ReadXAxisDataRegisters()
        y = ReadYAxisDataRegisters()
        z = ReadZAxisDataRegisters()
        x = TwosCompliment(x)
        #x = x * fsr
        y = TwosCompliment(y)
        #y = y * fsr
        z = TwosCompliment(z)
        #z = z * fsr
        avg_x = avg_x + x
        avg_y = avg_y + y
        avg_z = avg_z + z

    avg_x = avg_x / 10
    avg_y = avg_y / 10
    avg_z = avg_z / 10

    return [avg_x, avg_y, avg_z]

def TwosCompliment(value):
    # Convert the given 12bit hex value to decimal using 2's compliment
    return -(value & 0b100000000000) | (value & 0b011111111111)

def HelpText():
    # show the help text
    print("**************************************************************************\n")
    print("Available commands: -")
    print("\n")
    print("T - Self Test")
    print("d - Tap Detection")
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

#Set Repeated Start Mode
SetRepeatedStartMode()

while True:
    choice = input ("Select Menu Option:")

    if choice == "H" or choice == "h":
        HelpText()
    elif choice == "A":
        ReadAllData()
    elif choice == "E" or choice == "e":
        sys.exit()
    elif choice == "T":
        SelfTest()
    elif choice == "d":
        TapDetection()
    elif choice == "w":
        WhoAmI()
    elif choice == "x":
        fullscalerange = ReadFullScaleMode()
        g_force = CalculateValues(fullscalerange)
        print(" Y |             :%f" % g_force[1])
        print("   |")
        print("   |   Z         :%f" % g_force[2])
        print("   |  / ")
        print("   | /")
        print("   |_________ X  :%f" % g_force[0])
        print("\n")
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
        print("2 - ACTIVE")
        print("0 - return")
        mode = int(input ("Mode:"))
        if mode == 1:
            SetSystemMode(STANDBY)
        elif mode == 2:
            SetSystemMode(ACTIVE)
        elif mode == 0:
            time.sleep(0.1)
        else:
            print("Unknown System Mode Option")
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
        elif full == 4:
            SetFullScaleMode(FOURG)
        elif full == 8:
            SetFullScaleMode(EIGHTG)
        elif mode == 0:
            time.sleep(0.1)
        else:
            print("Unknown Full Scale Mode Option")
    else:
        print("Unknown Option")
        print("")
        print ("Press h for help")

