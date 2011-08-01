CellProfiler Pipeline: http://www.cellprofiler.org
Version:2
SVNRevision:11052

LoadImages:[module_num:1|svn_version:\'Unknown\'|variable_revision_number:11|show_window:True|notes:\x5B"Load the images by matching files in the folder against the unique text pattern \'.JPG\'"\x5D|batch_state:array(\x5B\x5D, dtype=uint8)]
    File type to be loaded:individual images
    File selection method:Text-Exact match
    Number of images in each group?:3
    Type the text that the excluded images have in common:Do not use
    Analyze all subfolders within the selected folder?:All
    Input image file location:Default Input Folder\x7C.
    Check image sets for missing or duplicate files?:No
    Group images by metadata?:No
    Exclude certain files?:No
    Specify metadata fields to group by:
    Select subfolders to analyze:
    Image count:1
    Text that these images have in common (case-sensitive):.JPG
    Position of this image in each group:t0.JPG
    Extract metadata from where?:None
    Regular expression that finds metadata in the file name:None
    Type the regular expression that finds metadata in the subfolder path:None
    Channel count:1
    Group the movie frames?:No
    Grouping method:Interleaved
    Number of channels per group:2
    Load the input as images or objects?:Images
    Name this loaded image:Orig
    Name this loaded object:Nuclei
    Retain outlines of loaded objects?:No
    Name the outline image:NucleiOutlines
    Channel number:1
    Rescale intensities?:Yes

ColorToGray:[module_num:2|svn_version:\'Unknown\'|variable_revision_number:2|show_window:True|notes:\x5B\'Combine the color image into a grayscale image.\'\x5D|batch_state:array(\x5B\x5D, dtype=uint8)]
    Select the input image:Orig
    Conversion method:Combine
    Image type\x3A:RGB
    Name the output image:Gray
    Relative weight of the red channel:1
    Relative weight of the green channel:1
    Relative weight of the blue channel:1
    Convert red to gray?:Yes
    Name the output image:OrigRed
    Convert green to gray?:Yes
    Name the output image:OrigGreen
    Convert blue to gray?:Yes
    Name the output image:OrigBlue
    Channel count:1
    Channel number\x3A:Red\x3A 1
    Relative weight of the channel:1
    Image name\x3A:Channel1

Smooth:[module_num:3|svn_version:\'Unknown\'|variable_revision_number:1|show_window:True|notes:\x5B\'Smooth the image using a Gaussian filter.\'\x5D|batch_state:array(\x5B\x5D, dtype=uint8)]
    Select the input image:Gray
    Name the output image:Corr
    Select smoothing method:Gaussian Filter
    Calculate artifact diameter automatically?:No
    Typical artifact diameter, in  pixels:20
    Edge intensity difference:0.1

IdentifyPrimaryObjects:[module_num:4|svn_version:\'Unknown\'|variable_revision_number:9|show_window:True|notes:\x5B\'Identify the tissue region using three-class Otsu.\'\x5D|batch_state:array(\x5B\x5D, dtype=uint8)]
    Select the input image:Corr
    Name the primary objects to be identified:Tissue
    Typical diameter of objects, in pixel units (Min,Max):10,40
    Discard objects outside the diameter range?:No
    Try to merge too small objects with nearby larger objects?:No
    Discard objects touching the border of the image?:No
    Select the thresholding method:Otsu Global
    Threshold correction factor:1.0
    Lower and upper bounds on threshold:0.000000,1.000000
    Approximate fraction of image covered by objects?:0.01
    Method to distinguish clumped objects:None
    Method to draw dividing lines between clumped objects:Intensity
    Size of smoothing filter:10
    Suppress local maxima that are closer than this minimum allowed distance:7
    Speed up by using lower-resolution image to find local maxima?:Yes
    Name the outline image:Do not use
    Fill holes in identified objects?:No
    Automatically calculate size of smoothing filter?:Yes
    Automatically calculate minimum allowed distance between local maxima?:Yes
    Manual threshold:0.46
    Select binary image:None
    Retain outlines of the identified objects?:No
    Automatically calculate the threshold using the Otsu method?:Yes
    Enter Laplacian of Gaussian threshold:0.5
    Two-class or three-class thresholding?:Three classes
    Minimize the weighted variance or the entropy?:Weighted variance
    Assign pixels in the middle intensity class to the foreground or the background?:Foreground
    Automatically calculate the size of objects for the Laplacian of Gaussian filter?:Yes
    Enter LoG filter diameter:5
    Handling of objects if excessive number of objects identified:Continue
    Maximum number of objects:500
    Select the measurement to threshold with:None
    Method to calculate adaptive window size:Image size
    Size of adaptive window:10

MeasureImageAreaOccupied:[module_num:5|svn_version:\'Unknown\'|variable_revision_number:3|show_window:True|notes:\x5B\'Measure the area occupied by the tissue region.\'\x5D|batch_state:array(\x5B\x5D, dtype=uint8)]
    Hidden:1
    Measure the area occupied in a binary image, or in objects?:Objects
    Select objects to measure:Tissue
    Retain a binary image of the object regions?:No
    Name the output binary image:Stain
    Select a binary image to measure:None
