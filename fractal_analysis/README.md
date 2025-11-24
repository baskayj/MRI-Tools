# Fractal Analysis Tool

Advanced fractal analysis for medical imaging datasets using the FracND library. Designed specifically for tumor analysis with separate geometric and texture measurements.

## Part of Medical Imaging Tools Repository

This tool provides sophisticated fractal analysis for research applications:
- **Geometric Analysis**: Fractal dimension of tumor boundaries/shape  
- **Texture Analysis**: Lacunarity of image intensities within tumor regions
- **Multi-modal Support**: T1, T1CE, T2, FLAIR sequences
- **Publication-ready**: Generates plots and statistical summaries

## Key Concepts

### Fractal Dimension (FD) - Geometric Complexity
- **Measured on**: Segmentation masks (`*_seg.nii.gz`)
- **Represents**: Complexity of tumor boundary/shape geometry
- **Clinical relevance**: May correlate with tumor aggressiveness, invasion patterns

### Lacunarity (LD) - Texture Heterogeneity  
- **Measured on**: Image intensities (T1, T1CE, T2, FLAIR) masked by segmentation
- **Represents**: Spatial heterogeneity of tumor tissue
- **Clinical relevance**: May reflect tumor texture, necrosis, enhancement patterns

## Usage

### Command Line

```bash
# Analyze single patient
python -m fractal_analysis.cli --patient patient_001/ -o fractal_results/

# Analyze entire dataset
python -m fractal_analysis.cli --dataset input_data/ -o fractal_results/

# Analyze specific modalities only
python -m fractal_analysis.cli --dataset data/ -o results/ --modalities t1ce t2

# Custom parameters for research
python -m fractal_analysis.cli --patient patient_001/ -o results/ --n-samples 200 --stride 1

# Resume large dataset analysis
python -m fractal_analysis.cli --dataset data/ -o results/ --start-from 50
```

### Python Import (Jupyter Notebook)

```python
from fractal_analysis import analyze_patient, analyze_dataset

# Single patient analysis
result = analyze_patient('patient_001/')
print(f"Segmentation FD: {result['segmentation']['FD']:.3f}")
print(f"T1CE Lacunarity: {result['modalities']['t1ce']['LD']:.3f}")

# Dataset analysis
summary = analyze_dataset('input_data/', 'fractal_results/')
print(f"Analyzed {summary['successful']} patients successfully")
```

### Advanced Usage

```python
from fractal_analysis import analyze_patient_folder, FractalConfig

# Custom configuration for research
config = FractalConfig()
config.n_samples = 200        # Higher resolution
config.stride = 1             # Denser sampling
config.intensity_levels = 512  # Higher precision
config.subsample_intensity = 0.005  # More intensive analysis

result = analyze_patient_folder(
    'patient_001/',
    modalities=['t1ce', 't2'],
    config=config,
    output_folder='detailed_results/'
)
```

## Output Structure

### Results CSV
```
fractal_results/
├── fractal_analysis_results.csv     # Main results table
├── plots/                           # Individual plots
│   ├── patient_001_seg_FD.png      # Segmentation fractal dimension
│   ├── patient_001_seg_LD.png      # Segmentation lacunarity  
│   ├── patient_001_t1ce_LD.png     # T1CE lacunarity
│   └── ...
```

### CSV Columns
| Column | Description |
|--------|-------------|
| `patient_id` | Patient identifier |
| `seg_FD` | Segmentation fractal dimension |
| `t1_LD` | T1 image lacunarity |
| `t1ce_LD` | T1CE image lacunarity |
| `t2_LD` | T2 image lacunarity |
| `flair_LD` | FLAIR image lacunarity |



## Parameters and Optimization

### Default Parameters (Balanced)
```python
config = FractalConfig()
config.n_samples = 100           # Good balance of resolution vs speed
config.stride = 2                # Efficient sliding window
config.subsample_intensity = 0.01  # 1% subsampling for intensity analysis
config.intensity_levels = 255    # Standard 8-bit precision
```

### Research-Grade Parameters (High Precision)
```python
config = FractalConfig()
config.n_samples = 200           # Higher resolution
config.stride = 1                # Denser sampling
config.subsample_intensity = 0.005  # 0.5% subsampling
config.intensity_levels = 512    # Higher precision
```

### Fast Screening Parameters (Quick Analysis)
```python
config = FractalConfig()
config.n_samples = 50            # Lower resolution
config.stride = 4                # Coarser sampling  
config.subsample_intensity = 0.02   # 2% subsampling
config.intensity_levels = 128    # Lower precision
```

## Example Output

```
$ python -m fractal_analysis.cli --dataset meningioma_data/ -o fractal_results/

INFO: Found 67 patients to analyze
Analyzing patients: 100%|██████████| 67/67 [8:45:32<00:00, 469.89s/it]
INFO: Fractal analysis complete: 67 successful, 0 failed

✓ Dataset analysis completed!
  Total patients: 67
  Successful: 67
  Failed: 0
  Success rate: 100.0%
  Results saved to: fractal_results/fractal_analysis_results.csv
  Plots saved to: fractal_results/plots/
```