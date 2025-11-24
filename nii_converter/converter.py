"""
NII Converter - Core Conversion Logic
============================================
Core functionality for converting .nii files to .nii.gz format with automatic
fixes for common issues, especially from ImageJ exports. Includes proper affine
matrix scaling for unit conversions.
"""
import os
import nibabel as nib
import numpy as np
from pathlib import Path
from tqdm import tqdm
import logging

logger = logging.getLogger(__name__)

def fix_signed_array(data, offset=32768.0):
    """
    Fix signed arrays by adding offset if minimum value is negative.
    
    Args:
        data: numpy array
        offset: offset to add to negative arrays
        
    Returns:
        Fixed array
    """
    if np.min(data) < 0:
        logger.info(f"Signed array detected (min: {np.min(data):.1f}), applying offset +{offset}")
        return data + offset
    return data

def fix_header_and_affine_issues(header, affine):
    """
    Fix common header and affine issues from ImageJ exports.
    
    Args:
        header: nibabel header object
        affine: nibabel affine matrix
        
    Returns:
        tuple: (fixed_header, fixed_affine, list_of_fixes_applied)
    """
    fixes_applied = []
    affine = affine.copy()  # Don't modify the original
    
    # Fix data type to uint32
    header.set_data_dtype(np.uint32)
    
    # Get voxel size and units
    voxel_size = np.array(header.get_zooms())
    spatial_units, temporal_units = header.get_xyzt_units()
    
    # Fix unit conversion (micron to mm)
    if spatial_units == 'micron':
        voxel_size[:3] = voxel_size[:3] / 1000
        header.set_zooms(voxel_size)
        header.set_xyzt_units('mm', temporal_units)
        # CRITICAL: Also scale the affine matrix
        affine[:3, :] /= 1000
        fixes_applied.append("converted_units_micron_to_mm")
        logger.info("Converted voxel units from micron to mm and scaled affine matrix")
    elif spatial_units != 'mm' and spatial_units != 'unknown':
        # Check if the voxel size suggests microns (typically > 100)
        if np.any(voxel_size[:3] > 100):
            voxel_size[:3] = voxel_size[:3] / 1000
            header.set_zooms(voxel_size)
            header.set_xyzt_units('mm', temporal_units)
            # Scale the affine matrix
            affine[:3, :] /= 1000
            fixes_applied.append("converted_units_assumed_micron_to_mm")
            logger.info(f"Converted voxel units from {spatial_units} to mm (assumed microns) and scaled affine matrix")
        else:
            header.set_xyzt_units('mm', temporal_units)
            fixes_applied.append("set_units_to_mm")
            logger.info(f"Set spatial units to mm (was {spatial_units})")
    
    # Fix temporal voxel size if it's not 0
    voxel_size = np.array(header.get_zooms())
    if len(voxel_size) > 3 and voxel_size[3] != 0:
        voxel_size[3] = 0
        header.set_zooms(voxel_size)
        fixes_applied.append("fixed_temporal_voxel_size")
        logger.info("Set temporal voxel size to 0")
    
    return header, affine, fixes_applied

def convert_nii_file(input_path, output_path=None, check_existing=True, offset=32768.0):
    """
    Convert a single .nii file to .nii.gz with fixes.
    
    Args:
        input_path: path to input .nii file
        output_path: path for output .nii.gz file (optional)
        check_existing: skip if output already exists
        offset: offset for signed array correction
        
    Returns:
        dict with conversion results
    """
    input_path = Path(input_path)
    
    if not input_path.exists():
        return {'success': False, 'error': 'Input file does not exist'}
    
    if not input_path.name.endswith('.nii'):
        return {'success': False, 'error': 'Input file is not a .nii file'}
    
    # Determine output path
    if output_path is None:
        output_path = input_path.with_suffix('.nii.gz')
    else:
        output_path = Path(output_path)
        if output_path.is_dir():
            output_path = output_path / (input_path.stem + '.nii.gz')
    
    # Check if output already exists
    if check_existing and output_path.exists():
        logger.info(f"Skipping {input_path.name} - output already exists")
        return {'success': True, 'skipped': True, 'output_path': str(output_path)}
    
    try:
        # Load the image
        logger.debug(f"Loading {input_path.name}")
        img = nib.load(input_path)
        data = img.get_fdata()
        affine = img.affine.copy()
        header = img.header.copy()
        
        # Fix signed array issues
        original_min = np.min(data)
        data = fix_signed_array(data, offset)
        
        # Fix header AND affine issues (this is the key fix)
        header, affine, fixes_applied = fix_header_and_affine_issues(header, affine)
        
        # Create output directory if needed
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Save as compressed NIfTI with fixed affine
        new_img = nib.Nifti1Image(data, affine, header)
        nib.save(new_img, output_path)
        
        # Calculate file size reduction
        size_reduction = input_path.stat().st_size / output_path.stat().st_size
        
        # Check final result
        final_min = np.min(data)
        if final_min < 0:
            logger.warning(f"Warning: {output_path.name} still has negative values (min: {final_min:.1f})")
        
        result = {
            'success': True,
            'input_path': str(input_path),
            'output_path': str(output_path),
            'original_min_value': float(original_min),
            'final_min_value': float(final_min),
            'fixes_applied': fixes_applied,
            'file_size_reduction': f"{size_reduction:.1f}x"
        }
        
        logger.info(f"✓ Converted {input_path.name} → {output_path.name}")
        return result
        
    except Exception as e:
        error_msg = f"Error converting {input_path.name}: {str(e)}"
        logger.error(error_msg)
        return {'success': False, 'error': error_msg, 'input_path': str(input_path)}

def convert_directory(input_dir, output_dir=None, recursive=True, offset=32768.0, 
                     overwrite=False, show_progress=True):
    """
    Convert all .nii files in a directory to .nii.gz.
    
    Args:
        input_dir: input directory path
        output_dir: output directory path (optional, defaults to same as input)
        recursive: search subdirectories
        offset: offset for signed array correction
        overwrite: overwrite existing files
        show_progress: show progress bar
        
    Returns:
        dict with conversion summary
    """
    input_dir = Path(input_dir)
    
    if not input_dir.exists():
        raise ValueError(f"Input directory does not exist: {input_dir}")
    
    if output_dir is None:
        output_dir = input_dir
    else:
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
    
    # Find all .nii files
    if recursive:
        nii_files = list(input_dir.rglob("*.nii"))
    else:
        nii_files = list(input_dir.glob("*.nii"))
    
    if not nii_files:
        logger.warning(f"No .nii files found in {input_dir}")
        return {'total_files': 0, 'successful': 0, 'failed': 0, 'skipped': 0, 'results': []}
    
    logger.info(f"Found {len(nii_files)} .nii files to convert")
    
    results = []
    successful = 0
    failed = 0
    skipped = 0
    
    # Convert files with optional progress bar
    iterator = tqdm(nii_files, desc="Converting files") if show_progress else nii_files
    
    for nii_file in iterator:
        # Calculate relative path for output structure
        rel_path = nii_file.relative_to(input_dir)
        output_file = output_dir / rel_path.with_suffix('.nii.gz')
        
        result = convert_nii_file(
            nii_file, 
            output_file, 
            check_existing=not overwrite,
            offset=offset
        )
        results.append(result)
        
        if result['success']:
            if result.get('skipped', False):
                skipped += 1
            else:
                successful += 1
        else:
            failed += 1
    
    summary = {
        'total_files': len(nii_files),
        'successful': successful,
        'failed': failed,
        'skipped': skipped,
        'success_rate': (successful / len(nii_files)) * 100 if nii_files else 0,
        'results': results
    }
    
    logger.info(f"Conversion complete: {successful} successful, {failed} failed, {skipped} skipped")
    return summary

# Convenience functions for simple usage
def convert_file(input_file, output_file=None, **kwargs):
    """Simple wrapper for single file conversion."""
    return convert_nii_file(input_file, output_file, **kwargs)

def convert_folder(input_folder, output_folder=None, **kwargs):
    """Simple wrapper for directory conversion."""
    return convert_directory(input_folder, output_folder, **kwargs)