#!/usr/bin/env python

# Copyright (c) 2009 Max Planck Institute for Extraterrestrial Physics
# All Rights Reserved.

# Abdullah Yoldas <yoldas@mpe.mpg.de>
# Vladimir Sudilovsky <vsudilovsky@gmail.com>

import os
import sys

from math import *

def angsep(ra1, dec1, ra2, dec2):
    ra1, dec1, ra2, dec2 = map(radians, (ra1, dec1, ra2, dec2))
    d = ra2-ra1
    cos_dec1, cos_dec2, cos_d = map(cos, (dec1, dec2, d))
    sin_dec1, sin_dec2, sin_d = map(sin, (dec1, dec2, d))
    x = (cos_dec1 * sin_dec2) - (sin_dec1 * cos_dec2 * cos_d)
    y = cos_dec2 * sin_d
    z = sin_dec1 * sin_dec2 + cos_dec1 * cos_dec2 * cos_d
    r = atan2(sqrt(x * x + y * y), z)
    return degrees(r)

def equ2std(ra, dec, ct_ra, ct_dec):
    ct_ra, ct_dec, ra, dec = map(radians, (ct_ra, ct_dec, ra, dec))
    d = ra - ct_ra
    cos_ct_dec, cos_dec, cos_d = map(cos, (ct_dec, dec, d))
    sin_ct_dec, sin_dec, sin_d = map(sin, (ct_dec, dec, d))
    z = cos_ct_dec * cos_dec * cos_d + sin_ct_dec * sin_dec
    x = cos_dec * sin_d / z
    y = (cos_ct_dec * sin_dec - sin_ct_dec * cos_dec * cos_d) / z
    return -x, y

def std2equ(x, y, ct_ra, ct_dec):
    ct_ra = radians(ct_ra)
    ct_dec = radians(ct_dec)
    cos_ct_dec = cos(ct_dec)
    sin_ct_dec = sin(ct_dec)
    ra = ct_ra + atan(x / (cos_ct_dec - y * sin_ct_dec))
    dec = asin((sin_ct_dec + y * cos_ct_dec) / sqrt(1 + x * x + y * y))
    return degrees(ra), degrees(dec)

def std_where(x, y, x0, y0, x1, y1):
    return  (y - y0) * (x1 - x0) - (x - x0) * (y1 - y0)

def std_inside(x, y, ne_x, ne_y, nw_x, nw_y, sw_x, sw_y, se_x, se_y):
    r1 = std_where(x, y, ne_x, ne_y, nw_x, nw_y)
    r2 = std_where(x, y, nw_x, nw_y, sw_x, sw_y)
    r3 = std_where(x, y, sw_x, sw_y, se_x, se_y)
    r4 = std_where(x, y, se_x, se_y, ne_x, ne_y)
    if ((r1 >= 0 and r2 >= 0 and r3 >= 0 and r4 >= 0) or
        (r1 <= 0 and r2 <= 0 and r3 <= 0 and r4 <= 0)):
        return 1
    else:
        return 0

def equ2std_inside(ra, dec, ct_ra, ct_dec, ne_x, ne_y, nw_x, nw_y, sw_x,
                  sw_y, se_x, se_y):
    x, y = equ2std(ra, dec, ct_ra, ct_dec)
    r = std_inside(x, y, ne_x, ne_y, nw_x, nw_y, sw_x, sw_y, se_x, se_y)
    return r

def equ_inside(ra, dec, ct_ra, ct_dec, ne_ra, ne_dec, nw_ra, nw_dec,
               sw_ra, sw_dec, se_ra, se_dec):
    ne_x, ne_y = equ2std(ne_ra, ne_dec, ct_ra, ct_dec)
    nw_x, nw_y = equ2std(nw_ra, nw_dec, ct_ra, ct_dec)
    sw_x, sw_y = equ2std(sw_ra, sw_dec, ct_ra, ct_dec)
    se_x, se_y = equ2std(se_ra, se_dec, ct_ra, ct_dec)
    x, y = equ2std(ra, dec, ct_ra, ct_dec)
    r = std_inside(x, y, ne_x, ne_y, nw_x, nw_y, sw_x, sw_y, se_x, se_y)
    return r

def hms2deg(s):
    s = map(float, s.split(':'))
    x = 15*(s[0]+((s[1] + s[2]/60.0)/60.0))
    if x < 0 or x >= 360:
        x %= 360
    return x

def dms2deg(s):
    s = s.split(':')
    if s[0][0] == '-':
        sign = -1
        s[0] = s[0][1:]
    else:
        sign = 1
    s = map(float, s)
    x = sign*(s[0]+((s[1] + s[2]/60.0)/60.0))
    if x < -90 or x > 90:
        #x = degrees(asin(sin(radians(x))))
        raise ValueError("declination is out of range")
    return x

def deg2hms(x):
    x = float(x)
    if x < 0 or x >= 360:
        x %= 360
    t = x/15.0
    h = int(t)
    t = 60.0 * (t-h)
    m = int(t)
    s = 60.0 * (t-m)
    if round(s,3) >= 59.999:
        m += 1
        s -= 60
        if s < 0:
            s = 0
    if m >= 60:
        h += 1
        m -= 60
        if m < 0:
            m = 0
    if h >= 24:
        h %= 24
    return "%02d:%02d:%05.2f" % (h, m, s)
    
def deg2dms(x):
    t = float(x)
    if t < -90 or t > 90:
        #x = degrees(asin(sin(radians(t))))
        raise ValueError("declination is out of range")
    if t < 0:
        sign = '-'
        t *= -1
    else:
        sign = '+'
    d = int(t)
    t = 60.0 * (t - d)
    m = int(t)
    s = 60.0 * (t - m)
    if round(s,2) >= 59.99:
        m += 1
        s -= 60
        if s < 0:
            s = 0
    if m >= 60:
        d += 1
        m -= 60
        if m < 0:
            m = 0
        
    return "%s%02d:%02d:%05.2f" % (sign, d, m, s)



def main(ra,dec):
    ra = deg2hms(ra)
    dec = deg2dms(dec)
    return ra, dec

if __name__ == '__main__':
    ra,dec=main(ra=sys.argv[1],dec=sys.argv[2])
    print ra,dec
