# Configuration Guide

The Dataset Parse Tool uses a `config.toml` file in the project root to control its behavior. This allows you to customize processing without modifying code.

## Configuration File Location

The tool looks for `config.toml` in the project root directory. If not found, it will exit with an error.

## Quick Start

1. Use the default `config.toml` for basic processing
2. Or copy `config.example.toml` to `config.toml` and customize

```bash
cp config.example.toml config.toml
```

## Manual Exclusions

One of the most powerful features is the ability to manually exclude data from processing.

### Exclude by Profile ID

Exclude specific patients/profiles:

```toml
[exclusions]
excluded_profiles = [123, 456, 789]
```

### Exclude by Date Range

Exclude data from specific date ranges:

```toml
[exclusions]
excluded_date_ranges = [
    "20251201-20251231",  # All of December 2025
    "20260115",           # Just January 15th, 2026
    "20250601-20250630"   # All of June 2025
]
```

Date format: `YYYYMMDD` or `YYYYMMDD-YYYYMMDD`

### Exclude by Consultation ID

Exclude specific consultations:

```toml
[exclusions]
excluded_consultations = [1234, 5678, 9012]
```

### Exclude by Filename

Exclude specific files by exact filename match:

```toml
[exclusions]
excluded_files = [
    "corrupted_audio.mp3",
    "bad_scan.jpg",
    "test_file.mp3"
]
```

## Other Configuration Options

### Paths

```toml
[paths]
input_dir = "data/input/datasets_03-04-26"
output_dir = "data/output"
use_timestamp = true  # Add timestamp to output folder name
```

### Validation

Control which validation checks are performed:

```toml
[validation]
check_file_existence = true     # Verify files exist
check_required_fields = true    # Check for empty required fields
check_file_formats = true       # Validate file formats
check_orphaned_files = true     # Find files not in CSV
strict_mode = false             # If true, skip invalid records
```

### Deduplication

Control how duplicates are detected:

```toml
[deduplication]
use_metadata_deduplication = true  # Use CSV metadata
use_hash_deduplication = true      # Use file hashes
keep_occurrence = "first"          # or "last"
```

### Output Control

Choose what gets generated:

```toml
[output]
copy_files = true                   # Copy files to output
generate_csv = true                 # Create consolidated CSV
generate_summary_report = true      # Create summary report
generate_errors_report = true       # Create errors report
generate_visualizations = true      # Create charts
generate_dashboard = true           # Create dashboard
```

### CSV Output Options

```toml
[output.csv]
include_source_snapshot = true      # Show which snapshot each record came from
include_file_hash = false           # Include SHA256 hash column
include_validation_status = true    # Show validation status
```

### Logging

```toml
[logging]
verbosity = "normal"       # Options: "quiet", "normal", "verbose"
max_errors_in_report = 100 # Limit errors shown (0 = unlimited)
```

## Example: Exclude December 2025 Data

```toml
[exclusions]
excluded_date_ranges = ["20251201-20251231"]
```

## Example: Exclude Test Patients

```toml
[exclusions]
excluded_profiles = [550, 551]  # Test patient profile IDs
```

## Example: Performance Mode (Fast Processing)

```toml
[validation]
check_file_formats = false
check_orphaned_files = false

[output]
generate_visualizations = false
generate_dashboard = false

[logging]
verbosity = "quiet"
```

## Viewing Exclusions

When you run the tool, it will show active exclusion rules at startup:

```
Active exclusion rules:
  • Profiles: [463, 550]
  • Consultations: [2175, 2170]
  • Date ranges: ['20251201-20251231']
```

And in the final report, you'll see how many records were excluded.

## Generated Reports

Exclusions are tracked in:
- **Summary Report**: Shows total exclusions count
- **Errors Report**: Lists all excluded records with reasons
- **Consolidated CSV**: Only contains non-excluded records

## Tips

1. **Start with defaults**: Run once with default config to see all data
2. **Review errors report**: Identify problem records to exclude
3. **Iterative exclusions**: Add exclusions gradually based on findings
4. **Keep backup**: Save different config files for different scenarios
   - `config.toml` - Current active config
   - `config.full.toml` - Process everything
   - `config.clean.toml` - Exclude known bad data
