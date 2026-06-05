import unittest

from UTF8000.encode import encode

class TestEncode(unittest.TestCase):
    def test_encode_ascii(self) -> None:
        a = 0x61

        a_encoded = encode(a)

        self.assertEqual(a_encoded, b"a")

    def test_builtin_consistency(self):
        surr_start = 0xD800
        surr_end   = 0xE000 # not inclusive
        maxx       = (1 << 20) + (1 << 16)

        # for x in range((1 << 20) + (1 << 16)):
        for x in range(0, surr_start):
            c = chr(x)
            b = c.encode()
            self.assertEqual(b, encode(x))

        for x in range(surr_end, maxx):
            c = chr(x)
            b = c.encode()
            self.assertEqual(b, encode(x))

        for x in range(surr_start, surr_end):
            self.assertRaises(UnicodeEncodeError, chr(x).encode)
