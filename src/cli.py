"""
cli.py

Builds the command-line interface for the image-inspector tool.
"""

import argparse
import sys as _sys

PROG = "image-inspector"

# Help screen layout described in the project subject.
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
    """ArgumentParser that prints a custom help screen."""

    def format_help(self):
        """Return the custom help text."""
        return HELP_TEXT

    def exit(self, status=0, message=None):
        """Print the error message (if any) and exit with the given status."""
        if message:
            self._print_message(message, _sys.stderr)
        raise SystemExit(status)


def build_parser():
    """Create and return the configured argument parser."""
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