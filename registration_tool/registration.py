"""
Custom Registration Tool - Core Registration Logic
=================================================

DIPY-based affine registration for cases where CaPTk fails or produces 
suboptimal results. Performs multi-level registration with mutual information.
"""

import os
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
from time import time
import logging

# DIPY imports
from dipy.io.image import load_nifti, save_nifti
from dipy.align.imaffine import (
    transform_centers_of_mass,
    AffineMap,
    MutualInformationMetric,
    AffineRegistration
)
from dipy.align.transforms import (
    TranslationTransform3D,
    RigidTransform3D,
    AffineTransform3D
)

# Optional visualization (FURY not always available)
try:
    from dipy.viz import regtools
    VIZ_AVAILABLE = True
except ImportError:
    VIZ_AVAILABLE = False

logger = logging.getLogger(__name__)


class RegistrationConfig:
    """Configuration class for registration parameters."""
    
    def __init__(self):
        # Mutual Information parameters
        self.nbins = 32
        self.sampling_prop = None
        
        # Multi-level optimization parameters
        self.level_iters = [10000, 1000, 100]
        self.sigmas = [3.0, 1.0, 0.0]
        self.factors = [4, 2, 1]
        
        # Visualization
        self.show_plots = False
        self.save_plots = False
        
        # Output
        self.output_format = "nii.gz"


def affine_registration(moving_file, static_file, output_file=None, 
                       config=None, show_plots=False, progress_callback=None):
    """
    Perform affine registration between two images.
    
    Args:
        moving_file: Path to moving image
        static_file: Path to static (reference) image  
        output_file: Path for output registered image (optional)
        config: RegistrationConfig object (optional)
        show_plots: Show visualization plots
        progress_callback: Function to call with progress updates
        
    Returns:
        dict with registration results
    """
    start_time = time()
    
    if config is None:
        config = RegistrationConfig()
    
    if progress_callback is None:
        progress_callback = lambda msg: logger.info(msg)
    
    try:
        # Load the data
        progress_callback("Loading images...")
        static_data, static_affine, static_img = load_nifti(static_file, return_img=True)
        moving_data, moving_affine, moving_img = load_nifti(moving_file, return_img=True)
        
        # Handle 4D data by taking first volume
        if static_data.ndim == 4:
            static = static_data[:,:,:,0]
        else:
            static = static_data
            
        if moving_data.ndim == 4:
            moving = moving_data[:,:,:,0]
        else:
            moving = moving_data
        
        static_grid2world = static_affine
        moving_grid2world = moving_affine
        
        # Center of mass transform
        progress_callback("Computing center of mass alignment...")
        c_of_mass = transform_centers_of_mass(static, static_grid2world, 
                                            moving, moving_grid2world)
        
        # Set up Affine Registration
        metric = MutualInformationMetric(config.nbins, config.sampling_prop)
        affreg = AffineRegistration(
            metric=metric,
            level_iters=config.level_iters,
            sigmas=config.sigmas,
            factors=config.factors
        )
        
        # Translation transform
        progress_callback("Computing translation transform...")
        transform = TranslationTransform3D()
        starting_affine = c_of_mass.affine
        translation = affreg.optimize(
            static, moving, transform, None,
            static_grid2world, moving_grid2world,
            starting_affine=starting_affine
        )
        
        # Rigid transform  
        progress_callback("Computing rigid transform...")
        transform = RigidTransform3D()
        starting_affine = translation.affine
        rigid = affreg.optimize(
            static, moving, transform, None,
            static_grid2world, moving_grid2world,
            starting_affine=starting_affine
        )
        
        # Affine transform
        progress_callback("Computing affine transform...")
        transform = AffineTransform3D()
        starting_affine = rigid.affine
        affine = affreg.optimize(
            static, moving, transform, None,
            static_grid2world, moving_grid2world,
            starting_affine=starting_affine
        )
        
        # Apply the transformation
        progress_callback("Applying transformation...")
        transformed = affine.transform(moving)
        
        # Save result if output path specified
        if output_file:
            output_path = Path(output_file)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            save_nifti(str(output_path), transformed, static_affine)
            progress_callback(f"Saved registered image to {output_path}")
        
        # Show plots if requested
        if show_plots and VIZ_AVAILABLE:
            _show_registration_plots(static, transformed)
        elif show_plots and not VIZ_AVAILABLE:
            logger.warning("Visualization not available (FURY not installed)")
        
        elapsed_time = time() - start_time
        progress_callback(f"Registration completed in {elapsed_time:.1f} seconds")
        
        return {
            'success': True,
            'transformed_data': transformed,
            'affine_transform': affine.affine,
            'static_affine': static_affine,
            'output_file': str(output_file) if output_file else None,
            'elapsed_time': elapsed_time,
            'transforms': {
                'center_of_mass': c_of_mass.affine,
                'translation': translation.affine,
                'rigid': rigid.affine,
                'affine': affine.affine
            }
        }
        
    except Exception as e:
        error_msg = f"Registration failed: {str(e)}"
        logger.error(error_msg)
        return {
            'success': False,
            'error': error_msg,
            'elapsed_time': time() - start_time
        }


def _show_registration_plots(static, transformed):
    """Show overlay plots of registration results."""
    if not VIZ_AVAILABLE:
        return
        
    try:
        # Show axial, sagittal, and coronal views
        for axis in [0, 1, 2]:
            regtools.overlay_slices(static, transformed, None, axis,
                                  "Static", "Transformed", None)
            plt.show()
    except Exception as e:
        logger.warning(f"Could not display plots: {e}")


def register_to_reference(moving_file, reference_file, output_file=None, **kwargs):
    """
    Simple wrapper for single file registration.
    
    Args:
        moving_file: Image to be registered
        reference_file: Reference (static) image
        output_file: Output path for registered image
        **kwargs: Additional parameters for affine_registration
        
    Returns:
        Registration result dictionary
    """
    return affine_registration(moving_file, reference_file, output_file, **kwargs)


def batch_register_folder(input_folder, reference_file, output_folder, 
                         pattern="*.nii.gz", reference_pattern=None):
    """
    Register all images in a folder to a reference image.
    
    Args:
        input_folder: Folder containing images to register
        reference_file: Reference image path
        output_folder: Output folder for registered images
        pattern: File pattern to match (default: "*.nii.gz")
        reference_pattern: If provided, find reference in each subfolder
        
    Returns:
        Dictionary with batch registration results
    """
    input_path = Path(input_folder)
    output_path = Path(output_folder)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Find files to process
    if reference_pattern:
        # Process patient folders with reference in each
        patient_folders = [d for d in input_path.iterdir() if d.is_dir()]
        files_to_process = []
        
        for patient_folder in patient_folders:
            # Find reference file in this folder
            ref_files = list(patient_folder.glob(reference_pattern))
            if not ref_files:
                logger.warning(f"No reference file found in {patient_folder}")
                continue
            local_ref = ref_files[0]
            
            # Find other files to register
            other_files = [f for f in patient_folder.glob(pattern) 
                          if f != local_ref]
            
            for file_to_register in other_files:
                files_to_process.append({
                    'moving': file_to_register,
                    'reference': local_ref,
                    'output_folder': output_path / patient_folder.name
                })
    else:
        # Register all files to single reference
        files_to_process = []
        for file_path in input_path.rglob(pattern):
            if file_path.name != Path(reference_file).name:
                rel_path = file_path.relative_to(input_path)
                output_file = output_path / rel_path
                files_to_process.append({
                    'moving': file_path,
                    'reference': reference_file,
                    'output_file': output_file
                })
    
    logger.info(f"Found {len(files_to_process)} files to register")
    
    results = []
    successful = 0
    failed = 0
    
    for i, item in enumerate(files_to_process):
        logger.info(f"Processing {i+1}/{len(files_to_process)}: {item['moving'].name}")
        
        # Determine output file path
        if 'output_file' in item:
            output_file = item['output_file']
        else:
            output_file = item['output_folder'] / item['moving'].name
        
        result = affine_registration(
            moving_file=item['moving'],
            static_file=item['reference'],
            output_file=output_file,
            progress_callback=lambda msg: logger.debug(msg)
        )
        
        result['input_file'] = str(item['moving'])
        result['reference_file'] = str(item['reference'])
        results.append(result)
        
        if result['success']:
            successful += 1
        else:
            failed += 1
            logger.error(f"Failed to register {item['moving'].name}: {result['error']}")
    
    summary = {
        'total_files': len(files_to_process),
        'successful': successful,
        'failed': failed,
        'success_rate': (successful / len(files_to_process)) * 100 if files_to_process else 0,
        'results': results
    }
    
    logger.info(f"Batch registration complete: {successful} successful, {failed} failed")
    return summary


def register_modalities_to_reference(patient_folder, reference_modality="t1ce", 
                                    modalities=None, output_folder=None):
    """
    Register multiple modalities to a reference modality for a single patient.
    
    Args:
        patient_folder: Folder containing patient images
        reference_modality: Modality to use as reference (e.g., "t1ce")
        modalities: List of modalities to register (if None, registers all)
        output_folder: Output folder (defaults to input folder)
        
    Returns:
        Registration results
    """
    patient_path = Path(patient_folder)
    patient_name = patient_path.name
    
    if output_folder is None:
        output_folder = patient_path
    else:
        output_folder = Path(output_folder) / patient_name
    
    # Find reference file
    ref_pattern = f"*{reference_modality}*.nii.gz"
    ref_files = list(patient_path.glob(ref_pattern))
    
    if not ref_files:
        return {
            'success': False,
            'error': f"No reference file found matching {ref_pattern} in {patient_folder}"
        }
    
    reference_file = ref_files[0]
    logger.info(f"Using reference: {reference_file.name}")
    
    # Find modalities to register
    if modalities is None:
        # Find all .nii.gz files except reference
        all_files = list(patient_path.glob("*.nii.gz"))
        files_to_register = [f for f in all_files if f != reference_file]
    else:
        files_to_register = []
        for modality in modalities:
            pattern = f"*{modality}*.nii.gz"
            mod_files = [f for f in patient_path.glob(pattern) if f != reference_file]
            files_to_register.extend(mod_files)
    
    logger.info(f"Registering {len(files_to_register)} files to {reference_file.name}")
    
    results = []
    for file_to_register in files_to_register:
        output_file = output_folder / file_to_register.name
        
        result = affine_registration(
            moving_file=file_to_register,
            static_file=reference_file,
            output_file=output_file
        )
        
        result['modality'] = file_to_register.stem.split('_')[-1]  # Extract modality name
        results.append(result)
    
    return {
        'patient': patient_name,
        'reference_file': str(reference_file),
        'results': results,
        'successful': sum(1 for r in results if r['success']),
        'failed': sum(1 for r in results if not r['success'])
    }


# Convenience functions for simple usage
def register_file(moving_file, reference_file, output_file=None, **kwargs):
    """Simple wrapper for single file registration."""
    return register_to_reference(moving_file, reference_file, output_file, **kwargs)


def register_folder(input_folder, reference_file, output_folder, **kwargs):
    """Simple wrapper for batch folder registration."""
    return batch_register_folder(input_folder, reference_file, output_folder, **kwargs)
