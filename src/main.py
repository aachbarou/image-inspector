"""
main.py

This is the entry point (controller) for the image-inspector program.
It only handles command-line arguments and decides which function to call.
It does NOT contain any real image-processing logic.
"""

import argparse

from metadata import run_metadata_analysis
from steganography import run_steganography_analysis
from utils import save_output


def main():
    # Create the argument parser with a description shown in --help
    parser = argparse.ArgumentParser(
        prog="image-inspector",
        description="A tool for inspecting images (metadata and steganography analysis)."
    )

    # Positional argument: the image file path (always required)
    parser.add_argument(
        "image_path",
        help="Path to the image file you want to analyze"
    )

    # Optional flag: run metadata analysis
    parser.add_argument(
        "-m", "--metadata",
        action="store_true",
        help="Run metadata analysis on the image"
    )

    # Optional flag: run steganography analysis
    parser.add_argument(
        "-s", "--steganography",
        action="store_true",
        help="Run steganography analysis on the image"
    )

    # Optional flag: specify an output file for results
    parser.add_argument(
        "-o", "--output",
        help="Optional path to save the analysis results"
    )

    # Parse the arguments given by the user
    args = parser.parse_args()

    # This will collect whatever results our placeholder functions return
    results = []

    # If the user chose metadata analysis, call the placeholder function
    if args.metadata:
        result = run_metadata_analysis(args.image_path)
        results.append(result)

    # If the user chose steganography analysis, call the placeholder function
    if args.steganography:
        result = run_steganography_analysis(args.image_path)
        results.append(result)

    # If the user didn't choose any analysis type, tell them how to use the tool
    if not args.metadata and not args.steganography:
        parser.print_help()
        return

    # If the user specified an output file, save the results there
    if args.output:
        save_output(results, args.output)
    else:
        # Otherwise, just print the results to the screen
        for result in results:
            print(result)


if __name__ == "__main__":
    main()