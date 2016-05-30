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

"""


##
##
## This software is ready for testing
##
##


#BUG: Need to check all uses of bit setting, ORing bytes is great for gsetting bits
#       but no use for clearing bits!
#       towrite = byte & (mask | mode)

#BUG: Self Test isn't returning the right values

#BUG: Reading of values may be incorrect

#TODO: Use reg_addr = 0xxx in all registers
#TODO: Write some code to do Tap Detection

import smbus
import logging
import time
import math
import sys
import subprocess

SENSOR_ADDR = 0x1d

#Full Scale Ranges
TWOG = 0b00
FOURG = 0b01
EIGHTG = 0b10

#Operating Modes
STANDBY = 0b0
ACTIVE = 0b1

def SetRepeatedStartMode():
    # This function sets the I2C bus to use Repeated Start Mode
    # Command to run as Superuser is
    #   echo -n 1 > /sys/module/i2c_bcm2708/parameters/combined
    logging.info("Setting Repeated Start for I2C comms")
    try:
        response = subprocess.call("echo -n 1 > /sys/module/i2c_bcm2708/parameters/combined", shell=True)
        logging.debug("Used subprocess call to set Repeated Start command and got this response %x" % response)
    except:
        logging.critical("Failed to Set Repeated Start mode, program aborted")
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
    byte = bus.read_byte_data(SENSOR_ADDR,0x0d)
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
    fgerr = (byte & 0b01111100)
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

def SetSystemMode(mode):
    # Set the System Mode in the SYSMOD Register 0x2A, it can be read from 0x0B
    # mode can be either STANDBY (0b0) or ACTIVE (0b1)
    reg_addr = 0x2A
    mask = 0b11111110
    byte = bus.read_byte_data(SENSOR_ADDR,reg_addr)
    logging.info ("Set System Mode (CTRL_REG1) before setting (%x): %x" % (reg_addr,byte))
    logging.debug("Requested System Mode of operation %x" % mode)
    # Modify the register to set bit 0 to the mode
    towrite = (byte & mask) | mode
    logging.debug("Byte to write to turn on the requested system Mode: %x" % towrite)
    bus.write_byte_data(SENSOR_ADDR, reg_addr, towrite)
    time.sleep(0.5)
    byte = bus.read_byte_data(SENSOR_ADDR,reg_addr)
    logging.info ("Set System Mode (CTRL_REG1) Register After turning on the required mode: %x" % byte)
    if (byte & 0b00000001) == mode:
        print("Sensor Turned in to requested System Mode: %x" % mode)
    else:
        print("Sensor Not in the requested System Mode: %x" % mode)
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
    mask = 0b11111100
    byte = bus.read_byte_data(SENSOR_ADDR,reg_addr)
    logging.info ("XYZ_DATA_CFG Register before setting (%x):%x" % (reg_addr,byte))
    logging.debug("Requested Full Scale mode of operation %x" % mode)
    # Modify the register to set bits 1 - 0 to the mode
    towrite = (byte & mask) | mode
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

def SetSelfTest(onoff):
    """
    To activate the self-test by setting the ST bit in the CTRL_REG2 register (0x2B).

    """
    # Enable the Self Test using CTRL_Register 0x2b
    reg_addr = 0x2b
    byte = bus.read_byte_data(SENSOR_ADDR,reg_addr)
    logging.info ("Self Test byte before setting Self Test bit (%x):%x" % (reg_addr,byte))
    # Modify the register to set bit 7 to on or off
    mask = 0b01111111
    towrite = (byte & mask) | (onoff << 7)
    logging.debug("Self Test Byte to write to turn on the Self Test %x" % towrite)
    bus.write_byte_data(SENSOR_ADDR, reg_addr, towrite)
    time.sleep(0.5)
    byte = bus.read_byte_data(SENSOR_ADDR,reg_addr)
    logging.info ("Self Test After turning on the required mode:%x" % byte)

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

def TapDetection():
    """
    This is how I'm configuring the sensor so far:

    // Enter STANDBY mode
    accel.write(MMA8652_CTRL_REG1  0);
    // set the INT_EN_PULSE bit by writing 0x08 to the CTRL_REG4 register

    // Dynamic range
    accel.write(MMA8652_XYZ_DATA_CFG  0);  // Dynamic range = +-2g
    // Enable interrupts
    accel.write(MMA8652_CTRL_REG3, 0x10)   // Pulse function interrupt can wake-up system
    // Enable Pulse detection
    accel.write(MMA8652_CTRL_REG4, 0x04)   // Enable Pulse Detection Interrupt
    // Enable pulse detection on each axis
    accel.write(MMA8652_PULSE_CFG, 0x55);  // Enable single Pulse Detection on all axis
    // Pulse thresholds
    accel.write(MMA8652_PULSE_THSX, 0x0A); // Threshold X = 10
    accel.write(MMA8652_PULSE_THSY, 0x0A); // Threshold Y = 10
    accel.write(MMA8652_PULSE_THSZ, 0x0A); // Threshold Z = 10
    // Enter ACTIVE mode
    accel.write(MMA8652_CTRL_REG1  0x21);    // ACTIVE mode, Normal mode, data rate = 400 Hz

    The above code is supposed to generate a (falling) interrupt on INT2 when a tap or double-tap
    event is detected but it's not the case. Is there any sample code where I could get some ideas from?

    """

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

