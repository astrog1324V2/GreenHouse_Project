import dht

from machine import I2C, Pin

from bh1750 import BH1750


class SensorSuite:
    def __init__(self, config):
        self.dht_sensor = dht.DHT22(Pin(config.DHT_PIN))
        self.i2c = I2C(
            config.I2C_BUS_ID,
            scl=Pin(config.I2C_SCL_PIN),
            sda=Pin(config.I2C_SDA_PIN),
            freq=100000,
        )
        self.light_sensor = BH1750(self.i2c, config.BH1750_ADDR)

    def read_all(self):
        values = {
            "temperature_c": None,
            "humidity_pct": None,
            "light_lux": None,
            "errors": [],
        }

        try:
            self.dht_sensor.measure()
            values["temperature_c"] = round(float(self.dht_sensor.temperature()), 1)
            values["humidity_pct"] = round(float(self.dht_sensor.humidity()), 1)
        except Exception as exc:
            values["errors"].append("dht:%s" % exc)

        try:
            values["light_lux"] = self.light_sensor.read_lux()
        except Exception as exc:
            values["errors"].append("bh1750:%s" % exc)

        return values
