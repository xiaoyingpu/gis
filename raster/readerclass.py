import time
import gdal
from gdalconst import *
from osgeo import osr
from osgeo import ogr

from shapely.wkb import loads

import numpy as np
import matplotlib.pyplot as plt

# see http://www.gis.usu.edu/~chrisg/python/2009/lectures/ospy_slides4.pdf


class Reader:
    """
    Loads raster data point one at a time
    """
    def __init__(self,file_name):
        """
        initializes the data_set member
        """
        # register all of the drivers
        gdal.AllRegister()

        # open image
        self.data_set = gdal.Open(file_name, GA_ReadOnly)
        if self.data_set is None:
            print("Could not open file")
            exit(1)
        print(file_name + " read successfully")

        # coordinates:
        #  |
        #--+--------------> x
        #  |
        #  |
        #  |
        #  |
        #  V y
        # 
        # instance variables
        # originX and originY are at the upper left corner of the raster image
        # these coordinates are in universal transverse merator coordinate system
        #, a 2-D projection coordinate system that is suitable for a large-`scale`
        # map, i.e., around Lewisburg instead of the entire state
        # UTM could be converted to latitude are longitudes, but UTM 
        # might provid more precision
        self._originX = 0           # easting; UTM
        self._originY = 0           # northing; UTM

        self._pixelWidth = 0
        self._pixelHeight = 0
        self._bands = 0             # number of `channels` (like RGB channels) for one pixel
        self._rows = 0              # along y axis
        self._cols = 0              # along x axis
        self.x_list = []            # x-coordinates along the cross-section of choice
        self.y_list = []            # y-coordinates along the cross-section of choice
        self.elevation_list = []    # the elevation at point (x,y), unit: m
        self.k1 = 0                 # slop of transect in x-y plane
        self.b1 = 0                 # y-axis intersection
        self.n_step=0               

        self._define_boundaries()   # initialize boundary variables

    def __str__(self):
        """
        returns the projection spec.
        """
        pszProjection = self.data_set.GetProjectionRef()
        if pszProjection is not None:
            hSRS = osr.SpatialReference()
            if hSRS.ImportFromWkt(pszProjection ) == gdal.CE_None:
                pszPrettyWkt = hSRS.ExportToPrettyWkt(False)
                return pszPrettyWkt
            else:
                return pszProjection

    def _define_boundaries(self):
        """
        Defines the boundary of the raster files
        """
        self._cols = self.data_set.RasterXSize
        self._rows = self.data_set.RasterYSize
        self._bands = self.data_set.RasterCount

        geo_transform = self.data_set.GetGeoTransform()

        if geo_transform is None:
            print("geo_transform is None")

        self._originX = geo_transform[0]
        self._originY = geo_transform[3]
        self._pixelWidth = geo_transform[1]
        self._pixelHeight = geo_transform[5]

    def close(self):
        self.data_set = None

    def get_x_offset(self, x):
        """
        gets the pixel index on x-axis
        """
        return int((x - self._originX) / self._pixelWidth)

    def get_y_offset(self, y):
        """
        gets the pixel index on x-axis
        """
        return int((y - self._originY) / self._pixelHeight)

    def get_pixel_value(self, x, y):
        """
        x: easting
        y: northing
        the pixel value is -32768? for data points
        outside the raster image
        """

        x_offset = self.get_x_offset(x)
        y_offset = self.get_y_offset(y)

        for i in range(self._bands):
            band = self.data_set.GetRasterBand(i+1)
            # dataArray: one data point at a time
            data_array = band.ReadAsArray(x_offset, y_offset, 1, 1)
            value = data_array[0, 0]
            return value

    def get_line_feature(self, x1, y1, x2, y2):
        """
        four parameters are in UTM
        x1, x2: easting
        y1, y2: northing
        (x1, y1): coordinate for the transmitter
        (x2, y2): coordinate for the receiver
        samples the transect with interval = pixel width and
        generates the elevation list
        """
        self.k1 = (y2 - y1) / (x2 - x1)
        self.b1 = y1 - self.k1 * x1
        self.n_step = (x2 - x1) // self._pixelWidth

        for i in range(int(self.n_step)):
            x = x1 + i * self._pixelWidth
            y = self.k1 * x + self.b1
            self.x_list.append(x)
            self.y_list.append(y)
            value = self.get_pixel_value(x, y)
            self.elevation_list.append(value)



    def get_hindrance(self):
        """
        this method might be broken
        """
        hindrance_list = []
        sensor_elev = self.elevation_list[0]
        recv_elev = self.elevation_list[-1]
        delta_elev = sensor_elev - recv_elev
        x_square = (self.x_list[0] - self.x_list[-1]) ** 2
        y_square = (self.y_list[0] - self.y_list[-1]) ** 2
        distance = (x_square + y_square) ** 0.5

        k = (delta_elev) / (distance)
        b = self.elevation_list[0] - k * self.x_list[0]

        for i in range(len(self.elevation_list)):
            supposed_elev = self.x_list[i] * self.k1  + self.b1
            if self.elevation_list[i] >= supposed_elev:
                return (self.x_list[i], self.elevation_list[i])

    def plot_results(self):
        """
        this method is broken?
        """
        fig = plt.figure()
        fig.suptitle('Cross section', fontsize=14, fontweight='bold')
        ax = fig.add_subplot(111)        
        ax.plot(self.x_list, self.elevation_list)
        ax.set_xlabel('easting')
        ax.set_ylabel('elevation (m)')
        
        plt.show()




if __name__ == "__main__":
    # some convenient coordinates:
    # Breakiron:
    # lat: 40.954824, long: -76.881087
    # easting: 341685.7, northing: 4535445.9

    # the boat launch
    # lat: 40.955312, long: -76.877387
    # easting: 341998.2, northing: 4535493.4


    # north size of winfield
    # 342279.95, 4532332.21
    t_start = time.time()
    reader = Reader("../lewisburg_pa/lewisburg_pa.dem")

    # print(reader.get_pixel_value(341674.7, 4535455.3))
    reader.get_line_feature(338977.89, 4536688.13, 339514.93, 4534804.52)
    reader.plot_results()
    reader.close()
    t_end = time.time()
    print("Time: " + str(t_end - t_start))

    # add API: get_pixel_value(offset's)
    # another class: ruler:
    #   __init__(self, easting, northing)
    #   loops through every grid and get_pixel_value(offset's)
    # add converter: distance -> easting and northing
