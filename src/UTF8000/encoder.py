from .UTF8000Int import UTF8000Int
from .UTF8000Byte import FIRST_BYTE_FULL, CONTINUATION_FILLED, CONTINUATION_PREFIX, ceil_div, fill_n_bits_shifted_by_m

def empty_first_byte(n_bytes: int) -> int:
    # do not call for ASCII ie n_bytes == 1
    # XXX get rid of this function; make it inline in `encode()`

    return fill_n_bits_shifted_by_m(n_bytes, 8 - n_bytes)

def encode(x: int, signed: bool = False) -> bytes:
    if signed:
        # XXX implement signed behavior,
        # picking out bits until we reach -1
        # and ensuring unambiguous storage of +ve and -ve
        # in prefix-padded two's complement form
        raise NotImplementedError

    if x < 0:
        raise ValueError("Cannot encode negative number in unsigned mode")

    ret_ints = []

    if x < 0x80:
        # ASCII special case
        ret_ints.append(x)

        return bytes(ret_ints)

    # UTF-8000

    contents: list[int] = []
    y: int = x

    while y > 0:
        final_6_bits = y & (0b00111111)
        contents.insert(0, final_6_bits)
        y >>= 6

    n_bits_content_highest_six = contents[0].bit_length() # this feels cheeky to use

    n_bits_content_total = n_bits_content_highest_six + 6 * (len(contents) - 1)
    # round this up to the nearest '5 * k + 1' because k-byte UTF-8000
    # provides said number of bits of content storage
    n_utf_8000_bytes_needed = ceil_div(n_bits_content_total - 1, 5)

    if n_utf_8000_bytes_needed < 8:
        # single start byte

        final_start_byte = empty_first_byte(n_utf_8000_bytes_needed)
        # the first start byte is also the final in this case, the one and only!

        n_bytes_pure_content_and_final_start = n_utf_8000_bytes_needed
    else:
        # multiple start bytes, the power of UTF-8000!

        first_byte = FIRST_BYTE_FULL
        # the first start byte is always all 1s when n_bytes >= 8
        # may as well use this constant instead of `empty_first_byte(8)`

        ret_ints.append(first_byte)

        n_remaining_start_ones = n_utf_8000_bytes_needed - 8
        # how many more 1s we need to put in the start bytes sequence
        # we'll deal with the terminating 0 bit later and don't include it
        # in this count

        n_filled_continuation_start_bytes, n_ones_in_final_start_byte = divmod(n_remaining_start_ones, 6)

        for _ in range(n_filled_continuation_start_bytes):
            ret_ints.append(CONTINUATION_FILLED)

        final_start_byte_start_bits = fill_n_bits_shifted_by_m(n_ones_in_final_start_byte, 6 - n_ones_in_final_start_byte)
        final_start_byte = CONTINUATION_PREFIX | final_start_byte_start_bits
        # since 0 <= n_ones_in_final_start_byte <= 5, the terminating 0 bit
        # of the start sequence is contained in `final_start_byte`

        n_full_start_bytes = len(ret_ints)
        n_bytes_pure_content_and_final_start = n_utf_8000_bytes_needed - n_full_start_bytes
        # number of bytes that are purely content, ie 0b10yyyyyy,
        # and +1 for the final start byte, which contains the terminating
        # 0 bit and may or may not contain content

    if len(contents) == n_bytes_pure_content_and_final_start:
        #
        # if True,
        # then `len(contents) == n_bytes_pure_content_and_final_start`,
        # meaning the content !does! begin in the final start byte,
        # and certainly meaning the first 1 bit of the mandatory content bits
        # is in the <<final start byte<<
        #
        # Examples of the mandatory content bits
        # contained together in the <<final start byte<<
        #
        # UTF-8       0b110IIIIy (0b10yyyyyy)
        # UTF-8000    0b100IIIII (0b10yyyyyy ...)
        #
        # Examples of the mandatory content bits straddled across two bytes,
        # starting in the final start byte and continuing into
        # the first non-start byte,
        # with the first 1 bit in the <<final start byte<<
        #
        # UTF-8       0b11110III (0b10IIyyyy 0b10yyyyyy 0b10yyyyyy)
        # UTF-8000    0b10110III (0b10IIyyyy 0b10yyyyyy ...)
        #
        # if False,
        # then `len(contents) == n_bytes_pure_content_and_final_start - 1`,
        # meaning the content !may or may not! begin in the final start byte,
        # and certainly meaning the first 1 bit of the mandatory content bits
        # is in the >>first non-start byte>>
        #
        # Examples of the mandatory content bits
        # contained together in the >>first non-start byte>>
        #
        # UTF-8       0b11111110 (0b10IIIIIy 0b10yyyyyy ...)
        # UTF-8000    0b10111110 (0b10IIIIIy 0b10yyyyyy ...)
        #
        # Examples of the mandatory content bits straddled across two bytes,
        # starting in the final start byte and continuing into
        # the first non-start byte,
        # with the first 1 bit in the >>first non-start byte>>
        #
        # UTF-8       0b11110QQQ (0b10IIyyyy 0b10yyyyyy 0b10yyyyyy)
        # UTF-8000    0b10110QQQ (0b10IIyyyy 0b10yyyyyy ...)
        #
        final_start_byte_contents = contents.pop(0)
        final_start_byte |= final_start_byte_contents

    ret_ints.append(final_start_byte)

    for non_start_byte_contents in contents:
        non_start_byte = 0b10000000 | non_start_byte_contents
        ret_ints.append(non_start_byte)

    return bytes(ret_ints)

    # n_content_bits_final_start_byte = 6 - partly_ones_count - 1
    # # subtract length of 1 because the terminating 0 takes up one bit
    # # 0 <= n_content_bits_final_start_byte <= 5

    # print(len(contents), n_bytes)
    # raise NotImplementedError

    # multiple start bytes; first will be all ones
    # raise NotImplementedError
