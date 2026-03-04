"""Main entry point for the Dataset Parse Tool."""
import sys
from datetime import datetime
from pathlib import Path

from .config_parser import ConfigParser
from .csv_processor import CSVProcessor
from .file_processor import FileProcessor
from .statistics_generator import StatisticsGenerator
from .visualizations import VisualizationGenerator


def main():
    """Main function to orchestrate the dataset parsing process."""
    print("=" * 80)
    print("Dataset Parse Tool")
    print("=" * 80)
    print()
    
    # Define paths
    project_root = Path(__file__).parent.parent.parent
    
    # Load configuration
    print("Loading configuration...")
    try:
        config_parser = ConfigParser()
        config = config_parser.load_config(project_root)
        print(f"  ✓ Configuration loaded from {config_parser.config_path.name}")
    except Exception as e:
        print(f"ERROR: Failed to load configuration: {e}")
        sys.exit(1)
    
    # Get paths from config
    input_dir, output_base = config_parser.get_resolved_paths()
    
    # Create output directory
    if config.paths.get('use_timestamp', True):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = output_base / f"parsed_dataset_{timestamp}"
    else:
        output_dir = output_base / "parsed_dataset"
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    verbosity = config.get('logging.verbosity', 'normal')
    
    if verbosity != 'quiet':
        print(f"Input directory:  {input_dir}")
        print(f"Output directory: {output_dir}")
        
        # Show active exclusions
        exclusions = config.exclusions
        if (exclusions['excluded_profiles'] or exclusions['excluded_date_ranges'] or 
            exclusions['excluded_consultations'] or exclusions['excluded_files']):
            print("\nActive exclusion rules:")
            if exclusions['excluded_profiles']:
                print(f"  • Profiles: {exclusions['excluded_profiles']}")
            if exclusions['excluded_consultations']:
                print(f"  • Consultations: {exclusions['excluded_consultations']}")
            if exclusions['excluded_date_ranges']:
                print(f"  • Date ranges: {exclusions['excluded_date_ranges']}")
            if exclusions['excluded_files']:
                print(f"  • Files: {len(exclusions['excluded_files'])} filename(s)")
        print()
    
    # Check if input directory exists
    if not input_dir.exists():
        print(f"ERROR: Input directory not found: {input_dir}")
        sys.exit(1)
    
    # Step 1: Read and validate CSV files
    if verbosity != 'quiet':
        print("Step 1: Reading CSV files from snapshots...")
    csv_processor = CSVProcessor()
    df = csv_processor.read_csv_files(input_dir)
    
    if df.empty:
        print("ERROR: No data found in CSV files.")
        sys.exit(1)
    
    if verbosity != 'quiet':
        print(f"  ✓ Found {len(df)} total records from {df['source_snapshot'].nunique()} snapshots")
    
    # Step 2: Validate CSV data (if enabled)
    if config.validation.get('check_required_fields', True):
        if verbosity != 'quiet':
            print("\nStep 2: Validating CSV data...")
        df, csv_errors = csv_processor.validate_csv_data(df)
        csv_validation = csv_processor.get_validation_summary()
        if verbosity != 'quiet':
            print(f"  ✓ Validation complete: {csv_validation['total_errors']} errors found")
    else:
        csv_validation = {'total_errors': 0, 'error_counts': {}, 'errors': []}
        if verbosity != 'quiet':
            print("\nStep 2: Skipping CSV validation (disabled in config)")
    
    # Step 3: Apply manual exclusions
    if verbosity != 'quiet':
        print("\nStep 3: Applying manual exclusions...")
    file_processor = FileProcessor()
    df = file_processor.apply_exclusions(df, config_parser)
    exclusions_count = len(df[df['is_excluded'] == True])
    if verbosity != 'quiet':
        print(f"  ✓ {exclusions_count} records excluded by config rules")
    
    # Step 4: Identify duplicates
    if verbosity != 'quiet':
        print("\nStep 4: Identifying duplicates...")
    df, duplicate_info = file_processor.identify_duplicates(df)
    duplicates_count = len(df[df['is_duplicate'] == True])
    # Count only non-excluded, non-duplicate records
    unique_count = len(df[(df['is_duplicate'] == False) & (df['is_excluded'] == False)])
    if verbosity != 'quiet':
        print(f"  ✓ Found {duplicates_count} duplicates")
        print(f"  ✓ {unique_count} unique records remaining after exclusions")
    
    # Step 5: Validate files (if enabled)
    if config.validation.get('check_file_existence', True) or config.validation.get('check_file_formats', True):
        if verbosity != 'quiet':
            print("\nStep 5: Validating files...")
        file_processor.validate_files(df)
        file_validation = file_processor.get_validation_summary()
        if verbosity != 'quiet':
            print(f"  ✓ Missing files: {file_validation['missing_files']}")
            print(f"  ✓ Orphaned files: {file_validation['orphaned_files']}")
            print(f"  ✓ Invalid formats: {file_validation['invalid_formats']}")
    else:
        file_validation = file_processor.get_validation_summary()
        if verbosity != 'quiet':
            print("\nStep 5: Skipping file validation (disabled in config)")
    
    # Step 6: Copy unique files to output (if enabled)
    if config.output.get('copy_files', True):
        if verbosity != 'quiet':
            print("\nStep 6: Copying unique files to output directory...")
        copy_stats = file_processor.copy_unique_files(df, output_dir)
        if verbosity != 'quiet':
            print(f"  ✓ Copied {copy_stats['copied_audio']} audio files")
            print(f"  ✓ Copied {copy_stats['copied_images']} image files")
            if copy_stats['failed_copies']:
                print(f"  ⚠ {len(copy_stats['failed_copies'])} files failed to copy")
    else:
        copy_stats = {'copied_audio': 0, 'copied_images': 0, 'failed_copies': []}
        if verbosity != 'quiet':
            print("\nStep 6: Skipping file copy (disabled in config)")
    
    # Step 7: Save consolidated CSV (if enabled)
    if config.output.get('generate_csv', True):
        if verbosity != 'quiet':
            print("\nStep 7: Saving consolidated CSV...")
        # Filter to only non-duplicate, non-excluded records
        unique_df = df[(df['is_duplicate'] == False) & (df.get('is_excluded', False) == False)].copy()
        
        # Drop internal columns before saving based on config
        columns_to_drop = ['source_path', 'is_duplicate', 'duplicate_reason', 'file_hash', 
                          'is_excluded', 'exclusion_reason']
        
        # Keep columns based on config
        if not config.get('output.csv.include_source_snapshot', True):
            columns_to_drop.append('source_snapshot')
        if not config.get('output.csv.include_file_hash', False):
            columns_to_drop.append('file_hash')
        
        unique_df_clean = unique_df.drop(columns=[col for col in columns_to_drop if col in unique_df.columns])
        
        csv_output_path = output_dir / "consolidated_media_log.csv"
        unique_df_clean.to_csv(csv_output_path, index=False)
        if verbosity != 'quiet':
            print(f"  ✓ Saved consolidated CSV with {len(unique_df)} records")
    else:
        unique_df = df[(df['is_duplicate'] == False) & (df.get('is_excluded', False) == False)].copy()
        if verbosity != 'quiet':
            print("\nStep 7: Skipping CSV generation (disabled in config)")
    
    # Step 8: Generate statistics (if enabled)
    if config.statistics.get('calculate_demographics', True):
        if verbosity != 'quiet':
            print("\nStep 8: Generating statistics...")
        stats_generator = StatisticsGenerator()
        stats = stats_generator.generate_statistics(df, unique_df)
        if verbosity != 'quiet':
            print(f"  ✓ Statistics generated")
    else:
        stats = {}
        if verbosity != 'quiet':
            print("\nStep 8: Skipping statistics generation (disabled in config)")
    
    # Step 9: Create summary reports (if enabled)
    if config.output.get('generate_summary_report', True) or config.output.get('generate_errors_report', True):
        if verbosity != 'quiet':
            print("\nStep 9: Creating summary reports...")
        
        if stats and config.output.get('generate_summary_report', True):
            summary_report_path = stats_generator.create_summary_report(
                stats, csv_validation, file_validation, copy_stats, output_dir
            )
            if verbosity != 'quiet':
                print(f"  ✓ Summary report: {Path(summary_report_path).name}")
        
        if config.output.get('generate_errors_report', True):
            errors_report_path = stats_generator.create_detailed_errors_report(
                csv_validation, file_validation, output_dir
            )
            if verbosity != 'quiet':
                print(f"  ✓ Errors report: {Path(errors_report_path).name}")
    else:
        if verbosity != 'quiet':
            print("\nStep 9: Skipping report generation (disabled in config)")
    
    # Step 10: Generate visualizations (if enabled)
    if config.output.get('generate_visualizations', True) and stats:
        if verbosity != 'quiet':
            print("\nStep 10: Generating visualizations...")
        viz_generator = VisualizationGenerator()
        viz_generator.create_all_visualizations(stats, df, unique_df, output_dir)
        
        if config.output.get('generate_dashboard', True):
            viz_generator.create_summary_dashboard(stats, output_dir / "visualizations")
        
        if verbosity != 'quiet':
            print(f"  ✓ Visualizations saved to visualizations/")
    else:
        if verbosity != 'quiet':
            if not stats:
                print("\nStep 10: Skipping visualizations (no statistics available)")
            else:
                print("\nStep 10: Skipping visualizations (disabled in config)")
    
    # Final summary
    if verbosity != 'quiet':
        print("\n" + "=" * 80)
        print("PROCESSING COMPLETE")
        print("=" * 80)
        print(f"\nOutput location: {output_dir}")
        print("\nGenerated files:")
        if config.output.get('copy_files', True):
            print(f"  • audio/              - {copy_stats['copied_audio']} audio files")
            print(f"  • images/             - {copy_stats['copied_images']} image files")
        if config.output.get('generate_csv', True):
            print(f"  • consolidated_media_log.csv - {len(unique_df)} records")
        if config.output.get('generate_summary_report', True):
            print(f"  • summary_report.txt  - Overview and statistics")
        if config.output.get('generate_errors_report', True):
            print(f"  • errors_report.txt   - Detailed errors and warnings")
        if config.output.get('generate_visualizations', True) and stats:
            print(f"  • visualizations/     - Charts and graphs")
        
        if exclusions_count > 0:
            print(f"\nExcluded {exclusions_count} records based on config rules")
        print()
        print("=" * 80)


if __name__ == "__main__":
    main()
