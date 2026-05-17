"""
UTF-8000 CLI

- Info about UTF-8000 bytes
- stdin-stdout encoder
"""

import argparse

from .info   import main_info
from .encode import main_encode

def get_cli_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description = __doc__)
    action = parser.add_subparsers(title = "action", dest = "action", required = True)

    parser_info = action.add_parser("info",
        help = (h := "Show info about an integer encoded in UTF-8000 bytes"),
        description = ".\n\n".join((
            h,
        )),
    )
    parser_info.add_argument("-#", action = "store_true",
        help = f"Show base prefixes {'0b'!r} and {'0x'!r}"
    )
    parser_info.add_argument("--color", choices = ["yes", "no", "auto"], default = "auto",
        help = "Highlight the anatomy of UTF-8000 bytes in color"
    )
    parser_info.add_argument("n_str", metavar = "N",
        help = "The integer to encode. It must be either a decimal integer, or hex in the form U+(...X)X"
    )

    parser_encode = action.add_parser("encode",
        help = (h := "Read codepoint integers from stdin and output UTF-8000 bytes to stdout"),
        description = ".\n\n".join((
            h,
            "Inputted integers must be separated by newlines",
            "Inputted integers must be either a decimal integer, or hex in the form U+(...X)X"
        )),
    )

    args = parser.parse_args()

    return args

def main() -> None:
    args = get_cli_args()

    {
        "info":   main_info,
        "encode": main_encode,
    }[args.action](args)
