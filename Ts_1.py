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
import time

def TwosCompliment(value):
    # convert a 16bit 2'C number to decimal
    return -(value & 0b100000000000) | (value & 0b011111111111)

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
    logging.info ("Humidity Reading (0x29/0x28):%s/%s" % (humidity_out_h, humidity_out_l))
    #TODO: Merge the values into a signel reading

def ReadT_OUT():
    #Read out and decode the 2 bytes of temperature readings
    t_out_l = bus.read_byte_data(0x5f,0x2a)
    t_out_h = bus.read_byte_data(0x5f,0x2b)
    logging.debug ("T_OUT Reading (0x2b/0x2a):%s/%s" % (hex(t_out_h), hex(t_out_l)))
    #Merge the values into a single reading
    t_out = (t_out_h << 8) + t_out_l
    t_out = TwosCompliment(t_out)
    logging.info ("T_OUT Reading combined (0x2b/0x2a):%s" % t_out)
    return t_out

def ReadT0_DegC():
    #Read out and decode the 1.2 bytes of temperature calibraion reading T0
    t0_degc_l = bus.read_byte_data(0x5f,0x32)
    t0_degc_h = bus.read_byte_data(0x5f,0x35)
    logging.debug ("T0 Calibration Readings (0x32/0x35):%s/%s" % (hex(t0_degc_h), hex(t0_degc_l)))
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
    logging.debug ("T1 Calibration Readings (0x33/0x35):%s/%s" % (hex(t1_degc_h), hex(t1_degc_l)))
    #Merge the values into a single reading
    #extract 2 bits from T0 high
    t1_degc_h = (t1_degc_h & 0b00001100)
    logging.debug("Bits 2 & 3 of T1 High:%s" % bin(t1_degc_h))
    t1_degc = ((t1_degc_h << 8) + t1_degc_l) / 8
    logging.info("T1 Value:%s" % t1_degc)
    return t1_degc

def ReadT0_OUT():
    #Read out and decode the 2 bytes of temperature calibration readings
    t0_out_l = bus.read_byte_data(0x5f,0x3c)
    t0_out_h = bus.read_byte_data(0x5f,0x3d)
    logging.debug ("T0 OUT Reading (0x3c/0x3d):%s/%s" % (hex(t0_out_h), hex(t0_out_l)))
    #Merge the values into a single reading
    t0_out = (t0_out_h << 8) + t0_out_l
    t0_out = TwosCompliment(t0_out)
    logging.info ("T0 OUT combined (0x3c/0x3d):%s" % t0_out)
    return t0_out

def ReadT1_OUT():
    #Read out and decode the 2 bytes of temperature calibration readings
    t1_out_l = bus.read_byte_data(0x5f,0x3e)
    t1_out_h = bus.read_byte_data(0x5f,0x3f)
    logging.debug ("T1_OUT Reading (0x3e/0x3f):%s/%s" % (hex(t1_out_h), hex(t1_out_l)))
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

def TurnOnSensor():
    # set bit 7 of the CTRL Register 0x20
    byte = bus.read_byte_data(0x5f,0x20)
    logging.info ("Control Register Before turning on (0x20):%s" % hex(byte))
    #Modifyt the register to set bit7 = 1 and bits1,0 to 01
    towrite = byte | 0x80 | 0x01
    logging.debug("Byte to write to turn on %s" % towrite)
    bus.write_byte_data(0x5f, 0x20, towrite)
    byte = bus.read_byte_data(0x5f,0x20)
    logging.info ("Control Register After turning on (0x20):%s" % hex(byte))
    return
        
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

#TODO: Turn on the sensor!
TurnOnSensor()


while True:
    temp = CalculateTemperature()
    print ("Temperature Reading :%s" % temp)
    time.sleep(0.5)


