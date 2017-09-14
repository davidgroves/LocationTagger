Purpose
=======

- To take a directory of images, in almost any format imagemagick supports. Tested image formats include jpeg, tiff, png, DNG raws, Canon CR2 raws, Nikon NEF raws and Fuji RAF raws.
- To add exif geotag information based on your Google location data.
- To add a description and tags based on the Microsoft Vision services analysis of your image.

Requirements
============

To run this, you need.

1. exiftool installed on your machine (https://www.sno.phy.queensu.ca/~phil/exiftool/)
2. imagemagick installed on your machine. If this is hard (like on Windows), follow the instructions http://docs.wand-py.org/en/0.4.4/

Then install the Python dependencies, ideally into a virtual environment.
This project requires Python3 (tested with 3.5 and 3.6).

    $ pip install -r requirements.txt

3. You also need a config.ini file (see provided example-config.ini) with
a Microsoft Azure key from https://azure.microsoft.com/en-gb/try/cognitive-services/

The free tier allows you 5000 images to be identified per month.
Further pricing can be found at https://azure.microsoft.com/en-gb/pricing/details/cognitive-services/computer-vision/

Before Running
==============

1. To tag locations, you need the locations json document from Google.
You also obviously need to have Google tracking your location, and to
be using a device that allows Google to do so. Obtain this from
https://takeout.google.com/settings/takeout. Make sure you download the
json version, not the kml version.

Usage
=====

To print usage instructions :-

    $ ./tagger.py --help

A typical example usage will be :-

    $ ./tagger.py --config config.ini --location location.json --path example_images/

Note: This edits the exif/xmp data on the files directly. Make sure you
have a backup copy of the files.

BUGS / FEATURES TO COME
=======================

- Feature to use timezone information obtained to correct
Exif CreateTime and filesystem create timestamp to match local time. This will allow you to leave a camera in your "home" timezone, and still obtain files with the correct local time when traveling.

- Don't use the "last" location when doing geo, it can be a little inaccurate. Instead, if you are in location A at time 00:00:01, and location B at 00:00:05 and have an image taken at 00:00:03, it should tag it with the location at the midpoint between A and B.

- Use a Google API to obtain location information rather than you needing to get the takeout file.
