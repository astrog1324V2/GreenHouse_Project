from sh1106 import SH1106_I2C


def _format_value(value, suffix, precision=1):
    if value is None:
        return "--"
    if precision == 0:
        return "%d%s" % (int(value), suffix)
    return ("%0." + str(precision) + "f%s") % (value, suffix)


class StatusDisplay:
    def __init__(self, i2c, config):
        self.display = SH1106_I2C(
            config.OLED_WIDTH,
            config.OLED_HEIGHT,
            i2c,
            addr=config.OLED_ADDR,
        )

    def render(self, values, footer_text):
        oled = self.display
        oled.fill(0)

        oled.rect(0, 0, 128, 24, 1)
        oled.text("TEMP", 4, 4)
        oled.text(_format_value(values.get("temperature_c"), "C", 1), 4, 13)

        oled.rect(0, 28, 62, 28, 1)
        oled.text("HUM", 4, 32)
        oled.text(_format_value(values.get("humidity_pct"), "%", 1), 4, 42)

        oled.rect(66, 28, 62, 28, 1)
        oled.text("LIGHT", 70, 32)
        oled.text(_format_value(values.get("light_lux"), "lx", 0), 70, 42)

        oled.text(footer_text[:21], 0, 56)
        oled.show()
