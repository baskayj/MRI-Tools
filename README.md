# Medical Imaging Tools

A collection of specialized tools for medical imaging processing and analysis, designed to handle edge cases where standard tools like CaPTk fail or need supplementation.

## Tools Included

### 📄 NII Converter
Convert ImageJ `.nii` exports to compressed `.nii.gz` format with automatic fixes for common issues.

**Key Features:**
- Handles signed arrays (ImageJ export issue)
- Unit conversion (micron → mm) 
- Format standardization
- File size reduction (50-70%)

### 🎯 Custom Registration Tool
Alternative image registration when CaPTk registration fails or produces suboptimal results.

**Use Cases:**
- Difficult anatomical cases
- Non-standard image orientations
- When CaPTk preprocessing fails
- Custom registration workflows

### 🔬 Fractal Analysis Tool
Advanced fractal analysis for tumor characterization using geometric and texture measurements.

**Key Features:**
- Fractal dimension (FD) on segmentations (geometric complexity)
- Lacunarity (LD) on image intensities (texture heterogeneity)
- Multi-modal support (T1, T1CE, T2, FLAIR)
- Publication-ready statistics and plots
- Batch processing for research datasets

### 🖼️ ImageJ Macros
Specialized ImageJ macros for NIFTI processing and anonymization workflows.

**Key Features:**
- **Anonimize.ijm**: Batch face cutting for patient anonymization
- **SaveAsNiiGz.ijm**: Compressed NIFTI export utility
- Interactive cutting plane definition
- Automatic voxel size standardization
- HIPAA-compliant anonymization

## Installation

```bash
# Clone the repository
git clone https://emk.semmelweis.hu/gitea/baskay.janos/MRI-Tools.git
cd mri-tools

# Install dependencies
pip install -r requirements.txt

# Test installation
python -m nii_converter.cli --help
```

### ImageJ Macros Setup

For the ImageJ macros, additional setup is required:

1. **Install nifti_io plugin** in ImageJ/Fiji
2. **Ensure gzip** is available in system PATH
3. **Copy macros** to ImageJ macros folder
4. See detailed setup in `imagej_macros/README.md`

## Repository Structure

```
mri-tools/
├── nii_converter/          # ImageJ .nii → .nii.gz conversion
├── registration_tool/      # Custom registration algorithm
├── fractal_analysis/       # Fractal and Lacunarity measurements
├── imagej_macros/          # ImageJ macros for NIFTI processing
│   ├── Anonimize.ijm      # Batch face cutting tool
│   ├── SaveAsNiiGz.ijm    # NIFTI compression utility
│   └── README.md          # Detailed macro documentation
└── archive/                # Old code from previous projects
```

## Tool Selection Guide

| Task | Recommended Tool | Alternative |
|------|------------------|-------------|
| Format conversion | NII Converter | Manual nibabel |
| Standard registration | CaPTk | Custom Registration Tool |
| Difficult registration | Custom Registration Tool | — |
| Preprocessing | CaPTk → NII Converter | — |
| **Patient anonymization** | **Anonimize.ijm** | **Manual face cutting** |
| **NIFTI compression** | **SaveAsNiiGz.ijm** | **Command line gzip** |
| **Interactive NIFTI export** | **SaveAsNiiGz.ijm** | **Manual conversion** |

# Citation

If you use our tools in your research, please cite:

```
Markia, B., Mezei, T., Báskay, J. et al. Consistency and grade prediction of 
intracranial meningiomas based on fractal geometry analysis. Neurosurg Rev 48, 
598 (2025). https://doi.org/10.1007/s10143-025-03737-1
```