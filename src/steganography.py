"""
steganography.py

Detects and extracts hidden data (LSB steganography) from an image.
"""

from PIL import Image

import os
import re
import string

# Markers delimiting an ASCII-armored PGP block.
PGP_START = "-----BEGIN PGP"
PGP_END = "-----END PGP"

# Pattern matching a full ASCII-armored PGP block.
PGP_BLOCK_RE = re.compile(
    r"-----BEGIN PGP.*?-----END PGP[^\r\n]*",
    re.DOTALL,
)

# JPEG end-of-image marker; appended bytes after it may hide secrets.
JPEG_EOI = b"\xff\xd9"


def collect_lsb_bits(pixels):
    """Extract the least significant bit of each color channel of every pixel."""
    bits = []
    for red, green, blue in pixels:
        bits.append(red & 1)
        bits.append(green & 1)
        bits.append(blue & 1)
    return bits


def bits_to_bytes(bits, msb_first=True):
    """Reassemble a bit stream into bytes using the given bit ordering."""
    message = bytearray()
    for i in range(0, len(bits) - 7, 8):
        chunk = bits[i:i + 8]
        byte = 0
        if msb_first:
            for bit in chunk:
                byte = (byte << 1) | bit
        else:
            for position, bit in enumerate(chunk):
                byte |= bit << position
        message.append(byte)
    return bytes(message)


def decode_candidates(pixels):
    """Generate candidate text decodings of the hidden bit stream."""
    bits = collect_lsb_bits(pixels)
    candidates = []

    upstream = bits_to_bytes(bits, msb_first=True)
    candidates.append(upstream.decode("utf-8", errors="ignore"))
    candidates.append(upstream.decode("latin-1", errors="ignore"))

    reversed_stream = bits_to_bytes(bits, msb_first=False)
    candidates.append(reversed_stream.decode("utf-8", errors="ignore"))
    candidates.append(reversed_stream.decode("latin-1", errors="ignore"))

    return candidates


def find_pgp_block(text):
    """Search a text for an ASCII-armored PGP block."""
    match = PGP_BLOCK_RE.search(text)
    if match:
        return match.group(0)
    return None


def file_trailing_data(image_path):
    """Return the bytes appended after the JPEG end-of-image marker."""
    with open(image_path, "rb") as file:
        data = file.read()

    marker_position = data.rfind(JPEG_EOI)
    if marker_position == -1:
        return data

    return data[marker_position + 2:]


def find_pgp_block_in_data(data):
    """Search raw file bytes for an ASCII-armored PGP block."""
    text = data.decode("latin-1", errors="ignore")
    return find_pgp_block(text)


def extract_ascii_strings(text, min_length=10):
    """Extract runs of meaningful printable ASCII text from a stream."""
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
    """Check whether a string resembles meaningful text."""
    text = "".join(chars)
    if not word_re.search(text):
        return False
    meaningful_count = sum(c.isalnum() for c in text)
    return meaningful_count / len(text) >= letters_digits_ratio


def run_steganography_analysis(image_path):
    """Perform the full steganography analysis on an image and return the findings."""
    trailing = file_trailing_data(image_path)
    if trailing:
        pgp_block = find_pgp_block_in_data(trailing)
        if pgp_block:
            return (
                "Hidden PGP key found in appended image data:\n\n"
                f"{pgp_block}"
            )

    image = Image.open(image_path).convert("RGB")
    pixels = list(image.getdata())

    for text in decode_candidates(pixels):
        pgp_block = find_pgp_block(text)
        if pgp_block:
            return (
                "Hidden PGP key found via LSB extraction:\n\n"
                f"{pgp_block}"
            )

    for text in decode_candidates(pixels) + [trailing.decode("latin-1", "ignore")]:
        strings = extract_ascii_strings(text)
        if strings:
            return (
                "No PGP key found, but hidden ASCII strings were detected:\n\n"
                + "\n".join(strings)
            )

    return "No hidden data detected in the image."