
import os, sys, time, gdal
from gdalconst import *

# coordinates to get pixel values for
# UTM, zone 18

# Breakiron:
# lat: 40.954824, long: -76.881087
# easting: 341685.7, northing: 4535445.9

# the boat launch
# lat: 40.955312, long: -76.877387
# easting: 341998.2, northing: 4535493.4

x_values = [341685.7, 341998.2]
y_values = [4535445.9, 4535493.4]

startTime = time.time()

# register all of the drivers
gdal.AllRegister()


# open the image
current_path = os.getcwd()
os.chdir('..')
ds = gdal.Open("lewisburg_pa/lewisburg_pa.dem", GA_ReadOnly)

if ds is None:
    print ('Could not open image')
    sys.exit(1)


rows = ds.RasterYSize
cols = ds.RasterXSize
n_band = ds.RasterCount      # a.k.a, channels
print("rows, cols, bands: ", rows, cols, n_band)

transform = ds.GetGeoTransform()
x_origin = transform[0]
y_origin = transform[3]
print("x origin, y origin: " + str(x_origin) + " " + str(y_origin))
pixelWidth = transform[1]
pixelHeight = transform[5]

x_offset_list = []
y_offset_list = []

for i in range(len(x_values)):
    x = x_values[i]
    y = y_values[i]

    xOffset = int((x - x_origin) / pixelWidth)
    x_offset_list.add(xOffset)
    yOffset = int((y - y_origin) / pixelHeight)
    y_offset_list.add(yOffset)

    print( "xoffset, yoffset: ",xOffset, yOffset)


    s = "target UTM coordinate: " + str(x) + ' ' + str(y) + '; \n'
    s += "offset: " + str(xOffset) + ' ' + str(yOffset) + '; \n'
    for j in range(n_band):
        band = ds.GetRasterBand(j+1) # 1-based index
        # read data and add the value to the string
        data = band.ReadAsArray(xOffset, yOffset, 1, 1)
        value = data[0,0]
        s += str(value)

    print(s)

end_time = time.time()
print("Time: " + str(end_time - startTime))
