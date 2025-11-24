// Simple NIFTI.gz Saver
// Saves the currently active image as compressed NIFTI (.nii.gz)
// Bypasses nifti_io.jar compression limitation

// Check if an image is open
if (nImages == 0) {
    exit("No image is currently open. Please open an image first.");
}

// Get current image info
currentTitle = getTitle();
print("Current image: " + currentTitle);

// Get image dimensions for info
getDimensions(width, height, channels, slices, frames);
print("Image dimensions: " + width + "x" + height + "x" + slices);

// Get current voxel size for info
getVoxelSize(pixelWidth, pixelHeight, voxelDepth, unit);
print("Voxel size: " + pixelWidth + " x " + pixelHeight + " x " + voxelDepth + " " + unit);

// Get save location
saveDir = getDirectory("Choose directory to save NIFTI file");
if (saveDir == "") {
    exit("Save cancelled by user.");
}

// Get filename from user
defaultName = replace(defaultName, ".tiff", "");
defaultName = replace(currentTitle, ".tif", "");
defaultName = replace(defaultName, ".nii.gz", "");
defaultName = replace(defaultName, ".nii", "");


fileName = getString("Enter filename (without extension):", defaultName);
if (fileName == "") {
    exit("No filename provided.");
}

// Clean filename - remove extensions if user added them
fileName = replace(fileName, ".nii.gz", "");
fileName = replace(fileName, ".nii", "");

// Generate file paths
niiPath = saveDir + fileName + ".nii";
gzPath = saveDir + fileName + ".nii.gz";

print("Saving to: " + gzPath);

// Check if file already exists
if (File.exists(gzPath)) {
    if (!getBoolean("File " + fileName + ".nii.gz already exists. Overwrite?")) {
        exit("Save cancelled by user.");
    }
}

// Save as uncompressed NIFTI using nifti_io plugin
print("Saving uncompressed NIFTI...");
run("NIfTI-1", "save=[" + niiPath + "]");

// Check if .nii file was created
if (!File.exists(niiPath)) {
    exit("Error: Failed to save NIFTI file. Check if nifti_io plugin is installed.");
}

// Compress using system gzip command
print("Compressing with gzip...");
exec("gzip", niiPath);

// Verify compressed file was created
if (File.exists(gzPath)) {
    print("SUCCESS: Saved as " + fileName + ".nii.gz");
    print("File location: " + saveDir);
    
    // Show file size
    fileSize = round(File.length(gzPath) / 1024 / 1024 * 100) / 100; // MB with 2 decimals
    print("File size: " + fileSize + " MB");
} else {
    print("ERROR: Compression failed. Check if gzip is available on your system.");
    if (File.exists(niiPath)) {
        print("Uncompressed file saved as: " + fileName + ".nii");
    }
}

print("Done.");