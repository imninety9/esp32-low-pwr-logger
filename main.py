# ultra low power

from micropython import const

import time
import gc

import machine

import config
from ds3231rtc import ds3231
from sd_logger import SDLogger


# --------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------

def sync_machine_rtc_from_ds3231(rtc):
    """
    Copy DS3231 time into ESP32 internal RTC.
    ds3231.get_time() -> (Y, M, D, hh, mm, ss, ...)
    """
    try:
        t = rtc.get_time() # (y, m, d, hh, mm, ss, wday, _)
        if t is None:
            return

        # machine.RTC.datetime: (year, month, day, weekday, hours, minutes, seconds, subseconds)
        r = machine.RTC()
        r.datetime((t[0], t[1], t[2], t[6], t[3], t[4], t[5], 0))
    except Exception as e:
        if debug:
            print("sync_machine_rtc_from_ds3231 error:", e)
            
def rtc_tup(rtc):
    """Return (Y, M, D, H, M, S, ...) tuple using ds3231.get_time() if available."""
    if rtc is not None:
        t = rtc.get_time()
        if t:
            return t
    # fallback
    return time.localtime()
    
# Pre-allocate format strings at module level
_ISO_FMT = config.ISO_FMT
def tup_to_iso(t):  
    """Convert time tuple (Y, M, D, H, M, S, ...) to 'YYYY-MM-DD hh:mm:ss'."""
    if not t:
        return "0000-00-00 00:00:00"
    return _ISO_FMT % (t[0], t[1], t[2], t[3], t[4], t[5])

# Pre-allocate format strings at module level
_FMT_2DEC = "%.2f" # precision is fixed at 2 decimal digits
def format_value(value, default = ""):
    """
    Format values for CSV / MQTT.
    """
    if value is None:
        return default
    return str(value) if not isinstance(value, float) else _FMT_2DEC % value
    
    
def should_run_apm(t, APM10_INTERVAL_MIN=config.APM10_INTERVAL_MIN):
    # run exactly on the hour
    return (t[4] % APM_INTERVAL_MIN) == 0

def read_apm10(rtc, sd, apm_sensor=None, STABILIZATION_SECS=15):
    """
    Read APM10, average last few readings.
    """
    if apm_sensor is None:
        return None, None, None
    try:
        # Enter measurement mode
        apm_sensor.enter_measurement_mode()
        sleep(STABILIZATION_SECS) # warm-up for stabilization
        
        n = 0
        pm1 = pm2_5 = pm10 = 0.0
        # Take ~3 samples, keep last 2; sensor min interval ~1s
        for i in range(3):
            data = apm_sensor.read_measurements()  # (pm1, pm2_5, pm10) or (None,...)
            if data and data[0] is not None:
                # drop oldest reading
                if i > 0:
                    pm1 += data[0]
                    pm2_5 += data[1]
                    pm10 += data[2]
                    n += 1
            sleep(1.2) # APM10 min 1s interval
        
        if n == 0: # avoid division by zero
            return None, None, None
        else:
            inv_n = 1.0 / n
            pm1  *= inv_n
            pm2_5 *= inv_n
            pm10 *= inv_n 
        
        return pm1, pm2_5, pm10
        
    except Exception as e:
        sd.append_error("apm10_read_error", str(e), ts=rtc_tup(rtc))
    finally:
        # Ensure we exit measurement mode and clear running flag
        try:
            apm_sensor.exit_measurement_mode()
        except Exception:
            pass
    


# --------------------------------------------------------------------
# Main
# --------------------------------------------------------------------
# Last full row logged / ready to log (list of values)
'''
["timestamp","bmp_temp","bmp_press","aht_temp","aht_hum",
 "ds18b20_temp","sht_temp","sht_hum",
 "pm1_0","pm2_5","pm10"]
'''
readings_len = const(10)
sensor_row = [""] * (readings_len+1)

DEEPSLEEP_MS = const(config.SENSOR_INTERVAL_MIN * 60 * 1000)
debug = config.debug

def main():
    # ----------------- INITIALIZATIONS ------------------        
    # --- RTC ---
    # Initialize i2c bus and alarm pin
    '''
    NOTE: Multiple I2C instances: creating separate I2C(...) objects from different modules
    fragments the heap. I now use a single shared I2C instance created once and passed to
    sensors or returned from an internal getter.
    '''
    i2c = machine.I2C(0, scl=machine.Pin(config.sclPIN), sda=machine.Pin(config.sdaPIN), freq=100000)
    alarmPIN = machine.Pin(config.alarmPIN, machine.Pin.IN, machine.Pin.PULL_UP)
    rtc = ds3231(i2c, alarmPIN)
           
    # set internal RTC from DS3231 so filesystem timestamps (metadata) are correct
    sync_machine_rtc_from_ds3231(rtc)

    # --- SD logger ---
    sd = SDLogger(
        spi_pin_miso=config.SPI_PIN_MISO,
        spi_pin_mosi=config.SPI_PIN_MOSI,
        spi_pin_sck=config.SPI_PIN_SCK,
        spi_pin_cs=config.SPI_PIN_CS,
        data_path=config.DEFAULT_DATA_PATH,
        error_path=config.DEFAULT_ERROR_PATH,
        debug=config.debug,
    )

    # --- Sensors (I2C + onewire) ---
    # Initialize softi2c bus and onewire pin
    '''creating single instance of softi2c object and passing it to different sensor modules'''
    softi2c = machine.SoftI2C(scl=machine.Pin(config.soft_sclPIN), sda=machine.Pin(config.soft_sdaPIN), freq=100000)
    onewirePin = machine.Pin(config.ONEWIRE_PIN)
        
    if i2c is not None:
        try:
            from aht25_sensor import AHT25 # lazy import
            aht25 = AHT25(i2c, i2c_address=0x38)
        except:
            aht25 = None
        try:
            from bmp280_sensor import BMP280Driver
            bmp280 = BMP280Driver(i2c, i2c_address=0x76)
        except:
            bmp280 = None
        if config.run_apm:
            try:
                from apm10_sensor_i2c import APM10Driver # lazy import
                apm = APM10Driver(i2c, i2c_address=0x08)
            except:
                apm = None
    if softi2c is not None:
        try:
            from sht40_sensor import SHT40 # lazy import
            sht40 = SHT40(softi2c, i2c_address=0x44)
        except:
            sht40 = None
    if onewirePin is not None:
        try:
            from ds18b20_sensor import DS18B20 # lazy import
            ds18b20 = DS18B20(onewirePin)
        except:
            ds18b20 = None
    
    # VARIABLES
    mem_threshold = config.MIN_MEM_THRESHOLD
    sht_rh_thresh = config.SHT_HIGH_RH_COUNT_THRESHOLD
    sht_rh_cnt_thresh = config.SHT_HIGH_RH_COUNT_THRESHOLD
    sht_heat_cyc = config.SHT_HEATER_CYCLES
    
    # ------------------- LOOP ------------------
    while True:
        try:
            if gc.mem_free() < mem_threshold:
                gc.collect()
                
            # 1. Timestamp from RTC (DS3231)
            ts = rtc_tup(rtc)
            sensor_row[0] = tup_to_iso(ts)

            # 2. Read all local sensors
            if bmp280:
                sensor_row[1], sensor_row[2] = bmp280.read_measurements()
            else:
                sensor_row[1], sensor_row[2] = None, None
            if aht25:
                sensor_row[3], sensor_row[4] = aht25.read_measurements()
            else:
                sensor_row[3], sensor_row[4] = None, None
            if ds18b20:
                sensor_row[5] = ds18b20.read_temp()
            else:
                sensor_row[5] = None
            if sht40:
                sensor_row[6], sensor_row[7] = sht40.read_measurements()
            else:
                sensor_row[6], sensor_row[7] = None, None
            # --- optional APM ---
            if should_run_apm(ts): # otherwise keep the old cached reading
                sensor_row[8], sensor_row[9], sensor_row[10] = read_apm10(rtc, apm, sd)
            
            # 3. format sensor row
            for i in range(readings_len):
                i += 1
                sensor_row[i] = format_value(sensor_row[i])
            
            # 4. Append to SD
            sd.append_row(sensor_row, ts=ts)
            
        except Exception as e:
            sd.append_error("main_loop_error", str(e), ts=rtc_tup(rtc), min_interval=300)
        
        # DeepSleep until next sample to save power
        machine.deepsleep(DEEPSLEEP_MS)

#################################################################################################        
main()
