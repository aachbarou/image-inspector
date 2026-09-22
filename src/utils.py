"""
utils.py

Shared helper functions used by the rest of the program.
"""

import os


def dms_to_decimal(dms, ref):
    """Convert GPS degrees/minutes/seconds into a signed decimal value."""
    try:
        degrees = float(dms[0])
        minutes = float(dms[1])
        seconds = float(dms[2])

        decimal = degrees + minutes / 60.0 + seconds / 3600.0

        if str(ref).upper() in ("S", "W"):
            decimal = -decimal

        return decimal
    except (TypeError, ValueError, IndexError):
        return None


def save_output(results, output_path):
    """Write the analysis results to a text file and return its path."""
    directory = os.path.dirname(output_path)
    if directory and not os.path.isdir(directory):
        os.makedirs(directory, exist_ok=True)

    content = "\n\n".join(str(result) for result in results)

    with open(output_path, "w", encoding="utf-8") as handle:
        handle.write(content)
        handle.write("\n")

    return output_path