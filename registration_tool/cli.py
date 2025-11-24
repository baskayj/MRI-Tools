#!/usr/bin/env python3
"""
Registration Tool - Command Line Interface
==========================================

Command-line interface for the custom registration tool using DIPY.
Alternative to CaPTk registration for difficult cases.
"""

import argparse
import sys
import logging
from pathlib import Path

from .registration import (
    affine_registration,
    batch_register_folder,
    register_modalities_to_reference,
    RegistrationConfig
)


def setup_logging(verbose=False, quiet=False):
    """Setup logging configuration."""
    if quiet:
        level = logging.ERROR
    elif verbose:
        level = logging.DEBUG
    else:
        level = logging.INFO
        
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )


def create_parser():
    """Create command-line argument parser."""
    parser = argparse.ArgumentParser(
        description="Custom image registration tool using DIPY (alternative to CaPTk)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Register single file
  python -m registration_tool.cli moving.nii.gz reference.nii.gz -o registered.nii.gz
  
  # Register patient modalities (T2 to T1CE)
  python -m registration_tool.cli --patient-folder patient_001/ --reference t1ce
  
  # Batch register folder
  python -m registration_tool.cli --batch input_folder/ reference.nii.gz output_folder/
  
  # Register with visualization
  python -m registration_tool.cli moving.nii.gz reference.nii.gz -o output.nii.gz --show-plots
  
  # Process "no_compat" cases like in your notebook
  python -m registration_tool.cli --patient-folder meningioma_0023_no_compat/ --reference t1ce --modalities t2
        """
    )
    
    # Input specification (mutually exclusive groups)
    input_group = parser.add_mutually_exclusive_group(required=True)
    
    input_group.add_argument(
        'moving_file', nargs='?',
        help='Moving image file (for single file registration)'
    )
    
    input_group.add_argument(
        '--patient-folder',
        help='Patient folder containing multiple modalities'
    )
    
    input_group.add_argument(
        '--batch',
        help='Batch process folder of images'
    )
    
    # Reference specification
    parser.add_argument(
        'reference_file', nargs='?',
        help='Reference (static) image file'
    )
    
    parser.add_argument(
        '--reference', '--ref',
        help='Reference modality name for patient folder mode (e.g., t1ce)'
    )
    
    # Output specification
    parser.add_argument(
        '-o', '--output',
        help='Output file or folder'
    )
    
    # Processing options
    parser.add_argument(
        '--modalities', '-m',
        nargs='+',
        help='Specific modalities to register (for patient folder mode)'
    )
    
    parser.add_argument(
        '--pattern',
        default='*.nii.gz',
        help='File pattern to match (default: *.nii.gz)'
    )
    
    # Registration parameters
    parser.add_argument(
        '--nbins',
        type=int,
        default=32,
        help='Number of bins for mutual information (default: 32)'
    )
    
    parser.add_argument(
        '--level-iters',
        nargs=3,
        type=int,
        default=[10000, 1000, 100],
        help='Iterations per level (default: 10000 1000 100)'
    )
    
    parser.add_argument(
        '--sigmas',
        nargs=3,
        type=float,
        default=[3.0, 1.0, 0.0],
        help='Gaussian sigmas per level (default: 3.0 1.0 0.0)'
    )
    
    parser.add_argument(
        '--factors',
        nargs=3,
        type=int,
        default=[4, 2, 1],
        help='Subsampling factors per level (default: 4 2 1)'
    )
    
    # Visualization and output options
    parser.add_argument(
        '--show-plots',
        action='store_true',
        help='Show registration overlay plots (requires FURY)'
    )
    
    parser.add_argument(
        '--save-plots',
        action='store_true',
        help='Save registration plots to file'
    )
    
    # Logging options
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Verbose output'
    )
    
    parser.add_argument(
        '-q', '--quiet',
        action='store_true',
        help='Quiet mode (errors only)'
    )
    
    parser.add_argument(
        '--overwrite',
        action='store_true',
        help='Overwrite existing output files'
    )
    
    return parser


def validate_args(args):
    """Validate command-line arguments."""
    errors = []
    
    # Single file mode validation
    if args.moving_file:
        if not args.reference_file:
            errors.append("Reference file required for single file registration")
        
        moving_path = Path(args.moving_file)
        if not moving_path.exists():
            errors.append(f"Moving file does not exist: {args.moving_file}")
            
        ref_path = Path(args.reference_file)
        if not ref_path.exists():
            errors.append(f"Reference file does not exist: {args.reference_file}")
    
    # Patient folder mode validation
    elif args.patient_folder:
        if not args.reference:
            errors.append("--reference modality required for patient folder mode")
            
        patient_path = Path(args.patient_folder)
        if not patient_path.exists():
            errors.append(f"Patient folder does not exist: {args.patient_folder}")
        elif not patient_path.is_dir():
            errors.append(f"Patient folder is not a directory: {args.patient_folder}")
    
    # Batch mode validation
    elif args.batch:
        if not args.reference_file:
            errors.append("Reference file required for batch mode")
        if not args.output:
            errors.append("Output folder required for batch mode")
            
        batch_path = Path(args.batch)
        if not batch_path.exists():
            errors.append(f"Batch folder does not exist: {args.batch}")
    
    return errors


def main():
    """Main CLI entry point."""
    parser = create_parser()
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(args.verbose, args.quiet)
    logger = logging.getLogger(__name__)
    
    # Validate arguments
    validation_errors = validate_args(args)
    if validation_errors:
        for error in validation_errors:
            print(f"Error: {error}")
        return 1
    
    # Create registration configuration
    config = RegistrationConfig()
    config.nbins = args.nbins
    config.level_iters = args.level_iters
    config.sigmas = args.sigmas
    config.factors = args.factors
    config.show_plots = args.show_plots
    config.save_plots = args.save_plots
    
    try:
        # Single file registration
        if args.moving_file:
            output_file = args.output if args.output else None
            
            # Check if output exists
            if output_file and Path(output_file).exists() and not args.overwrite:
                print(f"Output file exists: {output_file} (use --overwrite to replace)")
                return 1
            
            logger.info(f"Registering {args.moving_file} to {args.reference_file}")
            
            result = affine_registration(
                moving_file=args.moving_file,
                static_file=args.reference_file,
                output_file=output_file,
                config=config,
                show_plots=args.show_plots
            )
            
            if result['success']:
                print(f"✓ Registration successful!")
                print(f"  Time: {result['elapsed_time']:.1f} seconds")
                if output_file:
                    print(f"  Output: {output_file}")
            else:
                print(f"✗ Registration failed: {result['error']}")
                return 1
        
        # Patient folder mode
        elif args.patient_folder:
            logger.info(f"Processing patient folder: {args.patient_folder}")
            logger.info(f"Reference modality: {args.reference}")
            
            result = register_modalities_to_reference(
                patient_folder=args.patient_folder,
                reference_modality=args.reference,
                modalities=args.modalities,
                output_folder=args.output
            )
            
            if result.get('success', True):  # No explicit success field for this function
                print(f"✓ Patient registration completed!")
                print(f"  Patient: {result['patient']}")
                print(f"  Reference: {Path(result['reference_file']).name}")
                print(f"  Successful: {result['successful']}")
                print(f"  Failed: {result['failed']}")
                
                # Show failed registrations
                if result['failed'] > 0:
                    failed_results = [r for r in result['results'] if not r['success']]
                    print(f"  Failed registrations:")
                    for failed in failed_results:
                        print(f"    - {failed.get('modality', 'unknown')}: {failed['error']}")
            else:
                print(f"✗ Patient processing failed: {result['error']}")
                return 1
        
        # Batch mode
        elif args.batch:
            logger.info(f"Batch processing: {args.batch}")
            
            summary = batch_register_folder(
                input_folder=args.batch,
                reference_file=args.reference_file,
                output_folder=args.output,
                pattern=args.pattern
            )
            
            print(f"✓ Batch registration completed!")
            print(f"  Total files: {summary['total_files']}")
            print(f"  Successful: {summary['successful']}")
            print(f"  Failed: {summary['failed']}")
            print(f"  Success rate: {summary['success_rate']:.1f}%")
            
            # Show failed registrations
            if summary['failed'] > 0:
                failed_results = [r for r in summary['results'] if not r['success']]
                print(f"  Failed registrations:")
                for failed in failed_results[:5]:  # Show first 5 failures
                    input_file = Path(failed['input_file']).name
                    print(f"    - {input_file}: {failed['error']}")
                if len(failed_results) > 5:
                    print(f"    ... and {len(failed_results) - 5} more")
            
            return 1 if summary['failed'] > 0 else 0
        
    except KeyboardInterrupt:
        print("\nRegistration interrupted by user")
        return 1
    except Exception as e:
        logger.error(f"Registration failed: {str(e)}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
