"""
main.py

This is the entry point (controller) for the image-inspector program.
It only parses command-line arguments (via cli.py) and decides which
function to call.  It does NOT contain any real image-processing logic;
that lives in metadata.py and steganography.py.
"""

from cli import build_parser
from metadata import run_metadata_analysis
from steganography import run_steganography_analysis
from utils import save_output

import os


def main():
    # Build (via cli.py) and parse the command-line arguments.
    parser = build_parser()
    args = parser.parse_args()

    # If the user didn't choose any analysis type, show the help screen.
    if not args.metadata and not args.steganography:
        parser.print_help()
        return

    # Give a friendly error instead of a traceback when the file is missing.
    if not os.path.isfile(args.image_path):
        parser.error("image file not found: %s" % args.image_path)

    # This will collect whatever results the analysis functions return.
    results = []

    # If the user chose metadata analysis, run it and remember the result.
    if args.metadata:
        results.append(run_metadata_analysis(args.image_path))

    # If the user chose steganography analysis, run it and remember the result.
    if args.steganography:
        results.append(run_steganography_analysis(args.image_path))

    # If the user specified an output file, save the results there.
    if args.output:
        output_path = save_output(results, args.output)
        print("Data saved in %s" % output_path)
    else:
        # Otherwise, just print the results to the screen.
        for result in results:
            print(result)
            print()


if __name__ == "__main__":
    main()