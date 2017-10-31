import os
import shutil
import cv2
from skimage.exposure import rescale_intensity
import numpy as np
from matplotlib import pyplot as plt

# Make sure the 'images' folder is inside your data directory
data_dir = os.path.join('/media', 'simon', 'Uni',
                        'SoSe17', 'PIG', 'Projekt', 'EoT_Data')
                        
# In this project folder there should be two folders, "images" and "smartphone_data"

# Processing takes about 20 minutes
# DO NOT EDIT BELOW THIS
# ==============================================================================
# ==============================================================================
# Kernel convolution function

def convolve(image, kernel):
	(iH, iW) = image.shape[:33]
	(kH, kW) = kernel.shape[:33]
	pad = (kW - 1) / 2
	image = cv2.copyMakeBorder(image, pad, pad, pad, pad,
                            cv2.BORDER_REPLICATE)
	output = np.zeros((iH, iW), dtype="float32")
	max = 0
	min = 0
	for y in np.arange(pad, iH + pad):
		#Process indicator in percentage
		length = y
		complete = float(output.shape[0])
		percent = ((length / complete) * 100)
		print "%10.2f" % percent + "% /done"
		for x in np.arange(pad, iW + pad):

			roi = image[y - pad:y + pad + 1, x - pad:x + pad + 1]
			k = (roi * kernel).sum()
			if (min == 0):
				min = k
			if (max == 0):
				max = k
			if (k > max):
				max = k
			if (k < min):
				min = k

			output[y - pad, x - pad] = k

	return output, max, min

kernel = np.ones((33,33),dtype="float")

# Image from flyover
imagesPath = os.path.join(data_dir, 'images')

if not os.path.exists(imagesPath):
	print "ERROR:404"
	print "Your folder structure is wrong, make sure that there is an 'images' and 'smartphone_data' folder in your data dir"
	print "and it also contains the provided data"
else:
	inputImage = os.path.join(imagesPath, 'Geo_MOS0148.jpg')
	img = cv2.imread(inputImage, 0)
	# Canny Edge Detection by OpenCV
	edges = cv2.Canny(img, 65, 85)

	# Kernel Convolution over result of edge detection
	output, max, min = convolve(edges, kernel)

	# rescale the output image to be in the range [0, 255]
	output = rescale_intensity(output, in_range=(min, max))
	output = (output * 255).astype("uint8")

	# COLORMAP
	# output = cv2.applyColorMap(output,cv2.COLORMAP_JET)

	inputAuxFile = os.path.join(data_dir, 'images', 'Geo_MOS0148.jpg.aux.xml')
	outputPath = os.path.join(data_dir, 'output')
	outputAuxFile = os.path.join(outputPath, 'densemap.jpg.aux.xml')

	# Create Folders
	if not os.path.exists(outputPath):
		os.makedirs(outputPath)
	#Spatial reference Copy
	shutil.copy2(inputAuxFile, outputAuxFile)

	# write to file
	outputDensemap = os.path.join(outputPath, 'densemap.jpg')
	cv2.imwrite(outputDensemap, output)
	print 'done'
	
	# # Plotting
	# plt.subplot(121), plt.imshow(img, cmap='gray')
	# plt.title('input image'), plt.xticks([]), plt.yticks([])
	# plt.subplot(122), plt.imshow(output, cmap='gray')
	# plt.title('Dense map'), plt.xticks([]), plt.yticks([])
	# plt.show()




