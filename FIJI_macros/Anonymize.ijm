// ImageJ Macro for Face Cutting Multiple NIFTI Files
// This macro processes all NIFTI files in a folder and applies the same face cut

// Get input and output directories
inputDir = getDirectory("Choose input directory with NIFTI files");
outputDir = getDirectory("Choose output directory");

// Get list of NIFTI files
fileList = getFileList(inputDir);
niftiFiles = newArray();
count = 0;
for (i = 0; i < fileList.length; i++) {
    if (endsWith(fileList[i], ".nii") || endsWith(fileList[i], ".nii.gz")) {
        niftiFiles[count] = fileList[i];
        count++;
    }
}

if (count == 0) {
    exit("No NIFTI files found in directory");
}

// Find reference file - prefer T1C (contrast-enhanced T1)
referenceFile = "";
for (i = 0; i < count; i++) {
    fileName = toLowerCase(niftiFiles[i]);
    if (indexOf(fileName, "t1c") >= 0) {
        referenceFile = niftiFiles[i];
        break;
    }
}

// If no T1C found, use first file
if (referenceFile == "") {
    referenceFile = niftiFiles[0];
    print("No T1C file found, using: " + referenceFile);
} else {
    print("Using T1C reference file: " + referenceFile);
}

// Open reference file with nifti_io.jar plugin
print("Opening reference file to define cutting plane...");
run("NIfTI-Analyze", "open=[" + inputDir + referenceFile + "]");
firstImage = getTitle();

// Get image dimensions
getDimensions(width, height, channels, slices, frames);
print("Original image dimensions: " + width + "x" + height + "x" + slices);

// Create sagittal reslice for cutting plane definition
print("Creating sagittal view for cutting plane selection...");
run("Reslice [/]...", "output=1.000 start=Left avoid");
sagittalImage = getTitle();

// Fix sagittal orientation - flip vertically to get correct anatomical view
selectWindow(sagittalImage);
run("Flip Vertically", "stack");
run("Enhance Contrast", "saturated=0.35");
getDimensions(sagWidth, sagHeight, sagChannels, sagSlices, sagFrames);

// Instructions in log window
print("=== INSTRUCTIONS ===");
print("SAGITTAL VIEW: Side view of the brain (corrected orientation)");
print("LEFT side = ANTERIOR (face region)");
print("RIGHT side = POSTERIOR (back of head)");
print("Draw a STRAIGHT LINE from top to bottom");
print("Everything LEFT of your line will be turned BLACK");
print("The line can be diagonal to follow anatomy");

// Set line tool and wait for user input
setTool("line");
waitForUser("Define Cutting Plane", 
    "SAGITTAL VIEW - Draw cutting line:\n \n" +
    "* LEFT = ANTERIOR (face) - will be BLACKED OUT\n" +
    "* RIGHT = POSTERIOR (brain) - will be KEPT\n" +
    "* Draw a line from TOP to BOTTOM\n" +
    "Click OK after drawing the line.");

// Get line selection
if (selectionType() != 5) { // 5 = line selection
    exit("Please draw a line selection and try again.");
}

getSelectionCoordinates(lineX, lineY);
if (lineX.length < 2) {
    exit("Invalid line selection. Please try again.");
}

// Store line coordinates for proper plane calculation
// In sagittal view: X = anterior-posterior (original Y), Y = superior-inferior (original Z)
startX = lineX[0];
startY = lineY[0];
endX = lineX[lineX.length-1];
endY = lineY[lineY.length-1];

print("Cutting line: from (" + startX + "," + startY + ") to (" + endX + "," + endY + ")");
print("This defines a cutting PLANE through the 3D volume");

// Close visualization images
close(sagittalImage);
close(firstImage);

// Process all files
for (i = 0; i < count; i++) {
    print("Processing file " + (i+1) + "/" + count + ": " + niftiFiles[i]);
    
    // Open with nifti_io.jar plugin
    run("NIfTI-Analyze", "open=[" + inputDir + niftiFiles[i] + "]");
    currentImage = getTitle();
    
    // Get current voxel size and unit
    getVoxelSize(pixelWidth, pixelHeight, voxelDepth, unit);
    print("  Original voxel size: " + pixelWidth + " x " + pixelHeight + " x " + voxelDepth + " " + unit);
    
    // Standardize to mm units
    newPixelWidth = pixelWidth;
    newPixelHeight = pixelHeight;
    newVoxelDepth = voxelDepth;
    
    if (unit == "micron" || unit == "µm") {
        // Convert from microns to mm (divide by 1000)
        newPixelWidth = pixelWidth / 1000;
        newPixelHeight = pixelHeight / 1000;
        newVoxelDepth = voxelDepth / 1000;
        print("  Converting from microns to mm");
    } else if (unit == "pixel" || unit == "" || unit == "pixels") {
        // Check if values suggest microns (>10) or mm scale (≤10)
        if (pixelWidth > 10 || pixelHeight > 10 || voxelDepth > 10) {
            // Likely micron values stored as pixels - convert to mm
            newPixelWidth = pixelWidth / 1000;
            newPixelHeight = pixelHeight / 1000;
            newVoxelDepth = voxelDepth / 1000;
            print("  Converting from pixel units (assuming microns) to mm");
        } else {
            // Likely already mm scale - just change unit
            print("  Setting unit to mm (values appear to be mm scale already)");
        }
    } else if (unit == "mm") {
        print("  Already in mm - no conversion needed");
    } else {
        // Unknown unit - make educated guess based on values
        if (pixelWidth > 10 || pixelHeight > 10 || voxelDepth > 10) {
            newPixelWidth = pixelWidth / 1000;
            newPixelHeight = pixelHeight / 1000;
            newVoxelDepth = voxelDepth / 1000;
            print("  Unknown unit '" + unit + "' with large values - assuming microns, converting to mm");
        } else {
            print("  Unknown unit '" + unit + "' with small values - assuming mm scale");
        }
    }
    
    // Set standardized voxel size in mm
    setVoxelSize(newPixelWidth, newPixelHeight, newVoxelDepth, "mm");
    print("  Standardized voxel size: " + newPixelWidth + " x " + newPixelHeight + " x " + newVoxelDepth + " mm");
    
    // Convert to 16-bit for consistent processing
    print("  Converting to 16-bit for processing");
    run("16-bit");
    
    // Get dimensions for face cutting
    getDimensions(w, h, c, s, f);
    
    // Black out anterior region following the cutting plane
    for (slice = 1; slice <= s; slice++) {
        setSlice(slice);
        
        // Calculate cutting Y-coordinate for this specific Z-slice
        // IMPORTANT: Account for the vertical flip we applied to sagittal view
        sliceZ = slice - 1; // 0-based slice number (0 = inferior, s-1 = superior)
        
        // Map to flipped sagittal coordinates 
        // After flip: sagittalY=0 is superior, sagittalY=sagHeight is inferior
        sagittalY = (s - 1 - sliceZ) * sagHeight / s;
        
        // Linear interpolation along the cutting line to find cutting X (which maps to original Y)
        if (endY != startY) {
            // Calculate where the cutting line intersects this Z-level
            t = (sagittalY - startY) / (endY - startY);
            // Clamp t between 0 and 1
            if (t < 0) t = 0;
            if (t > 1) t = 1;
            cutY = startX + t * (endX - startX);
        } else {
            // Horizontal line - use average
            cutY = (startX + endX) / 2;
        }
        
        cutY = round(cutY);
        // Ensure cutY is within valid range
        if (cutY < 0) cutY = 0;
        if (cutY >= h) cutY = h - 1;
        
        // Black out anterior region for this slice
        if (cutY > 0) {
            makeRectangle(0, 0, w, cutY);
            run("Set...", "value=0 slice");
        }
    }
    run("Select None");
    print("  Face cutting completed");
    
    // Generate output filename 
    baseName = replace(niftiFiles[i], ".nii.gz", "");
    baseName = replace(baseName, ".nii", "");
    niiPath = outputDir + baseName + ".nii";
    gzPath = outputDir + baseName + ".nii.gz";
    
    // Save as uncompressed NIFTI using nifti_io
    run("NIfTI-1", "save=[" + niiPath + "]");
    
    // Compress the file using system gzip command
    exec("gzip", niiPath);
    
    // Close current image
    close();
    print("  -> Saved: " + baseName + ".nii.gz");
}

print("");
print("=== PROCESSING COMPLETE ===");
print("Files processed: " + count);
print("Output directory: " + outputDir);
print("Cutting plane: from (" + startX + "," + startY + ") to (" + endX + "," + endY + ")");
print("Method: 3D plane-based blackout (follows diagonal cutting line)");