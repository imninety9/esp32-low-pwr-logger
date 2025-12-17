# configuration file

from micropython import const

debug = const(True)
run_apm = const(True)

# SENSOR UPDATE INTERVAL
SENSOR_INTERVAL_MIN = const(5) # [interval between weather readings update]
APM10_INTERVAL_MIN = const(60)


# PHYSICAL PARAMETRS [GPIO PINS]
# I2C Pins
sdaPIN = const(21)
sclPIN = const(22)

# DS3231 rtc INT/SQW Pin
alarmPIN = const(27)

# Software I2C pins (used by sht40 sensor module)
soft_sdaPIN = const(25)
soft_sclPIN = const(26)

# SPI Pins
SPI_PIN_MISO = const(19)
SPI_PIN_MOSI = const(23)
SPI_PIN_SCK = const(18)
SPI_PIN_CS = const(5) # You can choose any available GPIO pin for CS

SD_MOUNT_POINT = '/sd'

# Nokia 5510 LCD Pins (uses the hspi bus)
# Nokia 5510 LCD Pin Function ESP32 GPIO	Notes
LCD_RST = const(16) # Reset
LCD_CE = const(17) # Chip Enable (CS)
LCD_DC = const(32) # Data/Command
LCD_DIN = const(13) # Data In (MOSI) [SPI MOSI]
LCD_CLK = const(14) # Clock [SPI SCK]

# Onewire pin (for onewire communication protocol devices like ds18b20)
ONEWIRE_PIN = const(4)

# Input Button Pin
BUTTON_1 = const(35) # (LOW when pressed, pulled HIGH via 10k ohm resistor)
BUTTON_2 = const(34) # (LOW when pressed, pulled HIGH via 10k ohm resistor)


# Misc
CSV_FILEDS = """timestamp,
                bmp_temp,bmp_press,
                aht_temp,aht_hum,
                ds18b20_temp,
                sht_temp,sht_hum,
                pm1_0,pm2_5,pm10
                \n"""


# Logging
DEFAULT_DATA_PATH = "/sd/weather.csv"
DEFAULT_ERROR_PATH = "/sd/errors.log"
DEFAULT_HEALTH_PATH = "/sd/health.csv" # Health log (uptime, memory)
FLUSH_ROW_LIMIT = const(12) # flush every N rows
DEFAULT_ERROR_ROW_LIMIT = const(500)  #
ERROR_AVG_ROW = const(60) # bytes
DEFAULT_ERROR_RETENTION = const(5) # number of files
DEFAULT_ERROR_THROTTLE_MS = const(3600000)        # milliseconds


# string formats
ISO_FMT = "%04d-%02d-%02d %02d:%02d:%02d"


# min mem_free to run gc
MIN_MEM_THRESHOLD = const(30000) # bytes
