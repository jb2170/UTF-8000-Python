import sys
import argparse

from UTF8000.encode import encode

from .common import parse_codepoint

def main_encode(args: argparse.Namespace) -> None:
    for line in sys.stdin:
        n = parse_codepoint(line)

        utf_8000_bytes = encode(n)

        sys.stdout.buffer.write(utf_8000_bytes)
        sys.stdout.buffer.flush()
