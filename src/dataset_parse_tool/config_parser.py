"""Configuration parser and validator module."""
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple

# Use built-in tomllib for Python 3.11+, fallback to tomli for older versions
if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib


class Config:
    """Configuration container with easy attribute access."""
    
    def __init__(self, config_dict: Dict[str, Any]):
        self._config = config_dict
        
    def get(self, path: str, default: Any = None) -> Any:
        """
        Get a config value using dot notation.
        
        Args:
            path: Dot-separated path to config value (e.g., "paths.input_dir")
            default: Default value if not found
            
        Returns:
            Config value or default
        """
        keys = path.split('.')
        value = self._config
        
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        
        return value
    
    def __getattr__(self, name: str) -> Any:
        """Allow attribute-style access to top-level config sections."""
        if name.startswith('_'):
            return object.__getattribute__(self, name)
        return self._config.get(name)
    
    def to_dict(self) -> Dict[str, Any]:
        """Return the full configuration as a dictionary."""
        return self._config.copy()


class ConfigParser:
    """Parses and validates the configuration file."""
    
    DEFAULT_CONFIG_NAME = "config.toml"
    
    def __init__(self, config_path: Path = None):
        """
        Initialize config parser.
        
        Args:
            config_path: Path to config file. If None, looks for config.toml in project root.
        """
        self.config_path = config_path
        self.config = None
        
    def load_config(self, project_root: Path = None) -> Config:
        """
        Load and parse configuration file.
        
        Args:
            project_root: Project root directory. If None, derives from this file's location.
            
        Returns:
            Config object with parsed configuration
        """
        if project_root is None:
            # Derive project root from this file's location
            project_root = Path(__file__).parent.parent.parent
        
        # Determine config file path
        if self.config_path is None:
            self.config_path = project_root / self.DEFAULT_CONFIG_NAME
        
        # Check if config file exists
        if not self.config_path.exists():
            raise FileNotFoundError(
                f"Configuration file not found: {self.config_path}\n"
                f"Please create a config.toml file in the project root."
            )
        
        # Load TOML file
        try:
            with open(self.config_path, 'rb') as f:
                config_dict = tomllib.load(f)
        except Exception as e:
            raise ValueError(f"Error parsing config file: {e}")
        
        # Validate configuration
        self._validate_config(config_dict)
        
        # Store project root for path resolution
        config_dict['_project_root'] = str(project_root)
        
        self.config = Config(config_dict)
        return self.config
    
    def _validate_config(self, config: Dict[str, Any]):
        """
        Validate configuration structure and values.
        
        Args:
            config: Configuration dictionary
        """
        # Check required sections exist
        required_sections = ['paths', 'exclusions', 'validation', 'deduplication', 'output']
        missing_sections = [s for s in required_sections if s not in config]
        
        if missing_sections:
            raise ValueError(f"Missing required config sections: {', '.join(missing_sections)}")
        
        # Validate paths section
        if 'input_dir' not in config['paths']:
            raise ValueError("Missing required config: paths.input_dir")
        if 'output_dir' not in config['paths']:
            raise ValueError("Missing required config: paths.output_dir")
        
        # Validate exclusions are lists
        exclusions = config['exclusions']
        list_fields = ['excluded_profiles', 'excluded_date_ranges', 
                      'excluded_consultations', 'excluded_files']
        
        for field in list_fields:
            if field not in exclusions:
                exclusions[field] = []
            elif not isinstance(exclusions[field], list):
                raise ValueError(f"Config field exclusions.{field} must be a list")
        
        # Validate date ranges format
        for date_range in exclusions['excluded_date_ranges']:
            if not self._validate_date_range_format(date_range):
                raise ValueError(
                    f"Invalid date range format: {date_range}\n"
                    f"Expected format: 'YYYYMMDD' or 'YYYYMMDD-YYYYMMDD'"
                )
        
        # Validate keep_occurrence option
        keep_occurrence = config['deduplication'].get('keep_occurrence', 'first')
        if keep_occurrence not in ['first', 'last']:
            raise ValueError(
                f"Invalid deduplication.keep_occurrence value: {keep_occurrence}\n"
                f"Must be 'first' or 'last'"
            )
        
        # Validate logging verbosity
        if 'logging' in config:
            verbosity = config['logging'].get('verbosity', 'normal')
            if verbosity not in ['quiet', 'normal', 'verbose']:
                raise ValueError(
                    f"Invalid logging.verbosity value: {verbosity}\n"
                    f"Must be 'quiet', 'normal', or 'verbose'"
                )
    
    def _validate_date_range_format(self, date_range: str) -> bool:
        """
        Validate date range format.
        
        Args:
            date_range: Date range string
            
        Returns:
            True if valid, False otherwise
        """
        if not isinstance(date_range, str):
            return False
        
        # Check if it's a range (YYYYMMDD-YYYYMMDD) or single date (YYYYMMDD)
        if '-' in date_range:
            parts = date_range.split('-')
            if len(parts) != 2:
                return False
            return all(self._validate_date_format(part) for part in parts)
        else:
            return self._validate_date_format(date_range)
    
    def _validate_date_format(self, date_str: str) -> bool:
        """
        Validate single date format (YYYYMMDD).
        
        Args:
            date_str: Date string
            
        Returns:
            True if valid, False otherwise
        """
        if not isinstance(date_str, str):
            return False
        
        # Should be 8 digits
        if len(date_str) != 8 or not date_str.isdigit():
            return False
        
        # Basic validation: year, month, day ranges
        year = int(date_str[0:4])
        month = int(date_str[4:6])
        day = int(date_str[6:8])
        
        if year < 1900 or year > 2100:
            return False
        if month < 1 or month > 12:
            return False
        if day < 1 or day > 31:
            return False
        
        return True
    
    def get_resolved_paths(self) -> Tuple[Path, Path]:
        """
        Get resolved input and output paths.
        
        Returns:
            Tuple of (input_path, output_path)
        """
        if self.config is None:
            raise RuntimeError("Config not loaded. Call load_config() first.")
        
        project_root = Path(self.config._config['_project_root'])
        input_dir = project_root / self.config.paths['input_dir']
        output_dir = project_root / self.config.paths['output_dir']
        
        return input_dir, output_dir
    
    def should_exclude_record(self, record: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Check if a record should be excluded based on config.
        
        Args:
            record: Record dictionary with keys like 'profile_id', 'timestamp', etc.
            
        Returns:
            Tuple of (should_exclude, reason)
        """
        if self.config is None:
            raise RuntimeError("Config not loaded. Call load_config() first.")
        
        exclusions = self.config.exclusions
        
        # Check profile exclusions
        if exclusions['excluded_profiles']:
            profile_id = record.get('profile_id')
            if profile_id in exclusions['excluded_profiles']:
                return True, f"excluded_profile_{profile_id}"
        
        # Check consultation exclusions
        if exclusions['excluded_consultations']:
            consultation_id = record.get('consultation_id')
            if consultation_id in exclusions['excluded_consultations']:
                return True, f"excluded_consultation_{consultation_id}"
        
        # Check filename exclusions
        if exclusions['excluded_files']:
            file_name = record.get('file_name')
            if file_name in exclusions['excluded_files']:
                return True, f"excluded_filename"
        
        # Check date range exclusions
        if exclusions['excluded_date_ranges']:
            timestamp = str(record.get('timestamp', ''))
            if timestamp:
                # Extract date part (YYYYMMDD from YYYYMMDDTHHMMSS)
                date_str = timestamp.split('T')[0] if 'T' in timestamp else timestamp[:8]
                
                for date_range in exclusions['excluded_date_ranges']:
                    if self._is_date_in_range(date_str, date_range):
                        return True, f"excluded_date_range_{date_range}"
        
        return False, ""
    
    def _is_date_in_range(self, date_str: str, date_range: str) -> bool:
        """
        Check if a date falls within a date range.
        
        Args:
            date_str: Date string (YYYYMMDD)
            date_range: Range string (YYYYMMDD or YYYYMMDD-YYYYMMDD)
            
        Returns:
            True if date is in range, False otherwise
        """
        if '-' in date_range:
            # Range format
            start, end = date_range.split('-')
            return start <= date_str <= end
        else:
            # Single date format
            return date_str == date_range


def load_config(config_path: Path = None, project_root: Path = None) -> Config:
    """
    Convenience function to load configuration.
    
    Args:
        config_path: Optional path to config file
        project_root: Optional project root directory
        
    Returns:
        Config object
    """
    parser = ConfigParser(config_path)
    return parser.load_config(project_root)
