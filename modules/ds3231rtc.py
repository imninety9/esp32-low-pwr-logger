# ds3231 rtc

import ds3231_gen
import config

class ds3231:
    __slots__ = ("d", "alarm", "alarm1", "alarm2", "alarm_pin")
    
    def __init__(self, i2c, alarmPIN):
        """
        Initializes the ds3231 rtc.

        :param i2c: I2C object
        :param alarmPIN_address: GPIO pin object connected to alarm
        """
        try:            
            self.d = ds3231_gen.DS3231(i2c)
            self.alarm = [self.d.alarm1, self.d.alarm2] # ds3231 has two alarms
            # variiables to track, if an alarm is enabled (i.e. sending interrupts to the INT/SQW pin) or not
            self.alarm1 = False
            self.alarm2 = False
            
            # GPIO pin object for INT/SQW pin
            self.alarm_pin = alarmPIN
            
        except Exception as e:
            raise e # raise if initialization failed to let the caller know about it
        
    def get_time(self):
        '''get current time from ds3231'''
        ''' format: (year, month, day, hour, minutes, seconds, weekday, 0) '''
        ''' in 24 hour format '''
        try:
            return self.d.get_time()
        except Exception as e:
            return None
            
    def set_time(self, time):
        '''set ds3231 time'''
        ''' time tuple format: (year, month, day, hour, minutes, seconds, weekday, 0) '''
        ''' in 24 hour format '''
        try:
            return self.d.set_time(time)
        except Exception as e:
            pass
        