import unittest
from ..cpu import CPU


class TestCPU(unittest.TestCase):
    def setUp(self):
        """Set up a new CPU instance before each test."""
        self.cpu = CPU()

    def test_inc_A(self):
        """Test the __inc function for register A."""
        self.cpu.write_register("A", 0x00)  # Set register A to 0
        self.cpu.__inc("A")
        self.assertEqual(
            self.cpu.read_register("A"), 0x01
        )  # After incrementing, A should be 1

    def test_inc_A_wraparound(self):
        """Test the __inc function for register A with wraparound."""
        self.cpu.write_register("A", 0xFF)  # Set register A to 255 (0xFF)
        self.cpu.__inc("A")
        self.assertEqual(
            self.cpu.read_register("A"), 0x100
        )  # After incrementing, A should wrap around to 0x100


if __name__ == "__main__":
    unittest.main()
