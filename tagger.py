#!/usr/bin/env python3

import arrow
import logging
from PIL import Image
import piexif
import os
import json
import collections
import exiftool
from tzwhere import tzwhere
from os import fsencode

logging.basicConfig(level=logging.INFO)

def get_closest_location(timestamp, locations):
    for k,v in locations.items():
        if k < timestamp:
            return v
    return (0,0,0)

def dd2dms(deg):
    d = int(deg)
    md = abs(deg - d) * 60
    m = int(md)
    sd = (md - m) * 60
    return [d, m, sd]

# Load the location file and parse it into a dictionary with key=timestampinMS, and the rest of the exif tag as value.
locations = collections.OrderedDict()

with open('dave.json') as data_file:
    data = json.load(data_file)
    for l in data['locations']:
        try:
            altitude = l['altitude']
        except KeyError:
            altitude = 0

        locations[int(l['timestampMs'])] = (float(float(l['latitudeE7']) / 10000000),
                                            float(float(l['longitudeE7'] / 10000000)),
                                            altitude)

# FIXME: Don't hardcore directory.
os.chdir("example_images")

# Go through each file.
files = [f for f in os.listdir('.') if os.path.isfile(f)]
for filename in files:

    with exiftool.ExifTool() as et:
        resp = et.execute_json('-datetimeoriginal', filename)[0]
        print(resp)
        print(type(resp))


    # Get the timestamp from the file
    ts = arrow.get(resp['EXIF:DateTimeOriginal'], 'YYYY:MM:DD HH:mm:ss').timestamp * 1000
    print(ts)

    # Get the GPS location
    lat, long, alt = get_closest_location(ts, locations)
    print(lat, long, alt)

    if lat < 0:
        latref = "W"
    else:
        latref = "E"


    if long < 0:
        longref = "S"
    else:
        longref = "N"

    if alt < 0:
        altref = 1
    else:
        altref = 0

    latm, lats, latds = dd2dms(lat)
    longm, longs, longds = dd2dms(long)

    print(latm, lats, latds)

    # # Add GPS data
    # gps_ifd = {piexif.GPSIFD.GPSVersionID: (2, 0, 0, 0),
    #            piexif.GPSIFD.GPSAltitudeRef: altref,
    #            piexif.GPSIFD.GPSAltitude: (abs(alt), 1),
    #            piexif.GPSIFD.GPSLatitudeRef: latref,
    #            piexif.GPSIFD.GPSLatitude: [(latm, 1), (lats, 1), (int(latds * 10000000) , 10000000)],
    #            piexif.GPSIFD.GPSLongitudeRef: longref,
    #            piexif.GPSIFD.GPSLongitude: [(longm, 1), (longs, 1), (int(longds * 10000000), 10000000)]
    #            }

    tz = tzwhere.tzwhere()

    print(tz.tzNameAt(lat, long))
    #print(gps_ifd)

    # exif_dict["GPS"] = gps_ifd
    #
    # exif_bytes = piexif.dump(exif_dict)
    # im.save("example_output/" + filename, exif=exif_bytes)

    with exiftool.ExifTool() as et:
        print('-GPSLongitude="%s"' % str(long))
        params = map(fsencode, ['-GPSLongitude=%s' % str(long),
                                '-GPSLongitudeRef=%s' % str(longref),
                                '-GPSLatitude=%s' % str(lat),
                                '-GPSLatitudeRef=%s' % str(latref),
                                '-GPSAltitude=%s' % str(alt),
                                '-GPSAltitudeRef=%s' % str(altref),
                                '-overwrite_original',
                                '%s' % filename])
        print(params)
        et.execute(*params)
        # params = map(fsencode, ['-GPSLatitude="%s"' % str(lat), '%s' % filename])
        # et.execute(*params)
        # params = map(fsencode, ['-GPSAltitude="%s"' % str(alt), '%s' % filename])
        # et.execute(*params)

        # with exiftool.ExifTool() as et:
    #     params = map(fsencode, ['-GPSLongitude="%s"' % long, '%s' % outfile])
