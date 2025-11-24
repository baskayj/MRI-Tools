#!/usr/bin/env python3
"""
NII Converter - Command Line Interface
======================================

Command-line interface for the NII converter tool.
"""

import argparse
import sys
import logging
from pathlib import Path

from .converter import convert_nii_file, convert_directory


def setup_logging(verbose=False):
    """Setup basic logging."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(levelname)s: %(message)s'
    )


def create_parser():
    """Create command-line argument parser."""
    parser = argparse.ArgumentParser(
        description="Convert .nii files to .nii.gz with automatic fixes for ImageJ exports",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m nii_converter.cli data.nii                    # Convert single file
  python -m nii_converter.cli input_folder/               # Convert all .nii in folder
  python -m nii_converter.cli input/ output/              # Convert with different output folder
  python -m nii_converter.cli input/ --no-recursive       # Don't search subdirectories
  python -m nii_converter.cli data.nii -v                 # Verbose output
        """
    )
    
    parser.add_argument('input', help='Input .nii file or directory')
    parser.add_argument('output', nargs='?', help='Output .nii.gz file or directory (optional)')
    parser.add_argument('-v', '--verbose', action='store_true', help='Verbose output')
    parser.add_argument('--no-recursive', action='store_true', help='Don\'t search subdirectories')
    parser.add_argument('--overwrite', action='store_true', help='Overwrite existing files')
    parser.add_argument('--offset', type=float, default=32768.0, 
                       help='Offset for signed array correction (default: 32768)')
    parser.add_argument('--no-progress', action='store_true', help='Disable progress bar')
    
    return parser


def main():
    """Main CLI entry point."""
    parser = create_parser()
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(args.verbose)
    
    input_path = Path(args.input)
    
    try:
        if input_path.is_file():
            # Convert single file
            result = convert_nii_file(
                input_path, 
                args.output, 
                check_existing=not args.overwrite,
                offset=args.offset
            )
            
            if result['success']:
                if result.get('skipped'):
                    print(f"Skipped: {input_path.name} (output exists)")
                else:
                    print(f"Converted: {input_path.name} → {Path(result['output_path']).name}")
                    if args.verbose:
                        print(f"  Size reduction: {result['file_size_reduction']}")
                        if result['fixes_applied']:
                            print(f"  Fixes applied: {', '.join(result['fixes_applied'])}")
            else:
                print(f"Failed: {result['error']}")
                return 1
                
        elif input_path.is_dir():
            # Convert directory
            summary = convert_directory(
                input_path, 
                args.output, 
                recursive=not args.no_recursive,
                offset=args.offset,
                overwrite=args.overwrite,
                show_progress=not args.no_progress
            )
            
            print(f"\nConversion Summary:")
            print(f"  Total files: {summary['total_files']}")
            print(f"  Successful: {summary['successful']}")
            print(f"  Failed: {summary['failed']}")
            print(f"  Skipped: {summary['skipped']}")
            print(f"  Success rate: {summary['success_rate']:.1f}%")
            
            if summary['failed'] > 0:
                print(f"\nFailed conversions:")
                for result in summary['results']:
                    if not result['success']:
                        print(f"  - {result.get('error', 'Unknown error')}")
                        
            return 1 if summary['failed'] > 0 else 0
            
        else:
            print(f"Error: {input_path} is not a file or directory")
            return 1
            
    except Exception as e:
        logging.error(f"Conversion failed: {str(e)}")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
