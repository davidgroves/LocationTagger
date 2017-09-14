#!/usr/bin/env python3

import arrow
import os
import json
import collections
import exiftool
from tzwhere import tzwhere
from os import fsencode
from wand.image import Image
import tqdm
import requests
import configparser
import argparse


def get_closest_location(timestamp, locations):
    for k, v in locations.items():
        if k < timestamp:
            return v
    return (0, 0, 0)


def dd2dms(deg):
    d = int(deg)
    md = abs(deg - d) * 60
    m = int(md)
    sd = (md - m) * 60
    return [d, m, sd]


def mscv(jpeg, microsoft_key, microsoft_uri):
    headers = {
        # Request headers.
        'Content-Type': 'application/octet-stream',
        'Ocp-Apim-Subscription-Key': microsoft_key
    }

    params = {
        # Request parameters. All of them are optional.
        'visualFeatures': 'Categories,Description,Color',
        'language': 'en',
    }

    response = requests.post(url=microsoft_uri, params=params, headers=headers, data=jpeg)
    print(response.text)

    # Check for success.
    if response.status_code == 200:
        # Display the response headers.
        print('Success.')
        print('Response headers:')

        print(response.json())
        description = ""
        for caption in response.json()["description"]["captions"]:
            description += caption["text"] + ". "
        return description

        # FIXME: This really needs some error handling here as they are totally unhandled right now !


###################################################################################################################

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', default="config.ini", help='An ini formatted config file')
    parser.add_argument('--path', help='The pathspec to the images to work on. (Example: example_images/')
    parser.add_argument('--locations', help='The locations JSON file from Google')

    args = parser.parse_args()

    config = configparser.ConfigParser()
    config.read(args.config)

    # Load the location file and parse it into a dictionary with key=timestampinMS, and the rest of the exif tag as value.
    locations = collections.OrderedDict()

    with open(args.locations) as data_file:
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
    os.chdir(args.path)

    # Go through each file.
    files = [f for f in os.listdir('.') if os.path.isfile(f)]
    for filename in tqdm.tqdm(files):

        with exiftool.ExifTool() as et:
            resp = et.execute_json('-datetimeoriginal', filename)[0]

        # Get the timestamp from the file
        ts = arrow.get(resp['EXIF:DateTimeOriginal'], 'YYYY:MM:DD HH:mm:ss').timestamp * 1000

        # Get the GPS location (in decimal)
        lat, long, alt = get_closest_location(ts, locations)

        # West or East.
        if lat < 0:
            latref = "W"
        else:
            latref = "E"

        # North or South.
        if long < 0:
            longref = "S"
        else:
            longref = "N"

        # Above or Below Sea level.
        if alt < 0:
            altref = 1
        else:
            altref = 0

        latm, lats, latds = dd2dms(lat)
        longm, longs, longds = dd2dms(long)

        tz = tzwhere.tzwhere()

        with Image(filename=filename) as img:
            print("Transforming")
            img.transform(resize="1000000@")
            print("Converting to JPEG")
            img.format = 'jpeg'

            caption = mscv(img.make_blob(format='jpeg'), config['microsoft']['key'], config['microsoft']['uri'])
            print("Caption: " + caption)

        with exiftool.ExifTool() as et:
            params = map(fsencode, ['-GPSLongitude=%s' % str(long),
                                    '-GPSLongitudeRef=%s' % str(longref),
                                    '-GPSLatitude=%s' % str(lat),
                                    '-GPSLatitudeRef=%s' % str(latref),
                                    '-GPSAltitude=%s' % str(alt),
                                    '-GPSAltitudeRef=%s' % str(altref),
                                    '-ImageDescription=%s' % str(caption),
                                    '-overwrite_original',
                                    '%s' % filename])
            et.execute(*params)
