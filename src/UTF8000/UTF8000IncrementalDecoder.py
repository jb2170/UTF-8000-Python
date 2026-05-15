from typing import Generator

from .UTF8000Byte import UTF8000Byte, byte_is_continuation, byte_idx_0, byte_continuation_content_idx_0, OVERLONG_MASK_2_BYTE, OVERLONG_MASKS_N_BYTE
from .UTF8000Int import UTF8000Int

class UTF8000IncrementalDecoder:
    def __init__(self) -> None:
        self._results:      list[UTF8000Int] = []
        self._bytes_buffer: bytes            = b""

        self._generator = self._utf_8000_parse_forever()
        self._wakeup()

    def __iter__(self) -> Generator[UTF8000Int, None, None]:
        # queue
        while self._results:
            yield self._results.pop(0)

    def feed(self, utf_8000_bytes: bytes) -> None:
        self._bytes_buffer += utf_8000_bytes
        self._wakeup()

    def close(self) -> None:
        """
        Close the parser.

        Raises EOFError if we are part way through parsing a UTF-8000 sequence.

        Otherwise returns `None`.
        """
        self._generator.close()

    def _wakeup(self) -> None:
        self._generator.send(None)

    def _await_should_parse_again(self) -> Generator[None, None, None]:
        while not self._bytes_buffer:
            yield

    def _await_bytes(self, n_bytes: int) -> Generator[None, None, bytes]:
        while len(self._bytes_buffer) < n_bytes:
            yield

        ret                = self._bytes_buffer[:n_bytes]
        self._bytes_buffer = self._bytes_buffer[n_bytes:]

        return ret

    def _await_byte(self) -> Generator[None, None, int]:
        return (yield from self._await_bytes(1))[0]

    def _await_continuation_byte(self) -> Generator[None, None, int]:
        ret = yield from self._await_byte()
        if not byte_is_continuation(ret):
            self._unpop_byte(ret)
            self._on_error_invalid_continuation_byte()
        return ret

    def _unpop_bytes(self, b: bytes) -> None:
        self._bytes_buffer = b + self._bytes_buffer

    def _unpop_byte(self, c: int) -> None:
        self._unpop_bytes(bytes((c,)))

    def _on_error(self, error_message: str) -> UTF8000Byte:
        raise ValueError(error_message)

    def _on_error_invalid_start_byte(self) -> None:
        # XXX TODO 101: read all following continuation bytes to skip them
        self._on_error("Invalid start byte: continuation byte detected")

    def _on_error_invalid_continuation_byte(self) -> None:
        # XXX TODO 101: should we create / raise a ReplacementCharacterException?
        #               thus should we be calling return on the `_on_error`
        #               functions instead of just calling them?
        self._on_error("Not a continuation byte prefix")

    def _on_error_overlong(self) -> None:
        # XXX TODO 101: read all following continuation bytes to skip them
        self._on_error("Overlong encoding")

    def _utf_8000_parse_single(self) -> Generator[None, None, UTF8000Int]:
        parsed_bytes: list[UTF8000Byte] = []

        start_byte = yield from self._await_byte()
        idx_0 = byte_idx_0(start_byte)

        if idx_0 == 0:
            #
            # Treat ASCII as a special case.
            # This makes it easier for us to write the decoder, and allows a 'fast path'.
            # ASCII has no (need for) overlong checking, and by returning early
            # before the overlong checking code we skip code that checks for multiple
            # start bytes, and further continuation bytes.
            #
            parsed_bytes.append(UTF8000Byte.ASCII(start_byte))

            return UTF8000Int(parsed_bytes)
        elif idx_0 == 1:
            self._on_error_invalid_start_byte()
        elif idx_0 == 2:
            #
            # Treat two byte UTF-8 as a special case.
            #
            # Two byte UTF-8 has only 4 mandatory content bits to check
            # against overlong encoding, unlike all other UTF-8000 sequences that
            # have 5 to check. This is because the jump from ASCII to UTF-8 means
            # we jump from 7 bits of content to 11, a gain of 4 bits of content,
            # whereas with every next additional continuation byte jumping from
            # k-byte UTF-8(000) to k+1-byte UTF-8(000) we gain 5 bits
            # of content; +6 bits from the continuation byte, -1 from extending
            # the start sequence bits by 1.
            #
            # Two byte UTF-8 has all 4 mandatory content bits in one byte,
            # the start byte, unlike all other UTF-8000 sequences
            # which may have them straddled across two bytes.
            #
            # Fun fact: It is for this reason why you will never see the bytes
            #           0xC0 or 0xC1 in a valid UTF-8(000) stream, like anywhere!
            #
            if not start_byte & OVERLONG_MASK_2_BYTE:
                self._on_error_overlong()

            parsed_bytes.append(UTF8000Byte(
                start_byte,
                is_continuation_byte     = False,
                is_start_byte            = True,
                n_bits_content_total     = 5,
                n_bits_content_mandatory = 4
            ))

            n_bytes_expected = idx_0
        else:
            n_bytes_expected = idx_0
            # when idx_0 == 8, this is 8 *so far!*

            if idx_0 != 8:
                is_final_start_byte_a_continuation_byte = False
                final_start_byte_n_bits_content = 7 - idx_0
            else:
                parsed_bytes.append(UTF8000Byte.OnesFilledFirstStartByte())

                is_final_start_byte_a_continuation_byte = True

                # multiple start bytes, the power of UTF-8000!
                while True:
                    start_byte = yield from self._await_continuation_byte()
                    idx_0_content = byte_continuation_content_idx_0(start_byte)
                    n_bytes_expected += idx_0_content

                    if idx_0_content != 6:
                        break
                    else:
                        parsed_bytes.append(UTF8000Byte.OnesFilledContinuationStartByte())

                final_start_byte_n_bits_content = 5 - idx_0_content

            first_non_start_byte_n_bits_content_mandatory = 5 - final_start_byte_n_bits_content

            # Perform checking against overlong encodings.
            # We forbid overlong encodings for two main reasons in my opinion:
            #
            # 1: Security.
            #    To make sure 0b11100000 0b10000000 0b10000000 0b10000000
            #    can't be decoded as codepoint 0, the null 'byte', which speciously
            #    may lead to people carelessly passing such bytes to `strcpy(3)`
            #    and friends, which at best leads to segfaults...
            #
            # 2: Uniqueness of encoding.
            #    Every codepoint has one unique valid representation as UTF-8000 bytes.
            #
            # At this point `start_byte` is the final start byte.
            #
            mask_start, mask_non_start = OVERLONG_MASKS_N_BYTE[final_start_byte_n_bits_content]

            if not mask_non_start:
                # All of the mandatory content bits are
                # contained together in the <<final start byte<<.
                #
                # We can immediately check for overlong encoding, and we don't
                # need to check the first non-start byte.
                #
                # Examples:
                # UTF-8           Only possible for 2 byte UTF-8
                # UTF-8000    ... 0b100IIIII (0b10yyyyyy ...)
                #
                if not start_byte & mask_start:
                    self._on_error_overlong()

                first_non_start_byte = yield from self._await_continuation_byte()
            else:
                first_non_start_byte = yield from self._await_continuation_byte()

                if not mask_start:
                    # All of the mandatory content bits are
                    # contained together in the >>first non-start byte>>.
                    #
                    # Examples:
                    #
                    # UTF-8           Not possible for UTF-8
                    # UTF-8000        0b11111110 (0b10IIIIIy 0b10yyyyyy ...)
                    # UTF-8000    ... 0b10111110 (0b10IIIIIy 0b10yyyyyy ...)
                    #
                    if not first_non_start_byte & mask_non_start:
                        self._on_error_overlong()
                else:
                    # The mandatory content bits are
                    # straddled across two bytes,
                    # starting in the final start byte and continuing into
                    # the first non-start byte.
                    #
                    # Examples:
                    #
                    # UTF-8           0b11110III (0b10IIyyyy 0b10yyyyyy 0b10yyyyyy)
                    # UTF-8000    ... 0b10110III (0b10IIyyyy 0b10yyyyyy ...)
                    # UTF-8000    ... 0b10110III (0b10QQyyyy 0b10yyyyyy ...)
                    # UTF-8000    ... 0b10110QQQ (0b10IIyyyy 0b10yyyyyy ...)
                    #
                    if not (start_byte & mask_start | first_non_start_byte & mask_non_start):
                        self._on_error_overlong()

            parsed_bytes.append(UTF8000Byte(
                start_byte,
                is_continuation_byte     = is_final_start_byte_a_continuation_byte,
                is_start_byte            = True,
                n_bits_content_total     = final_start_byte_n_bits_content,
                n_bits_content_mandatory = final_start_byte_n_bits_content
            ))

            parsed_bytes.append(UTF8000Byte.ContinuationNonStartByteFirst(
                first_non_start_byte,
                n_bits_content_mandatory = first_non_start_byte_n_bits_content_mandatory
            ))

        while len(parsed_bytes) < n_bytes_expected:
            # Add the rest of the purely-content continuation bytes,
            # which have no mandatory content.
            continuation_byte = yield from self._await_continuation_byte()
            parsed_bytes.append(UTF8000Byte.ContinuationNonStartByteNotFirst(
                continuation_byte
            ))

        return UTF8000Int(parsed_bytes)

    def _utf_8000_parse_forever(self) -> Generator[None, None, None]:
        while True:
            try:
                yield from self._await_should_parse_again()
                # Park the generator in this 'parking lot' so that
                # if `close()` is called on the generator at this point
                # it's not an error, whereas if we are in the middle of
                # parsing a UTF-8000 sequence below that *should* be an
                # EOFError if `close()` is called early.
            except GeneratorExit:
                return
            try:
                x = yield from self._utf_8000_parse_single()
            except GeneratorExit as e:
                raise EOFError("Partially decoded UTF-8000 sequence didn't finish") from e
            else:
                self._results.append(x)
