"""
NII Converter Package
====================

A lightweight tool for converting .nii files to .nii.gz format with automatic
fixes for common issues, especially from ImageJ exports.

Quick usage:
    from nii_converter import convert_file, convert_folder
    
    # Convert single file
    result = convert_file('image.nii')
    
    # Convert entire folder
    summary = convert_folder('input_folder/', 'output_folder/')
"""

from .converter import (
    convert_nii_file,
    convert_directory,
    convert_file,
    convert_folder,
    fix_signed_array,
    fix_header_and_affine_issues
)

__version__ = "1.0.0"
__author__ = "Medical Imaging Tools"

# Main public API
__all__ = [
    'convert_file',
    'convert_folder', 
    'convert_nii_file',
    'convert_directory',
    'fix_signed_array',
    'fix_header_and_affine_issues'
]
