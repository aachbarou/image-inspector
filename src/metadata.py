"""
metadata.py

Extracts metadata (EXIF) from an image using PIL/Pillow.

EXIF = Exchangeable Image File Format.  It is a standard that stores extra
information *inside* the image file itself, written by the camera or phone
that took the photo.  Common EXIF fields:

  - GPS coordinates (where the photo was taken)
  - Make / Model (which device took the photo)
  - DateTimeOriginal (when the photo was taken)

EXIF data is stored as a TIFF directory of (tag_id -> value) pairs.
PIL parses this for us:  Image._getexif()  returns a dict where the keys
are numeric tag IDs and the values are raw.  We translate the numeric IDs
into human-readable names with PIL.ExifTags.TAGS.

GPS is special: it lives inside a separate nested directory under the
"GPSInfo" tag, and the coordinates are stored as  (Degrees, Minutes,
Seconds)  rationals plus a North/South/East/West letter.  We convert that
DMS format into a simple decimal number (the "Latitude / Longitude" that
maps and GPS devices display).
"""

from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS

from utils import dms_to_decimal


# Fall-back tags: these PIL versions / cameras may use a different tag name.
GPS_INFO_TAG = "GPSInfo"
DATE_TAGS = ("DateTimeOriginal", "DateTimeDigitized", "DateTime")


def get_exif_dict(image):
    """
    Return the EXIF dictionary keyed by *human-readable* tag names.
    If the image has no EXIF data, an empty dict is returned.

    Note: _getexif() sometimes raises on corrupt files, so we wrap it in a
    try/except and treat a failure as "no EXIF data".
    """
    exif = {}
    try:
        raw = image._getexif()
    except Exception:
        raw = None

    if not raw:
        return exif

    for tag_id, value in raw.items():
        name = TAGS.get(tag_id, tag_id)
        exif[name] = value

    return exif


def get_gps_coordinates(exif):
    """
    Extract and convert the GPS data (if any) from the EXIF dict.

    GPSInfo value looks like:  {1: 'N', 2: (32.0, 5.0, 11.86...), 3: 'E', ...}
    where (1,2,3) = (LatRef, Lat, LonRef), (4,5,6) = (Lon, AltRef, Alt).

      - tag 1 -> the latitude reference letter ('N' or 'S')
      - tag 2 -> the latitude  as (degrees, minutes, seconds)
      - tag 3 -> the longitude reference letter ('E' or 'W')
      - tag 4 -> the longitude as (degrees, minutes, seconds)

    Because dms_to_decimal returns signed values (negative for S / W), we
    give them the correct sign for the reference direction.

    Returns (lat, lon) as floats, or (None, None) when there is no GPS data.
    """
    if GPS_INFO_TAG not in exif:
        return None, None

    gps = exif[GPS_INFO_TAG]

    lat_ref = gps.get(1, "N")
    lon_ref = gps.get(3, "E")
    lat_dms = gps.get(2)
    lon_dms = gps.get(4)

    if lat_dms is None or lon_dms is None:
        return None, None

    lat = dms_to_decimal(lat_dms, lat_ref)
    lon = dms_to_decimal(lon_dms, lon_ref)

    return lat, lon


def get_device(exif):
    """
    Return the camera/device brand and model, e.g. "NIKON CORPORATION /
    NIKON D3200".  Returns "Unknown" when the image has no device tags.
    """
    make = exif.get("Make")
    model = exif.get("Model")

    pieces = [p for p in (make, model) if p]
    if not pieces:
        return "Unknown"

    return " / ".join(pieces)


def get_datetime(exif):
    """
    Return the capture date/time in a readable format.

    EXIF stores it as the string 'YYYY:MM:DD HH:MM:SS' (colons, not dashes,
    because JPEG has no way to escape colons).  We swap them for dashes so
    the output looks like a normal date:
        '2014:08:28 04:17:38'  ->  '2014-08-28 04:17:38'

    Returns "Unknown" when no date is present in the EXIF data.
    """
    for tag in DATE_TAGS:
        value = exif.get(tag)
        if value:
            return str(value).replace(":", "-", 2)
    return "Unknown"


def run_metadata_analysis(image_path):
    """
    Main entry point for the metadata analysis.

    Returns a single human-readable string that summarizes everything we
    found.  The CLI prints this string, or saves it to a file.
    """
    image = Image.open(image_path)
    exif = get_exif_dict(image)

    # Build a friendly report.  Each line is one piece of metadata.
    lines = ["Metadata report for: %s" % image_path]
    lines.append("----------------------------------------")

    if not exif:
        lines.append("No EXIF metadata found in this image.")
        return "\n".join(lines)

    lines.append("File format : %s (%sx%s)" % (
        image.format,
        image.width,
        image.height,
    ))

    # 1) Geolocation
    lat, lon = get_gps_coordinates(exif)
    if lat is not None and lon is not None:
        lines.append("Lat/Lon     : (%.4f) / (%.4f)" % (lat, lon))
    else:
        lines.append("Lat/Lon     : not available")

    # 2) Device that took the photo
    lines.append("Device      : %s" % get_device(exif))

    # 3) Date and time the photo was taken
    lines.append("Date        : %s" % get_datetime(exif))

    # 4) Anything else worth showing (keeps it useful, not required).
    for tag in ("Software", "ExifImageWidth", "ExifImageHeight",
                "Orientation", "ExposureTime", "FNumber", "ISOSpeedRatings"):
        if tag in exif:
            lines.append("%-11s : %s" % (tag, exif[tag]))

    return "\n".join(lines)