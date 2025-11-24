# Registration Tool

Custom image registration using DIPY for cases where CaPTk fails or produces suboptimal results. Performs robust multi-level affine registration with mutual information metric.

## Part of Medical Imaging Tools Repository

This tool provides an alternative to CaPTk registration when:
- CaPTk preprocessing fails
- Registration quality is poor
- Non-standard image orientations
- Difficult anatomical cases

## What it does

- ✅ **Multi-level registration**: Center of mass → Translation → Rigid → Affine
- ✅ **Mutual information metric**: Robust for multi-modal registration
- ✅ **Batch processing**: Handle multiple patients/modalities
- ✅ **Visualization**: Optional overlay plots (requires FURY)

## Usage

### Command Line

```bash
# Register single file (T2 to T1CE)
python -m registration_tool.cli moving_t2.nii.gz reference_t1ce.nii.gz -o registered_t2.nii.gz

# Process patient folder (register T2 to T1CE)
python -m registration_tool.cli --patient-folder patient_001/ --reference t1ce --modalities t2
```

### Python Import (Jupyter Notebook)

```python
from registration_tool import register_file, register_modalities_to_reference

# Simple file registration
result = register_file('t2.nii.gz', 't1ce.nii.gz', 'registered_t2.nii.gz')
print(f"Registration took {result['elapsed_time']:.1f} seconds")

# Patient folder registration (your typical workflow)
result = register_modalities_to_reference(
    patient_folder='meningioma_0023_no_compat/',
    reference_modality='t1ce',
    modalities=['t2']
)
print(f"Successful: {result['successful']}, Failed: {result['failed']}")
```

### Advanced Usage

```python
from registration_tool import affine_registration, RegistrationConfig

# Custom registration parameters
config = RegistrationConfig()
config.level_iters = [15000, 2000, 200]  # More iterations for difficult cases
config.nbins = 64  # Higher resolution for mutual information
config.show_plots = True

result = affine_registration(
    moving_file='difficult_t2.nii.gz',
    static_file='reference_t1ce.nii.gz', 
    output_file='registered_t2.nii.gz',
    config=config
)

# Access transformation matrices
print(f"Final affine transform:\n{result['affine_transform']}")
```

## Registration Process

The tool performs these steps automatically:

1. **Load Images**: Handles 3D/4D NIfTI files
2. **Center of Mass**: Initial alignment based on image centers
3. **Translation**: Optimize translation parameters
4. **Rigid**: Add rotation (6 DOF total)
5. **Affine**: Full 12-parameter affine transform
6. **Apply Transform**: Generate registered image
7. **Save Result**: Output in NIfTI format

## Configuration Options

### Registration Parameters
- `nbins`: Mutual information histogram bins (default: 32)
- `level_iters`: Iterations per level (default: [10000, 1000, 100])
- `sigmas`: Gaussian smoothing per level (default: [3.0, 1.0, 0.0])
- `factors`: Subsampling factors (default: [4, 2, 1])

### For Difficult Cases
```python
# More aggressive registration
config = RegistrationConfig()
config.level_iters = [20000, 5000, 1000]  # More iterations
config.nbins = 64  # Higher resolution
config.sigmas = [4.0, 2.0, 1.0]  # More smoothing
```

## Performance Notes

- **Typical registration time**: 15-45 minutes per volume pair
- **Memory usage**: ~2-4GB for typical brain images
- **Multi-level approach**: Coarse-to-fine optimization
- **Robust convergence**: Usually succeeds where simpler methods fail

## Example Output

```
$ python -m registration_tool.cli --patient-folder meningioma_0023_no_compat/ --reference t1ce --modalities t2

INFO: Processing patient folder: meningioma_0023_no_compat/
INFO: Using reference: meningioma_0023_no_compat_t1ce.nii.gz
INFO: Registering 1 files to meningioma_0023_no_compat_t1ce.nii.gz
INFO: Loading images...
INFO: Computing center of mass alignment...
INFO: Computing translation transform...
INFO: Computing rigid transform...
INFO: Computing affine transform...
INFO: Applying transformation...
INFO: Saved registered image to output/meningioma_0023_no_compat_t2.nii.gz
INFO: Registration completed in 1594.9 seconds

✓ Patient registration completed!
  Patient: meningioma_0023_no_compat
  Reference: meningioma_0023_no_compat_t1ce.nii.gz
  Successful: 1
  Failed: 0
```
