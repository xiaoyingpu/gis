import time
import gdal
from gdalconst import *
from osgeo import osr
from osgeo import ogr

from shapely.wkb import loads

import numpy as np
import matplotlib.pyplot as plt


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

        # instance variables
        self._originX = 0           # easting; UTM
        self._originY = 0           # northing; UTM

        self._pixelWidth = 0
        self._pixelHeight = 0
        self._bands = 0             # number of channels for one pixel
        self._rows = 0              # y axis
        self._cols = 0              # x axis

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
        Origin x, y's are defined in ??? coordinates
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
        return int((x - self._originX) / self._pixelWidth)

    def get_y_offset(self, y):
        return int((y - self._originY) / self._pixelHeight)

    def get_pixel_value(self, x, y):
        """
        x: easting
        y: northing
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
        x1, x2: easting
        y1, y2: northing
        """
        elevation_list = []
        x_list = []
        y_list = []
        k = (y2 - y1) / (x2 - x1)
        b = y1 - k * x1
        n_step = (x2 - x1) // self._pixelWidth

        for i in range(int(n_step)):
            x = x1 + i * self._pixelWidth
            y = k * x + b
            x_list.append(x)
            y_list.append(y)

            value = self.get_pixel_value(x, y)
            elevation_list.append(value)

        colors = np.random.rand(int(n_step))
        plt.scatter(x_list, elevation_list)
        plt.show()



if __name__ == "__main__":
    # Breakiron:
    # lat: 40.954824, long: -76.881087
    # easting: 341685.7, northing: 4535445.9

    # the boat launch
    # lat: 40.955312, long: -76.877387
    # easting: 341998.2, northing: 4535493.4
    t_start = time.time()
    reader = Reader("../lewisburg_pa/lewisburg_pa.dem")

    # print(reader.get_pixel_value(341674.7, 4535455.3))
    reader.get_line_feature(341685.7, 4535445.9, 341998.2, 4535493.4)
    reader.close()
    t_end = time.time()
    print("Time: " + str(t_end - t_start))

    # add API: get_pixel_value(offset's)
    # another class: ruler:
    #   __init__(self, easting, northing)
    #   loops through every grid and get_pixel_value(offset's)
    # add converter: distance -> easting and northing
