from .UTF8000Int import UTF8000Int
from .UTF8000Byte import UTF8000Byte, FIRST_BYTE_FULL, CONTINUATION_FILLED, CONTINUATION_PREFIX, ceil_div, fill_n_bits_shifted_by_m

def encode(x: int, signed: bool = False) -> bytes:
    """
    Encode an integer `x` into UTF-8000 bytes.
    """

    if signed:
        # XXX implement signed behavior,
        # picking out bits until we reach -1
        # and ensuring unambiguous storage of +ve and -ve
        # in prefix-padded two's complement form
        raise NotImplementedError

    if x < 0:
        raise ValueError("Cannot encode negative number in unsigned mode")

    ret_ints: list[int] = []

    if x < 0x80:
        # Treat ASCII as a special case.
        # This makes it easier for us to write the encoder, and allows a 'fast path'.
        ret_ints.append(x)

        return bytes(ret_ints)

    # UTF-8000

    contents: list[int] = []
    y: int = x

    while y > 0:
        # Extract bits from `x`, 6 bits at a time (sextets), until there's nothing left.
        # These blocks of 6 bits fit nicely into continuation bytes.
        # The 'uppermost' bits from the final extraction will fit into the final start
        # byte that may have has less than 6 bits of content, don't worry; continue
        # reading on.
        final_6_bits = y & (0b00111111)
        contents.insert(0, final_6_bits)
        y >>= 6

    n_bits_content_highest_six = contents[0].bit_length() # this feels cheeky to use

    n_bits_content_total = n_bits_content_highest_six + 6 * (len(contents) - 1)
    # Sextets below the 'uppermost' sextet contribute 6 bits of content
    # regardless of how many 1s or 0s they contain and wherein they
    # contain them. The uppermost sextet determines where to stop.

    # Round this up to the nearest '5 * k + 1' because k-byte UTF-8000
    # provides said number of bits of content storage. We wish to know k,
    # as this is how many bytes we need to allocate.
    n_utf_8000_bytes_needed = ceil_div(n_bits_content_total - 1, 5)

    if n_utf_8000_bytes_needed < 8:
        # We have a single start byte.

        final_start_byte = fill_n_bits_shifted_by_m(n_utf_8000_bytes_needed, 8 - n_utf_8000_bytes_needed)
        # The first start byte is also the final in this case, the one and only!
        # Since 2 <= `n_utf_8000_bytes_needed` <= 7, the terminating 0 bit
        # of the start sequence is contained in `final_start_byte`.
        # The possibilities for the final start byte are:
        # 0b110xxxxy 0b1110xxxx 0b11110xxx 0b111110xx 0b1111110x 0b11111110.
        # We fill its contents, if it has any, after this if-else block.

        n_bytes_pure_content_and_final_start = n_utf_8000_bytes_needed
        # This is the number of bytes that are purely content, ie 0b10yyyyyy,
        # and +1 for the final start byte, which contains the terminating
        # 0 bit and may or may not contain content.
    else:
        # We have multiple start bytes, the power of UTF-8000!

        first_byte = FIRST_BYTE_FULL
        # The first start byte is all 1s when `n_bytes` >= 8.

        ret_ints.append(first_byte)

        n_remaining_start_ones = n_utf_8000_bytes_needed - 8
        # This is how many more 1s we need to put in the start bytes sequence.
        # We'll deal with the terminating 0 bit later, and don't include it
        # in this count.

        n_filled_continuation_start_bytes, n_ones_in_final_start_byte = divmod(n_remaining_start_ones, 6)

        for _ in range(n_filled_continuation_start_bytes):
            # Add any filled-up continuation start bytes (0b10111111).
            ret_ints.append(CONTINUATION_FILLED)

        final_start_byte_start_bits = fill_n_bits_shifted_by_m(n_ones_in_final_start_byte, 6 - n_ones_in_final_start_byte)
        final_start_byte = CONTINUATION_PREFIX | final_start_byte_start_bits
        # Since 0 <= `n_ones_in_final_start_byte` <= 5, the terminating 0 bit
        # of the start sequence is contained in `final_start_byte`.
        # The possibilities for the final start byte are:
        # 0b100xxxxx 0b1010xxxx 0b10110xxx 0b101110xx 0b1011110x 0b10111110.
        # We fill its contents, if it has any, after this if-else block.

        n_full_start_bytes = 1 + n_filled_continuation_start_bytes # aka `len(ret_ints)`
        n_bytes_pure_content_and_final_start = n_utf_8000_bytes_needed - n_full_start_bytes
        # This is the number of bytes that are purely content, ie 0b10yyyyyy,
        # and +1 for the final start byte, which contains the terminating
        # 0 bit and may or may not contain content.

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
        # UTF-8       0b11110QII (0b10IIyyyy 0b10yyyyyy 0b10yyyyyy)
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
        # UTF-8*      0b11111110 (0b10IIIIIy 0b10yyyyyy ...)
        # UTF-8000    0b10111110 (0b10IIIIIy 0b10yyyyyy ...)
        #
        # *technically not UTF-8 since UTF-8 is restricted to 4 bytes,
        # but you know what I mean: <8-byte UTF-8000.
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
    # Add the final start byte.

    for non_start_byte_contents in contents:
        # Add the purely-content continuation bytes.
        non_start_byte = 0b10000000 | non_start_byte_contents
        ret_ints.append(non_start_byte)

    return bytes(ret_ints)

def fancy_encode(x: int, signed: bool = False) -> tuple[UTF8000Byte]:
    """
    Encode an integer `x` into a tuple of `UTF8000Byte`s.
    """

    # See `encode` for full comments. There's no point repeating them here.

    if signed:
        raise NotImplementedError

    if x < 0:
        raise ValueError("Cannot encode negative number in unsigned mode")

    ret_ints: list[UTF8000Byte] = []

    if x < 0x80:
        ret_ints.append(UTF8000Byte(
            x,
            is_start_byte = True,
            is_continuation_byte = False,
            is_content_byte = True
        ))

        return tuple(ret_ints)

    # UTF-8000

    contents: list[int] = []
    y: int = x

    while y > 0:
        final_6_bits = y & (0b00111111)
        contents.insert(0, final_6_bits)
        y >>= 6

    n_bits_content_highest_six = contents[0].bit_length()

    n_bits_content_total = n_bits_content_highest_six + 6 * (len(contents) - 1)

    n_utf_8000_bytes_needed = ceil_div(n_bits_content_total - 1, 5)

    if n_utf_8000_bytes_needed < 8:
        is_final_start_byte_a_continuation_byte = False
        is_final_start_byte_a_content_byte = n_utf_8000_bytes_needed < 7
        # For single start byte UTF-8000,
        # if there are less than 7 UTF-8000 bytes needed in total,
        # then there are less than 7 ones in the start sequence,
        # thus there are less than 8 bits in the start sequence,
        # thus there is space in the final start byte for content.

        final_start_byte = fill_n_bits_shifted_by_m(n_utf_8000_bytes_needed, 8 - n_utf_8000_bytes_needed)

        n_bytes_pure_content_and_final_start = n_utf_8000_bytes_needed
    else:
        first_byte = UTF8000Byte(
            FIRST_BYTE_FULL,
            is_start_byte = True,
            is_continuation_byte = False,
            is_content_byte = False
        )

        ret_ints.append(first_byte)

        n_remaining_start_ones = n_utf_8000_bytes_needed - 8

        n_filled_continuation_start_bytes, n_ones_in_final_start_byte = divmod(n_remaining_start_ones, 6)

        for _ in range(n_filled_continuation_start_bytes):
            ret_ints.append(UTF8000Byte(
                CONTINUATION_FILLED,
                is_start_byte = True,
                is_continuation_byte = True,
                is_content_byte = False
            ))

        is_final_start_byte_a_continuation_byte = True
        is_final_start_byte_a_content_byte = n_ones_in_final_start_byte < 5
        # For multi start byte UTF-8000,
        # if   there are less than 5 ones in the start sequence of the final start byte,
        # then there are less than 6 bits in the start sequence of the final start byte,
        # thus there are less than 8 bits used by the '10' continuation prefix and the start sequence bits,
        # thus there is space in the final start byte for content.

        final_start_byte_start_bits = fill_n_bits_shifted_by_m(n_ones_in_final_start_byte, 6 - n_ones_in_final_start_byte)
        final_start_byte = CONTINUATION_PREFIX | final_start_byte_start_bits

        n_full_start_bytes = 1 + n_filled_continuation_start_bytes # aka `len(ret_ints)`
        n_bytes_pure_content_and_final_start = n_utf_8000_bytes_needed - n_full_start_bytes

    if len(contents) == n_bytes_pure_content_and_final_start:
        final_start_byte_contents = contents.pop(0)
        final_start_byte |= final_start_byte_contents

    ret_ints.append(UTF8000Byte(
        final_start_byte,
        is_start_byte = True,
        is_continuation_byte = is_final_start_byte_a_continuation_byte,
        is_content_byte = is_final_start_byte_a_content_byte
    ))

    for non_start_byte_contents in contents:
        non_start_byte = 0b10000000 | non_start_byte_contents
        ret_ints.append(UTF8000Byte(
            non_start_byte,
            is_start_byte = False,
            is_continuation_byte = True,
            is_content_byte = True
        ))

    return tuple(ret_ints)
