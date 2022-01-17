class SiderealFramework:
    def __init__(self, geo_longitude, geo_latitude, LST, ramc, svp, obliquity):
        self.geo_longitude = geo_longitude
        self.geo_latitude = geo_latitude
        self.LST = LST
        self.ramc = ramc
        self.svp = svp
        self.obliquity = obliquity

    def __str__(self):
        return str({
            'Longitude': self.geo_longitude,
            'Latitude': self.geo_latitude,
            'LST': self.LST,
            'RAMC': self.ramc,
            'SVP': self.svp,
            'Obliquity': self.obliquity
        })

# Nova, a free sidereal astrological tool.
# Copyright (C) 2019  Mike Verducci
# This project is under the GNU General Public License V3.
# The full license may be found in LICENSE.txt
