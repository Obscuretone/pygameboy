import time


class SystemClock:
    """
    Manages the timing and synchronization of the GameBoy system.

    The GameBoy runs at a base clock speed of 4,194,304 Hz.
    """

    def __init__(self, clock_speed_hz: int):
        """
        Initialize the system clock.

        Args:
            clock_speed_hz: The target clock speed in Hertz.
        """
        self.clock_speed_hz: int = clock_speed_hz
        self.start_time: float = time.perf_counter()
        self.last_time: float = self.start_time
        self.cycles_elapsed: int = 0

    def reset(self) -> None:
        """Reset the clock and cycle count."""
        self.start_time = time.perf_counter()
        self.last_time = self.start_time
        self.cycles_elapsed = 0

    def update(self, cycles: int) -> None:
        """Update the total number of cycles elapsed."""
        self.cycles_elapsed += cycles

    def wait_for_next_cycle(self, cycles: int) -> None:
        """
        Pause execution to match the real-time clock speed.
        Uses an accumulated ideal time to prevent drift.
        """
        ideal_elapsed = cycles / self.clock_speed_hz
        self.last_time += ideal_elapsed
        current_time = time.perf_counter()

        if self.last_time > current_time:
            time.sleep(self.last_time - current_time)
        elif current_time - self.last_time > 0.1:
            # If we're lagging by more than 100ms, reset ideal time to current to avoid "speed-up" catch-up
            self.last_time = current_time

    def get_cycles_elapsed(self) -> int:
        """Get the total number of cycles elapsed since reset."""
        return self.cycles_elapsed
