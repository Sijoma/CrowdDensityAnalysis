import os
from osgeo import gdal, ogr, osr
import math
import numpy as np
from matplotlib import pyplot as plt

pi = math.pi

"""This module contains functions to calculate the density out of a shapefile track
and to write the density out of a raster file to a shapefile, while also providing
functions to plot these densities"""

####### Aerial Density Methods ##########


def reproject(in_rast, in_vect, out_fn):
    # Open the raster
    rast_data_source = gdal.Open(in_rast)
    if rast_data_source is None:
        print 'Could not open %s' % (in_rast)

    rast_spatial_ref = rast_data_source.GetProjection()
    driver = ogr.GetDriverByName('ESRI Shapefile')
    vect_data_source = driver.Open(in_vect, 0)

    # Check to see if shapefile is found.
    if vect_data_source is None:
        print 'Could not open %s' % (in_vect)

    # Get the Layer class object
    layer = vect_data_source.GetLayer(0)
    # Get reference system info
    vect_spatial_ref = layer.GetSpatialRef()
    # create osr object of raster spatial ref info
    sr = osr.SpatialReference(rast_spatial_ref)
    transform = osr.CoordinateTransformation(vect_spatial_ref, sr)

    # Delete if output file already exists
    # We can use the same driver
    if os.path.exists(out_fn):
        print 'exists, deleting'
        driver.DeleteDataSource(out_fn)
    out_ds = driver.CreateDataSource(out_fn)
    if out_ds is None:
        print 'Could not create %s' % (out_fn)

    # Create the shapefile layer WITH THE SR
    out_lyr = out_ds.CreateLayer('track_points', sr,
                                 ogr.wkbPoint)

    out_lyr.CreateFields(layer.schema)
    out_defn = out_lyr.GetLayerDefn()
    out_feat = ogr.Feature(out_defn)
    for in_feat in layer:
        geom = in_feat.geometry()
        geom.Transform(transform)
        out_feat.SetGeometry(geom)
        for i in range(in_feat.GetFieldCount()):
            value = in_feat.GetField(i)
            out_feat.SetField(i, value)
        out_lyr.CreateFeature(out_feat)

    del out_ds

    print 'done'


def writePixelsFromRasterToShp(src_filename, shp_filename, nameOfColumn):
    src_ds = gdal.Open(src_filename)
    gt = src_ds.GetGeoTransform()
    rb = src_ds.GetRasterBand(1)
    # Create new field if it doesnt exit
    # open shapefile in write-mode (2nd parameter of driver.Open has to be 1)
    driver = ogr.GetDriverByName('ESRI Shapefile')
    ds = driver.Open(shp_filename, 1)
    layer = ds.GetLayer()
    # Check if field already exists
    layer_defn = layer.GetLayerDefn()
    field_names = [layer_defn.GetFieldDefn(
        i).GetName() for i in range(layer_defn.GetFieldCount())]
    # create new attribute field "datetime" with datatype string
    if not nameOfColumn in field_names:
        new_field = ogr.FieldDefn(nameOfColumn, ogr.OFTString)
        layer.CreateField(new_field)
    else:
        print 'Field already exists'

    totalAmountofRows = float(layer.GetFeatureCount())
    rowNumber = 1

    for feature in layer:
        percent = ((rowNumber / totalAmountofRows) * 100)
        print "Current Shapefile processing status: ", "Feature #", rowNumber, "%10.2f" % percent, "% done"
        geom = feature.GetGeometryRef()
        mx, my = geom.GetX(), geom.GetY()  # coord in map units

        # Convert from map to pixel coordinates.
        # Only works for geotransforms with no rotation.
        px = int((mx - gt[0]) / gt[1])  # x pixel
        py = int((my - gt[3]) / gt[5])  # y pixel

        intval = rb.ReadAsArray(px, py, 1, 1)
        # intval is a numpy array, length=1 as we only asked for 1 pixel value
        densityValue = intval[0][0]
        # Convert from Density Value to persons per qm
        densityValue = (float(densityValue) / 163) * 7
        feature.SetField(nameOfColumn, float(densityValue))
        layer.SetFeature(feature)
        rowNumber = rowNumber + 1

####### Formula Density Methods ##########

# Calculate the distance between two coordinates
def calculateDistance(lat1, lng1, lat2, lng2):
    # Flattening of the earth
    f = 1 / 298.26
    # Radius of the earth
    radius = 6378.14
    # Convert degrees to radians
    lat1 = lat1 * pi / 180.0
    lng1 = lng1 * pi / 180.0
    lat2 = lat2 * pi / 180.0
    lng2 = lng2 * pi / 180.0

    # f, g and l values for the caluculation
    fRad = (lat1 + lat2) / 2
    gRad = (lat1 - lat2) / 2
    lRad = (lng1 - lng2) / 2
    # Values s and c for calculating distance
    s = (math.sin(gRad) * math.sin(gRad)) * (math.cos(lRad) * math.cos(lRad)) + \
        (math.cos(fRad) * math.cos(fRad)) * (math.sin(lRad) * math.sin(lRad))
    c = (math.cos(gRad) * math.cos(gRad)) * (math.cos(lRad) * math.cos(lRad)) + \
        (math.sin(fRad) * math.sin(fRad)) * (math.sin(lRad) * math.sin(lRad))
    w = math.atan(math.sqrt(s / c))

    # distance
    d = 2 * w * radius
    return d

# Calculate the speed of travelling between two coordinates and a specific time
def calculateSpeed(lat1, lng1, lat2, lng2):
    # Calculate the distance of the coordinates
    distance = calculateDistance(lat1, lng1, lat2, lng2)
    # convert distance to meters
    distance = distance * 1000

    # the time difference in seconds
    timeDiff = 5
    # meters per second
    speedMPS = distance / timeDiff
    return speedMPS

# Calculate the density (based on speed) using the equation introduced in
# "Routing in Dense Human Crowds Using Smartphone Movement Data and Optical Aerial Imagery" 
# (2015) by Florian Hillen , Oliver Meynberg and Bernhard Hoefle
# Two parameters of the equation had to be adjusted based on our data
def calculateDensity(speed):
    D = -1.913 / (math.log(1.9 - speed) - 0.989199)
    return D

# Calculates and writes the speed to a given shapefile
def CalSpeedToSHP(in_shp):
    driver = ogr.GetDriverByName('ESRI Shapefile')
    shp_source1 = driver.Open(in_shp, update=True)
    layer = shp_source1.GetLayer(0)

    # Create new field for the calculated speed value if not exists (in both
    # shapefiles)
    new_field_speed = ogr.FieldDefn('calSpeed', ogr.OFTReal)

    layer_defn1 = layer.GetLayerDefn()
    field_names1 = [layer_defn1.GetFieldDefn(
        i).GetName() for i in range(layer_defn1.GetFieldCount())]
    if not 'calSpeed' in field_names1:
        layer.CreateField(new_field_speed)

    prev = layer.GetNextFeature()
    prev.SetField("calSpeed", 0)
    layer.SetFeature(prev)
    # array to store the speed (to do statistical measurements to find
    # appropriate speed values)
    speeds = []

    # for every 5th point / every 5 seconds calculate the speed
    for i in range(0, layer.GetFeatureCount(), 5):
        # get coordinates of current point
        feat = layer.GetFeature(i)
        geom = feat.geometry()
        x = geom.GetX()
        y = geom.GetY()
        # get coordinates of previous point
        prevGeom = prev.geometry()
        xPrev = prevGeom.GetX()
        yPrev = prevGeom.GetY()
        # calculate speed between these points
        speed = calculateSpeed(y, x, yPrev, xPrev)
        feat.SetField("calSpeed", speed)
        speeds.append(speed)
        layer.SetFeature(feat)
        prev = feat

# Calculates the density out of speed values from the shapefile
def calcDensityToShp(in_shp, plotParam):
    driver = ogr.GetDriverByName('ESRI Shapefile')
    shp_source1 = driver.Open(in_shp, update=True)
    layer = shp_source1.GetLayer(0)
    # Create new field for the density value if not exists
    new_field_den = ogr.FieldDefn(plotParam, ogr.OFTReal)
    layer_defn1 = layer.GetLayerDefn()
    field_names1 = [layer_defn1.GetFieldDefn(
        i).GetName() for i in range(layer_defn1.GetFieldCount())]
    if not plotParam in field_names1:
        layer.CreateField(new_field_den)

    prev = layer.GetNextFeature()
    prev.SetField(plotParam, 0)
    layer.SetFeature(prev)

    for feat in layer:
        # calculate and store density
        speed = feat.GetField('calSpeed')
        density = calculateDensity(speed)
        feat.SetField(plotParam, density)
        layer.SetFeature(feat)


def percentile(shp_path1, shp_path2):
    driver = ogr.GetDriverByName('ESRI Shapefile')
    # Load each shapefiles (reading permission required)
    shp_source1 = driver.Open(shp_path1, update=True)
    shp_source2 = driver.Open(shp_path2, update=True)

    # Get layer of each shapefile
    layer = shp_source1.GetLayer(0)
    layer2 = shp_source2.GetLayer(0)
    # array to store the speed (to do statistical measurements to find
    # appropriate speed values)
    speeds = []
    for i in range(0, layer.GetFeatureCount(), 5):
        # get coordinates of current point
        feat = layer.GetFeature(i)
        # calculate speed between these points
        speed = feat.GetField("calSpeed")
        speeds.append(speed)
        # layer.SetFeature(feat)
        prev = feat

    for i in range(0, layer2.GetFeatureCount(), 5):
        # get coordinates of current point
        feat = layer2.GetFeature(i)
        # calculate speed between these points
        speed = feat.GetField("calSpeed")
        speeds.append(speed)
        # layer.SetFeature(feat)
        prev = feat

    # delete empty rows (calcuation just for every 5 seconds) and too high values in both shapefiles
    # Use a threshold to define appropriate speed values: 95 percentile -->
    # 1.86
    threshold = np.percentile(speeds, 95)
    for i in range(0, layer.GetFeatureCount()):
        feat = layer.GetFeature(i)
        speed = feat.GetField('calSpeed')
        if speed == None or speed >= threshold:
            layer.DeleteFeature(i)

    for i in range(0, layer2.GetFeatureCount()):
        feat = layer2.GetFeature(i)
        speed = feat.GetField('calSpeed')
        if speed == None or speed >= threshold:
            layer2.DeleteFeature(i)

# PLOTTING
##

# Plots the formula density or aerial density depending on the plotParam
def PlotCalDensity(savePath, in_shp, track_name, plotParam):
    driver = ogr.GetDriverByName('ESRI Shapefile')
    shp_source1 = driver.Open(in_shp, update=True)
    layer = shp_source1.GetLayer(0)
    # Calculate density and create plot for layer
    f, axarr = plt.subplots(1)
    density1 = []
    # arrays to store coordinates for the plot
    x = []
    y = []
    for feat in layer:
        # store coordinates in the arrays for the plot
        pt = feat.geometry()
        density1.append(feat.GetField(plotParam))
        x.append(pt.GetX())
        y.append(pt.GetY())

    # create and save plot
    scat = axarr.scatter(x, y, c=density1, cmap="hot_r",
                         label="Density", lw=0.2)
    cb = plt.colorbar(scat, spacing="proportional")
    cb.set_label("Density")
    plt.xticks(rotation=45)
    # Complete Track
    plt.xlim([316859.4, 317682.5])  # 402,5
    plt.ylim([5671962.5, 5672785.6])  # 823,1
    # # +- 1:30 around timestamp
    # plt.xlim([317296.0, 317401.9])
    # plt.ylim([5672561.73, 5672644.95])  
    if(plotParam == "airDens"):
        plt.title("Aerial density for track: " + track_name)

    if(plotParam == "formDens"):
        plt.title("Formula density for track: " + track_name)

    plt.ticklabel_format(useOffset=False)
    pngName = plotParam + "TRACK" + track_name + ".png"
    out_path = os.path.join(savePath,
                            pngName)

    plt.savefig(out_path, dpi=300, format="png")

# Plots the difference between both densities of the given shapefile
def compareDensities(savePath, in_shp, track_name):
    driver = ogr.GetDriverByName('ESRI Shapefile')
    shp_source1 = driver.Open(in_shp, update=True)
    layer = shp_source1.GetLayer(0)
    # Calculate density and create plot for layer
    f, axarr = plt.subplots(1)
    differenceArr = []
    # arrays to store coordinates for the plot
    x = []
    y = []
    for feat in layer:
        # store coordinates in the arrays for the plot
        pt = feat.geometry()

        formulaDensity = float(feat.GetField('formDens'))
        aerialDensity = float(feat.GetField('airDens'))
        difference = (formulaDensity - aerialDensity)
        differenceArr.append(difference)
        x.append(pt.GetX())
        y.append(pt.GetY())

    # create and save plot
    scat = axarr.scatter(x, y, c=differenceArr,
                         cmap="hot_r", label="Difference", lw=0.2)
    cb = plt.colorbar(scat, spacing="proportional")
    cb.set_label("Difference between formula density and aerial density")
    # Set if the plot should contain the complete track or just the timestamp
    # CompleteTrack limits
    # plt.xlim([316859.4, 317682.5])  
    # plt.ylim([5671962.5, 5672785.6]) 

    plt.xlim([317296.0, 317401.9])
    plt.ylim([5672561.73, 5672644.95])  
        
    

    plt.xticks(rotation=45)
    plt.ticklabel_format(useOffset=False)
    plt.title("Comparison of densities for track: " + track_name)
    pngName = "differenceTrack" + track_name + ".png"
    out_path = os.path.join(savePath,
                            pngName)

    plt.savefig(out_path, dpi=300, format="png")

# Plots bar charts for the given shapefile with a certain span around the timestamp
def plotBarCharts(savePath, in_shp, track_name, fileNumber, span):
    driver = ogr.GetDriverByName('ESRI Shapefile')
    shp_source1 = driver.Open(in_shp, update=True)
    layer = shp_source1.GetLayer(0)
    # Calculate density and create plot for layer
    f, axarr = plt.subplots(1)
    # Arrays to store data for the plot
    formDensityArr = []
    aerialDensityArr = []
    featureNumberArr = []

    # This would have to be changed to selected the appropriate timestamp 
    # when processing variable shapefiles
    if(fileNumber == 0):
        timestampNumber = 168
    if(fileNumber == 1):
        timestampNumber = 111
    lower = timestampNumber - span
    upper = timestampNumber + span

    featureCounter = 0
    for i in range(lower, upper):
        # get coordinates of current point
        feat = layer.GetFeature(i)
        # store coordinates in the arrays for the plot
        pt = feat.geometry()
        formulaDensity = float(feat.GetField('formDens'))
        aerialDensity = float(feat.GetField('airDens'))
        formDensityArr.append(formulaDensity)
        aerialDensityArr.append(aerialDensity)
        featureNumberArr.append(featureCounter - 10)
        featureCounter += 1

    f, axarr = plt.subplots(1)
    index = np.arange(featureCounter)
    bar_width = 0.3
    opacity = 0.8

    rects1 = plt.bar(index, formDensityArr, bar_width,
                     alpha=opacity, color='b', label='Formula Density')
    rects2 = plt.bar(index + bar_width, aerialDensityArr, bar_width,
                     alpha=opacity, color='g', label='Aerial Density')

    plt.xlabel("Track point")
    plt.ylabel("Density")
    plt.title("Comparison of densities for track: " + track_name)

    plt.xticks(index + bar_width, featureNumberArr)
    plt.legend()
    plt.tight_layout()

    pngName = "Barchart_Comparison" + track_name + ".png"
    out_path = os.path.join(savePath,
                            pngName)

    plt.savefig(out_path, dpi=300, format="png")

# Plots line charts for the given shapefile
def plotLineCharts(savePath, in_shp, track_name, fileNumber, span):
    driver = ogr.GetDriverByName('ESRI Shapefile')
    shp_source1 = driver.Open(in_shp, update=True)
    layer = shp_source1.GetLayer(0)
    # Calculate density and create plot for layer
    f, axarr = plt.subplots(1)
    # Arrays to store data for the plot

    differenceArr = []
    featureNumberArr = []

    if(fileNumber == 0):
        timestampNumber = 168
    if(fileNumber == 1):
        timestampNumber = 111    
    lower = timestampNumber - span
    upper = timestampNumber + span

    featureCounter = 0
    for i in range(lower, upper):
        # get coordinates of current point
        feat = layer.GetFeature(i)
        # store coordinates in the arrays for the plot
        pt = feat.geometry()
        formulaDensity = float(feat.GetField('formDens'))
        aerialDensity = float(feat.GetField('airDens'))
        difference = (formulaDensity - aerialDensity)
        differenceArr.append(difference)

        featureNumberArr.append(featureCounter - span)
        featureCounter += 1

    f, axarr = plt.subplots(1)

    plt.plot(featureNumberArr, differenceArr)

    plt.xlabel("Track point")
    plt.ylabel("Density")
    plt.axhline(0, color='black')
    plt.ylim(-5, 5)
    plt.xlim(-20, 20)

    plt.title("Comparison of densities for track: " + track_name)

    # plt.legend()
    # plt.tight_layout()

    pngName = "Linechart_Comparison" + track_name + ".png"
    out_path = os.path.join(savePath,
                            pngName)

    plt.savefig(out_path, dpi=300, format="png")
