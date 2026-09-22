"""
metadata.py

Extracts metadata (EXIF) from an image using PIL/Pillow.
"""

from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS

from utils import dms_to_decimal


# Fall-back tags used when a camera writes different tag names.
GPS_INFO_TAG = "GPSInfo"
DATE_TAGS = ("DateTimeOriginal", "DateTimeDigitized", "DateTime")


def get_exif_dict(image):
    """Return the image EXIF data keyed by human-readable tag names."""
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
    """Extract the GPS coordinates from the EXIF data, if present."""
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
    """Return the camera brand and model from the EXIF data."""
    make = exif.get("Make")
    model = exif.get("Model")

    pieces = [p for p in (make, model) if p]
    if not pieces:
        return "Unknown"

    return " / ".join(pieces)


def get_datetime(exif):
    """Return the capture date and time from the EXIF data."""
    for tag in DATE_TAGS:
        value = exif.get(tag)
        if value:
            return str(value).replace(":", "-", 2)
    return "Unknown"


def run_metadata_analysis(image_path):
    """Perform the full metadata analysis on an image and return the report."""
    image = Image.open(image_path)
    exif = get_exif_dict(image)

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

    # 4) Additional useful EXIF fields
    for tag in ("Software", "ExifImageWidth", "ExifImageHeight",
                "Orientation", "ExposureTime", "FNumber", "ISOSpeedRatings"):
        if tag in exif:
            lines.append("%-11s : %s" % (tag, exif[tag]))

    return "\n".join(lines)