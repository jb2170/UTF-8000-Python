import unittest

from UTF8000.encode import encode
from UTF8000.UTF8000Byte import UNICODE_SURROGATE_HIGH_MIN, UNICODE_SURROGATE_LOW_SUP, UNICODE_SUP

class TestEncode(unittest.TestCase):
    def test_unicode_range(self):
        for t in range(0, UNICODE_SURROGATE_HIGH_MIN):
            python_encoded = chr(t).encode()
            our_encoded = encode(t)
            self.assertEqual(python_encoded, our_encoded)

        for t in range(UNICODE_SURROGATE_LOW_SUP, UNICODE_SUP):
            python_encoded = chr(t).encode()
            our_encoded = encode(t)
            self.assertEqual(python_encoded, our_encoded)

    def test_mandatory_content_bits_final_start(self):
        # Mandatory content bits contained together in the final start byte
        for t, expected in (
            (   # UTF-8
                0b01100_001100,
                bytes((0b11001100, 0b10001100))
            ),
            (   # UTF-8000
                0b01110_000000_001100_100001_010010_001100_011110,
                bytes((0b11111111, 0b10001110, 0b10000000, 0b10001100, 0b10100001, 0b10010010, 0b10001100, 0b10011110))
            ),
        ):
            our_encoded = encode(t)
            self.assertEqual(expected, our_encoded)

    def test_mandatory_content_bits_straddled_final_start(self):
        # Mandatory content bits straddled across two bytes,
        # with the first 1 bit in the final start byte
        for t, expected in (
            (   # UTF-8
                0b011_110011_100001_000001,
                bytes((0b11110011, 0b10110011, 0b10100001, 0b10000001))
            ),
            (   # UTF-8000
                0b011_110011_100001_000001_111111_111111_111111_111111_111111,
                bytes((0b11111111, 0b10110011, 0b10110011, 0b10100001, 0b10000001, 0b10111111, 0b10111111, 0b10111111, 0b10111111, 0b10111111))
            ),
        ):
            our_encoded = encode(t)
            self.assertEqual(expected, our_encoded)

    def test_mandatory_content_bits_first_non_start(self):
        # Mandatory content bits contained together in the first non-start byte
        for t, expected in (
            (   # UTF-8000
                0b111110_100001_000001_000000_000000_000000,
                bytes((0b11111110, 0b10111110, 0b10100001, 0b10000001, 0b10000000, 0b10000000, 0b10000000))
            ),
            (   # UTF-8000
                0b111110_100001_000001_000000_000000_000000_000000_000000_000000_000000_000010,
                bytes((0b11111111, 0b10111110, 0b10111110, 0b10100001, 0b10000001, 0b10000000, 0b10000000, 0b10000000, 0b10000000, 0b10000000, 0b10000000, 0b10000000, 0b10000010))
            ),
        ):
            our_encoded = encode(t)
            self.assertEqual(expected, our_encoded)

    def test_mandatory_content_bits_straddled_first_non_start(self):
        # Mandatory content bits straddled across two bytes,
        # with the first 1 bit in the first non-start byte
        for t, expected in (
            (   # UTF-8
                0b000_110011_100001_000001,
                bytes((0b11110000, 0b10110011, 0b10100001, 0b10000001))
            ),
            (   # UTF-8000
                0b000_110011_100001_000001_111111_111111_111111_111111_111111,
                bytes((0b11111111, 0b10110000, 0b10110011, 0b10100001, 0b10000001, 0b10111111, 0b10111111, 0b10111111, 0b10111111, 0b10111111))
            ),
        ):
            our_encoded = encode(t)
            self.assertEqual(expected, our_encoded)

    def test_large(self):
        # 23 byte, 116 bit, just an example
        t = 0b11_000000_111111_000000_000000_000000_000000_000000_000000_000000_000000_000000_000000_000000_000000_000000_001100_000000_000000_000000
        expected = bytes((
            0b11111111, 0b10111111, 0b10111111, 0b10111011, 0b10000000, 0b10111111,
            0b10000000, 0b10000000, 0b10000000, 0b10000000, 0b10000000, 0b10000000,
            0b10000000, 0b10000000, 0b10000000, 0b10000000, 0b10000000, 0b10000000,
            0b10000000, 0b10001100, 0b10000000, 0b10000000, 0b10000000
        ))
        our_encoded = encode(t)
        self.assertEqual(expected, our_encoded)

        # 51 byte, 256 bit, a good example of where to stop
        t = 0b0001_000000_111111_000000_000000_000000_000000_000000_000000_000000_000000_000000_000000_000000_000000_000000_000000_000000_000000_000000_000000_000000_000000_000000_000000_000000_000000_000000_000000_000000_000000_000000_000000_000000_000000_000000_000000_000000_000000_000000_000000_000000_000001
        expected = bytes((
            0b11111111, 0b10111111, 0b10111111, 0b10111111, 0b10111111, 0b10111111,
            0b10111111, 0b10111111, 0b10100001, 0b10000000, 0b10111111, 0b10000000,
            0b10000000, 0b10000000, 0b10000000, 0b10000000, 0b10000000, 0b10000000,
            0b10000000, 0b10000000, 0b10000000, 0b10000000, 0b10000000, 0b10000000,
            0b10000000, 0b10000000, 0b10000000, 0b10000000, 0b10000000, 0b10000000,
            0b10000000, 0b10000000, 0b10000000, 0b10000000, 0b10000000, 0b10000000,
            0b10000000, 0b10000000, 0b10000000, 0b10000000, 0b10000000, 0b10000000,
            0b10000000, 0b10000000, 0b10000000, 0b10000000, 0b10000000, 0b10000000,
            0b10000000, 0b10000000, 0b10000001
        ))
        our_encoded = encode(t)
        self.assertEqual(expected, our_encoded)
