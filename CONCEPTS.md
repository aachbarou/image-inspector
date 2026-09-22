# Image Inspector - Study Guide (all the concepts you must learn)

This file gathers **every concept** the Image Inspector project touches.
Read it top to bottom. For each section: understand the IDEA, look at how
the code uses it, then be able to explain it in your own words (that is
what the role-play / audit will ask).

Level: junior CS student. If you understand all of this, you will be able
to explain the project confidently.

---

## 1. Bits and bytes (the foundation)

- A **bit** is the smallest unit of data: `0` or `1`.
- A **byte** is 8 bits: e.g. `0b10101000`. One byte can hold a number from
  `0` to `255` (2^8 = 256 values). "0b" means "this is binary".
- A byte has positions. The position with the highest weight (leftmost,
  value 128) is the **Most Significant Bit (MSB)**. The rightmost position
  (value 1) is the **Least Significant Bit (LSB)**.

```
R = 1 0 1 0 1 0 0 0    <- one byte (8 bits)
    ^             ^
  MOST significant  LEAST significant
```

- Changing the LSB only changes the byte by +1 or -1. In an image that
  changes a color by 1/255 - invisible to the human eye. That is why the
  LSB is perfect for hiding data.
- **Bitwise operators** used in the code:
  - `byte & 1`  -> keeps only the LSB (returns 0 or 1). This "reads" one
    bit.
  - `byte | bit` -> sets a bit. This "writes" bits when rebuilding bytes.
  - `byte << 1` -> shift all bits one position left (multiply by 2).

Study: binary numbers, hex (`0xFF` = 255), bitwise AND/OR/shift.

## 2. How an image is stored

- A digital image is a **grid of pixels** (rows and columns), e.g. 197x202.
- Each **pixel** is a color. In RGB color space a pixel has 3 **channels**:
  **R**ed, **G**reen, **B**lue. Each channel is one byte (0..255).
  (256^3 = ~16.7 million colors.)
- So one pixel = 3 bytes = 24 bits.
- `Image.open(path).convert("RGB")` guarantees every pixel is exactly 3
  bytes (drops the alpha/transparency channel).

## 3. Image file formats

- **JPEG (.jpeg/.jpg)**: *lossy* compression. It throws away color details
  humans can't see. That is why JPEG even *looks* different from the raw
  photo. Good for photos on the web.
- **PNG (.png)**: *lossless* compression. Every pixel is preserved exactly.
  PNG also supports transparency (alpha channel), so a pixel can have 4
  channels (RGBA).
- A file format stores bytes in a particular structure (headers, markers,
  compressed data, footer). Knowing the structure lets us find "places that
  are not really part of the picture".

## 4. JPEG structure (important for this project)

A JPEG file is built out of "segments". It starts with a marker and it
ends with an **End-Of-Image (EOI) marker:**

```
FF D8      Start Of Image (SOI)
...        image segments (EXIF, compressio data, ...)
FF D9      End Of Image (EOI)   <- the file is "finished" here
```

- Every decoder reads until `FF D9` and then **stops**.
- Therefore anything you write **after** `FF D9` will never be shown - a
  perfect hidden place.
- In `steganography.py`, `JPEG_EOI = b"\xff\xd9"` and the function
  `file_trailing_data()` returns everything after the LAST occurrence of
  `FF D9`. That is where the PGP keys in the example images are hidden:
  ```
  ...FF D9 | -----BEGIN PGP PUBLIC KEY BLOCK-----\n...
  ```

## 5. What a PGP key is and ASCII armor

- **PGP** (Pretty Good Privacy) = a way to encrypt/sign messages. You have
  a **public key** (to share, others use it to send you encrypted data) and
  a **private key** (secret, only you - used to decrypt/sign).
- PGP keys are often transmitted in **ASCII armor**: a text version wrapped
  in header/footer lines so you can copy them anywhere (email, chat, files):
  ```
  -----BEGIN PGP PUBLIC KEY BLOCK-----
  Version: 01
  xo0EZuV9/AEEAN...BhsK
  =BhsK
  -----END PGP PUBLIC KEY BLOCK-----
  ```
- The header/footer lines are a very recognizable "signature" -> perfect
  for detecting hidden keys. The project scans decoded bytes for
  `-----BEGIN PGP ... -----END PGP ...` using a **regular expression**.

## 6. Regular expressions (regex)

- A regex is a pattern that searches text. `re.search(pattern, text)` finds
  the first match.
- Pattern used: `-----BEGIN PGP.*?-----END PGP[^\r\n]*`
  - `.` matches any character, `*?` lazy (stop as soon as possible),
  - `[^\r\n]*` = "anything except end-of-line, zero or more" (the rest of
    the END line).
  - `re.DOTALL` makes `.` also match newlines, so the whole multi-line
    block is captured.

## 7. Text encodings (ASCII, UTF-8, latin-1)

- **ASCII**: maps bytes 0-127 to letters, digits, punctuation. Every PGP
  key is pure ASCII. ASCII is a subset of UTF-8 (so ASCII text is also
  valid UTF-8).
- **UTF-8**: the standard encoding for the web. Some bytes are multi-byte
  characters.
- **latin-1**: maps every byte 0-255 to a character, so it NEVER fails to
  decode - used as a safe lossless fallback.
- In the code: `bytes.decode("utf-8", errors="ignore")` decodes, and the
  "ignore" flag drops invalid bytes instead of crashing.

## 8. EXIF metadata

- **EXIF** = Exchangeable Image File Format. A standard that stores *data
  about the photo inside the photo file*: camera brand/model, date/time,
  GPS coordinates, lens, exposure settings, software, etc.
- Pillow exposes it as a dictionary of (tag -> value). Tag IDs are numbers;
  `PIL.ExifTags.TAGS` maps numbers to names like "Make", "Model",
  "DateTimeOriginal", "GPSInfo".
- Reading it: `img._getexif()` -> dict. If the image has no EXIF, it
  returns None (we handle that with try/except).

## 9. GPS coordinates and DMS -> decimal

- GPS stores a coordinate as **Degrees, Minutes, Seconds** plus a direction:
  latitude `N`/`S`, longitude `E`/`W`.
  ```
  lat = 32 deg, 05 min, 11.86 s  N
  ```
- Convert to the decimal number everyone uses on maps:
  ```
  decimal = degrees + minutes/60 + seconds/3600
  ```
- Direction sign: `S` and `W` make the number negative; `N` and `E` keep it
  positive.
- Example: `32 + 5/60 + 11.8667/3600 = 32.0866`
- This is implemented in `utils.dms_to_decimal()` and used by
  `metadata.get_gps_coordinates()`.

## 10. LSB steganography

- **Steganography** = hiding a secret inside an innocent file so the secret
  *looks like part of the file*. It is different from **cryptography**
  (which scrambles the message so it looks like noise). Steganography hides
  that a message exists at all.
- **LSB method**: use the least significant bit of each channel to store 1
  bit of the secret:
  - A list of pixels gives a stream of bits: R then G then B for each pixel.
  - The secret is a sequence of bytes (8 bits each).
  - Write secret bit 1 -> LSB of channel 1, bit 2 -> LSB of channel 2, ...
  - Max hidden size: image_width * image_height * 3 channels / 8 bytes.
    A 197x202 image can hide `197*202*3/8 ≈ 14893` bytes ~ 15 KB.
- Why invisible: changing LSB changes color by 1/255.
- **Extraction** (what the code does): read all LSBs, group into bytes
  (bonus: try both bit orders - MSB first and LSB first; the hiding tool
  decides the order, so we try both), decode as text, look for PGP armor.
- `collect_lsb_bits()` uses `channel & 1` per channel.
- `bits_to_bytes()` groups 8 bits into one byte.
- **Limits of LSB detection**: if the message is short or the picture is
  noisy/compressed, tools like this can miss it or report false positives.

## 11. Metadata vs. hidden data (why both parts exist)

- **Metadata** is *attached to the file by a normal camera* - not a
  secret, but sensitive (location, device, time). An investigator reads it
  to learn *who/when/where*.
- **Hidden data** is *deliberately inserted* (LSB, appended bytes, etc.).
  The investigator's job is to recover the payload (here: PGP keys).
- Key news-style line: "a photo can tell you not only *what you see*, but
  also *who took it, where, with which device* - and can carry a *secret
  message* nobody else sees."

## 12. Command-Line Interface (CLI) and argparse

- The user controls the program through command-line arguments.
- **Positional argument**: the image path (must be given).
- **Flags/options**: `-m` (metadata), `-s` (steganography), `-o FILE`
  (save output).
- `store_true` means the flag is a boolean: present or absent.
- **argparse** is Python's built-in argument parser: it creates the
  `--help` screen, checks the input, prints friendly errors.
- `main.py` is the controller: parse args -> call the right function ->
  print or save. No image logic in main - separation of concerns.

## 13. Files and exceptions

- Binary read: `open(path, "rb")` gives bytes (`b"..."`), needed to scan
  for `FF D9`.
- Text write: `open(path, "w", encoding="utf-8")` to save results.
- `try/except` where input can be corrupt (e.g., broken EXIF) so the tool
  doesn't crash - it reports "no data" instead.

## 14. Code organization (project structure)

- `main.py`      - entry point, controllers the flow.
- `cli.py`       - builds the parser + the help screen.
- `metadata.py`  - EXIF/GPS/device/date extraction.
- `steganography.py` - LSB extraction + appended-data detection.
- `utils.py`     - shared helpers (DMS conversion, save_output).
- `reports/`     - saved outputs (git-ignored).
- `images/`      - the test images (with GPS metadata and hidden PGP keys).

## 15. The ethical / security side (expected in the audit)

- Metadata (GPS, camera) = privacy risk: someone can find where you live.
- Steganography = used by malware, spies and criminals to sneak data past
  firewalls; also used by journalists to keep data secret.
- **Always get permission** before analyzing an image.
- Be able to say: "This tool is for education, CTFs, and authorized
  forensics. Using it on images without permission could break the law
  (privacy laws, GDPR, etc.)."

---

## Quick personal checklist (test yourself)

Answer these out loud before the audit:

1. How many bits are in a byte? What is the LSB?
2. What is `byte & 1` doing?
3. What RGB means and how many bytes one pixel is?
4. Difference between JPEG and PNG?
5. What two bytes end a JPEG file? What happens if I add bytes after them?
6. What is EXIF? Name 3 EXIF fields used in the tool.
7. How do you convert 40 deg 12' 30" N to decimal?
8. What is LSB steganography and why can't the eye see it?
9. What is the maximum size of a hidden message in a 100x100 RGB image?
10. What does a PGP key look like in ASCII armor?
11. Steganography vs cryptography: what is the difference?
12. What does `-m`, `-s`, `-o` do in the CLI?
13. Why must you never analyze an image without permission?