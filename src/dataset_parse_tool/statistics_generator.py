"""Statistics generation and report creation module."""
import json
from datetime import datetime
from pathlib import Path
from typing import Dict
import pandas as pd


class StatisticsGenerator:
    """Generates statistics and creates summary reports."""
    
    def __init__(self):
        self.stats = {}
        
    def generate_statistics(self, df: pd.DataFrame, unique_df: pd.DataFrame) -> Dict:
        """
        Generate comprehensive statistics from the dataset.
        
        Args:
            df: Complete DataFrame with all records
            unique_df: DataFrame with only unique (non-duplicate) records
            
        Returns:
            Dictionary containing all statistics
        """
        stats = {}
        
        # File counts and types
        stats['file_counts'] = {
            'total_records': len(df),
            'unique_records': len(unique_df),
            'duplicate_records': len(df[df['is_duplicate'] == True]),
            'audio_files': len(unique_df[unique_df['media_type'] == 'audio']),
            'image_files': len(unique_df[unique_df['media_type'] == 'image']),
            'total_unique_files': len(unique_df)
        }
        
        # Snapshot information
        stats['snapshots'] = {
            'total_snapshots': df['source_snapshot'].nunique(),
            'snapshot_names': sorted(df['source_snapshot'].unique().tolist()),
            'records_per_snapshot': df.groupby('source_snapshot').size().to_dict()
        }
        
        # Patient demographics
        stats['demographics'] = self._calculate_demographics(unique_df)
        
        # Date/Time ranges
        stats['temporal'] = self._calculate_temporal_stats(unique_df)
        
        # Consultation statistics
        stats['consultations'] = {
            'total_consultations': unique_df['consultation_id'].nunique(),
            'total_profiles': unique_df['profile_id'].nunique(),
            'consultations_with_symptoms': len(unique_df[unique_df['symptoms'].notna() & (unique_df['symptoms'] != '[]')]),
            'consultations_with_prescriptions': len(unique_df[unique_df['prescription'].notna() & (unique_df['prescription'] != '')]),
            'consultations_with_notes': len(unique_df[unique_df['physician_note'].notna() & (unique_df['physician_note'] != '')])
        }
        
        # Media type distribution by consultation
        stats['media_distribution'] = self._calculate_media_distribution(unique_df)
        
        self.stats = stats
        return stats
    
    def _calculate_demographics(self, df: pd.DataFrame) -> Dict:
        """Calculate patient demographic statistics."""
        demographics = {}
        
        # Gender distribution
        gender_counts = df['gender'].value_counts().to_dict()
        demographics['gender_distribution'] = gender_counts
        
        # Age statistics
        try:
            # Convert age to numeric, handling any non-numeric values
            ages = pd.to_numeric(df['age'], errors='coerce').dropna()
            if len(ages) > 0:
                demographics['age_stats'] = {
                    'min': int(ages.min()),
                    'max': int(ages.max()),
                    'mean': round(ages.mean(), 2),
                    'median': round(ages.median(), 2)
                }
                
                # Age groups
                age_groups = pd.cut(ages, bins=[0, 18, 30, 50, 70, 100], 
                                   labels=['0-18', '19-30', '31-50', '51-70', '71+'])
                demographics['age_groups'] = age_groups.value_counts().to_dict()
            else:
                demographics['age_stats'] = None
        except Exception:
            demographics['age_stats'] = None
        
        # Unique patients
        demographics['unique_profiles'] = df['profile_id'].nunique()
        
        return demographics
    
    def _calculate_temporal_stats(self, df: pd.DataFrame) -> Dict:
        """Calculate temporal statistics."""
        temporal = {}
        
        try:
            # Parse timestamps (format: YYYYMMDDTHHMMSS)
            def parse_timestamp(ts):
                try:
                    ts_str = str(ts)
                    if 'T' in ts_str:
                        date_part, time_part = ts_str.split('T')
                        return pd.to_datetime(date_part, format='%Y%m%d')
                    return pd.to_datetime(ts_str, format='%Y%m%d')
                except:
                    return None
            
            timestamps = df['timestamp'].apply(parse_timestamp).dropna()
            
            if len(timestamps) > 0:
                temporal['earliest_consultation'] = timestamps.min().strftime('%Y-%m-%d')
                temporal['latest_consultation'] = timestamps.max().strftime('%Y-%m-%d')
                temporal['date_range_days'] = (timestamps.max() - timestamps.min()).days
                
                # Consultations by month
                monthly = timestamps.dt.to_period('M').value_counts().sort_index()
                temporal['consultations_by_month'] = {str(k): int(v) for k, v in monthly.items()}
            else:
                temporal['earliest_consultation'] = None
                temporal['latest_consultation'] = None
        except Exception as e:
            temporal['error'] = str(e)
        
        return temporal
    
    def _calculate_media_distribution(self, df: pd.DataFrame) -> Dict:
        """Calculate media type distribution patterns."""
        distribution = {}
        
        # Files by media type and body part (extracted from filename)
        body_parts = []
        for filename in df['file_name']:
            parts = filename.split('_')
            if parts:
                body_parts.append(parts[0])
        
        df_copy = df.copy()
        df_copy['body_part'] = body_parts
        
        distribution['files_by_body_part'] = df_copy['body_part'].value_counts().to_dict()
        
        # Media per consultation
        media_per_consultation = df.groupby('consultation_id').size()
        distribution['media_per_consultation'] = {
            'min': int(media_per_consultation.min()),
            'max': int(media_per_consultation.max()),
            'mean': round(media_per_consultation.mean(), 2)
        }
        
        return distribution
    
    def create_summary_report(self, stats: Dict, csv_validation: Dict, 
                            file_validation: Dict, copy_stats: Dict,
                            output_path: Path) -> str:
        """
        Create a comprehensive text summary report.
        
        Args:
            stats: Statistics dictionary
            csv_validation: CSV validation results
            file_validation: File validation results
            copy_stats: File copy statistics
            output_path: Path to save the report
            
        Returns:
            Path to the saved report
        """
        report_lines = []
        
        # Header
        report_lines.append("=" * 80)
        report_lines.append("DATASET PARSING SUMMARY REPORT")
        report_lines.append("=" * 80)
        report_lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report_lines.append("")
        
        # File Counts and Types
        report_lines.append("FILE COUNTS AND TYPES")
        report_lines.append("-" * 80)
        fc = stats['file_counts']
        report_lines.append(f"Total Records Processed:    {fc['total_records']}")
        report_lines.append(f"Unique Records:             {fc['unique_records']}")
        report_lines.append(f"Duplicate Records Removed:  {fc['duplicate_records']}")
        report_lines.append(f"  - Audio Files:            {fc['audio_files']}")
        report_lines.append(f"  - Image Files:            {fc['image_files']}")
        report_lines.append("")
        
        # Snapshot Information
        report_lines.append("SNAPSHOT INFORMATION")
        report_lines.append("-" * 80)
        report_lines.append(f"Total Snapshots Processed:  {stats['snapshots']['total_snapshots']}")
        report_lines.append(f"Snapshots:")
        for snapshot in stats['snapshots']['snapshot_names']:
            count = stats['snapshots']['records_per_snapshot'][snapshot]
            report_lines.append(f"  - {snapshot}: {count} records")
        report_lines.append("")
        
        # Patient Demographics
        report_lines.append("PATIENT DEMOGRAPHICS")
        report_lines.append("-" * 80)
        demo = stats['demographics']
        report_lines.append(f"Unique Patient Profiles:    {demo['unique_profiles']}")
        report_lines.append(f"Gender Distribution:")
        for gender, count in demo['gender_distribution'].items():
            report_lines.append(f"  - {gender}: {count}")
        
        if demo.get('age_stats'):
            age_stats = demo['age_stats']
            report_lines.append(f"Age Statistics:")
            report_lines.append(f"  - Range: {age_stats['min']} - {age_stats['max']} years")
            report_lines.append(f"  - Mean: {age_stats['mean']} years")
            report_lines.append(f"  - Median: {age_stats['median']} years")
            
            if demo.get('age_groups'):
                report_lines.append(f"Age Groups:")
                for group, count in sorted(demo['age_groups'].items()):
                    report_lines.append(f"  - {group}: {count}")
        report_lines.append("")
        
        # Temporal Information
        report_lines.append("TEMPORAL INFORMATION")
        report_lines.append("-" * 80)
        temporal = stats['temporal']
        if temporal.get('earliest_consultation'):
            report_lines.append(f"Date Range:                 {temporal['earliest_consultation']} to {temporal['latest_consultation']}")
            report_lines.append(f"Total Days Covered:         {temporal['date_range_days']}")
            if temporal.get('consultations_by_month'):
                report_lines.append(f"Consultations by Month:")
                for month, count in sorted(temporal['consultations_by_month'].items()):
                    report_lines.append(f"  - {month}: {count}")
        report_lines.append("")
        
        # Consultation Statistics
        report_lines.append("CONSULTATION STATISTICS")
        report_lines.append("-" * 80)
        consult = stats['consultations']
        report_lines.append(f"Total Consultations:        {consult['total_consultations']}")
        report_lines.append(f"With Symptoms:              {consult['consultations_with_symptoms']}")
        report_lines.append(f"With Prescriptions:         {consult['consultations_with_prescriptions']}")
        report_lines.append(f"With Physician Notes:       {consult['consultations_with_notes']}")
        report_lines.append("")
        
        # Media Distribution
        report_lines.append("MEDIA DISTRIBUTION")
        report_lines.append("-" * 80)
        media_dist = stats['media_distribution']
        report_lines.append(f"Files by Body Part/Type:")
        for part, count in sorted(media_dist['files_by_body_part'].items(), 
                                  key=lambda x: x[1], reverse=True)[:10]:
            report_lines.append(f"  - {part}: {count}")
        
        mpc = media_dist['media_per_consultation']
        report_lines.append(f"Media per Consultation:")
        report_lines.append(f"  - Min: {mpc['min']}, Max: {mpc['max']}, Mean: {mpc['mean']}")
        report_lines.append("")
        
        # Data Quality Metrics
        report_lines.append("DATA QUALITY METRICS")
        report_lines.append("-" * 80)
        report_lines.append(f"CSV Validation Errors:      {csv_validation['total_errors']}")
        if csv_validation['total_errors'] > 0:
            for error_type, count in csv_validation['error_counts'].items():
                report_lines.append(f"  - {error_type}: {count}")
        
        report_lines.append(f"Missing Files:              {file_validation['missing_files']}")
        report_lines.append(f"Orphaned Files:             {file_validation['orphaned_files']}")
        report_lines.append(f"Invalid File Formats:       {file_validation['invalid_formats']}")
        report_lines.append(f"Duplicates Detected:        {file_validation['duplicates']}")
        report_lines.append(f"Manual Exclusions:          {file_validation.get('exclusions', 0)}")
        report_lines.append("")
        
        # File Copy Results
        report_lines.append("FILE COPY RESULTS")
        report_lines.append("-" * 80)
        report_lines.append(f"Audio Files Copied:         {copy_stats['copied_audio']}")
        report_lines.append(f"Image Files Copied:         {copy_stats['copied_images']}")
        report_lines.append(f"Failed Copies:              {len(copy_stats['failed_copies'])}")
        report_lines.append("")
        
        # Footer
        report_lines.append("=" * 80)
        report_lines.append("END OF REPORT")
        report_lines.append("=" * 80)
        
        # Write report to file
        report_text = "\n".join(report_lines)
        report_path = output_path / "summary_report.txt"
        report_path.write_text(report_text)
        
        return str(report_path)
    
    def create_detailed_errors_report(self, csv_validation: Dict, 
                                     file_validation: Dict, 
                                     output_path: Path) -> str:
        """
        Create a detailed errors report.
        
        Args:
            csv_validation: CSV validation results
            file_validation: File validation results
            output_path: Path to save the report
            
        Returns:
            Path to the saved report
        """
        report_lines = []
        
        report_lines.append("=" * 80)
        report_lines.append("DETAILED ERRORS AND WARNINGS REPORT")
        report_lines.append("=" * 80)
        report_lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report_lines.append("")
        
        # CSV Validation Errors
        if csv_validation['total_errors'] > 0:
            report_lines.append("CSV VALIDATION ERRORS")
            report_lines.append("-" * 80)
            for error in csv_validation['errors'][:100]:  # Limit to first 100
                report_lines.append(f"[{error['type']}] {error['message']}")
            if len(csv_validation['errors']) > 100:
                report_lines.append(f"... and {len(csv_validation['errors']) - 100} more errors")
            report_lines.append("")
        
        # Missing Files
        details = file_validation['details']
        if details['missing_files']:
            report_lines.append("MISSING FILES")
            report_lines.append("-" * 80)
            for item in details['missing_files'][:100]:
                report_lines.append(f"File: {item['file_name']}")
                report_lines.append(f"  Expected at: {item['expected_path']}")
                report_lines.append(f"  Snapshot: {item['snapshot']}")
            if len(details['missing_files']) > 100:
                report_lines.append(f"... and {len(details['missing_files']) - 100} more missing files")
            report_lines.append("")
        
        # Orphaned Files
        if details['orphaned_files']:
            report_lines.append("ORPHANED FILES (Found in folders but not in CSV)")
            report_lines.append("-" * 80)
            for item in details['orphaned_files'][:100]:
                report_lines.append(f"File: {item['file']}")
                report_lines.append(f"  Snapshot: {item['snapshot']}")
            if len(details['orphaned_files']) > 100:
                report_lines.append(f"... and {len(details['orphaned_files']) - 100} more orphaned files")
            report_lines.append("")
        
        # Invalid Formats
        if details['invalid_formats']:
            report_lines.append("INVALID FILE FORMATS")
            report_lines.append("-" * 80)
            for item in details['invalid_formats'][:100]:
                report_lines.append(f"File: {item['file_name']}")
                report_lines.append(f"  Expected Type: {item['media_type']}")
                report_lines.append(f"  Snapshot: {item['snapshot']}")
            if len(details['invalid_formats']) > 100:
                report_lines.append(f"... and {len(details['invalid_formats']) - 100} more invalid formats")
            report_lines.append("")
        
        # Duplicates
        if details['duplicates']:
            report_lines.append("DUPLICATE FILES REMOVED")
            report_lines.append("-" * 80)
            for item in details['duplicates'][:100]:
                report_lines.append(f"File: {item['file_name']}")
                report_lines.append(f"  Reason: {item['reason']}")
                report_lines.append(f"  Snapshot: {item['snapshot']}")
            if len(details['duplicates']) > 100:
                report_lines.append(f"... and {len(details['duplicates']) - 100} more duplicates")
            report_lines.append("")
        
        # Manual Exclusions
        if details.get('exclusions'):
            report_lines.append("MANUAL EXCLUSIONS (FROM CONFIG)")
            report_lines.append("-" * 80)
            for item in details['exclusions'][:100]:
                report_lines.append(f"File: {item['file_name']}")
                report_lines.append(f"  Reason: {item['reason']}")
                report_lines.append(f"  Profile: {item.get('profile_id')}, Consultation: {item.get('consultation_id')}")
                report_lines.append(f"  Snapshot: {item['snapshot']}")
            if len(details['exclusions']) > 100:
                report_lines.append(f"... and {len(details['exclusions']) - 100} more exclusions")
            report_lines.append("")
        
        report_lines.append("=" * 80)
        report_lines.append("END OF ERRORS REPORT")
        report_lines.append("=" * 80)
        
        # Write report to file
        report_text = "\n".join(report_lines)
        report_path = output_path / "errors_report.txt"
        report_path.write_text(report_text)
        
        return str(report_path)
