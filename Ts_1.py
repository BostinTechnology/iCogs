#! /usr/bin/python3

"""
iCogs Ts.1 Reader

For more information see www.BostinTechnology.com

The Ts.1 is based on the HTS221 combined Humidity and Temperature sensor, but like all iCogs, 
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

def TwosCompliment(value):
    # Convert the given 16bit hex value to decimal using 2's compliment
    return -(value & 0b100000000000) | (value & 0b011111111111)

def ReadAllData():
    # Read out all 255 bytes from the device
    # capture all the readings for printing later
    values = []
    # read each byte of data from 0x00 to 0xff
    for addr in range(0x00,0x100):
        byte = bus.read_byte_data(0x5f,addr)
        logging.debug ("Read All Data Byte %x:%x" % (addr, byte))
        values.append(byte)
    
    # print out the data, looping in steps of 16 to print the data out in blocks
    for i in range(0x00, 0xff, 0x10):
        print("Addr:%2x "% i, end="")
        for j in range(0x0, 0x):
            print(" %4x" % values[i+j], end="")
        print(" ")
    return
    
def WhoAmI():
    # Read out and confirm the 'Who Am I' value of 0xBC
    byte = bus.read_byte_data(0x5f,0x0F)
    if byte == 0xBC:
        print("Identified as Correct Device :%x" % byte)
    else:
        print("Check the Device WhoAm I as it is unrecognised")
    logging.info ("Who Am I (0x0f):%s" % byte)
    return

def ReadAV_Conf():
    #Read out and decode the humidty and temperature resolution mode
    byte = bus.read_byte_data(0x5f,0x10)
    logging.debug ("AV_Conf setting (0x10):%x" % byte)
    # Decode the values
    # Temperature is bits 5:3
    temp_avg = (byte & 0b00111000) >> 3
    logging.debug("Bits read for averaged temperature samples %s" % temp_avg)
    # The number of values is 2 ^ the 3 bits + 1
    temp_samp = math.pow(2, (temp_avg + 1))
    logging.info("Quantity of Temperature Samples :%d" % temp_samp) 
    print ("Quantity of Temperature Samples :%d" % temp_samp) 
    # Humidity is bits 2:0
    humid_avg = (byte & 0b00000111)
    logging.debug("Bits read for averaged humidity samples %s" % humid_avg)
    # The number of values is 2 ^ the 3 bits + 2
    humid_samp = math.pow(2, (humid_avg + 2))
    logging.info("Quantity of Humidity Samples :%d" % humid_samp) 
    print ("Quantity of Humidity Samples :%d" % humid_samp) 
    return

def ReadCtrl_Reg1():
    #Read out and decode the first control register
    byte = bus.read_byte_data(0x5f,0x20)
    logging.info ("Control Register 1 setting (0x20):%x" % byte)
    # Decode the values
    # Power Down Control
    pd = (byte & 0b10000000) >> 7
    logging.debug("Power Down Control (1=Active) %s" % pd)
    if pd:
        print("Ts.1 in Active Mode")
    else:
        print("Ts.1 in Power-Down Mode")
    
    # Block Data Update
    bdu = (byte & 0b00000100) >> 2
    logging.debug("Block Data Update (1=update on MSB and LSB) %s" % bdu)
    if bdu:
        print("Ts.1 Block Update Mode: Output Registers Not Updated until MSB and LSB reading")
    else:
        print("Ts.1 Block Update Mode: Continuous Update")
    
    # Output Data Rate
    odr = (byte & 0b00000011)
    logging.debug("Output Data Rate Selection %s" % odr)
    if odr == 0b00:
        print("Ts.1 Output Data Rate Configuration: One Shot")
    elif odr == 0b01:
        print("Ts.1 Output Data Rate Configuration: 1 Hz")
    elif odr == 0b10:
        print("Ts.1 Output Data Rate Configuration: 7 Hz")
    elif odr == 0b11:
        print("Ts.1 Output Data Rate Configuration: 12.5 Hz")
    return
   

def ReadCtrl_Reg2():
    #Read out and decode the second control register.
    # Most values are for control, hence not decoded
    byte = bus.read_byte_data(0x5f,0x21)
    logging.info ("Control Register 2 setting (0x21):%x" % byte)
    
    # Heater Status
    heat = (byte & 0b00000010) >> 1
    logging.debug("Heater Status (1=On) %s" % heat)
    if heat:
        print("Ts.1 Heater is currently ON")
    else:
        print("Ts.1 Heater is currently OFF")
    return

def ReadCtrl_Reg3():
    #Read out the third control register
    byte = bus.read_byte_data(0x5f,0x22)
    logging.info ("Control Register 3 setting (0x22):%x" % byte)
    return

def ReadStatus_Reg():
    #Read out and decode the status register
    byte = bus.read_byte_data(0x5f,0x27)
    logging.info ("Status Register setting (0x27):0x%x" % byte)
    # Decode the Values

    # Humidity Data Status
    humid = (byte & 0b00000010) >> 1
    logging.debug("Humidity Data Status (1=data available) %s" % humid)
    if humid:
        print("Ts.1 Humidity data available")
    else:
        print("Ts.1 Humidity data NOT available")
    # Temperature Data Status
    temp = byte & 0b00000001
    logging.debug("Temperature Data Status (1=data available) %s" % temp)
    if temp:
        print("Ts.1 Temperature data available")
    else:
        print("Ts.1 Temperature data NOT available")
    return
    

### Routines to control the sensor
def TurnOnSensor():
    # set bit 7 of the CTRL Register 0x20 to 1
    byte = bus.read_byte_data(0x5f,0x20)
    logging.info ("Control Register Before turning on Sensor (0x20):0x%x" % byte)
    #Modify the register to set bit7 = 1 and bits1,0 to 01
    towrite = byte | 0x80 | 0x01
    logging.debug("Byte to write to turn on Sensor 0x%x" % towrite)
    bus.write_byte_data(0x5f, 0x20, towrite)
    byte = bus.read_byte_data(0x5f,0x20)
    logging.info ("Control Register After turning on sensor(0x20):0x%x" % byte)
    if (byte & 0b10000000) >> 7 == 1:
        print("Sensor Turned on")
    else:
        print("Sensor Turned off")
    return

def TurnOffSensor():
    # set bit 7 of the CTRL Register 0x20 to 0
    byte = bus.read_byte_data(0x5f,0x20)
    logging.info ("Control Register Before turning off (0x20):%x" % byte)
    # Modify the register to set bit7 = 0 and bits1,0 to 00
    towrite = byte & 0b01111100
    logging.debug("Byte to write to turn off %s" % towrite)
    bus.write_byte_data(0x5f, 0x20, towrite)
    byte = bus.read_byte_data(0x5f,0x20)
    logging.info ("Control Register After turning off (0x20):%x" % byte)
    if (byte & 0b10000000) >> 7 == 1:
        print("Sensor Turned on")
    else:
        print("Sensor Turned off")

    return


def TurnOnHeater():
    # Turn on the heater for 1 second
    byte = bus.read_byte_data(0x5f,0x21)
    logging.info ("Control Register Before turning on heater (0x21):%x" % byte)
    # Modify the register to set bit1 = 1
    to_on = (byte | 0b00000010)
    to_off = (byte & 0b11111101)
    logging.debug("Byte to write to turn off / on 0x%2x / 0x%2x" % (to_on, to_off))
    # turn on the heater
    bus.write_byte_data(0x5f, 0x21, to_on)
    logging.info("Heater turned ON")
    print("Heater ON")
    time.sleep(1)
    # turn off the heater
    bus.write_byte_data(0x5f, 0x21, to_off)
    logging.info("Heater turned OFF")
    print ("Heater OFF")
    return

def RefreshRegisters():
    # set bit 7 of the CTRL Register 0x21 to 1 to reset the registers
    byte = bus.read_byte_data(0x5f,0x21)
    logging.info ("Control Register Before Refreshing data (0x21):%x" % byte)
    # Modify the register to set bit7 = 1
    towrite = byte | 0b10000000
    logging.debug("Byte to write to refresh the register %x" % towrite)
    bus.write_byte_data(0x5f, 0x21, towrite)
    # check bit 7 for return to zero on completion of refresh
    refreshing = True
    while refreshing:
        byte = bus.read_byte_data(0x5f,0x21)
        refreshing = (byte & 0b10000000) >> 7 
        logging.debug("Waiting for Refresh %x" % byte)
    logging.info ("Control Register After refreshing the register (0x20):%x" % byte)
    print("Registers Refeshed")
    return

def HumidityDataAvailable():
    # Waits until the Humidity data available flag is set
    humid = False
    while humid == False:
        byte = bus.read_byte_data(0x5f,0x27)
        humid = (byte & 0b00000010) >> 1
        logging.debug("Humidity Data Status (1=data available) %s" % humid)
    return

def TemperatureDataAvailable():
    # Waits until the Temperature data available flag is set
    temp = False
    while temp == False:
        byte = bus.read_byte_data(0x5f,0x27)
        temp = byte & 0b00000001
        logging.debug("Temperature Data Status (1=data available) %s" % temp)
    return
    
### Routines to read out the various temperature values and calculate the current temperature

def ReadT_OUT():
    #Read out and decode the 2 bytes of temperature readings
    t_out_l = bus.read_byte_data(0x5f,0x2a)
    t_out_h = bus.read_byte_data(0x5f,0x2b)
    logging.debug ("T_OUT Reading (0x2b/0x2a):%x/%x" % (t_out_h, t_out_l))
    #Merge the values into a single reading
    t_out = (t_out_h << 8) + t_out_l
    t_out = TwosCompliment(t_out)
    logging.info ("T_OUT Reading combined (0x2b/0x2a):%s" % t_out)
    return t_out

def ReadT0_DegC():
    #Read out and decode the 1.2 bytes of temperature calibraion reading T0
    t0_degc_l = bus.read_byte_data(0x5f,0x32)
    t0_degc_h = bus.read_byte_data(0x5f,0x35)
    logging.debug ("T0 Calibration Readings (0x35/0x32):%x/%x" % (t0_degc_h, t0_degc_l))
    #Merge the values into a single reading
    #extract 2 bits from T0 high
    t0_degc_h = (t0_degc_h & 0b00000011)
    logging.debug("bits 0 & 1 of T0 High:%s" % bin(t0_degc_h))
    t0_degc = ((t0_degc_h << 8) + t0_degc_l) / 8
    logging.info("T0 Value:%s" % t0_degc)
    return t0_degc

def ReadT1_DegC():
    #Read out and decode the 1.2 bytes of temperature calibraion reading T0
    t1_degc_l = bus.read_byte_data(0x5f,0x33)
    t1_degc_h = bus.read_byte_data(0x5f,0x35)
    logging.debug ("T1 Calibration Readings (0x35/0x33):%x/%x" % (t1_degc_h, t1_degc_l))
    #Merge the values into a single reading
    #extract 2 bits from T0 high
    t1_degc_h = (t1_degc_h & 0b00001100) >> 2
    logging.debug("Bits 2 & 3 of T1 High:%s" % bin(t1_degc_h))
    t1_degc = ((t1_degc_h << 8) + t1_degc_l) / 8
    logging.info("T1 Value:%s" % t1_degc)
    return t1_degc

def ReadT0_OUT():
    #Read out and decode the 2 bytes of temperature calibration readings
    t0_out_l = bus.read_byte_data(0x5f,0x3c)
    t0_out_h = bus.read_byte_data(0x5f,0x3d)
    logging.debug ("T0 OUT Reading (0x3c/0x3d):%x/%x" % (t0_out_h, t0_out_l))
    #Merge the values into a single reading
    t0_out = (t0_out_h << 8) + t0_out_l
    t0_out = TwosCompliment(t0_out)
    logging.info ("T0 OUT combined (0x3c/0x3d):%s" % t0_out)
    return t0_out

def ReadT1_OUT():
    #Read out and decode the 2 bytes of temperature calibration readings
    t1_out_l = bus.read_byte_data(0x5f,0x3e)
    t1_out_h = bus.read_byte_data(0x5f,0x3f)
    logging.debug ("T1_OUT Reading (0x3e/0x3f):%x/%x" % (t1_out_h, t1_out_l))
    #Merge the values into a single reading
    t1_out = (t1_out_h << 8) + t1_out_l
    t1_out = TwosCompliment(t1_out)
    logging.info ("T1_OUT Reading combined (0x3e/0x3f):%s" % t1_out)
    return t1_out

def CalculateTemperature():
    T_OUT = ReadT_OUT()
    T0_degC = ReadT0_DegC()
    T1_degC = ReadT1_DegC()
    T0_OUT = ReadT0_OUT()
    T1_OUT = ReadT1_OUT()
    T_DegC = (T0_degC + (T_OUT - T0_OUT) * (T1_degC - T0_degC) / (T1_OUT - T0_OUT))
    logging.info("Calculated Temperature: %s" % T_DegC)
    return T_DegC


### Routines to read out the various humidity values and calculate the current temperature
def ReadH_OUT():
    #Read out and decode the 2 bytes of humidity readings
    h_out_l = bus.read_byte_data(0x5f,0x28)
    h_out_h = bus.read_byte_data(0x5f,0x29)
    logging.debug ("H_OUT Reading (0x28/0x29):%x/%x" % (h_out_h, h_out_l))
    #Merge the values into a single reading
    h_out = (h_out_h << 8) + h_out_l
    h_out = TwosCompliment(h_out)
    logging.info ("H_OUT Reading combined (0x28/0x29):%s" % h_out)
    return h_out

def ReadH0_rH():
    #Read out and decode the 1 byte of humidity calibraion reading H0
    h0_rh = bus.read_byte_data(0x5f,0x30)
    logging.debug ("H0 Calibration Readings (0x30):%x" % h0_rh)
    h0_rh = h0_rh / 2
    logging.info("H0 Value:%s" % h0_rh)
    return h0_rh

def ReadH1_rH():
    #Read out and decode the 1 byte of humidity calibraion reading H1
    h1_rh = bus.read_byte_data(0x5f,0x31)
    logging.debug ("H1 Calibration Readings (0x30):%x" % h1_rh)
    h1_rh = h1_rh / 2
    logging.info("H1 Value:%s" % h1_rh)
    return h1_rh

def ReadH0_OUT():
    #Read out and decode the 2 bytes of humidity calibration readings
    h0_out_l = bus.read_byte_data(0x5f,0x36)
    h0_out_h = bus.read_byte_data(0x5f,0x37)
    logging.debug ("H0 OUT Reading (0x37/0x36):%x/%x" % (h0_out_h, h0_out_l))
    #Merge the values into a single reading
    h0_out = (h0_out_h << 8) + h0_out_l
    h0_out = TwosCompliment(h0_out)
    logging.info ("H0 OUT combined (0x37/0x36):%s" % h0_out)
    return h0_out

def ReadH1_OUT():
    #Read out and decode the 2 bytes of humidity calibration readings
    h1_out_l = bus.read_byte_data(0x5f,0x3A)
    h1_out_h = bus.read_byte_data(0x5f,0x3B)
    logging.debug ("H1 OUT Reading (0x3B/0x3A):%x/%x" % (h1_out_h, h1_out_l))
    #Merge the values into a single reading
    h1_out = (h1_out_h << 8) + h1_out_l
    h1_out = TwosCompliment(h1_out)
    logging.info ("H1 OUT combined (0x3B/0x3A):%s" % h1_out)
    return h1_out

def CalculateRelativeHumidity():
    H_OUT = ReadH_OUT()
    H0_rH = ReadH0_rH()
    H1_rH = ReadH1_rH()
    H0_OUT = ReadH0_OUT()
    H1_OUT = ReadH1_OUT()
    H_rH = (H0_rH + (H_OUT - H0_OUT) * (H1_rH - H0_rH) / (H1_OUT - H0_OUT))
    logging.info("Calculated Relative Humidity: %s" % H_rH)
    return H_rH



def HelpText():
    # show the help text
    print("**************************************************************************\n")
    print("Available commands: -")
    print("W - Read Who Am I Information")
    print("R - Read Registers")
    print("A - Read All Data")
    print("F - Refresh Registers")
    print("n - Turn on Sensor")
    print("o - Turn off Sensor")
    print("T - Read the Temperature")
    print("U - Read the Humidity")
    print("q - Turn on Heater for 1 second")
    print("e - Exit Program")



# main code loop

print ("Bostin Technology Ltd")
print ("Cogniot Products")
print ("Ts.1 - Temperature and Humidity Sensor")
print ("")
print ("Press h for help")
print ("")

bus = smbus.SMBus(1)

logging.basicConfig(filename="Ts_1.txt", filemode="w", level=logging.DEBUG, format='%(asctime)s:%(levelname)s:%(message)s')


while True:
    choice = input ("Select Menu Option:")

    if choice == "H" or choice == "h":
        HelpText()
    elif choice == "W":
        WhoAmI()
    elif choice == "R":
        ReadAV_Conf()
        ReadCtrl_Reg1()
        ReadCtrl_Reg2()
        ReadCtrl_Reg3()
        ReadStatus_Reg()
    elif choice == "A":
        ReadAllData()
    elif choice == "F":
        RefreshRegisters()
    elif choice == "n":
        TurnOnSensor()
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


