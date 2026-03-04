"""File processing, hashing, and deduplication module."""
import hashlib
import shutil
from pathlib import Path
from typing import Dict, List, Set, Tuple
import pandas as pd
from PIL import Image


class FileProcessor:
    """Handles file operations, validation, and duplicate detection."""
    
    AUDIO_EXTENSIONS = {'.mp3', '.wav', '.m4a', '.aac', '.ogg', '.flac'}
    IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp'}
    
    def __init__(self):
        self.file_hashes = {}
        self.duplicate_records = []
        self.missing_files = []
        self.orphaned_files = []
        self.invalid_formats = []
        self.processed_keys = set()
        self.excluded_records = []
        
    def calculate_file_hash(self, file_path: Path) -> str:
        """
        Calculate SHA256 hash of a file.
        
        Args:
            file_path: Path to the file
            
        Returns:
            Hex string of the file hash
        """
        sha256_hash = hashlib.sha256()
        
        try:
            with open(file_path, "rb") as f:
                # Read file in chunks to handle large files
                for byte_block in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(byte_block)
            return sha256_hash.hexdigest()
        except Exception as e:
            return None
    
    def create_record_key(self, row: pd.Series) -> str:
        """
        Create a unique key for a record based on metadata.
        
        Args:
            row: DataFrame row
            
        Returns:
            Unique key string
        """
        return f"{row['consultation_id']}_{row['profile_id']}_{row['timestamp']}_{row['file_name']}"
    
    def apply_exclusions(self, df: pd.DataFrame, config_parser) -> pd.DataFrame:
        """
        Apply manual exclusions from config to the DataFrame.
        
        Args:
            df: DataFrame with records
            config_parser: ConfigParser instance with exclusion rules
            
        Returns:
            DataFrame with is_excluded and exclusion_reason columns added
        """
        df['is_excluded'] = False
        df['exclusion_reason'] = ''
        
        # Check each record against exclusion rules
        for idx, row in df.iterrows():
            should_exclude, reason = config_parser.should_exclude_record(row.to_dict())
            
            if should_exclude:
                df.at[idx, 'is_excluded'] = True
                df.at[idx, 'exclusion_reason'] = reason
                self.excluded_records.append({
                    'file_name': row['file_name'],
                    'snapshot': row['source_snapshot'],
                    'reason': reason,
                    'profile_id': row.get('profile_id'),
                    'consultation_id': row.get('consultation_id'),
                    'timestamp': row.get('timestamp')
                })
        
        return df
    
    def validate_file_format(self, file_path: Path, media_type: str) -> bool:
        """
        Validate that a file matches its expected media type and format.
        
        Args:
            file_path: Path to the file
            media_type: Expected media type ('audio' or 'image')
            
        Returns:
            True if valid, False otherwise
        """
        if not file_path.exists():
            return False
            
        ext = file_path.suffix.lower()
        
        if media_type == 'audio':
            return ext in self.AUDIO_EXTENSIONS
        elif media_type == 'image':
            if ext not in self.IMAGE_EXTENSIONS:
                return False
            # Try to open the image to verify it's valid
            try:
                with Image.open(file_path) as img:
                    img.verify()
                return True
            except Exception:
                return False
        
        return False
    
    def find_orphaned_files(self, snapshot_dir: Path, csv_files: Set[str]) -> List[str]:
        """
        Find files in audio/images folders that aren't in the CSV.
        
        Args:
            snapshot_dir: Path to the snapshot directory
            csv_files: Set of filenames from CSV
            
        Returns:
            List of orphaned file paths
        """
        orphaned = []
        
        for subfolder in ['audio', 'images']:
            folder_path = snapshot_dir / subfolder
            if not folder_path.exists():
                continue
                
            for file_path in folder_path.iterdir():
                if file_path.is_file() and file_path.name not in csv_files:
                    orphaned.append(str(file_path.relative_to(snapshot_dir)))
        
        return orphaned
    
    def identify_duplicates(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, List[Dict]]:
        """
        Identify and mark duplicate records based on metadata and file hashes.
        
        Args:
            df: DataFrame with all records
            
        Returns:
            Tuple of (df with is_duplicate column, list of duplicate info)
        """
        df['is_duplicate'] = False
        df['duplicate_reason'] = ''
        df['file_hash'] = ''
        
        duplicates_info = []
        
        for idx, row in df.iterrows():
            # Create metadata-based key
            record_key = self.create_record_key(row)
            
            # Get file path
            source_path = Path(row['source_path'])
            if row['media_type'] == 'audio':
                file_path = source_path / 'audio' / row['file_name']
            elif row['media_type'] == 'image':
                file_path = source_path / 'images' / row['file_name']
            else:
                continue
            
            # Check if file exists
            if not file_path.exists():
                self.missing_files.append({
                    'file_name': row['file_name'],
                    'expected_path': str(file_path),
                    'snapshot': row['source_snapshot']
                })
                continue
            
            # Calculate file hash
            file_hash = self.calculate_file_hash(file_path)
            df.at[idx, 'file_hash'] = file_hash if file_hash else ''
            
            # Check for duplicates
            is_duplicate = False
            duplicate_reason = []
            
            # Check metadata-based duplicate
            if record_key in self.processed_keys:
                is_duplicate = True
                duplicate_reason.append('metadata_match')
            
            # Check hash-based duplicate
            if file_hash and file_hash in self.file_hashes:
                is_duplicate = True
                duplicate_reason.append('hash_match')
                original_file = self.file_hashes[file_hash]
                duplicates_info.append({
                    'duplicate_file': row['file_name'],
                    'original_file': original_file,
                    'snapshot': row['source_snapshot'],
                    'consultation_id': row['consultation_id'],
                    'hash': file_hash
                })
            else:
                if file_hash:
                    self.file_hashes[file_hash] = row['file_name']
            
            # Mark as duplicate if found
            if is_duplicate:
                df.at[idx, 'is_duplicate'] = True
                df.at[idx, 'duplicate_reason'] = ', '.join(duplicate_reason)
                self.duplicate_records.append({
                    'file_name': row['file_name'],
                    'snapshot': row['source_snapshot'],
                    'reason': ', '.join(duplicate_reason)
                })
            else:
                # Add to processed set only if not duplicate
                self.processed_keys.add(record_key)
        
        return df, duplicates_info
    
    def validate_files(self, df: pd.DataFrame) -> List[Dict]:
        """
        Validate all files in the DataFrame for existence and format.
        
        Args:
            df: DataFrame with file records
            
        Returns:
            List of validation errors
        """
        validation_errors = []
        
        # Group by source snapshot to check for orphaned files
        for snapshot in df['source_snapshot'].unique():
            snapshot_df = df[df['source_snapshot'] == snapshot]
            snapshot_path = Path(snapshot_df.iloc[0]['source_path'])
            
            # Get all files mentioned in CSV
            csv_files = set(snapshot_df['file_name'].values)
            
            # Find orphaned files
            orphaned = self.find_orphaned_files(snapshot_path, csv_files)
            for orphaned_file in orphaned:
                self.orphaned_files.append({
                    'file': orphaned_file,
                    'snapshot': snapshot
                })
        
        # Validate file formats
        for idx, row in df.iterrows():
            if row['is_duplicate']:
                continue
                
            source_path = Path(row['source_path'])
            if row['media_type'] == 'audio':
                file_path = source_path / 'audio' / row['file_name']
            elif row['media_type'] == 'image':
                file_path = source_path / 'images' / row['file_name']
            else:
                continue
            
            if file_path.exists():
                if not self.validate_file_format(file_path, row['media_type']):
                    self.invalid_formats.append({
                        'file_name': row['file_name'],
                        'media_type': row['media_type'],
                        'snapshot': row['source_snapshot']
                    })
        
        return validation_errors
    
    def copy_unique_files(self, df: pd.DataFrame, output_dir: Path) -> Dict:
        """
        Copy unique (non-duplicate) files to output directory.
        
        Args:
            df: DataFrame with is_duplicate column
            output_dir: Path to output directory
            
        Returns:
            Dictionary with copy statistics
        """
        # Create output subdirectories
        audio_output = output_dir / 'audio'
        images_output = output_dir / 'images'
        audio_output.mkdir(parents=True, exist_ok=True)
        images_output.mkdir(parents=True, exist_ok=True)
        
        stats = {
            'copied_audio': 0,
            'copied_images': 0,
            'failed_copies': []
        }
        
        # Copy only non-duplicate, non-excluded files
        unique_df = df[(df['is_duplicate'] == False) & (df.get('is_excluded', False) == False)]
        
        for idx, row in unique_df.iterrows():
            source_path = Path(row['source_path'])
            
            if row['media_type'] == 'audio':
                source_file = source_path / 'audio' / row['file_name']
                dest_file = audio_output / row['file_name']
            elif row['media_type'] == 'image':
                source_file = source_path / 'images' / row['file_name']
                dest_file = images_output / row['file_name']
            else:
                continue
            
            if not source_file.exists():
                stats['failed_copies'].append({
                    'file': row['file_name'],
                    'reason': 'source file not found'
                })
                continue
            
            try:
                shutil.copy2(source_file, dest_file)
                if row['media_type'] == 'audio':
                    stats['copied_audio'] += 1
                else:
                    stats['copied_images'] += 1
            except Exception as e:
                stats['failed_copies'].append({
                    'file': row['file_name'],
                    'reason': str(e)
                })
        
        return stats
    
    def get_validation_summary(self) -> Dict:
        """Get summary of all file validation issues."""
        return {
            'missing_files': len(self.missing_files),
            'orphaned_files': len(self.orphaned_files),
            'invalid_formats': len(self.invalid_formats),
            'duplicates': len(self.duplicate_records),
            'exclusions': len(self.excluded_records),
            'details': {
                'missing_files': self.missing_files,
                'orphaned_files': self.orphaned_files,
                'invalid_formats': self.invalid_formats,
                'duplicates': self.duplicate_records,
                'exclusions': self.excluded_records
            }
        }
