class Joypad:
    def __init__(self):
        # bits 0-3: Right/A, Left/B, Up/Select, Down/Start (0=pressed, 1=not pressed)
        self.direction_keys = 0x0F
        self.button_keys = 0x0F
        # bits 4, 5 (0=selected, 1=not selected)
        self.selection = 0x30

    def read(self):
        res = self.selection | 0xCF  # bits 6-7 always 1, bits 0-3 start as 1
        if not (self.selection & 0x10):  # Direction keys selected (bit 4=0)
            res &= 0xF0 | self.direction_keys
        if not (self.selection & 0x20):  # Button keys selected (bit 5=0)
            res &= 0xF0 | self.button_keys
        return res

    def write(self, value):
        # Only bits 4 and 5 are writable
        self.selection = value & 0x30

    def set_key(self, key, pressed):
        mask = 0
        is_button = False
        if key == "right" or key == "a":
            mask = 0x01
        elif key == "left" or key == "b":
            mask = 0x02
        elif key == "up" or key == "select":
            mask = 0x04
        elif key == "down" or key == "start":
            mask = 0x08

        if key in ["a", "b", "select", "start"]:
            is_button = True

        if pressed:
            if is_button:
                self.button_keys &= ~mask
            else:
                self.direction_keys &= ~mask
        else:
            if is_button:
                self.button_keys |= mask
            else:
                self.direction_keys |= mask
