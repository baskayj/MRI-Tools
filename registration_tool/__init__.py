"""
Registration Tool Package
========================

Custom image registration using DIPY for cases where CaPTk fails or produces
suboptimal results. Performs multi-level affine registration with mutual information.

Quick usage:
    from registration_tool import register_file, register_folder
    
    # Register single file
    result = register_file('moving.nii.gz', 'reference.nii.gz', 'output.nii.gz')
    
    # Register patient folder (e.g., T2 to T1CE)
    result = register_modalities_to_reference(
        'patient_folder/', 
        reference_modality='t1ce',
        modalities=['t2']
    )
"""

from .registration import (
    affine_registration,
    register_to_reference,
    batch_register_folder,
    register_modalities_to_reference,
    register_file,
    register_folder,
    RegistrationConfig
)

__version__ = "1.0.0"
__author__ = "Medical Imaging Tools"

# Main public API
__all__ = [
    'register_file',
    'register_folder',
    'affine_registration',
    'register_to_reference', 
    'batch_register_folder',
    'register_modalities_to_reference',
    'RegistrationConfig'
]
