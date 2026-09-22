"""
main.py

Entry point of the image-inspector program; parses the command-line
arguments and dispatches the analysis.
"""

from cli import build_parser
from metadata import run_metadata_analysis
from steganography import run_steganography_analysis
from utils import save_output

import os


def main():
    """Run the program: parse arguments and launch the requested analyses."""
    parser = build_parser()
    args = parser.parse_args()

    if not args.metadata and not args.steganography:
        parser.print_help()
        return

    if not os.path.isfile(args.image_path):
        parser.error("image file not found: %s" % args.image_path)

    results = []

    if args.metadata:
        results.append(run_metadata_analysis(args.image_path))

    if args.steganography:
        results.append(run_steganography_analysis(args.image_path))

    if args.output:
        output_path = save_output(results, args.output)
        print("Data saved in %s" % output_path)
    else:
        for result in results:
            print(result)
            print()


if __name__ == "__main__":
    main()