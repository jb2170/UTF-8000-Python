import sys
import argparse

from UTF8000.decode import UTF8000IncrementalDecoder

from .common import format_codepoint

def main_decode(args: argparse.Namespace) -> None:
    decoder = UTF8000IncrementalDecoder()

    while chunk := sys.stdin.buffer.raw.read(4096):
        decoder.feed(chunk)

        for n in decoder:
            print(format_codepoint(int(n)))

    decoder.close()
