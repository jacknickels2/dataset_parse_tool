"""CSV processing and validation module."""
import json
from pathlib import Path
from typing import Dict, List, Tuple
import pandas as pd


class CSVProcessor:
    """Handles reading and validating consultation media log CSV files."""
    
    REQUIRED_FIELDS = [
        'file_name', 'media_type', 'consultation_id', 
        'profile_id', 'timestamp', 'gender', 'name', 'age'
    ]
    
    def __init__(self):
        self.validation_errors = []
        self.all_records = []
        
    def read_csv_files(self, input_dir: Path) -> pd.DataFrame:
        """
        Read all consultation_media_log.csv files from snapshot folders.
        
        Args:
            input_dir: Path to the input directory containing snapshot folders
            
        Returns:
            Combined DataFrame with all records and source snapshot info
        """
        all_dataframes = []
        
        # Find all snapshot folders
        snapshot_folders = [d for d in input_dir.iterdir() if d.is_dir()]
        
        for snapshot_folder in snapshot_folders:
            csv_file = snapshot_folder / "consultation_media_log.csv"
            
            if not csv_file.exists():
                self.validation_errors.append({
                    'type': 'missing_csv',
                    'message': f"No CSV file found in {snapshot_folder.name}"
                })
                continue
                
            try:
                df = pd.read_csv(csv_file)
                df['source_snapshot'] = snapshot_folder.name
                df['source_path'] = str(snapshot_folder)
                all_dataframes.append(df)
            except Exception as e:
                self.validation_errors.append({
                    'type': 'csv_read_error',
                    'message': f"Error reading {csv_file}: {str(e)}"
                })
                
        if not all_dataframes:
            return pd.DataFrame()
            
        combined_df = pd.concat(all_dataframes, ignore_index=True)
        return combined_df
    
    def validate_csv_data(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, List[Dict]]:
        """
        Validate CSV data for required fields and data integrity.
        
        Args:
            df: DataFrame to validate
            
        Returns:
            Tuple of (validated_df, list of validation errors)
        """
        errors = []
        
        # Check for required fields
        missing_fields = [field for field in self.REQUIRED_FIELDS if field not in df.columns]
        if missing_fields:
            errors.append({
                'type': 'missing_fields',
                'message': f"Missing required fields: {', '.join(missing_fields)}"
            })
            return df, errors
        
        # Check for empty required fields in each row
        for idx, row in df.iterrows():
            row_errors = []
            
            for field in self.REQUIRED_FIELDS:
                if pd.isna(row[field]) or str(row[field]).strip() == '':
                    row_errors.append(field)
            
            if row_errors:
                errors.append({
                    'type': 'empty_required_fields',
                    'message': f"Row {idx} (file: {row.get('file_name', 'unknown')}): "
                              f"empty fields: {', '.join(row_errors)}",
                    'row_index': idx,
                    'file_name': row.get('file_name', 'unknown')
                })
        
        # Validate media_type
        valid_media_types = ['audio', 'image']
        invalid_media = df[~df['media_type'].isin(valid_media_types)]
        for idx, row in invalid_media.iterrows():
            errors.append({
                'type': 'invalid_media_type',
                'message': f"Row {idx} (file: {row['file_name']}): "
                          f"invalid media_type '{row['media_type']}'",
                'row_index': idx,
                'file_name': row['file_name']
            })
        
        # Validate timestamp format (basic check)
        def is_valid_timestamp(ts):
            if pd.isna(ts):
                return False
            ts_str = str(ts)
            return len(ts_str) >= 8 and ts_str.isalnum()
        
        invalid_timestamps = df[~df['timestamp'].apply(is_valid_timestamp)]
        for idx, row in invalid_timestamps.iterrows():
            errors.append({
                'type': 'invalid_timestamp',
                'message': f"Row {idx} (file: {row['file_name']}): "
                          f"invalid timestamp '{row['timestamp']}'",
                'row_index': idx,
                'file_name': row['file_name']
            })
        
        # Validate symptoms JSON (if not empty)
        for idx, row in df.iterrows():
            symptoms = row.get('symptoms', '')
            if pd.notna(symptoms) and symptoms and symptoms != '[]':
                try:
                    json.loads(symptoms)
                except json.JSONDecodeError:
                    errors.append({
                        'type': 'invalid_json',
                        'message': f"Row {idx} (file: {row['file_name']}): "
                                  f"invalid JSON in symptoms field",
                        'row_index': idx,
                        'file_name': row['file_name']
                    })
        
        self.validation_errors.extend(errors)
        return df, errors
    
    def get_validation_summary(self) -> Dict:
        """Get a summary of validation errors grouped by type."""
        error_counts = {}
        for error in self.validation_errors:
            error_type = error['type']
            error_counts[error_type] = error_counts.get(error_type, 0) + 1
        
        return {
            'total_errors': len(self.validation_errors),
            'error_counts': error_counts,
            'errors': self.validation_errors
        }
