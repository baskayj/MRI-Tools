# ImageJ Macros for Medical Imaging

Two specialized ImageJ macros for NIFTI file processing and anonymization in medical imaging workflows.

## 📋 Requirements

- **ImageJ/Fiji** with the following plugins:
  - `nifti_io.jar` plugin for NIFTI file support
  - System `gzip` command available in PATH (for compression)

## 🎯 Anonimize.ijm - Batch Face Cutting Tool

Anonymizes medical brain images by removing facial features through automated face cutting across multiple NIFTI files.

### Features

- **Batch Processing**: Processes all NIFTI files in a directory
- **Smart Reference Selection**: Automatically uses T1C (contrast-enhanced T1) files as reference for cutting plane definition
- **Interactive Cutting Plane**: User-defined cutting line in sagittal view with anatomical guidance
- **Voxel Size Standardization**: Automatically converts units to mm (handles micron conversions)
- **3D Plane Cutting**: Applies cutting plane across entire 3D volume following diagonal geometry
- **Compressed Output**: Saves as `.nii.gz` files for efficient storage

### Usage

1. **Launch macro** in ImageJ/Fiji
2. **Select input directory** containing NIFTI files (`.nii` or `.nii.gz`)
3. **Select output directory** for anonymized files
4. **Define cutting plane**:
   - Sagittal view will open (corrected anatomical orientation)
   - Draw a line from top to bottom
   - **Left side = Anterior (face)** - will be blacked out
   - **Right side = Posterior (brain)** - will be preserved
5. **Process automatically** - all files will be anonymized using the same cutting plane

### File Selection Logic

- **Priority**: T1C (contrast-enhanced) files used as reference
- **Fallback**: First available NIFTI file if no T1C found
- **Supported formats**: `.nii`, `.nii.gz`

### Output

- **Format**: Compressed NIFTI (`.nii.gz`)
- **Naming**: Preserves original filenames
- **Location**: User-specified output directory
- **Processing log**: Detailed console output with dimensions and processing steps

---

## 💾 SaveAsNiiGz.ijm - NIFTI Compression Tool

Simple utility for saving the currently active ImageJ image as a compressed NIFTI file, bypassing nifti_io.jar compression limitations.

### Features

- **Single Image Processing**: Works with currently active ImageJ image
- **Automatic Compression**: Uses system gzip for optimal compression
- **User-Friendly Interface**: Interactive filename input with validation
- **Overwrite Protection**: Confirms before overwriting existing files
- **File Size Reporting**: Shows compressed file size in MB

### Usage

1. **Open image** in ImageJ/Fiji
2. **Run macro**
3. **Choose output directory**
4. **Enter filename** (without extension)
5. **Confirm save** - file will be saved as `.nii.gz`

### Technical Details

- **Process**: Saves uncompressed `.nii` first, then compresses with gzip
- **Cleanup**: Automatically removes temporary uncompressed file
- **Validation**: Checks for successful compression before cleanup

---

## 🔧 Installation

1. **Download macros** to your ImageJ macros folder:
   ```
   ImageJ/macros/
   ├── Anonimize.ijm
   └── SaveAsNiiGz.ijm
   ```

2. **Install nifti_io plugin**:
   - Download from [ImageJ Plugin Database](https://imagej.net/plugins/nifti)
   - Place `nifti_io.jar` in `ImageJ/plugins/` folder

3. **Verify gzip availability**:
   ```bash
   # Test gzip command
   gzip --version
   ```

4. **Restart ImageJ/Fiji**

## 📊 Use Cases

### Research Anonymization
- **Batch anonymize** entire datasets for publication
- **Consistent cutting plane** across study participants
- **HIPAA compliance** through facial feature removal

### Clinical Workflows
- **Quick anonymization** of single cases
- **Format standardization** to compressed NIFTI
- **Unit conversion** for multi-scanner data

### Data Sharing
- **Prepare datasets** for public repositories
- **Reduce file sizes** for efficient transfer
- **Maintain imaging quality** while removing identifiers

## ⚠️ Important Notes

### Anatomical Orientation
- **Anonimize.ijm** assumes standard radiological orientation
- **Sagittal view** is automatically corrected for proper anatomical display
- **Cutting line** should follow natural anatomical boundaries

### File Handling
- **Original files** are preserved (never overwritten)
- **Batch processing** uses consistent parameters across all files
- **Error handling** provides detailed console feedback

### System Requirements
- **Sufficient RAM** for large NIFTI files (typically 4GB+ recommended)
- **Disk space** for both original and processed files during batch operations
- **gzip command** must be available in system PATH

## 🐛 Troubleshooting

### Common Issues

**"No NIFTI files found"**
- Verify files have `.nii` or `.nii.gz` extensions
- Check file permissions in input directory

**"Please draw a line selection"**
- Ensure line tool is used (not rectangle or other tools)
- Draw from top to bottom of sagittal view

**"Compression failed"**
- Verify gzip is installed and in PATH
- Check output directory permissions
- Ensure sufficient disk space

**"nifti_io plugin not found"**
- Install nifti_io.jar plugin in ImageJ/plugins/ folder
- Restart ImageJ after installation

### Performance Optimization

- **Close unnecessary images** before batch processing
- **Increase ImageJ memory** allocation for large datasets
- **Use SSD storage** for faster file I/O during batch operations

## 📝 Output Examples

### Anonimize.ijm Console Output
```
Using T1C reference file: patient001_t1c.nii.gz
Original image dimensions: 240x240x155
Processing file 1/4: patient001_t1.nii.gz
  Original voxel size: 1.0 x 1.0 x 1.0 mm
  Converting to 16-bit for processing
  Face cutting completed
  -> Saved: patient001_t1.nii.gz
```

### SaveAsNiiGz.ijm Console Output
```
Current image: brain_scan.tif
Image dimensions: 256x256x180
Voxel size: 1.0 x 1.0 x 1.0 mm
Saving to: /output/brain_anonymized.nii.gz
SUCCESS: Saved as brain_anonymized.nii.gz
File size: 12.5 MB
```