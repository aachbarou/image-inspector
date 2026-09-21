"""
cli.py

Builds the command-line interface for the image-inspector tool.

The program is used like this:

    image-inspector [-m] [-s] [-o FILE] IMAGE

Where the flags mean:
    -m  run the metadata analysis
    -s  run the steganography analysis
    -o  save the results into a file instead of printing them

argparse gives us argument parsing, the --help flag and error messages for
free.  We customize the --help screen so it looks like the one described in
the project subject.
"""

import argparse
import sys as _sys

PROG = "image-inspector"

# This exact layout is the help screen described in the project subject.
HELP_TEXT = (
    "Welcome to Image Inspector\n"
    "\n"
    "OPTIONS:\n"
    "    -m  Metadata          Extract metadata from the image (e.g., geolocation, device info)\n"
    "    -s  Steganography     Detect and extract hidden data from the image using steganography techniques\n"
    "    -o  \"FileName\"        Specify the file name to save output\n"
    "    --help                Display this help message\n"
)


class CustomHelpParser(argparse.ArgumentParser):
    """
    An ArgumentParser that prints our custom help screen instead of the
    default one.  Everything else (parsing, errors, exit codes) still works
    exactly like a normal argparse parser.
    """

    def format_help(self):
        return HELP_TEXT

    def exit(self, status=0, message=None):
        if message:
            self._print_message(message, _sys.stderr)
        raise SystemExit(status)


def build_parser():
    """
    Create and return the configured argument parser.

    The parser understands:
        IMAGE            a positional argument: the path to the image file
        -m/--metadata    run the metadata analysis     (store_true flag)
        -s/--steganography run the stego analysis      (store_true flag)
        -o/--output FILE save the results into a file (stores a string)

    Returns a CustomHelpParser that is ready to parse_args().
    """
    parser = CustomHelpParser(
        prog=PROG,
        description="A tool for inspecting images (metadata and steganography analysis).",
        add_help=True,
    )

    parser.add_argument(
        "image_path",
        help="Path to the image file you want to analyze",
    )

    parser.add_argument(
        "-m", "--metadata",
        action="store_true",
        help="Run the metadata analysis on the image",
    )

    parser.add_argument(
        "-s", "--steganography",
        action="store_true",
        help="Detect hidden data (e.g. PGP keys) in the image",
    )

    parser.add_argument(
        "-o", "--output",
        help="File name to save the analysis results",
    )

    return parser