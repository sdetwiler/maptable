#!/usr/bin/env python3


# https://wiki.openstreetmap.org/wiki/Slippy_map_tilenames#Resolution_and_Scale


import math


from PIL import Image, ImageDraw


DEG_TO_RAD = math.pi/180
METERS_PER_DEGREE = 87843.36
DEGREES_PER_METER = 1.0/METERS_PER_DEGREE

# Reference Anchors
# a  Adeline and 10th street     @37.8066432,-122.2894024
# b  San Pablo and Broadway      @37.8043284,-122.273357
# c  Jackson and 4th street      @37.795114,-122.2717142

data = { 
    'anchors': {
        'a': [37.8066432,-122.2894024],
        'b': [37.8043284,-122.273357],
        'c': [37.795114,-122.2717142]
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
            'file':'data/1899-oakland.jpg',
            'anchors': {
                'a': [3143,4764],
                'b': [3743,4576],
                'c': [4004,4951]
            }
        },
        {
            'file':'data/1912-oakland-terminal-railways.jpg',
            'anchors': {
                'a': [711,786],
                'b': [743,812],
                'c': [714,839]
            }
        },
        {
            'file':'data/1898-oakland.jpg',
            'anchors': {
                'a': [550,1260],
                'b': [837,1310],
                'c': [870,1512]
            }
        }


    ]
}


def deg2num(lat_deg, lon_deg, zoom):
  lat_rad = math.radians(lat_deg)
  n = 2.0 ** zoom
  xtile = int((lon_deg + 180.0) / 360.0 * n)
  ytile = int((1.0 - math.asinh(math.tan(lat_rad)) / math.pi) / 2.0 * n)
  return (xtile, ytile)


def meters_per_pixel(latitude, zoom_level):
    '''Returns the number of meters covered by each pixel at a given latitude and zoom level.
        latitude: latitude in degrees.
        zoom_level: zoom level index 1-17
    '''
    latitude_rad = latitude * DEG_TO_RAD
    return 156543.03 * math.cos(latitude_rad) / math.pow(2, zoom_level)


def degres_per_pixel(latitude, zoom_level):
    zoom_meters_per_pixel = meters_per_pixel(latitude, zoom_level)
    return zoom_meters_per_pixel * DEGREES_PER_METER


def compute_map_scale(map, zoom_level, anchors):
    # How many meters between anchors a and b
    anchor_x_meters = math.fabs(anchors['a'][1] - anchors['b'][1]) * METERS_PER_DEGREE
    print('meters:       {}'.format(anchor_x_meters))

    # How many pixels between anchors a and b on the map
    map_x_pixels = math.fabs(map['anchors']['a'][0] - map['anchors']['b'][0])
    print('pixels:       {}'.format(map_x_pixels))

    # How many meters per pixel on the map
    map_meters_per_pixel = anchor_x_meters / map_x_pixels
    print('m/px:         {}'.format(map_meters_per_pixel))

    # https://wiki.openstreetmap.org/wiki/Slippy_map_tilenames#Resolution_and_Scale
    print('zoom:         {}'.format(zoom_level))
    zoom_meters_per_pixel = meters_per_pixel(anchors['a'][0], zoom_level)
    print('zoom m/px:    {}'.format(zoom_meters_per_pixel))
    map_scale = map_meters_per_pixel/zoom_meters_per_pixel

    print('scale:        {}'.format(map_scale))
    return map_scale

def compute_anchor_rotation(anchors):
    # find angle between a and b
    y = anchors['b'][0] - anchors['a'][0]   # latitude is y axis
    x = anchors['b'][1] - anchors['a'][1]   # longitude is x axis
    anchor_rotation = math.atan(y/x)*(180/math.pi)
    print('anchor_rotation:     {}'.format(anchor_rotation))
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

def rotate_point(point, theta):
    '''Rotates a point by theta degrees around the origin.
    '''
    
    theta_rad = theta * DEG_TO_RAD
    x = point[0]
    y = point[1]
    xp = x * math.cos(theta_rad) - y * math.sin(theta_rad)
    yp = y * math.cos(theta_rad) + x * math.sin(theta_rad)
    return(xp, yp)


def rotate_anchor(anchor, theta, map_width, map_height):
    origin = (map_width/2, map_height/2)
    point = (anchor[0], anchor[1])

    print('origin:    {}'.format(origin))
    print('point:     {}'.format(point))
    print('theta:     {}'.format(theta))

    # Coordinate space places (0,0) in upper left, so negate the rotation.
    theta*=-1

    theta_rad = theta * (math.pi/180)
    print('theta_rad: {}'.format(theta_rad))

    new_x = origin[0] + ((point[0] - origin[0]) * math.cos(theta_rad)) - ((point[1] - origin[1]) * math.sin(theta_rad))
    new_y = origin[1] + ((point[0] - origin[0]) * math.sin(theta_rad)) + ((point[1] - origin[1]) * math.cos(theta_rad))

    new_point = (new_x, new_y)
    print('new_point: {}'.format(new_point))

    return new_point


def draw_anchor(anchor, im, color='#ff0000', length=10):
    # Draw anchors for debugging.
    draw = ImageDraw.Draw(im)
    
    hs = (anchor[0]-length, anchor[1])
    he = (anchor[0]+length, anchor[1])
    vs = (anchor[0], anchor[1]-length)
    ve = (anchor[0], anchor[1]+length)

    draw.line([hs,he], fill=color, width=int(length/10.0)*4)    # hack to scale the width from reference length
    draw.line([vs,ve], fill=color, width=int(length/10.0)*4)


def vec2_add(a, b):
    return (a[0]+b[0], a[1]+b[1])


def vec2_sub(a, b):
    return (a[0]-b[0], a[1]-b[1])


def vec2_scale(a, s):
    return(a[0]*s, a[1]*s)


def fit_map(map, zoom_level, anchors):
    print(map['file'])
    map_rotation = compute_map_rotation(map, anchors)
    map_scale = compute_map_scale(map, zoom_level, anchors)

    # Compute some filenames.
    tokens = map['file'].split('.')
    extension = tokens[-1]
    filename = '.'.join(tokens[0:-1])
    output_filename = '{}-{}.{}'.format(filename, zoom_level, extension)

    im = Image.open(map['file'])

    # Scale the image first to work at the correct zoom level.
    im_scaled = im.resize((int(round(im.width*map_scale)), int(round(im.height*map_scale))))
    map_scaled_center_pixels = (im_scaled.width/2, im_scaled.height/2)
    map_scaled_center_latlong = latlong_for_pixel(map_scaled_center_pixels, map['anchors']['a'], anchors['a'], zoom_level)

    # Draw anchors for debugging. Anchors must be scaled to zoom level.
    draw_anchor(map_scaled_center_pixels, im_scaled, color='#00aa00', length=10*map_scale)
    draw_anchor(vec2_scale(map['anchors']['a'], map_scale), im_scaled, length=10*map_scale)
    draw_anchor(vec2_scale(map['anchors']['b'], map_scale), im_scaled, length=10*map_scale)
    draw_anchor(vec2_scale(map['anchors']['c'], map_scale), im_scaled, length=10*map_scale)

    # Now rotate the image. Expand the image bounds so it fully fits in the rotated image.
    im_rotated = im_scaled.rotate(map_rotation, expand=True)
    im_rotated.save(output_filename)

    # The image has been scaled. Get the new pixel coordinates center which changes because the image was expanded.
    map_rotated_center_pixels = (im_rotated.width/2, im_rotated.height/2)
    
    # With the image expansion, how much bigger did the image bounds become?
    map_delta = vec2_sub(map_rotated_center_pixels, map_scaled_center_pixels)

    # Now compute the latitude and longitude for the upper left and lower right corners of the rotated image.
    zoom_degrees_per_pixel = degres_per_pixel(map['anchors']['a'][0], zoom_level)    
    # Distribute half the difference to each dimension because it resized from the center. Convert to lat long
    map_rotated_ul_latlong = (  map_scaled_center_latlong[0]-(map_delta[0]/2.0)*zoom_degrees_per_pixel, 
                                map_scaled_center_latlong[1]-(map_delta[1]/2.0)*zoom_degrees_per_pixel
                            )
    map_rotated_lr_latlong = (  map_scaled_center_latlong[0]+(map_delta[0]/2.0)*zoom_degrees_per_pixel, 
                                map_scaled_center_latlong[1]+(map_delta[1]/2.0)*zoom_degrees_per_pixel
                            )
    print('map_rotated_ul_latlong: {}'.format(map_rotated_ul_latlong))
    print('map_rotated_lr_latlong: {}'.format(map_rotated_lr_latlong))


def latlong_for_pixel(pixel_xy, image_anchor, map_anchor, zoom_level):
    '''Returns the latitude and longitude for a given pixel in an image.

    pixel_xy:     The pixel to evaluate, in pixel space (x,y).
    image_anchor: Anchor coordinates in pixel space (x,y).
    map_anchor:   Anchor coordinates in latlong space (lat,long).
    zoom_level:   The zoom level for the image.

    Returns: Tuple with (lat,long)
    '''
    
    # Distance in pixels from image anchor to pixel
    distance_pixels = vec2_sub(image_anchor, pixel_xy)

    # convert distance in pixels to meters
    zoom_meters_per_pixel = meters_per_pixel(map_anchor[0], zoom_level)
    distance_meters = (distance_pixels[0] / zoom_meters_per_pixel, distance_pixels[1] / zoom_meters_per_pixel)
    # convert distance in meters to degrees
    distance_degrees = (distance_meters[0] / METERS_PER_DEGREE, distance_meters[1] / METERS_PER_DEGREE)

    print("map_anchor:    {}".format(map_anchor))
    pixel_latlong = vec2_add(map_anchor, distance_degrees)
    print('pixel_latlong: {}'.format(pixel_latlong))
    
    return pixel_latlong



def test():
    # origin = (2,2)
    # point = (3,4)
    # theta = 45

    # origin = (996.0, 1398.0)
    origin = (10.0, 14.0)
    point = (0, 0)
    theta = -5


    print('origin:    {}'.format(origin))
    print('point:     {}'.format(point))
    print('theta:     {}'.format(theta))

    theta_rad = theta * (math.pi/180)
    print('theta_rad: {}'.format(theta_rad))

    new_x = origin[0] + ((point[0] - origin[0]) * math.cos(theta_rad)) - ((point[1]-origin[1])*math.sin(theta_rad))
    new_y = origin[1] + ((point[0] - origin[0]) * math.sin(theta_rad)) + ((point[1]-origin[1])*math.cos(theta_rad))

    new_point = (new_x, new_y)
    print('new_point: {}'.format(new_point))

    return new_point



def compute_map_ul_latlong(map, anchor_rotation):
    '''
    Computes the latitude and longitude for the upper left corner of the map after it has been rotated.
    '''

    map_rotation = compute_map_rotation(map)
    rotation = anchor_rotation + map_rotation


def main():
    # test()

    map = data['maps'][4]
    zoom_level = 17
    fit_map(map, zoom_level, data['anchors'])


if __name__ == '__main__':
    main()