## Instructions

The following frameworks need to be installed as explained in the lecture: numpy, gdal, matplotlib.
Additionally OpenCV and Scikit learn are required if you want to run the Script1DensemapGenerator, however this will take 
take some time depending on your hardware. If you do not want to create the densemap yourself you can copy it from the
'suppliedDensemap' Folder to the 'output' folder and thus skip Script1DensemapGenerator.py. (Make sure that you copy the .jpg and the .aux file)

When the dependencies are installed, please run the script Script1DensemapGenerator.py and Script2ProcessShapes.py 
to reproduce the project. 

Make sure that you edit the first line of the scripts to match the path of your data directory and note that you need 
to use the data file provided with the code.

If you want to run 'Script2ProcessShapes.py' more than once you have to  copy the shapefiles in 'rawDataSave' to the 'smartphone_data' folder. This is necessary as the script deletes features.

## Installation guide
### OpenCV 

#### Windows
OpenCV requires the following packages:
 -  Python-2.7.x. http://python.org/ftp/python/2.7.5/python-2.7.5.msi
 -  Numpy. (At least version 1.7.1) http://sourceforge.net/projects/numpy/files/NumPy/1.7.1/numpy-1.7.1-win32-superpack-python2.7.exe/download
 -  Matplotlib https://downloads.sourceforge.net/project/matplotlib/matplotlib/matplotlib-1.3.0/matplotlib-1.3.0.win32-py2.7.exe
 -  Download latest OpenCV (Version 3.2.0) release from sourceforge site and double-click to extract it.

Goto opencv/build/python/2.7 folder.
Copy cv2.pyd to C:/Python27/lib/site-packages.

#### Linux, OSX
`Pip install opencv-python`

Check if it is installed correctly:
Open Python IDLE and type following codes in Python terminal.

`import cv2`

`print cv2.__version__`

If the results are printed out without any errors, you have installed OpenCV-Python successfully.
### Scikit learn 
#### Windows
1. Open the following page: http://www.lfd.uci.edu/~gohlke/pythonlibs/#scikit-image
2. Search for ‘Scikit Image’
3. Download scikit_image‑0.13.0‑cp27‑cp27m‑win32.whl (Python 2.7.x)
4. Install this .whl file with the command
 `pip install C:/your-dir/scikit_name-file.whl`

#### Linux, OSX
1. `pip install -U scikit-image`
