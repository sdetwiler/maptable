#!/usr/bin/env python3


# https://wiki.openstreetmap.org/wiki/Slippy_map_tilenames#Resolution_and_Scale


import math
import os


from PIL import Image, ImageDraw

# Disable max pixel size
Image.MAX_IMAGE_PIXELS = None


DEG_TO_RAD = math.pi/180

CIRCUMFERENCE_METERS = 40075.016686 * 1000
TILE_WIDTH_PIXELS = 256


# FIXME: This is all sorts of broken. How did I even come up with this constant????
# METERS_PER_DEGREE = 87843.36
# METERS_PER_DEGREE_LAT = 111111.0
# DEGREES_LAT_PER_METER = 1.0/METERS_PER_DEGREE_LAT

# Reference Anchors
# a  Adeline and 10th street     @37.806645, -122.287200
# b  San Pablo and Broadway      @37.804334, -122.271155
# c  Jackson and 4th street      @37.795135, -122.269526

data = { 
    'anchors': {
        'a': [37.806645, -122.287200],
        'b': [37.804334, -122.271155],
        'c': [37.795135, -122.269526]
    },

    'maps': [
        {
            'file':'data/1868-oakland.jpg',
            'anchors': {
                'a': [3350,2915],
                'b': [4326,2810],
                'c': [4626,3474]
            }
        },
        {
            'file':'data/1876-oakland.jpg',
            'anchors': {
                'a': [1906,1946],
                'b': [2324,1821],
                'c': [2501,2086]
            }
        },
        {
            'file':'data/1898-oakland.jpg',
            'anchors': {
                'a': [550,1260],
                'b': [837,1310],
                'c': [870,1512]
            }
        },
        {
            'file':'data/1899-oakland.jpg',
            'anchors': {
                'a': [3143,4764],
                'b': [3743,4576],
                'c': [4004,4951]
            }
        },
        {
            'file':'data/2022-oakland-debug.png',
            'anchors': {
                'a': [517,850],
                'b': [1265,987],
                'c': [1340,1532]
            }
        }

        # ,
        # {
        #     'file':'data/1912-oakland-terminal-railways.jpg',
        #     'anchors': {
        #         'a': [711,786],
        #         'b': [743,812],
        #         'c': [714,839]
        #     }
        # }


    ]
}

def vec2_add(a, b):
    return (a[0]+b[0], a[1]+b[1])


def vec2_sub(a, b):
    return (a[0]-b[0], a[1]-b[1])


def vec2_scale(a, s):
    return(a[0]*s, a[1]*s)



def meters_lat_per_pixel(zoom_level):
    zoom_tile_width_meters = CIRCUMFERENCE_METERS / math.pow(2, zoom_level)
    return zoom_tile_width_meters / TILE_WIDTH_PIXELS


def meters_long_per_pixel(at_lat, zoom_level):
    zoom_tile_width_meters = (CIRCUMFERENCE_METERS * math.cos(at_lat)) / math.pow(2, zoom_level)
    return zoom_tile_width_meters / TILE_WIDTH_PIXELS


def degrees_per_pixel(zoom_level):
    zoom_tile_width_degrees = 360.0 / math.pow(2, zoom_level)
    return zoom_tile_width_degrees / TILE_WIDTH_PIXELS


def meters_lat_per_deg(zoom_level):
    return meters_lat_per_pixel(zoom_level) / degrees_per_pixel(zoom_level)


def meters_long_per_deg(at_lat, zoom_level):
    return meters_long_per_pixel(at_lat, zoom_level) / degrees_per_pixel(zoom_level)

def degrees_per_meter():
    return 360.0 / CIRCUMFERENCE_METERS



# def meters_per_pixel(latitude, zoom_level):
#     '''Returns the number of meters covered by each pixel at a given latitude and zoom level.
#         latitude: latitude in degrees.
#         zoom_level: zoom level index 1-17
#     '''

#     # https://wiki.openstreetmap.org/wiki/Slippy_map_tilenames#Resolution_and_Scale
#     latitude_rad = latitude * DEG_TO_RAD
#     return 156543.03 * math.cos(latitude_rad) / math.pow(2, zoom_level)


# def degrees_lat_per_pixel(zoom_level):
#     return METERS_PER_DEGREE_LAT / math.pow(2, zoom_level)

# def degrees_long_per_pixel(at_latitude, zoom_level):
#     at_latitude_rad = at_latitude * DEG_TO_RAD
#     return METERS_PER_DEGREE_LAT * math.cos(at_latitude_rad) / math.pow(2, zoom_level)

    



# def degrees_per_pixel(latitude, zoom_level):
#     # FIXME: This is all sorts of broken. How did I even come up with this constant????
#     zoom_meters_per_pixel = meters_per_pixel(latitude, zoom_level)
#     return zoom_meters_per_pixel * DEGREES_PER_METER


def compute_map_scale(map, zoom_level, anchors):
    # How many meters between anchors a and b    
    anchor_y_meters = math.fabs(anchors['a'][0] - anchors['b'][0]) * meters_lat_per_deg(zoom_level) # Remember its (lat,long)
    # print('meters:       {}'.format(anchor_y_meters))

    # How many pixels between anchors a and b on the map
    map_y_pixels = math.fabs(map['anchors']['a'][1] - map['anchors']['b'][1])   # Remember latitude is the y axis in pixels.
    # print('pixels:       {}'.format(map_y_pixels))

    # How many meters per pixel on the map
    map_meters_per_pixel = anchor_y_meters / map_y_pixels
    # print('m/px:         {}'.format(map_meters_per_pixel))

    print('zoom:         {}'.format(zoom_level))
    zoom_meters_per_pixel = meters_long_per_pixel(anchors['a'][0], zoom_level)   # TODO: Should scale be derived from latitude or longitude?
    # print('zoom m/px:    {}'.format(zoom_meters_per_pixel))
    map_scale = map_meters_per_pixel/zoom_meters_per_pixel

    print('scale:        {}'.format(map_scale))
    return map_scale


def compute_anchor_rotation(anchors):
    # find angle between a and b
    y = anchors['b'][0] - anchors['a'][0]   # latitude is y axis
    x = anchors['b'][1] - anchors['a'][1]   # longitude is x axis
    anchor_rotation = math.atan(y/x)*(180/math.pi)
    # print('anchor_rotation:     {}'.format(anchor_rotation))
    return anchor_rotation


def compute_map_rotation(map, anchors):
    anchor_rotation = compute_anchor_rotation(anchors)

    # find angle between a and b
    x = map['anchors']['b'][0] - map['anchors']['a'][0]
    y = map['anchors']['b'][1] - map['anchors']['a'][1]
    theta = math.atan(y/x)*(180/math.pi)
    map_rotation = anchor_rotation + theta
    print('map_rotation:     {}'.format(map_rotation))
    return map_rotation


def latlong_for_pixel(pixel_xy, image_anchor, map_anchor, zoom_level):
    '''Returns the latitude and longitude for a given pixel in an image.

    pixel_xy:     The pixel to evaluate, in pixel space (x,y).
    image_anchor: Anchor coordinates in pixel space (x,y).
    map_anchor:   Anchor coordinates in latlong space (lat,long).
    zoom_level:   The zoom level for the image.

    Returns: Tuple with (lat,long)
    '''
    print('--latlong_for_pixel--')
    print('pixel_xy:     {}'.format(pixel_xy))
    print('image_anchor: {}'.format(image_anchor))

    # Distance in pixels from image anchor to pixel
    distance_pixels = vec2_sub(pixel_xy, image_anchor)
    print('distance_pixels: {}'.format(distance_pixels))

    # convert distance in pixels to meters
    distance_meters = (
        distance_pixels[0] * meters_long_per_pixel(map_anchor[0], zoom_level),
        distance_pixels[1] * meters_lat_per_pixel(zoom_level)
    )

    print('distance_meters: {}'.format(distance_meters))
    
    # convert distance in meters to degrees
    # FIXME?
    distance_degrees = (
        distance_meters[1] * degrees_per_meter(),
        distance_meters[0] * degrees_per_meter()
    )
    
    print('distance_degrees: {}'.format(distance_degrees))
    pixel_latlong = (
        map_anchor[0] - distance_degrees[0],
        map_anchor[1] + distance_degrees[1],
    )

    print('--/latlong_for_pixel--\n')
    
    return pixel_latlong


def rotate_around(point, origin, theta):
    '''Rotates point theta degrees around the specified origin.
    (0,0)
      +------------------> +x
      |
      |
      |
      |
      |
     \/
      +y

    Returns rotated point location

    '''
    
    # print('point:     {}'.format(point))
    # print('origin:    {}'.format(origin))
    # print('theta:     {}'.format(theta))

    # Coordinate space places (0,0) in upper left, so negate the rotation.
    theta*=-1

    theta_rad = theta * DEG_TO_RAD

    new_x = origin[0] + ((point[0] - origin[0]) * math.cos(theta_rad)) - ((point[1] - origin[1]) * math.sin(theta_rad))
    new_y = origin[1] + ((point[0] - origin[0]) * math.sin(theta_rad)) + ((point[1] - origin[1]) * math.cos(theta_rad))

    new_point = (new_x, new_y)
    # print('new_point: {}'.format(new_point))

    return new_point


def rotate_anchor(anchor, theta, map_width, map_height):
    '''Rotates an anchor point theta degrees around the center of a map of the given width and height.

    (0,0)
      +------------------> +x
      |
      |
      |
      |
      |
     \/
      +y

    Returns rotated anchor location
    '''
    
    origin = (map_width/2, map_height/2)
    point = (anchor[0], anchor[1])
    return rotate_around(point, origin, theta)


def draw_anchor(anchor, im, color='#ff0000', length=10):
    # Draw anchors for debugging.
    draw = ImageDraw.Draw(im)
    
    hs = (anchor[0]-length, anchor[1])
    he = (anchor[0]+length, anchor[1])
    vs = (anchor[0], anchor[1]-length)
    ve = (anchor[0], anchor[1]+length)

    draw.line([hs,he], fill=color, width=int(length/10.0)*6)    # HACK: scale the width from reference length
    draw.line([vs,ve], fill=color, width=int(length/10.0)*6)


def filepath_for_map(map):
    tokens = map['file'].split('.')
    filepath = '.'.join(tokens[0:-1])
    
    return filepath


def filename_for_zoom_level(map, zoom_level):
    tokens = map['file'].split('.')
    extension = tokens[-1]
    extension = 'png'
    filename = '.'.join(tokens[0:-1])
    filename_with_zoom_level = '{}-{}.{}'.format(filename, zoom_level, extension)
    
    return filename_with_zoom_level


# https://wiki.openstreetmap.org/wiki/Slippy_map_tilenames
def deg2num(lat_deg, lon_deg, zoom):
  lat_rad = math.radians(lat_deg)
  n = 2.0 ** zoom
  xtile = int((lon_deg + 180.0) / 360.0 * n)
  ytile = int((1.0 - math.asinh(math.tan(lat_rad)) / math.pi) / 2.0 * n)
  return (xtile, ytile)


def num2deg(xtile, ytile, zoom):
  n = 2.0 ** zoom
  lon_deg = xtile / n * 360.0 - 180.0
  lat_rad = math.atan(math.sinh(math.pi * (1 - 2 * ytile / n)))
  lat_deg = math.degrees(lat_rad)
  return (lat_deg, lon_deg)


def generate_map_tiles(map, zoom_level, map_ul_latlong, map_lr_latlong):
    print('\ngenerate_map_tiles\n-------')
    filename = filename_for_zoom_level(map, zoom_level)
    filepath = filepath_for_map(map)
    filepath = os.path.join(filepath, str(zoom_level))
    os.makedirs(filepath, exist_ok=True)

    print('{}'.format(filename))
    print('map_ul_latlong: {}'.format(map_ul_latlong))
    print('map_lr_latlong: {}'.format(map_lr_latlong))

    lr_tile_xy = deg2num(map_lr_latlong[0], map_lr_latlong[1], zoom_level)
    ul_tile_xy = deg2num(map_ul_latlong[0], map_ul_latlong[1], zoom_level)
    ul_tile_latlong = num2deg(ul_tile_xy[0], ul_tile_xy[1], zoom_level)
    
    delta_latlong = vec2_sub(map_ul_latlong, ul_tile_latlong)
    delta_pixels = (
        delta_latlong[1] * 1 / degrees_per_pixel(zoom_level),
        delta_latlong[0] * 1 / degrees_per_pixel(zoom_level)
    )

    # print('ul_tile_xy:      {}'.format(ul_tile_xy))
    # print('ul_tile_latlong: {}'.format(ul_tile_latlong))
    # print('delta_latlong:     {}'.format(delta_latlong))
    # print('delta_pixels:      {}'.format(delta_pixels))

    im = Image.open(filename)
    
    tile_width = 256

    pixel_y = delta_pixels[0]

    i=0
    for y in range(ul_tile_xy[1], lr_tile_xy[1]+1):
        pixel_x = -delta_pixels[1]
        for x in range(ul_tile_xy[0], lr_tile_xy[0]+1):
            filepath_with_x = os.path.join(filepath, str(x))
            os.makedirs(filepath_with_x, exist_ok=True)
            
            tile_filename = os.path.join(filepath_with_x, '{}.png'.format(y))            
            print(tile_filename)

            box = (int(pixel_x), int(pixel_y), int(pixel_x+tile_width), int(pixel_y+tile_width))
            print(box)

            im_tile = im.crop(box)
            im_tile.save(tile_filename)

            i+=1

            pixel_x+=tile_width
        print('-------------------')
        pixel_y+=tile_width

    print('tile files: {}'.format(i))



def fit_map(map, zoom_level, anchors):
    '''Rotates and scales the input map. Writes map to disk with the zoom_level included in the filename.
    '''
    
    print('\nfit_map\n-------')

    # Compute some filenames.
    output_filename = filename_for_zoom_level(map, zoom_level)
    print('{} -> {} '.format(map['file'], output_filename))

    map_rotation = compute_map_rotation(map, anchors)
    map_scale = compute_map_scale(map, zoom_level, anchors)

    im = Image.open(map['file']).convert('RGBA')

    # First, scale the image to work at the correct zoom level.
    im_scaled = im.resize((int(round(im.width*map_scale)), int(round(im.height*map_scale))))
    map_scaled_center_pixels = (im_scaled.width/2, im_scaled.height/2)
    map_scaled_center_latlong = latlong_for_pixel(map_scaled_center_pixels, vec2_scale(map['anchors']['a'], map_scale), anchors['a'], zoom_level)
    # print('map_scaled_center_latlong: {}'.format(map_scaled_center_latlong))

    # DEBUG: Draw anchors for debugging. Anchors must be scaled to zoom level.
    draw_anchor(map_scaled_center_pixels, im_scaled, color='#00aa00', length=10*map_scale)
    draw_anchor(vec2_scale(map['anchors']['a'], map_scale), im_scaled, length=10*map_scale)
    draw_anchor(vec2_scale(map['anchors']['b'], map_scale), im_scaled, length=10*map_scale)
    draw_anchor(vec2_scale(map['anchors']['c'], map_scale), im_scaled, length=10*map_scale)

    # Now rotate the image. Expand the image bounds so it fully fits in the rotated image.
    im_rotated = im_scaled.rotate(map_rotation, expand=True)
    im_rotated.save(output_filename)

    # The image has been scaled. Get the new pixel coordinates center which changes because the image was expanded.
    map_rotated_center_pixels = (im_rotated.width/2, im_rotated.height/2)

    # Compute latlong for each corner.
    image_anchor = vec2_scale(map['anchors']['a'], map_scale)
    map_anchor = anchors['a']
    ul_latlong = latlong_for_pixel((0, 0), image_anchor, map_anchor, zoom_level)
    ur_latlong = latlong_for_pixel((im_scaled.width, 0), image_anchor, map_anchor, zoom_level)
    lr_latlong = latlong_for_pixel((im_scaled.width, im_scaled.height), image_anchor, map_anchor, zoom_level)
    ll_latlong = latlong_for_pixel((0, im_scaled.height), image_anchor, map_anchor, zoom_level)

    # Rotate each latlong.
    rotated_ul_latlong = rotate_around(ul_latlong, map_scaled_center_latlong, map_rotation)
    rotated_ur_latlong = rotate_around(ur_latlong, map_scaled_center_latlong, map_rotation)
    rotated_lr_latlong = rotate_around(lr_latlong, map_scaled_center_latlong, map_rotation)
    rotated_ll_latlong = rotate_around(ll_latlong, map_scaled_center_latlong, map_rotation)

    # Find extents.
    # SCD: All sorts of things to rethink when considering southern hemisphere, etc...
    points = [rotated_ul_latlong, rotated_ur_latlong, rotated_lr_latlong, rotated_ll_latlong]
    # find min and max lat and long
    min_lat = 999
    max_lat = -999
    min_long = 999
    max_long = -999

    for point in points:
        if point[0] < min_lat:
            min_lat = point[0]
        if point[0] > max_lat:
            max_lat = point[0]
        if point[1] < min_long:
            min_long = point[1]
        if point[1] > max_long:
            max_long = point[1]
    
    map_rotated_ul_latlong = (max_lat, min_long)
    map_rotated_lr_latlong = (min_lat, max_long)

    print('map_scaled_center_latlong: {}'.format(map_scaled_center_latlong))
    print('map_rotated_ul_latlong: {}'.format(map_rotated_ul_latlong))
    print('map_rotated_lr_latlong: {}'.format(map_rotated_lr_latlong))
    
    return (map_rotated_ul_latlong, map_rotated_lr_latlong)



def test__foo():

    # 40075.016686 * 1000 / 256 ≈ 6378137.0 * 2 * pi / 256 ≈ 156543.03


    # circumference_meters = 40075.016686 * 1000
    # tile_width_pixels = 256

    # At zoom level 0, one tile covers the entire earth (360 degrees), or circumference_meters wide
    # At zoom level 1, two tiles cover the entire width (180 degrees each), or circumference_meters/2 wide
    # At zoom level 2, four tiles cover the entire width (90 degrees each), or circumference_meters/4 wide...
    # At zoom level 3, eight tiles cover the entire width (360/8 degrees each), or circumference_meters/8 wide...

    # zoom_tile_width_meters = circumference_meters / 2^zoom_level
    # zoom_tile_width_degrees = 360 / 2^zoom_level

    # zoom_tile_meters_per_pixel = zoom_tile_width_meters / tile_width_pixels
    # zoom_tile_degrees_per_pixel = zoom_tile_width_degrees / tile_width_pixels


    def meters_lat_per_pixel(zoom_level):
        zoom_tile_width_meters = CIRCUMFERENCE_METERS / math.pow(2, zoom_level)
        return zoom_tile_width_meters / TILE_WIDTH_PIXELS


    def meters_long_per_pixel(at_lat, zoom_level):
        zoom_tile_width_meters = (CIRCUMFERENCE_METERS * math.cos(at_lat)) / math.pow(2, zoom_level)
        return zoom_tile_width_meters / TILE_WIDTH_PIXELS


    def degrees_per_pixel(zoom_level):
        zoom_tile_width_degrees = 360.0 / math.pow(2, zoom_level)
        return zoom_tile_width_degrees / TILE_WIDTH_PIXELS


    def meters_lat_per_deg(zoom_level):
        return meters_lat_per_pixel(zoom_level) / degrees_per_pixel(zoom_level)


    def meters_long_per_deg(at_lat, zoom_level):
        return meters_long_per_pixel(at_lat, zoom_level) / degrees_per_pixel(zoom_level)


def test__latlong_for_pixel():
    map = {
            'file':'data/2022-oakland-debug.png',
            'anchors': {
                'a': [517,850],
                'b': [1265,987],
                'c': [1340,1532]
            }
    }

    anchors = {
        'a': [37.806645, -122.287200],
        'b': [37.804334, -122.271155],
        'c': [37.795135, -122.269526]
    }

    for zoom_level in range(13,17):
        print('====')

        map_scale = compute_map_scale(map, zoom_level, anchors)
        print('map_scale:     {}'.format(map_scale))

        pixel_latlong = latlong_for_pixel(
            vec2_scale(map['anchors']['c'], map_scale), 
            vec2_scale(map['anchors']['a'], map_scale),
            anchors['a'],
            zoom_level
        )

        print('pixel_latlong: {}'.format(pixel_latlong))
        print('anchor_c:      {}'.format(anchors['c']))

        delta_latlong = vec2_sub(pixel_latlong, anchors['c'])
        print('delta_latlong: {}'.format(delta_latlong))
        print('====\n\n')


def main():

    # test__latlong_for_pixel()
    # return

    #### For testing
    map = data['maps'][4]
    zoom_level = 13
    (map_ul_latlong, map_lr_latlong) = fit_map(map, zoom_level, data['anchors'])
    generate_map_tiles(map, zoom_level, map_ul_latlong, map_lr_latlong)


    # for map in data['maps']:
    # for zoom_level in range(13, 17):
    #     (map_ul_latlong, map_lr_latlong) = fit_map(map, zoom_level, data['anchors'])
    #     generate_map_tiles(map, zoom_level, map_ul_latlong, map_lr_latlong)

if __name__ == '__main__':
    main()