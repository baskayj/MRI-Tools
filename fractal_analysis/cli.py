#!/usr/bin/env python3
"""
Fractal Analysis Tool - Command Line Interface
==============================================

Command-line interface for fractal analysis of medical imaging datasets.
Measures fractal dimension on segmentations and lacunarity on image intensities.
"""

import argparse
import sys
import logging
from pathlib import Path

from .analyzer import (
    analyze_patient_folder,
    batch_analyze_dataset,
    FractalConfig
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
        description="Fractal analysis for medical imaging datasets",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Analyze single patient
  python -m fractal_analysis.cli --patient patient_001/ -o results/
  
  # Analyze entire dataset  
  python -m fractal_analysis.cli --dataset input_data/ -o fractal_results/
  
  # Analyze specific modalities only
  python -m fractal_analysis.cli --dataset data/ -o results/ --modalities t1ce t2
  
  # Custom fractal parameters
  python -m fractal_analysis.cli --patient patient_001/ -o results/ --n-samples 50 --stride 1
  
  # Resume dataset analysis from patient 10
  python -m fractal_analysis.cli --dataset data/ -o results/ --start-from 10
        """
    )
    
    # Input specification (mutually exclusive)
    input_group = parser.add_mutually_exclusive_group(required=True)
    
    input_group.add_argument(
        '--patient',
        help='Single patient folder to analyze'
    )
    
    input_group.add_argument(
        '--dataset',
        help='Dataset folder containing multiple patients'
    )
    
    # Output specification
    parser.add_argument(
        '-o', '--output',
        required=True,
        help='Output folder for results and plots'
    )
    
    # Analysis options
    parser.add_argument(
        '--modalities', '-m',
        nargs='+',
        default=['t1', 't1ce', 't2', 'flair'],
        help='Modalities to analyze for lacunarity (default: t1 t1ce t2 flair)'
    )
    
    # Fractal analysis parameters
    parser.add_argument(
        '--n-samples',
        type=int,
        default=100,
        help='Number of scale samples for fractal analysis (default: 100)'
    )
    
    parser.add_argument(
        '--stride',
        type=int,
        default=2,
        help='Stride for sliding window (default: 2)'
    )
    
    parser.add_argument(
        '--subsample-intensity',
        type=float,
        default=0.01,
        help='Subsampling rate for intensity analysis (default: 0.01)'
    )
    
    parser.add_argument(
        '--intensity-levels',
        type=int,
        default=255,
        help='Number of intensity levels for binary conversion (default: 255)'
    )
    
    # Dataset processing options
    parser.add_argument(
        '--start-from',
        type=int,
        default=0,
        help='Patient index to start from (for resuming dataset analysis)'
    )
    
    parser.add_argument(
        '--no-intermediate-save',
        action='store_true',
        help='Disable saving results after each patient'
    )
    
    # Output options
    parser.add_argument(
        '--no-plots',
        action='store_true',
        help='Disable plot generation'
    )
    
    parser.add_argument(
        '--plot-format',
        choices=['png', 'pdf', 'svg'],
        default='png',
        help='Plot file format (default: png)'
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
    
    return parser


def validate_args(args):
    """Validate command-line arguments."""
    errors = []
    
    # Check input paths
    if args.patient:
        patient_path = Path(args.patient)
        if not patient_path.exists():
            errors.append(f"Patient folder does not exist: {args.patient}")
        elif not patient_path.is_dir():
            errors.append(f"Patient path is not a directory: {args.patient}")
    
    elif args.dataset:
        dataset_path = Path(args.dataset)
        if not dataset_path.exists():
            errors.append(f"Dataset folder does not exist: {args.dataset}")
        elif not dataset_path.is_dir():
            errors.append(f"Dataset path is not a directory: {args.dataset}")
    
    # Check for reasonable parameter values
    if args.n_samples < 10:
        errors.append("Number of samples should be at least 10")
    
    if args.stride < 1:
        errors.append("Stride must be at least 1")
    
    if args.subsample_intensity <= 0 or args.subsample_intensity > 1:
        errors.append("Subsample rate must be between 0 and 1")
    
    if args.start_from < 0:
        errors.append("Start-from index must be non-negative")
    
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
    
    # Check FracND availability
    try:
        from .analyzer import validate_fracnd
        validate_fracnd()
    except ImportError as e:
        print(f"Error: {e}")
        print("Please ensure 'fracnd.py' is available in your Python path.")
        return 1
    
    # Create configuration
    config = FractalConfig()
    config.n_samples = args.n_samples
    config.stride = args.stride
    config.subsample_intensity = args.subsample_intensity
    config.intensity_levels = args.intensity_levels
    config.save_plots = not args.no_plots
    config.plot_format = args.plot_format
    
    try:
        # Single patient analysis
        if args.patient:
            logger.info(f"Analyzing patient: {args.patient}")
            
            result = analyze_patient_folder(
                patient_folder=args.patient,
                modalities=args.modalities,
                config=config,
                output_folder=args.output
            )
            
            print(f"✓ Patient analysis completed!")
            print(f"  Patient: {result['patient_id']}")
            print(f"  Segmentation FD: {result['segmentation']['FD']:.3f}")
            print(f"  Segmentation LD: {result['segmentation']['LD']:.3f}")
            
            # Show modality results
            successful_modalities = [mod for mod, res in result['modalities'].items() 
                                   if 'error' not in res]
            failed_modalities = [mod for mod, res in result['modalities'].items() 
                               if 'error' in res]
            
            print(f"  Modalities analyzed: {len(successful_modalities)}")
            for modality in successful_modalities:
                ld_value = result['modalities'][modality]['LD']
                print(f"    {modality.upper()} LD: {ld_value:.3f}")
            
            if failed_modalities:
                print(f"  Failed modalities: {', '.join(failed_modalities)}")
        
        # Dataset analysis
        elif args.dataset:
            logger.info(f"Analyzing dataset: {args.dataset}")
            
            summary = batch_analyze_dataset(
                input_folder=args.dataset,
                output_folder=args.output,
                modalities=args.modalities,
                config=config,
                start_from=args.start_from,
                save_intermediate=not args.no_intermediate_save
            )
            
            print(f"✓ Dataset analysis completed!")
            print(f"  Total patients: {summary['total_patients']}")
            print(f"  Successful: {summary['successful']}")
            print(f"  Failed: {summary['failed']}")
            print(f"  Success rate: {summary['success_rate']:.1f}%")
            print(f"  Results saved to: {summary['results_file']}")
            
            if config.save_plots:
                print(f"  Plots saved to: {summary['plots_directory']}")
            
            # Show failed cases
            if summary['failed'] > 0:
                print(f"  Some analyses failed - check logs for details")
            
            return 1 if summary['failed'] > 0 else 0
        
    except KeyboardInterrupt:
        print("\nAnalysis interrupted by user")
        return 1
    except Exception as e:
        logger.error(f"Analysis failed: {str(e)}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
