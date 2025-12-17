# SHT40 sensor driver based on sht4x.py library

import sht4x  # Import the sht4x library

class SHT40:
    __slots__ = ("sensor", "mode")
    
    def __init__(self, i2c, i2c_address=0x44):
        """
        Initializes the SHT40 sensor.

        :param i2c: I2C object
        :param i2c_address: I2C address of the SHT40 sensor (default address is 0x44)
        """
        try:            
            self.sensor = sht4x.SHT4X(i2c, address=i2c_address)
            self.mode = 1  # Default: No heater, high precision [by default this is the mode]
        except Exception as e:
            raise e # raise if initialization failed to let the caller know about it
        
    def read_measurements(self):
        """
        Reads temperature and humidity measurements.

        :return: A tuple (temperature in °C, relative humidity in %)
        """
        try:
            return self.sensor.measurements # temperature, humidity
        except Exception as e:
            return None, None
        
