# NII Converter

A lightweight tool specifically designed to convert `.nii` files (especially from ImageJ) to compressed `.nii.gz` format while automatically fixing common issues.

## What it does

- ✅ Converts `.nii` → `.nii.gz`
- ✅ Fixes signed arrays (adds offset of 32768 if negative values detected)
- ✅ Handles unit conversion (micron → mm)
- ✅ Fixes temporal voxel size issues
- ✅ Sets appropriate data types (uint32)

## Installation

From the repository root:
```bash
# Install dependencies for all tools
pip install -r requirements.txt

# Or just for NII converter
pip install nibabel numpy tqdm
```

## Usage

### Command Line

```bash
# From repository root
python -m nii_converter.cli image.nii

# Convert all .nii files in a folder
python -m nii_converter.cli input_folder/

# Convert to different output folder
python -m nii_converter.cli input_folder/ output_folder/

# Verbose output to see what fixes are applied
python -m nii_converter.cli image.nii -v

# Overwrite existing files
python -m nii_converter.cli input_folder/ --overwrite
```

### Python Import (Jupyter Notebook)

```python
from nii_converter import convert_file, convert_folder

# Convert single file
result = convert_file('data.nii')
print(f"Success: {result['success']}")

# Convert entire folder
summary = convert_folder('input_data/', 'output_data/')
print(f"Converted {summary['successful']}/{summary['total_files']} files")
```

### Advanced Usage

```python
from nii_converter import convert_nii_file, convert_directory

# Convert single file with detailed info
result = convert_nii_file('meningioma_001_t1.nii')
if result['success']:
    print(f"Original min value: {result['original_min_value']}")
    print(f"Final min value: {result['final_min_value']}")
    print(f"Fixes applied: {result['fixes_applied']}")
    print(f"File size reduction: {result['file_size_reduction']}")

# Convert directory with full control
summary = convert_directory(
    input_dir='./data/raw/',
    output_dir='./data/processed/',
    recursive=True,
    offset=32768.0,
    overwrite=False
)
```

## Example Output

```
$ python -m nii_converter.cli meningioma_data/
INFO: Found 12 .nii files to convert
Converting files: 100%|██████████| 12/12 [00:15<00:00,  1.2s/it]
INFO: Signed array detected (min: -1024.0), applying offset +32768
INFO: Converted voxel units from micron to mm
INFO: ✓ Converted meningioma_001_t1.nii → meningioma_001_t1.nii.gz
...
INFO: Conversion complete: 12 successful, 0 failed, 0 skipped

Conversion Summary:
  Total files: 12
  Successful: 12
  Failed: 0
  Skipped: 0
  Success rate: 100.0%
```

## File Structure Preservation

The tool maintains your folder structure:

```
Before:
input_folder/
├── patient_001/
│   ├── patient_001_t1.nii
│   └── patient_001_t1ce.nii
└── patient_002/
    └── patient_002_t1.nii

After:
output_folder/
├── patient_001/
│   ├── patient_001_t1.nii.gz
│   └── patient_001_t1ce.nii.gz
└── patient_002/
    └── patient_002_t1.nii.gz
```
