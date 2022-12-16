#!/usr/bin/env python3

import math
import os
import json

from PIL import Image, ImageDraw

# Disable max pixel size
Image.MAX_IMAGE_PIXELS = None

# Values from mapbox
RADIUS_METERS = 6378137.0
CIRCUMFERENCE_METERS = 2 * math.pi * RADIUS_METERS
EPSILON = 1e-14
TILE_WIDTH_PIXELS = 256


TILE_PATH = 'site/assets/tiles'

# Reference Anchors
# a  Adeline and 10th street     @37.806645, -122.287200
# b  San Pablo and Broadway      @37.804334, -122.271155
# c  Jackson and 4th street      @37.795135, -122.269526


data = None

def vec2_add(a, b):
    return (a[0]+b[0], a[1]+b[1])


def vec2_sub(a, b):
    return (a[0]-b[0], a[1]-b[1])


def vec2_scale(a, s):
    if type(s) is tuple:
        return(a[0]*s[0], a[1]*s[1])
    else:
        return(a[0]*s, a[1]*s)


def pixels_per_degree_lat(at_lat, zoom_level):
    S = (TILE_WIDTH_PIXELS / (2 * math.pi)) * math.pow(2, zoom_level)
    a = at_lat - 0.5
    b = at_lat + 0.5

    v1 = S * (math.pi - math.log(math.tan(math.pi/4 + math.radians(a)/2)))
    v2 = S * (math.pi - math.log(math.tan(math.pi/4 + math.radians(b)/2)))
    return math.fabs(v1-v2)


def pixels_per_degree_long(at_lat, zoom_level):
    S = (TILE_WIDTH_PIXELS / (2 * math.pi)) * math.pow(2,zoom_level)
    
    a = 0
    b = 1
    v1 = math.fabs(S * math.radians(a) + math.pi)
    v2 = math.fabs(S * math.radians(b) + math.pi)
    return math.fabs(v1-v2)


def meters_lat_per_pixel(at_lat, zoom_level):
    y = pixels_per_degree_lat(at_lat, zoom_level)
    return meters_per_degree_lat(at_lat) / y


def meters_long_per_pixel(at_lat, zoom_level):
    x = pixels_per_degree_long(at_lat, zoom_level)
    return meters_per_degree_long(at_lat) / x


def degrees_lat_per_pixel(at_lat, zoom_level):
    return 1 / pixels_per_degree_lat(at_lat, zoom_level)


def degrees_long_per_pixel(at_lat, zoom_level):
    return 1 / pixels_per_degree_long(at_lat, zoom_level)


def meters_per_degree_lat(at_lat):
    i_latlong = (at_lat-0.5, 0)
    j_latlong = (at_lat+0.5, 0)
    return distance_between(i_latlong, j_latlong)


def meters_per_degree_long(at_lat):
    i_latlong = (at_lat, 0)
    j_latlong = (at_lat, 1)
    return distance_between(i_latlong, j_latlong)


def degrees_lat_per_meter():
    return 1.0 / meters_per_degree_lat()


def degrees_long_per_meter(at_lat):
    return 1.0 / meters_per_degree_long(at_lat)


def distance_between(i_latlong, j_latlong):
    # https://www.movable-type.co.uk/scripts/latlong.html
    i_latlong_rad = (math.radians(i_latlong[0]), math.radians(i_latlong[1]))
    j_latlong_rad = (math.radians(j_latlong[0]), math.radians(j_latlong[1]))

    delta_lat = j_latlong_rad[0] - i_latlong_rad[0]
    delta_long = j_latlong_rad[1] - i_latlong_rad[1]

    a = math.sin(delta_lat/2) * math.sin(delta_lat/2) + math.cos(i_latlong_rad[0]) * math.cos(j_latlong_rad[0]) * math.sin(delta_long/2) * math.sin(delta_long/2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    d = RADIUS_METERS * c
    return d


def compute_map_scale(map, zoom_level, anchors):
    print('\n--compute_map_scale--')
    print('anchors: {}'.format(anchors))

    distance_anchors_meters = distance_between(anchors['a'], anchors['b'])
    print('distance_anchors_meters: {}'.format(distance_anchors_meters))

    map_x_pixels = map['anchors']['a'][0] - map['anchors']['b'][0]
    map_y_pixels = map['anchors']['a'][1] - map['anchors']['b'][1]

    distance_anchors_pixels = math.sqrt((map_x_pixels * map_x_pixels) + (map_y_pixels * map_y_pixels))
    print('distance_anchors_pixels: {}'.format(distance_anchors_pixels))

    map_meters_per_pixel = distance_anchors_meters / distance_anchors_pixels
    print('map_meters_per_pixel:    {}'.format(map_meters_per_pixel))

    print('zoom_level:              {}'.format(zoom_level))
    zoom_x_meters_per_pixel = meters_long_per_pixel(anchors['a'][0], zoom_level)
    print('zoom_x m/px:             {}'.format(zoom_x_meters_per_pixel))
    zoom_y_meters_per_pixel = meters_lat_per_pixel(anchors['a'][0], zoom_level)
    print('zoom_y m/px:             {}'.format(zoom_y_meters_per_pixel))

    map_x_scale = map_meters_per_pixel/zoom_x_meters_per_pixel
    map_y_scale = map_meters_per_pixel/zoom_y_meters_per_pixel

    print('map_x_scale:             {}'.format(map_x_scale))
    print('map_y_scale:             {}'.format(map_y_scale))

    print('--/compute_map_scale--\n')
    return (map_x_scale, map_y_scale)


def compute_anchor_rotation(anchors):
    # find angle between a and b
    y = anchors['b'][0] - anchors['a'][0]   # latitude is y axis
    x = anchors['b'][1] - anchors['a'][1]   # longitude is x axis
    anchor_rotation = math.degrees(math.atan(y/x))
    return anchor_rotation


def compute_map_rotation(map, anchors):
    anchor_rotation = compute_anchor_rotation(anchors)

    # find angle between a and b
    x = map['anchors']['b'][0] - map['anchors']['a'][0]
    y = map['anchors']['b'][1] - map['anchors']['a'][1]
    theta = math.degrees(math.atan(y/x))
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

    print('\n--latlong_for_pixel--')
    print('pixel_xy:         {}'.format(pixel_xy))
    print('map_anchor:       {}'.format(map_anchor))
    print('image_anchor:     {}'.format(image_anchor))

    # Distance in pixels from image anchor to pixel
    distance_pixels = vec2_sub(pixel_xy, image_anchor)
    print('distance_pixels:  {}'.format(distance_pixels))

    # Convert distance in pixels to degrees
    distance_degrees = (        
        distance_pixels[1] * degrees_lat_per_pixel(map_anchor[0], zoom_level),
        distance_pixels[0] * degrees_long_per_pixel(map_anchor[0], zoom_level)
    )
    
    print('distance_degrees: {}'.format(distance_degrees))
    pixel_latlong = (
        map_anchor[0] - distance_degrees[0],
        (map_anchor[1] + distance_degrees[1])
    )

    print('--/latlong_for_pixel--\n')

    return pixel_latlong


def rotate_around(point, origin, theta):
    print('--rotate_around--')
    print('point:  {}'.format(point))
    print('origin: {}'.format(origin))
    print('theta:  {}'.format(theta))
    theta+=180
    
    s = origin[0] - point[0]
    t = origin[1] - point[1]
    print('s:     {}'.format(s))
    print('t:     {}'.format(t))

    theta_rad = math.radians(theta)
    u = s * math.cos(theta_rad) + t * math.sin(theta_rad)
    v = -s * math.sin(theta_rad) + t * math.cos(theta_rad)
    print('u:     {}'.format(u))
    print('v:     {}'.format(v))

    xp = u + origin[0]
    yp = v + origin[1]

    print('xp:    {}'.format(xp))
    print('yp:    {}'.format(yp))
    print('--/rotate_around--')

    return (xp, yp)


def draw_anchor(anchor, im, color='#ff0000', length=10):
    # Draw anchors for debugging.
    draw = ImageDraw.Draw(im)
    
    hs = (anchor[0]-length, anchor[1])
    he = (anchor[0]+length, anchor[1])
    vs = (anchor[0], anchor[1]-length)
    ve = (anchor[0], anchor[1]+length)

    draw.line([hs,he], fill=color, width=int(length/10.0)*6)    # HACK: scale the width from reference length
    draw.line([vs,ve], fill=color, width=int(length/10.0)*6)


def filepath_for_tiles(map):
    # Remove file extension.
    tokens = map['file'].split('.')
    filepath = '.'.join(tokens[0:-1])

    # Remove leading path.
    tokens = filepath.split('/')
    filepath = '.'.join(tokens[1:])

    # Prepend tile path.
    filepath = os.path.join(TILE_PATH, filepath)
    
    return filepath


def filename_for_zoom_level(map, zoom_level):
    tokens = map['file'].split('.')
    extension = tokens[-1]
    extension = 'png'
    filename = '.'.join(tokens[0:-1])
    filename_with_zoom_level = '{}-{}.{}'.format(filename, zoom_level, extension)
    
    return filename_with_zoom_level


def _xy(lat, long):

    # if truncate:
    #     lng, lat = truncate_lnglat(lng, lat)

    x = long / 360.0 + 0.5
    sinlat = math.sin(math.radians(lat))

    y = 0.5 - 0.25 * math.log((1.0 + sinlat) / (1.0 - sinlat)) / math.pi
    return x, y


def tile_for_latlong(lat, long, zoom):
    x, y = _xy(lat, long)
    Z2 = math.pow(2, zoom)

    if x <= 0:
        xtile = 0
    elif x >= 1:
        xtile = int(Z2 - 1)
    else:
        # To address loss of precision in round-tripping between tile
        # and lng/lat, points within EPSILON of the right side of a tile
        # are counted in the next tile over.
        xtile = int(math.floor((x + EPSILON) * Z2))

    if y <= 0:
        ytile = 0
    elif y >= 1:
        ytile = int(Z2 - 1)
    else:
        ytile = int(math.floor((y + EPSILON) * Z2))

    return (xtile, ytile)


def ul_latlong_for_tile(xtile, ytile, zoom):
  n = math.pow(2, zoom)
  lon_deg = xtile / n * 360.0 - 180.0
  lat_rad = math.atan(math.sinh(math.pi * (1 - 2 * ytile / n)))
  lat_deg = math.degrees(lat_rad)
  return (lat_deg, lon_deg)


def generate_map_tiles(map, zoom_level, map_ul_latlong, map_lr_latlong):
    print('\ngenerate_map_tiles\n-------')
    filename = filename_for_zoom_level(map, zoom_level)
    filepath = filepath_for_tiles(map)
    filepath = os.path.join(filepath, str(zoom_level))
    print('filepath:          {}'.format(filepath))
    os.makedirs(filepath, exist_ok=True)

    print('{}'.format(filename))
    print('map_ul_latlong:    {}'.format(map_ul_latlong))
    print('map_lr_latlong:    {}'.format(map_lr_latlong))

    lr_tile_xy = tile_for_latlong(map_lr_latlong[0], map_lr_latlong[1], zoom_level)

    ul_tile_xy = tile_for_latlong(map_ul_latlong[0], map_ul_latlong[1], zoom_level)
    ul_tile_latlong = ul_latlong_for_tile(ul_tile_xy[0], ul_tile_xy[1], zoom_level)
    delta_latlong = vec2_sub(map_ul_latlong, ul_tile_latlong)
    delta_pixels = (
        delta_latlong[1] * pixels_per_degree_lat(map_ul_latlong[0], zoom_level),
        delta_latlong[0] * pixels_per_degree_long(map_ul_latlong[0], zoom_level)
    )

    print('ul_tile_xy:        {}'.format(ul_tile_xy))
    print('ul_tile_latlong:   {}'.format(ul_tile_latlong))
    print('delta_latlong:     {}'.format(delta_latlong))
    print('delta_pixels:      {}'.format(delta_pixels))

    im = Image.open(filename)
    
    pixel_y = delta_pixels[1] * (0.5+math.cos(math.radians(map_ul_latlong[0]))) # SCD: These offsets are still weird.

    i=0
    for y in range(ul_tile_xy[1], lr_tile_xy[1]+1):
        pixel_x = -delta_pixels[0] * math.cos(math.radians(map_ul_latlong[0]))

        for x in range(ul_tile_xy[0], lr_tile_xy[0]+1):
            filepath_with_x = os.path.join(filepath, str(x))
            os.makedirs(filepath_with_x, exist_ok=True)
            
            tile_filename = os.path.join(filepath_with_x, '{}.png'.format(y))            
            print(tile_filename)

            box = (int(pixel_x), int(pixel_y), int(pixel_x+TILE_WIDTH_PIXELS), int(pixel_y+TILE_WIDTH_PIXELS))
            print(box)

            im_tile = im.crop(box)
            im_tile.save(tile_filename)

            i+=1

            pixel_x+=TILE_WIDTH_PIXELS
        print('-------------------')
        pixel_y+=TILE_WIDTH_PIXELS

    print('tile files: {}'.format(i))


def fit_map(map, zoom_level, anchors):
    '''Rotates and scales the input map. Writes map to disk with the zoom_level included in the filename.

    Returns tuple with the latitude and longitude for the upper left and lower right corners.
    '''
    
    print('--fit_map--')

    # Compute some filenames.
    map_rotation = compute_map_rotation(map, anchors)
    output_filename = filename_for_zoom_level(map, zoom_level)
    print('{} -> {} '.format(map['file'], output_filename))

    map_scale = compute_map_scale(map, zoom_level, anchors)

    im = Image.open(map['file']).convert('RGBA')

    # First, scale the image to work at the correct zoom level.
    im_scaled = im.resize((int(round(im.width*map_scale[0])), int(round(im.height*map_scale[1]))))
    print('im_scaled dim: {}'.format((im_scaled.width, im_scaled.height)))

    map_scaled_center_pixels = (im_scaled.width/2, im_scaled.height/2)
    map_scaled_center_latlong = latlong_for_pixel(map_scaled_center_pixels, vec2_scale(map['anchors']['a'], map_scale), anchors['a'], zoom_level)
    print('map_scaled_center_latlong: {}'.format(map_scaled_center_latlong))

    # # DEBUG: Draw anchors for debugging. Anchors must be scaled to zoom level.
    # draw_anchor(map_scaled_center_pixels, im_scaled, color='#00aa00', length=10*map_scale[0])
    # draw_anchor(vec2_scale(map['anchors']['a'], map_scale), im_scaled, length=10*map_scale[0])
    # draw_anchor(vec2_scale(map['anchors']['b'], map_scale), im_scaled, length=10*map_scale[0])
    # draw_anchor(vec2_scale(map['anchors']['c'], map_scale), im_scaled, length=10*map_scale[0])

    # Now rotate the image. Expand the image bounds so it fully fits in the rotated image.
    im_rotated = im_scaled.rotate(map_rotation, expand=True)
    im_rotated.save(output_filename)

    # The image has been rotated. Get the new pixel coordinates center which changes because the image was expanded.
    origin = (im_rotated.width/2, im_rotated.height/2)
    expand_delta = ((im_rotated.width-im_scaled.width)/2, (im_rotated.height-im_scaled.height)/2)
    print('expand_delta:  {}'.format(expand_delta))
    
    # Compute latlong for each corner of the rotated map image.
    image_anchor = rotate_around(vec2_add(vec2_scale(map['anchors']['a'], map_scale), expand_delta), origin, map_rotation)

    map_anchor = anchors['a']
    rotated_ul_latlong = latlong_for_pixel((0, 0), image_anchor, map_anchor, zoom_level)
    rotated_ur_latlong = latlong_for_pixel((im_rotated.width, 0), image_anchor, map_anchor, zoom_level)
    rotated_lr_latlong = latlong_for_pixel((im_rotated.width, im_rotated.height), image_anchor, map_anchor, zoom_level)
    rotated_ll_latlong = latlong_for_pixel((0, im_rotated.height), image_anchor, map_anchor, zoom_level)

    # # DEBUG: Rotate anchors in pixel space and draw for debugging.
    # rotated_anchor_a = rotate_around(vec2_add(vec2_scale(map['anchors']['a'], map_scale), expand_delta), origin, map_rotation)
    # print('rotated_anchor_a: {}'.format(rotated_anchor_a))
    # draw_anchor(rotated_anchor_a, im_rotated, color='#00FFFF', length=10*map_scale[0])

    # rotated_anchor_b = rotate_around(vec2_add(vec2_scale(map['anchors']['b'], map_scale), expand_delta), origin, map_rotation)
    # print('rotated_anchor_b: {}'.format(rotated_anchor_b))
    # draw_anchor(rotated_anchor_b, im_rotated, color='#00FFFF', length=10*map_scale[0])

    # rotated_anchor_c = rotate_around(vec2_add(vec2_scale(map['anchors']['c'], map_scale), expand_delta), origin, map_rotation)
    # print('rotated_anchor_c: {}'.format(rotated_anchor_c))
    # draw_anchor(rotated_anchor_c, im_rotated, color='#00FFFF', length=10*map_scale[0])

    im_rotated.save(output_filename)

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
    
    print('--/fit_map--')

    return (map_rotated_ul_latlong, map_rotated_lr_latlong)


def test__rotate_around():
    point = (0, 10)
    origin = (0, 1)
    theta = 90

    new_point = rotate_around(point, origin, theta)
    print('new_point:  {}'.format(new_point))


def test__latlong_for_pixel():
    map = {
            'file':'data/2022-oakland-debug.png',
            'anchors': {
                'a': [819,837],
                'b': [1192,905],
                'c': [1230,1177]
            }
    }

    anchors = {
        'a': [37.806645, -122.287200],
        'b': [37.804334, -122.271155],
        'c': [37.795135, -122.269526]
    }

    for zoom_level in range(14,15):
        print('====')
        map_scale = compute_map_scale(map, zoom_level, anchors)
        print('map_scale:   {}'.format(map_scale))

        print('anchor_a:      {}'.format(anchors['a']))

        pixel_xy = vec2_scale(map['anchors']['c'], map_scale)
        print('pixel_xy:      {}'.format(pixel_xy))
        pixel_latlong = latlong_for_pixel(
            pixel_xy, 
            vec2_scale(map['anchors']['a'], map_scale), 
            anchors['a'],
            zoom_level
        )

        print('pixel_latlong: {}'.format(pixel_latlong))
        print('known_latlong: {}'.format(anchors['c']))

        delta_latlong = vec2_sub(pixel_latlong, anchors['c'])
        print('delta_latlong: {}'.format(delta_latlong))
        print('====\n\n')

        origin_latlong = latlong_for_pixel((0,0),
            vec2_scale(map['anchors']['a'], map_scale), 
            anchors['a'],
            zoom_level
        )
        print('origin_latlong:   {}'.format(origin_latlong))

        # at zoom_level 14 for anchor['c']
        known_tile_xy = (2627, 6331)
        tile_xy = tile_for_latlong(anchors['c'][0], anchors['c'][1], zoom_level)
        print('tile_xy:       {}'.format(tile_xy))
        print('known_tile_xy: {}'.format(known_tile_xy))


def generate_manifest():
    global data    

    manifest = {
        'maps':[]
    }

    for map in data['maps']:
        manifest['maps'].append(
            {
                'path': '/'.join(filepath_for_tiles(map).split('/')[1:]), # remove leading 'site' dir from path.
                'name': map['name'],
                'attribution':map['attribution']
            }
        )

    manifest_filename = os.path.join(TILE_PATH, 'manifest.json')
    f = open(manifest_filename, 'w')
    f.write(json.dumps(manifest, indent=2))
    f.close()


def load_config():
    global data
    data = json.load(open('config.json', 'r'))


def main():
    load_config()

    for map in data['maps']:
        for zoom_level in range(13, 17):
            (map_ul_latlong, map_lr_latlong) = fit_map(map, zoom_level, data['anchors'])
            generate_map_tiles(map, zoom_level, map_ul_latlong, map_lr_latlong)

    generate_manifest()


if __name__ == '__main__':
    main()