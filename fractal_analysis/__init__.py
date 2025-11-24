"""
Fractal Analysis Package
=======================

Medical imaging fractal analysis using the FracND library.
Separates geometric analysis (fractal dimension on segmentations) from 
texture analysis (lacunarity on image intensities).

Key Features:
- Fractal Dimension (FD): Measured on segmentation masks (geometric complexity)
- Lacunarity (LD): Measured on masked image intensities (texture heterogeneity)
- Multi-modal support: T1, T1CE, T2, FLAIR
- Batch processing capabilities

Quick usage:
    from fractal_analysis import analyze_patient, analyze_dataset
    
    # Single patient analysis
    result = analyze_patient('patient_001/')
    print(f"Segmentation FD: {result['segmentation']['FD']}")
    
    # Dataset analysis
    summary = analyze_dataset('input_data/', 'fractal_results/')
"""

from .analyzer import (
    analyze_patient_folder,
    batch_analyze_dataset,
    analyze_segmentation_fractal_dimension,
    analyze_intensity_lacunarity,
    analyze_patient,
    analyze_dataset,
    FractalConfig
)

__version__ = "1.0.0"
__author__ = "Medical Imaging Tools"

# Main public API
__all__ = [
    'analyze_patient',
    'analyze_dataset',
    'analyze_patient_folder',
    'batch_analyze_dataset',
    'analyze_segmentation_fractal_dimension',
    'analyze_intensity_lacunarity',
    'FractalConfig'
]
