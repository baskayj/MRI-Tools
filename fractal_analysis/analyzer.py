"""
Fractal Analysis Tool - Core Analysis Logic
==========================================

Fractal analysis for medical imaging datasets using the FracND library.
Separates fractal dimension analysis (on segmentations) from lacunarity analysis 
(on masked image intensities).
"""

import os
import sys
import numpy as np
import pandas as pd
import nibabel as nib
import matplotlib.pyplot as plt
from pathlib import Path
from tqdm import tqdm
import logging

# Import FracND library (assumes fracnd.py is available)
try:
    from fracnd import FracND, greyscale_to_binary, crop_segmentation, crop_image
    FRACND_AVAILABLE = True
except ImportError:
    FRACND_AVAILABLE = False

logger = logging.getLogger(__name__)


class FractalConfig:
    """Configuration class for fractal analysis parameters."""
    
    def __init__(self):
        # FracND parameters
        self.n_samples = 100
        self.stride = 2
        self.subsample = None  # For segmentation analysis
        self.subsample_intensity = 0.01  # For intensity analysis (much denser)
        
        # Greyscale conversion
        self.intensity_levels = 255
        
        # Output options
        self.save_plots = True
        self.plot_format = 'png'
        self.save_individual_results = True


def validate_fracnd():
    """Check if FracND library is available."""
    if not FRACND_AVAILABLE:
        raise ImportError(
            "FracND library not found. Please ensure 'fracnd.py' is in your Python path."
        )


def load_and_prepare_segmentation(seg_file):
    """
    Load segmentation file and prepare for analysis.
    
    Args:
        seg_file: Path to segmentation file
        
    Returns:
        tuple: (cropped_seg, minima, maxima) for cropping other images
    """
    seg = nib.load(seg_file)
    seg_data = seg.get_fdata()
    
    # Handle 4D data
    if len(seg_data.shape) == 4:
        seg_data = seg_data[:, :, :, 0]
    
    # Crop to minimal bounding box
    cropped_seg, minima, maxima = crop_segmentation(seg_data, return_indices=True)
    
    return cropped_seg, minima, maxima


def analyze_segmentation_fractal_dimension(seg_data, config=None, patient_id=None, output_folder=None):
    """
    Analyze fractal dimension of segmentation (geometric complexity).
    
    Args:
        seg_data: Segmentation array
        config: FractalConfig object
        patient_id: Patient identifier for output files
        output_folder: Directory for saving plots
        
    Returns:
        dict with fractal dimension results
    """
    validate_fracnd()
    
    if config is None:
        config = FractalConfig()
    
    logger.info("Calculating fractal dimension for segmentation...")
    
    # Initialize fractal calculator for segmentation
    fractal_calculator = FracND(
        n_samples=config.n_samples,
        stride=config.stride,
        subsample=config.subsample  # No subsampling for segmentation
    )
    
    # Perform analysis
    fractal_calculator(seg_data)
    
    # Extract results
    results = {
        'FD': fractal_calculator.FD,
        'LD': fractal_calculator.LD,  # Also available but not primary focus
        'lacunarity_stats': fractal_calculator.lacunarity_statistics()
    }
    
    # Save plots if requested
    if config.save_plots and output_folder and patient_id:
        output_path = Path(output_folder)
        output_path.mkdir(parents=True, exist_ok=True)
        
        fd_plot = output_path / f"{patient_id}_seg_FD.{config.plot_format}"
        ld_plot = output_path / f"{patient_id}_seg_LD.{config.plot_format}"
        
        fractal_calculator.plot_FD(show_plot=False, filename=str(fd_plot))
        fractal_calculator.plot_lacunarity(show_plot=False, filename=str(ld_plot))
        
        results['fd_plot'] = str(fd_plot)
        results['ld_plot'] = str(ld_plot)
    
    return results


def analyze_intensity_lacunarity(image_data, seg_data, minima, maxima, modality, 
                                config=None, patient_id=None, output_folder=None):
    """
    Analyze lacunarity of image intensities within segmented region.
    
    Args:
        image_data: Image intensity array
        seg_data: Segmentation mask (uncropped)
        minima, maxima: Cropping indices from segmentation
        modality: Modality name (e.g., 't1ce', 't2')
        config: FractalConfig object
        patient_id: Patient identifier
        output_folder: Directory for saving plots
        
    Returns:
        dict with lacunarity results
    """
    validate_fracnd()
    
    if config is None:
        config = FractalConfig()
    
    logger.info(f"Calculating lacunarity for {modality}...")
    
    # Handle 4D data
    if len(image_data.shape) == 4:
        image_data = image_data[:, :, :, 0]
    
    # Crop image to same region as segmentation
    cropped_image = crop_image(image_data, minima, maxima)
    
    # Crop segmentation for masking
    cropped_seg, _, _ = crop_segmentation(seg_data)
    
    # Mask image with segmentation
    masked_image = cropped_image * cropped_seg
    
    # Convert to binary representation for fractal analysis
    binary_image = greyscale_to_binary(masked_image, levels=config.intensity_levels)
    
    # Initialize fractal calculator for intensity analysis
    fractal_calculator = FracND(
        n_samples=config.n_samples,
        stride=config.stride,
        subsample=config.subsample_intensity  # Heavy subsampling for efficiency
    )
    
    # Perform analysis
    fractal_calculator(binary_image)
    
    # Extract results (focus on lacunarity)
    results = {
        'LD': fractal_calculator.LD,
        'FD': fractal_calculator.FD,  # Available but not primary focus
        'lacunarity_stats': fractal_calculator.lacunarity_statistics(),
        'modality': modality
    }
    
    # Save plots if requested
    if config.save_plots and output_folder and patient_id:
        output_path = Path(output_folder)
        output_path.mkdir(parents=True, exist_ok=True)
        
        fd_plot = output_path / f"{patient_id}_{modality}_FD.{config.plot_format}"
        ld_plot = output_path / f"{patient_id}_{modality}_LD.{config.plot_format}"
        
        fractal_calculator.plot_FD(show_plot=False, filename=str(fd_plot))
        fractal_calculator.plot_lacunarity(show_plot=False, filename=str(ld_plot))
        
        results['fd_plot'] = str(fd_plot)
        results['ld_plot'] = str(ld_plot)
    
    return results


def analyze_patient_folder(patient_folder, modalities=None, config=None, output_folder=None):
    """
    Perform fractal analysis on a patient folder.
    
    Args:
        patient_folder: Path to patient folder containing images
        modalities: List of modalities to analyze (default: ['t1', 't1ce', 't2', 'flair'])
        config: FractalConfig object
        output_folder: Output directory for results
        
    Returns:
        dict with all analysis results
    """
    patient_path = Path(patient_folder)
    patient_id = patient_path.name
    
    if modalities is None:
        modalities = ['t1', 't1ce', 't2', 'flair']
    
    if config is None:
        config = FractalConfig()
    
    logger.info(f"Analyzing patient: {patient_id}")
    
    # Find segmentation file
    seg_files = list(patient_path.glob("*_seg.nii.gz"))
    if not seg_files:
        raise FileNotFoundError(f"No segmentation file found in {patient_folder}")
    
    seg_file = seg_files[0]
    logger.info(f"Using segmentation: {seg_file.name}")
    
    # Load and prepare segmentation
    cropped_seg, minima, maxima = load_and_prepare_segmentation(seg_file)
    
    # Analyze segmentation fractal dimension
    seg_results = analyze_segmentation_fractal_dimension(
        cropped_seg, config, patient_id, output_folder
    )
    
    # Initialize results dictionary
    results = {
        'patient_id': patient_id,
        'segmentation': seg_results,
        'modalities': {}
    }
    
    # Analyze each modality for lacunarity
    for modality in modalities:
        modality_files = list(patient_path.glob(f"*_{modality}.nii.gz"))
        
        if not modality_files:
            logger.warning(f"No {modality} file found for patient {patient_id}")
            continue
        
        modality_file = modality_files[0]
        logger.info(f"Analyzing {modality}: {modality_file.name}")
        
        try:
            # Load image
            img = nib.load(modality_file)
            img_data = img.get_fdata()
            
            # Load full segmentation for masking
            seg = nib.load(seg_file)
            seg_data = seg.get_fdata()
            
            # Analyze lacunarity
            modality_results = analyze_intensity_lacunarity(
                img_data, seg_data, minima, maxima, modality,
                config, patient_id, output_folder
            )
            
            results['modalities'][modality] = modality_results
            
        except Exception as e:
            logger.error(f"Failed to analyze {modality} for patient {patient_id}: {e}")
            results['modalities'][modality] = {'error': str(e)}
    
    return results


def batch_analyze_dataset(input_folder, output_folder, modalities=None, config=None, 
                         start_from=0, save_intermediate=True):
    """
    Perform fractal analysis on entire dataset.
    
    Args:
        input_folder: Folder containing patient subfolders
        output_folder: Output folder for results
        modalities: List of modalities to analyze
        config: FractalConfig object
        start_from: Patient index to start from (for resuming)
        save_intermediate: Save results after each patient
        
    Returns:
        dict with summary and detailed results
    """
    input_path = Path(input_folder)
    output_path = Path(output_folder)
    output_path.mkdir(parents=True, exist_ok=True)
    
    if modalities is None:
        modalities = ['t1', 't1ce', 't2', 'flair']
    
    if config is None:
        config = FractalConfig()
    
    # Find patient folders
    patient_folders = [d for d in input_path.iterdir() if d.is_dir()]
    patient_folders.sort()
    
    logger.info(f"Found {len(patient_folders)} patients to analyze")
    
    # Initialize or load existing results
    results_file = output_path / 'fractal_analysis_results.csv'
    if results_file.exists():
        df_main = pd.read_csv(results_file)
    else:
        columns = ['patient_id', 'seg_FD', 'seg_LD'] + [f'{mod}_LD' for mod in modalities]
        df_main = pd.DataFrame(columns=columns)
    
    # Create plots directory
    plots_dir = output_path / 'plots'
    plots_dir.mkdir(exist_ok=True)
    
    successful = 0
    failed = 0
    all_results = []
    
    # Process patients
    for i, patient_folder in enumerate(tqdm(patient_folders[start_from:], 
                                          desc="Analyzing patients")):
        try:
            results = analyze_patient_folder(
                patient_folder, modalities, config, plots_dir
            )
            
            # Extract data for CSV
            row_data = {
                'patient_id': results['patient_id'],
                'seg_FD': results['segmentation']['FD'],
                'seg_LD': results['segmentation']['LD']
            }
            
            # Add modality lacunarity values
            for modality in modalities:
                if modality in results['modalities']:
                    if 'error' not in results['modalities'][modality]:
                        row_data[f'{modality}_LD'] = results['modalities'][modality]['LD']
                    else:
                        row_data[f'{modality}_LD'] = np.nan
                else:
                    row_data[f'{modality}_LD'] = np.nan
            
            # Add to dataframe
            df_main = pd.concat([df_main, pd.DataFrame([row_data])], ignore_index=True)
            
            # Save intermediate results
            if save_intermediate:
                df_main.to_csv(results_file, index=False)
            
            all_results.append(results)
            successful += 1
            
        except Exception as e:
            logger.error(f"Failed to analyze {patient_folder.name}: {e}")
            failed += 1
    
    # Save final results
    df_main.to_csv(results_file, index=False)
    
    summary = {
        'total_patients': len(patient_folders),
        'successful': successful,
        'failed': failed,
        'success_rate': (successful / len(patient_folders)) * 100 if patient_folders else 0,
        'results_file': str(results_file),
        'plots_directory': str(plots_dir),
        'detailed_results': all_results
    }
    
    logger.info(f"Fractal analysis complete: {successful} successful, {failed} failed")
    return summary


# Convenience functions for simple usage
def analyze_patient(patient_folder, **kwargs):
    """Simple wrapper for single patient analysis."""
    return analyze_patient_folder(patient_folder, **kwargs)


def analyze_dataset(input_folder, output_folder, **kwargs):
    """Simple wrapper for dataset analysis."""
    return batch_analyze_dataset(input_folder, output_folder, **kwargs)
