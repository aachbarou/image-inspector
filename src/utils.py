"""
utils.py

Small helper functions shared by the rest of the program:
  - dms_to_decimal : convert GPS (Degrees, Minutes, Seconds) to decimal
  - save_output    : write analysis results to a file
"""

import os


def dms_to_decimal(dms, ref):
    """
    Convert GPS coordinates from Degrees/Minutes/Seconds into a decimal
    number, the same way maps and GPS devices show them.

    EXIF stores one coordinate as a tuple of three rational numbers:
        (degrees, minutes, seconds)
    so a latitude like 32<deg> 05' 11.8" becomes:

        decimal = degrees + minutes/60 + seconds/3600
                = 32     + 5/60      + 11.8/3600
                = 32.0866...

    The letter in `ref` tells us which direction it is:
        'N' (north) and 'E' (east)  -> positive number
        'S' (south) and 'W' (west)  -> negative number

    Returns the signed decimal value, or None if the input is invalid.
    """
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
    """
    Write the analysis results (a list of strings) into a text file.

    This function also makes sure the parent directory exists, so saving to
    a folder like "reports/" works even if that folder is new.  It returns
    the path that was written, so the caller can tell the user where the
    data was saved.
    """
    directory = os.path.dirname(output_path)
    if directory and not os.path.isdir(directory):
        os.makedirs(directory, exist_ok=True)

    # Each result is already a multi-line string; a separator between
    # multiple results keeps the file readable when both -m and -s are used.
    content = "\n\n".join(str(result) for result in results)

    with open(output_path, "w", encoding="utf-8") as handle:
        handle.write(content)
        handle.write("\n")

    return output_path