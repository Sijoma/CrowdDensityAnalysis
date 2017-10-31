import shutil
import os

# Own Module
import DensityFunctions as denseF


#############
# Change this line to your Project folder
# In this project folder there should be two folders, "images" and "smartphone_data"        
data_dir = os.path.join('/media', 'simon', 'Uni',
                        'SoSe17', 'PIG', 'Projekt', 'EoT_Data')

folderNameOfShapefiles = ('smartphone_data')

# DO NOT EDIT BELOW THIS
# ==============================================================================
# ==============================================================================

outputPath = os.path.join(data_dir, 'output')
# Check if Script 1 was run.
if not os.path.exists(outputPath):
    print "ERROR:Run SCRIPT 1:DensemapGenerator first"
else:
    # Path to the raster
    in_rast = os.path.join(outputPath, 'densemap.jpg')
    # Path to the gps track
    shapefiles = os.path.join(data_dir, folderNameOfShapefiles)
    shapefile1 = 'tp1_17-17-11_nach-abpfiff.shp'
    shapefile2 = 'tp2_17-17-27_nach-abpfiff.shp'
    namesOfShapefiles = [shapefile1, shapefile2]

    # Generate input paths arrays
    in_SHP1 = os.path.join(shapefiles, shapefile1)
    in_SHP2 = os.path.join(shapefiles, shapefile2)
    inShapefiles = [in_SHP1, in_SHP2]
    # Generate output paths array
    out_SHP1 = os.path.join(outputPath, shapefile1)
    out_SHP2 = os.path.join(outputPath, shapefile2)
    outShapefiles = [out_SHP1, out_SHP2]
    # Copy and rename missing prj files
    inputPRJfile = os.path.join(shapefiles, 'tp1_17-17-29_nach-abpfiff.prj')
    outputPRJfile1 = os.path.join(shapefiles, 'tp1_17-17-11_nach-abpfiff.prj')
    outputPRJfile2 = os.path.join(shapefiles, 'tp2_17-17-27_nach-abpfiff.prj')
    # Copy projection
    shutil.copy2(inputPRJfile, outputPRJfile1)
    shutil.copy2(inputPRJfile, outputPRJfile2)

    # Shapefile for-loop -- 
    for i in range(0, (len(inShapefiles))):
        # Calculates speed for the given shapefile
        denseF.CalSpeedToSHP(inShapefiles[i])

    # statistical measurements to find appropriate speed values)
    denseF.percentile(inShapefiles[0], inShapefiles[1])

    for i in range(0, (len(inShapefiles))):
        # Calculates the density out of the speed measurements
        denseF.calcDensityToShp(inShapefiles[i], 'formDens')
        # Reprojects the shapefile to the projection of 'in_rast'
        # and store the SHP file in output folder.
        denseF.reproject(in_rast, inShapefiles[i], outShapefiles[i])
        # Get the aerial density value out of the densemap and write it to the
        # shapefile
        denseF.writePixelsFromRasterToShp(in_rast, outShapefiles[i], 'airDens')

        # Plotting of the values in graph with correct projection,
        # the correct column is choosen depending on the input parameter
        denseF.PlotCalDensity(
            outputPath, outShapefiles[i], namesOfShapefiles[i], "formDens")
        denseF.PlotCalDensity(
            outputPath, outShapefiles[i], namesOfShapefiles[i], "airDens")
        # Plots the absolute difference between both density values
        denseF.compareDensities(
            outputPath, outShapefiles[i], namesOfShapefiles[i])
        # Bar chart for features around specific timestamps
        denseF.plotBarCharts(
            outputPath, outShapefiles[i], namesOfShapefiles[i],i, 10)
        # Line chart for features around specific timestamps
        denseF.plotLineCharts(
            outputPath, outShapefiles[i], namesOfShapefiles[i],i, 18)

    print 'done'
