# Image Inspector

A command-line tool that inspects image files and reveals the information
hidden inside them:

1. **Metadata extraction** – reads EXIF data: GPS coordinates, the device
   (make/model) and the date/time the photo was taken.
2. **Steganography detection** – finds and extracts hidden data such as
   PGP public keys, using Least Significant Bit (LSB) analysis and
   appended-data detection.

Built with Python and [Pillow](https://pillow.readthedocs.io/).

> **Disclaimer:** This project is for educational purposes only. Analyzing
> an image that you do not own – or that was taken by someone else – can be
> illegal. See the [Ethical and Legal Considerations](#ethical-and-legal-considerations)
> section before using the tool.

---

## Table of Contents

- [Features](#features)
- [Prerequisites](#prerequisites)
- [Setup](#setup)
- [Usage](#usage)
- [Examples](#examples)
- [How it works](#how-it-works)
- [Project structure](#project-structure)
- [Testing](#testing)
- [Ethical and Legal Considerations](#ethical-and-legal-considerations)
- [Acknowledgments](#acknowledgments)

---

## Features

- Extract and display **geolocation** (latitude / longitude) stored in GPS
  EXIF tags.
- Extract **device information** (camera make and model).
- Extract the **date and time** the photo was taken.
- Detect hidden **PGP keys** with ASCII-armor (`-----BEGIN PGP ... ----`)
  hidden via LSB steganography or appended to the image file.
- Optional fallback detection of readable plain-text strings.
- Save results to a file (`-o`) or print them to the screen.
- Human-readable `--help` screen.

---

## Prerequisites

- **Python 3.7+** (tested with Python 3.14)
- **Pillow** – the Python Imaging Library.

Check your Python version:

```sh
python3 --version
```

---

## Setup

1. Clone or copy the project folder.
2. (Recommended) create a virtual environment:

   ```sh
   python3 -m venv venv
   source venv/bin/activate
   ```

3. Install the dependency:

   ```sh
   pip install -r requirements.txt
   ```

`requirements.txt` contains a single line: `Pillow`.

---

## Usage

Run the tool from inside the `src/` directory:

```sh
cd src
python3 main.py --help
```

```
Welcome to Image Inspector

OPTIONS:
    -m  Metadata          Extract metadata from the image (e.g., geolocation, device info)
    -s  Steganography     Detect and extract hidden data from the image using steganography techniques
    -o  "FileName"        Specify the file name to save output
    --help                Display this help message
```

### Options

| Option | Description |
| ------ | ----------- |
| `-m` / `--metadata`       | Run the metadata analysis. |
| `-s` / `--steganography`  | Run the steganography analysis. |
| `-o FILE` / `--output FILE` | Save the results into `FILE` instead of printing them. |
| `--help`                  | Show the help screen. |

The image path is a positional argument and is always required.

> **Note:** usage on Windows: `py main.py ...`, on Linux/macOS: `python3 main.py ...`
> If you prefer to run it as a program (`image-inspector`), add a symlink or
> a small wrapper script in your shell's `PATH` pointing to `main.py`.

---

## Examples

### 1. Metadata extraction (printed to screen)

```sh
python3 main.py -m ../images/image-example3.jpeg
```

```
Metadata report for: ../images/image-example3.jpeg
----------------------------------------
File format : JPEG (2719x1808)
Lat/Lon     : not available
Device      : NIKON CORPORATION / NIKON D3200
Date        : 2014-08-28 04:17:38
Software    : Adobe Photoshop CS4 Macintosh
...
```

### 2. Metadata extraction (saved to a file)

```sh
python3 main.py -m -o "../reports/metadata.txt" ../images/image-example1.jpeg
Data saved in ../reports/metadata.txt
```

### 3. Steganography detection (printed to screen)

```sh
python3 main.py -s ../images/image-example2.jpeg
```

```
Hidden PGP key found in appended image data:

-----BEGIN PGP PUBLIC KEY BLOCK-----
xo0EZuV9/AEEAN...BhsK
-----END PGP PUBLIC KEY BLOCK-----
```

### 4. Steganography detection (saved to a file)

```sh
python3 main.py -s -o "../reports/hidden_data.txt" ../images/image-example2.jpeg
Data saved in ../reports/hidden_data.txt
```

### 5. Both analyses at once

```sh
python3 main.py -m -s -o "../reports/report.txt" ../images/image-example1.jpeg
```

---

## How it works

### Metadata

EXIF (Exchangeable Image File Format) is a metadata standard embedded in the
image file by the camera/phone. Pillow parses it; we translate numeric EXIF
tag IDs into readable names and format the useful ones:

- GPS coordinates are stored as (degrees, minutes, seconds) plus a direction
  letter (`N`/`S`/`E`/`W`). We convert them to a single decimal number:

  ```
  decimal = degrees + minutes/60 + seconds/3600
  ```

  `S` and `W` become negative.

### Steganography

Steganography is the practice of hiding a secret *inside* an innocent-looking
cover file. The tool checks two carriers:

1. **LSB (Least Significant Bit):** every pixel channel (Red, Green, Blue)
   is one byte. The rightmost bit of a byte barely changes the color, so it is
   invisible to the eye. We read the LSB of every channel and rebuild the
   hidden bytes (trying both bit orders and text encodings).
2. **Appended data:** a JPEG always ends with the marker `0xFF 0xD9`
   (End-Of-Image). Decoders stop reading there, so a secret appended after
   that marker goes unnoticed. The tool reads everything after the last
   `0xFF 0xD9` and scans it for a message.

In both cases the tool first looks for an ASCII-armored **PGP key block**
(`-----BEGIN PGP PUBLIC KEY BLOCK-----` ... `-----END PGP...`) and reports it
in full. If no PGP armor is found, it falls back to reporting long readable
ASCII strings.

---

## Project structure

```
image-inspector/
├── README.md            # this file
├── requirements.txt     # Python dependencies (Pillow)
├── subject.txt          # the project subject
├── images/              # example test images
├── samples/             # (optional) extra samples
├── reports/             # saved analysis results (git-ignored)
└── src/
    ├── main.py          # entry point / controller (parses args, runs analyses)
    ├── cli.py           # command-line interface (parser + help screen)
    ├── metadata.py      # EXIF / GPS / device / date extraction
    ├── steganography.py # hidden-data detection (LSB + appended data)
    └── utils.py         # helpers: GPS conversion, saving output
```

---

## Testing

All example images should produce the expected output:

```sh
cd src
python3 main.py -m -o report1.txt ../images/image-example1.jpeg   # GPS coords
python3 main.py -m -o report3.txt ../images/image-example3.jpeg   # NIKON D3200 + date
python3 main.py -s -o key2.txt    ../images/image-example2.jpeg   # PGP key
python3 main.py -s -o key4.txt    ../images/image-example4.jpeg   # PGP key
```

Each PGP output must contain one complete block:

```
-----BEGIN PGP PUBLIC KEY BLOCK-----
...
-----END PGP PUBLIC KEY BLOCK-----
```

---

## Ethical and Legal Considerations

- **Get Permission:** always obtain explicit permission before analyzing any
  image. Analyzing someone else's image without consent may be illegal.
- **Respect Privacy:** metadata and hidden data are sensitive. Handle whatever
  you find responsibly and do not share it publicly.
- **Follow Laws:** respect data privacy and digital-forensics regulations in
  your jurisdiction (e.g., GDPR, national cybercrime laws).
- This tool is meant to be used for **education**, **CTF challenges**, and
  **legitimate digital forensics** with authorization.

---

## Acknowledgments

- [Wikipedia – Steganography](https://en.wikipedia.org/wiki/Steganography)
- [Wikipedia – Exif](https://en.wikipedia.org/wiki/Exif)
- [Pillow documentation](https://pillow.readthedocs.io/en/stable/)

---

## Role-play / audit preparation

If you are presenting this project, be ready to explain:

- What EXIF metadata is and which tags you read (GPS, Make/Model, date).
- What LSB steganography is and why it is invisible to the human eye.
- Why the secret is capped at ~1/8 of the image size with LSB.
- The difference between hiding (steganography) and scrambling (cryptography).
- What an ASCII-armored PGP key looks like and why it is detectable.

See `CONCEPTS.md` for a full study guide.