CellProfiler Pipeline: http://www.cellprofiler.org
Version:2
SVNRevision:11052

LoadImages:[module_num:1|svn_version:\'Unknown\'|variable_revision_number:11|show_window:False|notes:\x5B\'Load the images by matching files in the folder against the unique text pattern for each stain\x3A D.TIF for DAPI, F.TIF for the FITC image, R.TIF for the rhodamine image. The three images together comprise an image set.\'\x5D|batch_state:array(\x5B\x5D, dtype=uint8)]
    File type to be loaded:individual images
    File selection method:Text-Exact match
    Number of images in each group?:3
    Type the text that the excluded images have in common:Do not use
    Analyze all subfolders within the selected folder?:None
    Input image file location:Default Input Folder\x7C.
    Check image sets for missing or duplicate files?:No
    Group images by metadata?:No
    Exclude certain files?:No
    Specify metadata fields to group by:
    Select subfolders to analyze:
    Image count:3
    Text that these images have in common (case-sensitive):D.TIF
    Position of this image in each group:D.TIF
    Extract metadata from where?:None
    Regular expression that finds metadata in the file name:None
    Type the regular expression that finds metadata in the subfolder path:None
    Channel count:1
    Group the movie frames?:No
    Grouping method:Interleaved
    Number of channels per group:2
    Load the input as images or objects?:Images
    Name this loaded image:OrigBlue
    Name this loaded object:Nuclei
    Retain outlines of loaded objects?:No
    Name the outline image:NucleiOutlines
    Channel number:1
    Rescale intensities?:Yes
    Text that these images have in common (case-sensitive):F.TIF
    Position of this image in each group:F.T
    Extract metadata from where?:None
    Regular expression that finds metadata in the file name:None
    Type the regular expression that finds metadata in the subfolder path:None
    Channel count:1
    Group the movie frames?:No
    Grouping method:Interleaved
    Number of channels per group:2
    Load the input as images or objects?:Images
    Name this loaded image:OrigGreen
    Name this loaded object:Nuclei
    Retain outlines of loaded objects?:No
    Name the outline image:NucleiOutlines
    Channel number:1
    Rescale intensities?:Yes
    Text that these images have in common (case-sensitive):R.TIF
    Position of this image in each group:R.T
    Extract metadata from where?:None
    Regular expression that finds metadata in the file name:None
    Type the regular expression that finds metadata in the subfolder path:None
    Channel count:1
    Group the movie frames?:No
    Grouping method:Interleaved
    Number of channels per group:2
    Load the input as images or objects?:Images
    Name this loaded image:OrigRed
    Name this loaded object:Nuclei
    Retain outlines of loaded objects?:No
    Name the outline image:NucleiOutlines
    Channel number:1
    Rescale intensities?:Yes

Crop:[module_num:2|svn_version:\'Unknown\'|variable_revision_number:2|show_window:False|notes:\x5B\'Crop the DAPI image down to a 200 x 200 rectangle by entering specific coordinates.\'\x5D|batch_state:array(\x5B\x5D, dtype=uint8)]
    Select the input image:OrigBlue
    Name the output image:CropBlue
    Select the cropping shape:Rectangle
    Select the cropping method:Coordinates
    Apply which cycle\'s cropping pattern?:First
    Left and right rectangle positions:501,700
    Top and bottom rectangle positions:251,450
    Coordinates of ellipse center:200,500
    Ellipse radius, X direction:400
    Ellipse radius, Y direction:200
    Use Plate Fix?:No
    Remove empty rows and columns?:Edges
    Select the masking image:None
    Select the image with a cropping mask:None
    Select the objects:None

Crop:[module_num:3|svn_version:\'Unknown\'|variable_revision_number:2|show_window:False|notes:\x5B\'Use the same cropping from the DAPI image for the FITC image.\'\x5D|batch_state:array(\x5B\x5D, dtype=uint8)]
    Select the input image:OrigGreen
    Name the output image:CropGreen
    Select the cropping shape:Previous cropping
    Select the cropping method:Coordinates
    Apply which cycle\'s cropping pattern?:First
    Left and right rectangle positions:300,600
    Top and bottom rectangle positions:300,600
    Coordinates of ellipse center:500,500
    Ellipse radius, X direction:400
    Ellipse radius, Y direction:200
    Use Plate Fix?:No
    Remove empty rows and columns?:Edges
    Select the masking image:None
    Select the image with a cropping mask:CropBlue
    Select the objects:None

Crop:[module_num:4|svn_version:\'Unknown\'|variable_revision_number:2|show_window:False|notes:\x5B\'Use the same cropping from the DAPI image for the rhodamine image.\'\x5D|batch_state:array(\x5B\x5D, dtype=uint8)]
    Select the input image:OrigRed
    Name the output image:CropRed
    Select the cropping shape:Previous cropping
    Select the cropping method:Coordinates
    Apply which cycle\'s cropping pattern?:First
    Left and right rectangle positions:300,600
    Top and bottom rectangle positions:300,600
    Coordinates of ellipse center:500,500
    Ellipse radius, X direction:400
    Ellipse radius, Y direction:200
    Use Plate Fix?:No
    Remove empty rows and columns?:Edges
    Select the masking image:None
    Select the image with a cropping mask:CropBlue
    Select the objects:None

IdentifyPrimaryObjects:[module_num:5|svn_version:\'Unknown\'|variable_revision_number:9|show_window:False|notes:\x5B\'Identify the nuclei from the DAPI image. Three-class thresholding performs better than the default two-class thresholding in this case.\'\x5D|batch_state:array(\x5B\x5D, dtype=uint8)]
    Select the input image:CropBlue
    Name the primary objects to be identified:Nuclei
    Typical diameter of objects, in pixel units (Min,Max):10,40
    Discard objects outside the diameter range?:Yes
    Try to merge too small objects with nearby larger objects?:No
    Discard objects touching the border of the image?:Yes
    Select the thresholding method:Otsu Global
    Threshold correction factor:1.0
    Lower and upper bounds on threshold:0,1
    Approximate fraction of image covered by objects?:0.2
    Method to distinguish clumped objects:Intensity
    Method to draw dividing lines between clumped objects:Intensity
    Size of smoothing filter:10
    Suppress local maxima that are closer than this minimum allowed distance:5
    Speed up by using lower-resolution image to find local maxima?:Yes
    Name the outline image:None
    Fill holes in identified objects?:Yes
    Automatically calculate size of smoothing filter?:Yes
    Automatically calculate minimum allowed distance between local maxima?:Yes
    Manual threshold:0.0
    Select binary image:MoG Global
    Retain outlines of the identified objects?:No
    Automatically calculate the threshold using the Otsu method?:Yes
    Enter Laplacian of Gaussian threshold:.5
    Two-class or three-class thresholding?:Three classes
    Minimize the weighted variance or the entropy?:Weighted variance
    Assign pixels in the middle intensity class to the foreground or the background?:Background
    Automatically calculate the size of objects for the Laplacian of Gaussian filter?:Yes
    Enter LoG filter diameter:5
    Handling of objects if excessive number of objects identified:Continue
    Maximum number of objects:500
    Select the measurement to threshold with:None
    Method to calculate adaptive window size:Image size
    Size of adaptive window:10

IdentifySecondaryObjects:[module_num:6|svn_version:\'Unknown\'|variable_revision_number:8|show_window:False|notes:\x5B\'Identify the cells by using the nuclei as a "seed" region, then growing outwards until stopped by the image threshold or by a neighbor. The Propagation method is used to delineate the boundary between neighboring cells.\'\x5D|batch_state:array(\x5B\x5D, dtype=uint8)]
    Select the input objects:Nuclei
    Name the objects to be identified:Cells
    Select the method to identify the secondary objects:Propagation
    Select the input image:CropGreen
    Select the thresholding method:Otsu Global
    Threshold correction factor:1
    Lower and upper bounds on threshold:0,1
    Approximate fraction of image covered by objects?:10%
    Number of pixels by which to expand the primary objects:10
    Regularization factor:0.05
    Name the outline image:Do not use
    Manual threshold:0
    Select binary image:Do not use
    Retain outlines of the identified secondary objects?:No
    Two-class or three-class thresholding?:Two classes
    Minimize the weighted variance or the entropy?:Weighted variance
    Assign pixels in the middle intensity class to the foreground or the background?:Foreground
    Discard secondary objects that touch the edge of the image?:No
    Discard the associated primary objects?:No
    Name the new primary objects:FilteredNuclei
    Retain outlines of the new primary objects?:No
    Name the new primary object outlines:FilteredNucleiOutlines
    Select the measurement to threshold with:None
    Fill holes in identified objects?:Yes
    Method to calculate adaptive window size:Image size
    Size of adaptive window:10

IdentifyTertiaryObjects:[module_num:7|svn_version:\'Unknown\'|variable_revision_number:1|show_window:False|notes:\x5B\'Identify the cytoplasm by "subtracting" the nuclei objects from the cell objects.\'\x5D|batch_state:array(\x5B\x5D, dtype=uint8)]
    Select the larger identified objects:Cells
    Select the smaller identified objects:Nuclei
    Name the tertiary objects to be identified:Cytoplasm
    Name the outline image:Do not use
    Retain outlines of the tertiary objects?:No

MeasureObjectSizeShape:[module_num:8|svn_version:\'1\'|variable_revision_number:1|show_window:False|notes:\x5B\'Measure morphological features from the cell, nuclei and cytoplasm objects.\'\x5D|batch_state:array(\x5B\x5D, dtype=uint8)]
    Select objects to measure:Cells
    Select objects to measure:Nuclei
    Select objects to measure:Cytoplasm
    Calculate the Zernike features?:No

MeasureObjectIntensity:[module_num:9|svn_version:\'Unknown\'|variable_revision_number:3|show_window:False|notes:\x5B\'Measure intensity features from nuclei and cell objects against the cropped DAPI image.\'\x5D|batch_state:array(\x5B\x5D, dtype=uint8)]
    Hidden:1
    Select an image to measure:CropBlue
    Select objects to measure:Nuclei
    Select objects to measure:Cells
    Select objects to measure:Cytoplasm

MeasureTexture:[module_num:10|svn_version:\'1\'|variable_revision_number:2|show_window:False|notes:\x5B\'Measure texture features of the nuclei, cells and cytoplasm from the cropped DAPI image.\'\x5D|batch_state:array(\x5B\x5D, dtype=uint8)]
    Hidden:1
    Hidden:3
    Hidden:1
    Select an image to measure:CropBlue
    Select objects to measure:Nuclei
    Select objects to measure:Cells
    Select objects to measure:Cytoplasm
    Texture scale to measure:3
    Measure Gabor features?:Yes
    Number of angles to compute for Gabor:4

MeasureObjectNeighbors:[module_num:11|svn_version:\'Unknown\'|variable_revision_number:2|show_window:False|notes:\x5B\'Obtain the nuclei neighborhood measures, considering nuclei within 4 pixels in any direction as a neighbor.\'\x5D|batch_state:array(\x5B\x5D, dtype=uint8)]
    Select objects to measure:Nuclei
    Select neighboring objects to measure:Nuclei
    Method to determine neighbors:Within a specified distance
    Neighbor distance:4
    Retain the image of objects colored by numbers of neighbors for use later in the pipeline (for example, in SaveImages)?:No
    Name the output image:Do not use
    Select colormap:Default
    Retain the image of objects colored by percent of touching pixels for use later in the pipeline (for example, in SaveImages)?:No
    Name the output image:PercentTouching
    Select a colormap:Default

MeasureCorrelation:[module_num:12|svn_version:\'Unknown\'|variable_revision_number:2|show_window:False|notes:\x5B\'Measure the pixel intensity correlation between the pixels in the nuclei objects in the cropped DAPI and FITC images, as well as the entire image.\'\x5D|batch_state:array(\x5B\x5D, dtype=uint8)]
    Hidden:2
    Hidden:1
    Select an image to measure:CropBlue
    Select an image to measure:CropGreen
    Select where to measure correlation:Both
    Select an object to measure:Nuclei

MeasureImageIntensity:[module_num:13|svn_version:\'Unknown\'|variable_revision_number:2|show_window:False|notes:\x5B\'Measure the image intensity from the cropped DAPI image.\'\x5D|batch_state:array(\x5B\x5D, dtype=uint8)]
    Select the image to measure:CropBlue
    Measure the intensity only from areas enclosed by objects?:No
    Select the input objects:None

MeasureImageQuality:[module_num:14|svn_version:\'Unknown\'|variable_revision_number:4|show_window:False|notes:\x5B\'Obtain some measurements for quality control purposes.\'\x5D|batch_state:array(\x5B\x5D, dtype=uint8)]
    Calculate metrics for which images?:Select...
    Image count:3
    Scale count:1
    Threshold count:1
    Scale count:1
    Threshold count:1
    Scale count:1
    Threshold count:1
    Select the images to measure:OrigBlue
    Include the image rescaling value?:Yes
    Calculate blur metrics?:Yes
    Spatial scale for blur measurements:20
    Calculate saturation metrics?:Yes
    Calculate intensity metrics?:Yes
    Calculate thresholds?:Yes
    Use all thresholding methods?:No
    Select a thresholding method:Otsu Global
    Typical fraction of the image covered by objects:0.1
    Two-class or three-class thresholding?:Two classes
    Minimize the weighted variance or the entropy?:Weighted variance
    Assign pixels in the middle intensity class to the foreground or the background?:Foreground
    Select the images to measure:OrigGreen
    Include the image rescaling value?:Yes
    Calculate blur metrics?:Yes
    Spatial scale for blur measurements:20
    Calculate saturation metrics?:Yes
    Calculate intensity metrics?:Yes
    Calculate thresholds?:Yes
    Use all thresholding methods?:No
    Select a thresholding method:Otsu Global
    Typical fraction of the image covered by objects:0.1
    Two-class or three-class thresholding?:Two classes
    Minimize the weighted variance or the entropy?:Weighted variance
    Assign pixels in the middle intensity class to the foreground or the background?:Foreground
    Select the images to measure:OrigRed
    Include the image rescaling value?:Yes
    Calculate blur metrics?:Yes
    Spatial scale for blur measurements:20
    Calculate saturation metrics?:Yes
    Calculate intensity metrics?:Yes
    Calculate thresholds?:Yes
    Use all thresholding methods?:No
    Select a thresholding method:Otsu Global
    Typical fraction of the image covered by objects:0.1
    Two-class or three-class thresholding?:Two classes
    Minimize the weighted variance or the entropy?:Weighted variance
    Assign pixels in the middle intensity class to the foreground or the background?:Foreground

CalculateMath:[module_num:15|svn_version:\'Unknown\'|variable_revision_number:1|show_window:False|notes:\x5B\'Compute a ratio of nuclei mean intensity to nuclear area for each nucleus.\'\x5D|batch_state:array(\x5B\x5D, dtype=uint8)]
    Name the output measurement:Ratio
    Operation:Divide
    Select the numerator measurement type:Object
    Select the numerator objects:Nuclei
    Select the numerator measurement:Intensity_MeanIntensity_CropBlue
    Multiply the above operand by:1.0
    Raise the power of above operand by:1.0
    Select the denominator measurement type:Object
    Select the denominator objects:Nuclei
    Select the denominator measurement:AreaShape_Area
    Multiply the above operand by:1.0
    Raise the power of above operand by:1.0
    Take log10 of result?:No
    Multiply the result by:1.0
    Raise the power of result by:1.0

ClassifyObjects:[module_num:16|svn_version:\'Unknown\'|variable_revision_number:2|show_window:False|notes:\x5B\'Classify the nuclei on the basis of area. Divide the areas into 3 bins and give each bin a name.\'\x5D|batch_state:array(\x5B\x5D, dtype=uint8)]
    Should each classification decision be based on a single measurement or on the combination of a pair of measurements?:Single measurement
    Hidden:1
    Select the object to be classified:Nuclei
    Select the measurement to classify by:AreaShape_Area
    Select bin spacing:Evenly spaced bins
    Number of bins:3
    Lower threshold:350
    Use a bin for objects below the threshold?:No
    Upper threshold:700
    Use a bin for objects above the threshold?:No
    Enter the custom thresholds separating the values between bins:0,1
    Give each bin a name?:Yes
    Enter the bin names separated by commas:Small,Medium,Large
    Retain an image of the objects classified by their measurements, for use later in the pipeline (for example, in SaveImages)?:No
    Name the output image:Do not use
    Enter the object name:Nuclei
    Select the first measurement:None
    Method to select the cutoff:Mean
    Enter the cutoff value:.5
    Select the second measurement:None
    Method to select the cutoff:Mean
    Enter the cutoff value:.5
    Use custom names for the bins?:No
    Enter the low-low bin name:LowLow
    Enter the low-high bin name:HighLow
    Enter the high-low bin name:LowHigh
    Enter the high-high bin name:HighHigh
    Retain an image of the objects classified by their measurements, for use later in the pipeline (for example, in SaveImages)?:No
    Enter the image name:ClassifiedNuclei

GrayToColor:[module_num:17|svn_version:\'Unknown\'|variable_revision_number:2|show_window:False|notes:\x5B\'Combine the cropped grayscale channels into a color RGB image.\'\x5D|batch_state:array(\x5B\x5D, dtype=uint8)]
    Select a color scheme:RGB
    Select the input image to be colored red:CropRed
    Select the input image to be colored green:CropGreen
    Select the input image to be colored blue:CropBlue
    Name the output image:RGBImage
    Relative weight for the red image:1
    Relative weight for the green image:1
    Relative weight for the blue image:1
    Select the input image to be colored cyan:None
    Select the input image to be colored magenta:None
    Select the input image to be colored yellow:None
    Select the input image that determines brightness:None
    Relative weight for the cyan image:1
    Relative weight for the magenta image:1
    Relative weight for the yellow image:1
    Relative weight for the brightness image:1
    Select the input image to add to the stacked image:None

SaveImages:[module_num:18|svn_version:\'Unknown\'|variable_revision_number:7|show_window:False|notes:\x5B\'Save the color image as an 8-bit TIF, appending the text RBG to the original filename of the DAPI image.\'\x5D|batch_state:array(\x5B\x5D, dtype=uint8)]
    Select the type of image to save:Image
    Select the image to save:RGBImage
    Select the objects to save:None
    Select the module display window to save:RGBImage
    Select method for constructing file names:From image filename
    Select image name for file prefix:OrigBlue
    Enter single file name:OrigBlue
    Do you want to add a suffix to the image file name?:Yes
    Text to append to the image name:RGB
    Select file format to use:tif
    Output file location:Default Output Folder\x7CNone
    Image bit depth:8
    Overwrite existing files without warning?:No
    Select how often to save:Every cycle
    Rescale the images? :No
    Save as grayscale or color image?:Grayscale
    Select colormap:gray
    Store file and path information to the saved image?:No
    Create subfolders in the output folder?:No
