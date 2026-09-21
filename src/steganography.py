"""
steganography.py

Detects and extracts hidden data (LSB steganography) from an image.

Concept: Least Significant Bit (LSB) steganography.
====================================================
An image is a grid of pixels.  Each pixel has 3 color channels (Red, Green,
Blue) and each channel is stored as one byte (8 bits):  e.g.  R = 168.

The leftmost bit of a byte is called the MOST significant bit, and the
rightmost bit is the LEAST significant bit:

    R = 1 0 1 0 1 0 0 0          <- bits of one byte
        ^             ^
    most significant  least significant

The last bit only changes the color by 1/255, which the human eye cannot
see.  That is exactly why it is a good place to hide a message:

    - we can overwrite the LSB of a color byte without anyone noticing,
    - each color byte hides exactly 1 bit of the secret message.

So a 8-bit ASCII character (e.g. 'A' = 0b01000001) is spread over 8
different color bytes, one bit per byte.
"""

from PIL import Image

import os
import re
import string

# PGP keys are ASCII-armored: they always start and end with these markers.
# PGP_START / PGP_END are kept short so ARMOR_HEADER can match any PGP type
# (PUBLIC KEY, PRIVATE KEY, SIGNATURE, ...).
PGP_START = "-----BEGIN PGP"
PGP_END = "-----END PGP"

# Full-block matcher: from the BEGIN line up to the end of the END line.
# Using re.DOTALL lets "." match newlines so the whole block is captured.
PB_BEGIN = r"-----BEGIN PGP"
PB_END = r"-----END PGP[^\r\n]*"
PGP_BLOCK_RE = re.compile(
    PB_BEGIN + r".*?" + PB_END,
    re.DOTALL,
)

# JPEG End-Of-Image (EOI) marker.  A valid JPEG always finishes with the two
# bytes 0xFF 0xD9.  Anything found AFTER that marker is not part of the
# actual photo - it is *appended* data and a classic place to hide secrets,
# because nobody expects bytes after the end of the file.
JPEG_EOI = b"\xff\xd9"


def collect_lsb_bits(pixels):
    """
    Concept: extract one bit per color byte.
    ---------------------------------------

    For every pixel we do a bitwise AND with 1:

        byte & 1

    This returns 0 if the byte is even and 1 if the byte is odd, which is
    exactly the value of the least significant bit.

    We collect the bits of R, G and B for every pixel in row-major order
    (left to right, top to bottom).  The returned list is a flat stream of
    hidden bits:  [1, 0, 1, ...]
    """
    bits = []
    for red, green, blue in pixels:
        bits.append(red & 1)    # LSB of the red channel
        bits.append(green & 1)  # LSB of the green channel
        bits.append(blue & 1)   # LSB of the blue channel
    return bits


def bits_to_bytes(bits, msb_first=True):
    """
    Concept: rebuild 8-bit bytes from the bit stream.
    ------------------------------------------------

    The hidden message is a sequence of bytes.  We group the extracted bits
    into chunks of 8 and assemble each chunk into a single byte value.

    Two conventions exist for the order of the bits inside a byte:

      1. msb_first=True  -> first extracted bit is the MOST significant bit
                            of the byte.  This is how the message is stored
                            when it is written sequentially into the image.
      2. msb_first=False -> first extracted bit is the LEAST significant
                            bit (the bit order is reversed).

    We support both because different hiding tools use different orders.
    """
    message = bytearray()
    for i in range(0, len(bits) - 7, 8):
        chunk = bits[i:i + 8]
        byte = 0
        if msb_first:
            # msb_first: shift left each time, then append the next bit.
            for bit in chunk:
                byte = (byte << 1) | bit
        else:
            # lsb_first: the first bit is the least significant one.
            for position, bit in enumerate(chunk):
                byte |= bit << position
        message.append(byte)
    return bytes(message)


def decode_candidates(pixels):
    """
    Concept: try both possible bit orders and both text encodings.

    We do not know, a priori, how the image was encoded, so we generate
    several candidate texts and let the caller look for the PGP marker in
    each of them.

    Encoding note: ASCII is a subset of UTF-8, and PGP keys are pure ASCII.
    Latin-1 is used only as a "lossless" fallback so no byte ever raises an
    error when a non-ASCII byte is encountered.
    """
    bits = collect_lsb_bits(pixels)
    candidates = []

    # Candidate 1: receive the bits most-significant-bit first.
    upstream = bits_to_bytes(bits, msb_first=True)
    candidates.append(upstream.decode("utf-8", errors="ignore"))
    candidates.append(upstream.decode("latin-1", errors="ignore"))

    # Candidate 2: receive the bits least-significant-bit first.
    reversed_stream = bits_to_bytes(bits, msb_first=False)
    candidates.append(reversed_stream.decode("utf-8", errors="ignore"))
    candidates.append(reversed_stream.decode("latin-1", errors="ignore"))

    return candidates


def find_pgp_block(text):
    """
    Concept: locate the hidden message inside a large byte stream.

    The hidden payload rarely starts at the very first byte of the image.
    There is often "garbage" before and after the real message.  Instead of
    assuming where the message starts, we scan the whole decoded text for
    the PGP ASCII-armor pattern and slice out only that block.

    A regular expression is used so we match the complete block, including
    the full END line (e.g. "-----END PGP PUBLIC KEY BLOCK-----"), no
    matter what type of PGP block is hidden.
    """
    match = PGP_BLOCK_RE.search(text)
    if match:
        return match.group(0)
    return None


def file_trailing_data(image_path):
    """
    Return the bytes that appear *after* the JPEG end-of-image marker.

    A JPEG picture is a sequence of segments that ends with the two bytes
    0xFF 0xD9 (the EOI marker).  Decoding tools simply stop reading there,
    so if a secret is appended after those two bytes:

       ... 0xFF 0xD9  |  -----BEGIN PGP PUBLIC KEY BLOCK-----  \n ...

    ...nobody looks at it.  We grab "everything after the LAST EOI" and
    search it for the hidden message.

    If the file is not a JPEG (no EOI marker), we return the whole file so
    the caller can still scan it.
    """
    with open(image_path, "rb") as bytes:
        data = bytes.read()

    marker_position = data.rfind(JPEG_EOI)
    if marker_position == -1:
        return data

    # +2 -> skip the two EOI bytes themselves.
    return data[marker_position + 2:]


def find_pgp_block_in_data(data):
    """
    Search raw bytes (from the file) for an ASCII-armored PGP block.

    We decode the bytes as latin-1 because it maps every possible byte
    (0-255) to a character without ever raising an error.  Since PGP armor
    is pure ASCII and ASCII is a subset of latin-1, the block decodes fine.
    """
    text = data.decode("latin-1", errors="ignore")
    return find_pgp_block(text)


def extract_ascii_strings(text, min_length=10):
    """
    Concept: fallback detection for plain-text hidden messages.

    If no PGP marker is found, we still scan the decoded stream for runs of
    printable ASCII characters.  Long readable runs are strong signals that
    some text was hidden inside the image (not just compressed image data).

    Compressed (JPEG) data is often *binary*, so its printable runs usually
    contain lots of weird punctuation.  To cut down those false positives we
    only keep strings that are mostly letters/digits and contain at least one
    real word - that is what actual hidden text looks like.
    """
    word_re = re.compile(r"[A-Za-z]{4,}")
    strings = []
    current = []

    for char in text:
        if char in string.printable and char not in "\r\n\t\x0b\x0c":
            current.append(char)
        else:
            if len(current) >= min_length and _is_meaningful(current):
                strings.append("".join(current))
            current = []

    if len(current) >= min_length and _is_meaningful(current):
        strings.append("".join(current))

    return strings


def _is_meaningful(chars, letters_digits_ratio=0.6):
    """
    A string is "meaningful" when most of its characters are letters or
    digits, and it contains at least one four-letter word.  Random JPEG
    noise is usually punctuation-heavy and fails this check.
    """
    text = "".join(chars)
    if not word_re.search(text):
        return False
    meaningful_count = sum(c.isalnum() for c in text)
    return meaningful_count / len(text) >= letters_digits_ratio


def run_steganography_analysis(image_path):
    """
    Main entry point for the steganography analysis.

    The hidden data in a JPEG can live in several different places, so we
    check them all and return the first hit:

      1. Raw-file data appended AFTER the JPEG end-of-image marker (0xFFD9).
         This is where the example images keep their PGP keys.
      2. The LSBs of every pixel (classic LSB steganography inside the
         actual picture data).
      3. Long runs of readable ASCII text in either stream, as a fallback
         for secret plain-text messages.

    Each step searches for a PGP ASCII-armor block first ("-----BEGIN PGP
    PUBLIC KEY BLOCK-----") and only reports other text if no PGP block is
    found.
    """
    # 1) Look inside the raw bytes of the image file (trailing data).
    trailing = file_trailing_data(image_path)
    if trailing:
        pgp_block = find_pgp_block_in_data(trailing)
        if pgp_block:
            return (
                "Hidden PGP key found in appended image data:\n\n"
                f"{pgp_block}"
            )

    # 2) Classic LSB steganography inside the pixels.
    #    Load the image.  "convert('RGB')" makes sure every pixel has exactly
    #    3 channels and drops the alpha channel, so the math stays predictable.
    image = Image.open(image_path).convert("RGB")
    pixels = list(image.getdata())  # list of (R, G, B) tuples, row by row

    # Build every candidate text from the LSBs of the pixels and look for a
    # PGP key block in each one.
    for text in decode_candidates(pixels):
        pgp_block = find_pgp_block(text)
        if pgp_block:
            return (
                "Hidden PGP key found via LSB extraction:\n\n"
                f"{pgp_block}"
            )

    # 3) No PGP key anywhere: check for any other readable text.
    for text in decode_candidates(pixels) + [trailing.decode("latin-1", "ignore")]:
        strings = extract_ascii_strings(text)
        if strings:
            return (
                "No PGP key found, but hidden ASCII strings were detected:\n\n"
                + "\n".join(strings)
            )

    # Nothing readable was found.
    return "No hidden data detected in the image."