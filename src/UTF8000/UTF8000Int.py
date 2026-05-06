from __future__ import annotations

from .UTF8000Byte import UTF8000Byte

class UTF8000Int:
    def __init__(self, utf_8000_bytes: list[UTF8000Byte]) -> None:
        # No validation is done; we're assuming these come from `UTF8000IncrementalDecoder`
        self.utf_8000_bytes = utf_8000_bytes

    def __str__(self) -> str:
        return " ".join(str(b) for b in self.utf_8000_bytes)

    def debug_str(self) -> str:
        return " ".join(b.debug_str() for b in self.utf_8000_bytes)

    def __int__(self) -> int:
        ret = 0
        content_bytes = (b for b in self.utf_8000_bytes if b.is_content_byte) # wasteful; just skip to first
        for content_byte in content_bytes:
            ret <<= content_byte.n_content_bits
            ret += content_byte.content
        return ret

    @property
    def n_bytes(self) -> int:
        return len(self.utf_8000_bytes)

    @property
    def n_bits_capacity(self) -> int:
        if self.n_bytes == 1:
            return 7
        else:
            return 1 + 5 * self.n_bytes

    @property
    def n_bits_used(self) -> int:
        content_bytes = (b for b in self.utf_8000_bytes if b.is_content_byte)
        raise NotImplementedError

    @classmethod
    def blank(cls, n_bytes: int):
        raise NotImplementedError
        if n_bytes < 1:
            raise ValueError

        if n_bytes == 1:
            segments = bytearray([_ZERO])

        elif n_bytes < 8:
            # lol whatever this is hardcoded
            segments = bytearray(
                [_ZERO + (((1 << n_bytes) - 1) << (8 - n_bytes))] +
                [_CONTINUATION_PREFIX for _ in range(n_bytes - 1)]
            )

        else:
            start_byte = [0b11111111]
            # cont bytes
            n_filled, n_bits_partial = divmod(n_bytes - 8, 6)
            filled  = [_CONTINUATION_FILLED for _ in range(n_filled)]
            partial = [_CONTINUATION_PREFIX + (((1 << n_bits_partial) - 1) << (6 - n_bits_partial))]
            empty   = [
                0b10000000
                for _ in range(
                    n_bytes - (len(start_byte) + len(filled) + len(partial))
                )
            ]

            segments = bytearray(start_byte + filled + partial + empty)

        return cls(segments)

    def promote(self) -> UTF8000Int:
        # reserve another continuation byte, adjust start byte(s), move start byte(s) content to new continuation byte, and pad new prefix with 0s if +ve or 1s if -ve
        raise NotImplementedError

    def __add__(self, rhs: UTF8000Int) -> UTF8000Int:
        raise NotImplementedError
