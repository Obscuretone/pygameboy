import time


class SystemClock:
    def __init__(self, clock_speed_hz):
        self.clock_speed_hz = clock_speed_hz
        self.start_time = time.time()
        self.last_time = self.start_time
        self.cycles_elapsed = 0

    def reset(self):
        self.start_time = time.time()
        self.last_time = self.start_time
        self.cycles_elapsed = 0

    def update(self, cycles):
        self.cycles_elapsed += cycles

    def wait_for_next_cycle(self, cycles):
        elapsed_time = cycles / self.clock_speed_hz
        next_cycle_time = self.last_time + elapsed_time
        current_time = time.time()

        if next_cycle_time > current_time:
            time_to_wait = next_cycle_time - current_time
            time.sleep(time_to_wait)

        self.last_time = time.time()

    def get_cycles_elapsed(self):
        return self.cycles_elapsed
