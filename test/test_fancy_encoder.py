import unittest

from UTF8000.encode import encode, fancy_encode

class TestFancyEncode(unittest.TestCase):
    def test_encode_ascii(self) -> None:
        a = 0x61

        a_encoded = fancy_encode(a)

        print(" ".join(f"{c}" for c in a_encoded))

        # self.assertEqual(a_encoded, b"a")

    def xtest_fancy_encode_consistent_with_encode(self) -> None:
        for x in range(1 << 21, 1 << 22):
            fancy = " ".join(f"{c}" for c in fancy_encode(x))
            normal = " ".join(f"{c:#010b}" for c in encode(x))

            self.assertEqual(fancy, normal)

# def test_main() -> None:
#     decoder = UTF8000IncrementalDecoder()

#     b = bytes([
#         0b11111111,  0b10_111111, 0b10_110000, 0b10_010000,
#         0b10_000000, 0b10_000000, 0b10_000000, 0b10_000000,
#     ])
#     decoder.feed(b)
#     for utf_8000_int in decoder:
#         print(utf_8000_int.debug_str()) # nothing

#     b = bytes([
#         0b10_000000, 0b10_000000, 0b10_000000, 0b10_000000,
#         0b10_000000, 0b10_000000, 0b10_000000, 0b10_000001,
#     ])
#     decoder.feed(b)
#     for utf_8000_int in decoder:
#         print(utf_8000_int.debug_str()) # single UTF-8000 int
#         print(int(utf_8000_int))        # a big big number
