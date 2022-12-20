# Map Table

Map Table anchors any map image to known geographic locations and generates map tiles to be viewed on top of [OpenStreetMap](https://openstreetmap.org) data using [Leaflet](https://leafletjs.com
). The web viewer provides controls to view multiple map layers and to control their opacity to see each map's differenes and similiarities.

# Getting Started

Map Tile requires a Python3 virtual environment:

## Create and Configure Virtual Environment
```bash
python3 -m venv env
source env/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

# Generating Map Tiles

The `config.json` file is used to configure `maptiles.py` to generate map tiles. 

## Pick Map Anchors
First, you must pick three known locations to use as anchors for map alignment. Pick anchors that can be shared by all of the maps you intend to use. For each anchor, determine it's latitude and longitude and enter it into `config.json` here:

```json
    "anchors": {
        "a": [37.806645, -122.287200],
        "b": [37.804334, -122.271155],
        "c": [37.795135, -122.269526]
    },
```

The simplest way to determine the latitude and longitude is to locate your anchors on Google Maps by dropping a pin at each location, then copyicopyng the latitude and longitude shown in the popover. Values are provided in the format `[latitude, longitude]`.

### Notes
Technically Map Table only uses anchors `"a"` and `"b"`, however anchor `"c"` is used for testing and debugging to validate computed results.

## Adding Maps
Each map is added to the `"maps"` list in `config.json`. For each map, add an object with the following keys:

```json
    {
        "file": "data/1868-oakland.jpg",
        "name": "Oakland 1868",
        "source": "Stanford Digital Respository",
        "attribution": "https://purl.stanford.edu/by678mk5298",
        "license": "Creative Commons Public Domain",
        "anchors": {
            "a": [3350,2915],
            "b": [4326,2810],
            "c": [4626,3474]
        }
    },
```

All key/value pairs are required.

### Map Image File
Place your map file in the location you indicate in the object. You will get better results with higher resolution source images, so generally you should obtain the largest image you can.

### Pick Map Image Anchors
Next, pick the pixel coordinates in the map image that corrispond to the defined map anchors and enter them into `"anchors"`. An easy way to do this is to load the map into a tool like Photoshop and observe the pixel coordinates for each anchor. Accuracy is key for good results. Anchors are provided in `[x,y]` where `(0,0)` is the upper-left corner of the image.


## Run maptiles
Once your `config.json` is ready, run `maptiles.py` to generate your map tile sets.

```bash
source env/bin/activate
./maptiles.py
```

For each tile zoom level, an aligned, scaled version of the map image will be generated and written along side to the source map image with the filename `originalFileName-<zoom_level>.png`. From this file, tiles will be generated and stored in the `site/assets/tiles/` directory. If the single zoom level image already exists, it will be skipped and map tiles will not be processed. If you want to regenerate tiles for a map, delete the zoom level files for the map.

# Local Map Table Testing


## Run Local HTTP Server
You can use Python's base HTTP server to locally host Map Table for testing:

```bash
source env/bin/activate
cd site
python3 -m http.server 8000
```

# Public Hosting

Map Table can be fully hosted as a set of static files. Deploy the contents of the `site/` directory to your web server for hosting. 

## Hosting with AWS

A simple deploy script lives in `tools/deploy.sh` that syncs the site to an S3 bucket and invalidates the Cloudfront distribution.

# Development Notes

Additional development notes.

## Reference Anchors

|Anchor | Location                | Latitude  | Longitude   |
|-------|-------------------------|-----------|-------------|
| a     | Adeline and 10th street | 37.806645 | -122.287200 |
| b     | San Pablo and Broadway  | 37.804334 | -122.271155 |
| c     | Jackson and 4th street  | 37.795135 | -122.269526 |


## Links

https://www.maptiler.com/google-maps-coordinates-tile-bounds-projection/#14/-122.29/37.81

https://gist.github.com/maptiler

https://en.wikipedia.org/wiki/Mercator_projection

https://en.wikipedia.org/wiki/Web_Mercator_projection#References

https://wiki.openstreetmap.org/wiki/Zoom_levels

https://wiki.openstreetmap.org/wiki/Slippy_map_tilenames#Resolution_and_Scale

https://github.com/mapbox/mercantile

https://github.com/chrisveness/geodesy

https://www.movable-type.co.uk/scripts/latlong.html

https://virtual-graph-paper.com

