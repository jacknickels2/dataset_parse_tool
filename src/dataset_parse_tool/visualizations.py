"""Visualization generation module for creating charts and graphs."""
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from typing import Dict
import pandas as pd


class VisualizationGenerator:
    """Generates visualizations for dataset statistics."""
    
    def __init__(self):
        # Set style for better-looking plots
        sns.set_style("whitegrid")
        plt.rcParams['figure.figsize'] = (10, 6)
        plt.rcParams['font.size'] = 10
        
    def create_all_visualizations(self, stats: Dict, df: pd.DataFrame, 
                                 unique_df: pd.DataFrame, output_dir: Path):
        """
        Create all visualizations and save them to the output directory.
        
        Args:
            stats: Statistics dictionary
            df: Complete DataFrame
            unique_df: Unique records DataFrame
            output_dir: Directory to save visualizations
        """
        viz_dir = output_dir / "visualizations"
        viz_dir.mkdir(exist_ok=True)
        
        # Create each visualization
        self.plot_file_type_distribution(stats, viz_dir)
        self.plot_duplicates_overview(stats, viz_dir)
        self.plot_gender_distribution(stats, viz_dir)
        self.plot_age_distribution(unique_df, viz_dir)
        self.plot_media_by_body_part(stats, viz_dir)
        self.plot_snapshots_distribution(stats, viz_dir)
        self.plot_temporal_distribution(stats, viz_dir)
        self.plot_data_quality_metrics(stats, unique_df, viz_dir)
        
    def plot_file_type_distribution(self, stats: Dict, output_dir: Path):
        """Create pie chart of file type distribution."""
        fc = stats['file_counts']
        
        fig, ax = plt.subplots(figsize=(10, 8))
        
        sizes = [fc['audio_files'], fc['image_files']]
        labels = [f"Audio Files\n({fc['audio_files']})", 
                 f"Image Files\n({fc['image_files']})"]
        colors = ['#3498db', '#e74c3c']
        explode = (0.05, 0.05)
        
        ax.pie(sizes, explode=explode, labels=labels, colors=colors,
               autopct='%1.1f%%', shadow=True, startangle=90)
        ax.set_title('File Type Distribution', fontsize=16, fontweight='bold', pad=20)
        
        plt.tight_layout()
        plt.savefig(output_dir / 'file_type_distribution.png', dpi=300, bbox_inches='tight')
        plt.close()
        
    def plot_duplicates_overview(self, stats: Dict, output_dir: Path):
        """Create bar chart showing duplicates vs unique records."""
        fc = stats['file_counts']
        
        fig, ax = plt.subplots(figsize=(10, 6))
        
        categories = ['Total\nRecords', 'Unique\nRecords', 'Duplicate\nRecords']
        values = [fc['total_records'], fc['unique_records'], fc['duplicate_records']]
        colors = ['#95a5a6', '#27ae60', '#e67e22']
        
        bars = ax.bar(categories, values, color=colors, edgecolor='black', linewidth=1.5)
        
        # Add value labels on bars
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                   f'{int(height)}',
                   ha='center', va='bottom', fontweight='bold', fontsize=12)
        
        ax.set_ylabel('Number of Records', fontsize=12, fontweight='bold')
        ax.set_title('Records Overview: Duplicates vs Unique', fontsize=16, fontweight='bold', pad=20)
        ax.grid(axis='y', alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(output_dir / 'duplicates_overview.png', dpi=300, bbox_inches='tight')
        plt.close()
        
    def plot_gender_distribution(self, stats: Dict, output_dir: Path):
        """Create bar chart of gender distribution."""
        gender_dist = stats['demographics']['gender_distribution']
        
        fig, ax = plt.subplots(figsize=(10, 6))
        
        genders = list(gender_dist.keys())
        counts = list(gender_dist.values())
        colors = sns.color_palette("Set2", len(genders))
        
        bars = ax.bar(genders, counts, color=colors, edgecolor='black', linewidth=1.5)
        
        # Add value labels on bars
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                   f'{int(height)}',
                   ha='center', va='bottom', fontweight='bold', fontsize=12)
        
        ax.set_xlabel('Gender', fontsize=12, fontweight='bold')
        ax.set_ylabel('Number of Records', fontsize=12, fontweight='bold')
        ax.set_title('Patient Gender Distribution', fontsize=16, fontweight='bold', pad=20)
        ax.grid(axis='y', alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(output_dir / 'gender_distribution.png', dpi=300, bbox_inches='tight')
        plt.close()
        
    def plot_age_distribution(self, df: pd.DataFrame, output_dir: Path):
        """Create histogram of age distribution."""
        ages = pd.to_numeric(df['age'], errors='coerce').dropna()
        
        if len(ages) == 0:
            return
        
        fig, ax = plt.subplots(figsize=(12, 6))
        
        ax.hist(ages, bins=20, color='#3498db', edgecolor='black', linewidth=1.2, alpha=0.7)
        
        # Add mean and median lines
        mean_age = ages.mean()
        median_age = ages.median()
        ax.axvline(mean_age, color='red', linestyle='--', linewidth=2, label=f'Mean: {mean_age:.1f}')
        ax.axvline(median_age, color='green', linestyle='--', linewidth=2, label=f'Median: {median_age:.1f}')
        
        ax.set_xlabel('Age (years)', fontsize=12, fontweight='bold')
        ax.set_ylabel('Frequency', fontsize=12, fontweight='bold')
        ax.set_title('Patient Age Distribution', fontsize=16, fontweight='bold', pad=20)
        ax.legend(fontsize=11)
        ax.grid(axis='y', alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(output_dir / 'age_distribution.png', dpi=300, bbox_inches='tight')
        plt.close()
        
    def plot_media_by_body_part(self, stats: Dict, output_dir: Path):
        """Create horizontal bar chart of media files by body part."""
        body_part_dist = stats['media_distribution']['files_by_body_part']
        
        # Sort and take top 10
        sorted_items = sorted(body_part_dist.items(), key=lambda x: x[1], reverse=True)[:10]
        body_parts = [item[0] for item in sorted_items]
        counts = [item[1] for item in sorted_items]
        
        fig, ax = plt.subplots(figsize=(12, 8))
        
        colors = sns.color_palette("viridis", len(body_parts))
        bars = ax.barh(body_parts, counts, color=colors, edgecolor='black', linewidth=1.2)
        
        # Add value labels on bars
        for i, bar in enumerate(bars):
            width = bar.get_width()
            ax.text(width, bar.get_y() + bar.get_height()/2.,
                   f'{int(counts[i])}',
                   ha='left', va='center', fontweight='bold', fontsize=10, 
                   bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.8))
        
        ax.set_xlabel('Number of Files', fontsize=12, fontweight='bold')
        ax.set_ylabel('Body Part / Media Type', fontsize=12, fontweight='bold')
        ax.set_title('Top 10 Media Files by Body Part/Type', fontsize=16, fontweight='bold', pad=20)
        ax.grid(axis='x', alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(output_dir / 'media_by_body_part.png', dpi=300, bbox_inches='tight')
        plt.close()
        
    def plot_snapshots_distribution(self, stats: Dict, output_dir: Path):
        """Create bar chart of records per snapshot."""
        records_per_snapshot = stats['snapshots']['records_per_snapshot']
        
        # Sort by snapshot name
        sorted_items = sorted(records_per_snapshot.items())
        snapshots = [item[0] for item in sorted_items]
        counts = [item[1] for item in sorted_items]
        
        fig, ax = plt.subplots(figsize=(14, 6))
        
        colors = sns.color_palette("coolwarm", len(snapshots))
        bars = ax.bar(range(len(snapshots)), counts, color=colors, 
                     edgecolor='black', linewidth=1.2)
        
        # Add value labels on bars
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                   f'{int(height)}',
                   ha='center', va='bottom', fontweight='bold', fontsize=9)
        
        ax.set_xticks(range(len(snapshots)))
        ax.set_xticklabels(snapshots, rotation=45, ha='right')
        ax.set_xlabel('Snapshot', fontsize=12, fontweight='bold')
        ax.set_ylabel('Number of Records', fontsize=12, fontweight='bold')
        ax.set_title('Records per Snapshot', fontsize=16, fontweight='bold', pad=20)
        ax.grid(axis='y', alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(output_dir / 'snapshots_distribution.png', dpi=300, bbox_inches='tight')
        plt.close()
        
    def plot_temporal_distribution(self, stats: Dict, output_dir: Path):
        """Create line chart of consultations over time."""
        temporal = stats['temporal']
        
        if not temporal.get('consultations_by_month'):
            return
        
        consultations_by_month = temporal['consultations_by_month']
        
        # Sort by month
        sorted_items = sorted(consultations_by_month.items())
        months = [item[0] for item in sorted_items]
        counts = [item[1] for item in sorted_items]
        
        fig, ax = plt.subplots(figsize=(14, 6))
        
        ax.plot(months, counts, marker='o', linestyle='-', linewidth=2.5, 
               markersize=8, color='#2c3e50', markerfacecolor='#e74c3c',
               markeredgewidth=2, markeredgecolor='#2c3e50')
        
        # Fill area under the line
        ax.fill_between(range(len(months)), counts, alpha=0.3, color='#3498db')
        
        # Add value labels
        for i, (month, count) in enumerate(zip(months, counts)):
            ax.text(i, count, f'{count}', ha='center', va='bottom', 
                   fontweight='bold', fontsize=9)
        
        ax.set_xticks(range(len(months)))
        ax.set_xticklabels(months, rotation=45, ha='right')
        ax.set_xlabel('Month', fontsize=12, fontweight='bold')
        ax.set_ylabel('Number of Consultations', fontsize=12, fontweight='bold')
        ax.set_title('Consultations Over Time', fontsize=16, fontweight='bold', pad=20)
        ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(output_dir / 'temporal_distribution.png', dpi=300, bbox_inches='tight')
        plt.close()
        
    def plot_data_quality_metrics(self, stats: Dict, df: pd.DataFrame, output_dir: Path):
        """Create stacked bar chart showing data quality metrics."""
        consult = stats['consultations']
        
        total = consult['total_consultations']
        with_symptoms = consult['consultations_with_symptoms']
        with_prescriptions = consult['consultations_with_prescriptions']
        with_notes = consult['consultations_with_notes']
        
        fig, ax = plt.subplots(figsize=(12, 6))
        
        categories = ['With\nSymptoms', 'With\nPrescriptions', 'With\nPhysician\nNotes']
        values = [with_symptoms, with_prescriptions, with_notes]
        percentages = [(v/total)*100 for v in values]
        
        colors = ['#27ae60', '#3498db', '#9b59b6']
        bars = ax.bar(categories, values, color=colors, edgecolor='black', linewidth=1.5)
        
        # Add value labels with percentages
        for i, bar in enumerate(bars):
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                   f'{int(values[i])}\n({percentages[i]:.1f}%)',
                   ha='center', va='bottom', fontweight='bold', fontsize=11)
        
        ax.set_ylabel('Number of Consultations', fontsize=12, fontweight='bold')
        ax.set_title(f'Data Completeness Metrics (Total Consultations: {total})', 
                    fontsize=16, fontweight='bold', pad=20)
        ax.grid(axis='y', alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(output_dir / 'data_quality_metrics.png', dpi=300, bbox_inches='tight')
        plt.close()
        
    def create_summary_dashboard(self, stats: Dict, output_dir: Path):
        """Create a single dashboard image with key metrics."""
        fig = plt.figure(figsize=(16, 10))
        gs = fig.add_gridspec(3, 3, hspace=0.4, wspace=0.3)
        
        # File counts
        ax1 = fig.add_subplot(gs[0, 0])
        fc = stats['file_counts']
        ax1.text(0.5, 0.7, f"{fc['total_unique_files']}", 
                ha='center', va='center', fontsize=48, fontweight='bold', color='#2c3e50')
        ax1.text(0.5, 0.3, "Total Unique Files", 
                ha='center', va='center', fontsize=14, color='#7f8c8d')
        ax1.axis('off')
        ax1.set_facecolor('#ecf0f1')
        
        # Duplicates removed
        ax2 = fig.add_subplot(gs[0, 1])
        ax2.text(0.5, 0.7, f"{fc['duplicate_records']}", 
                ha='center', va='center', fontsize=48, fontweight='bold', color='#e74c3c')
        ax2.text(0.5, 0.3, "Duplicates Removed", 
                ha='center', va='center', fontsize=14, color='#7f8c8d')
        ax2.axis('off')
        ax2.set_facecolor('#ecf0f1')
        
        # Unique profiles
        ax3 = fig.add_subplot(gs[0, 2])
        profiles = stats['demographics']['unique_profiles']
        ax3.text(0.5, 0.7, f"{profiles}", 
                ha='center', va='center', fontsize=48, fontweight='bold', color='#3498db')
        ax3.text(0.5, 0.3, "Unique Patients", 
                ha='center', va='center', fontsize=14, color='#7f8c8d')
        ax3.axis('off')
        ax3.set_facecolor('#ecf0f1')
        
        # File type pie chart
        ax4 = fig.add_subplot(gs[1, :2])
        sizes = [fc['audio_files'], fc['image_files']]
        labels = ['Audio', 'Image']
        colors = ['#3498db', '#e74c3c']
        ax4.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%', 
               startangle=90, textprops={'fontsize': 12, 'fontweight': 'bold'})
        ax4.set_title('File Type Distribution', fontsize=14, fontweight='bold')
        
        # Age statistics
        ax5 = fig.add_subplot(gs[1, 2])
        age_stats = stats['demographics'].get('age_stats')
        if age_stats:
            ax5.text(0.5, 0.8, f"{age_stats['mean']:.1f}", 
                    ha='center', va='center', fontsize=36, fontweight='bold', color='#27ae60')
            ax5.text(0.5, 0.5, "Mean Age (years)", 
                    ha='center', va='center', fontsize=12, color='#7f8c8d')
            ax5.text(0.5, 0.2, f"Range: {age_stats['min']}-{age_stats['max']}", 
                    ha='center', va='center', fontsize=10, color='#95a5a6')
        ax5.axis('off')
        ax5.set_facecolor('#ecf0f1')
        
        # Snapshot count
        ax6 = fig.add_subplot(gs[2, 0])
        snapshot_count = stats['snapshots']['total_snapshots']
        ax6.text(0.5, 0.7, f"{snapshot_count}", 
                ha='center', va='center', fontsize=48, fontweight='bold', color='#9b59b6')
        ax6.text(0.5, 0.3, "Snapshots Processed", 
                ha='center', va='center', fontsize=14, color='#7f8c8d')
        ax6.axis('off')
        ax6.set_facecolor('#ecf0f1')
        
        # Consultations
        ax7 = fig.add_subplot(gs[2, 1])
        consult_count = stats['consultations']['total_consultations']
        ax7.text(0.5, 0.7, f"{consult_count}", 
                ha='center', va='center', fontsize=48, fontweight='bold', color='#f39c12')
        ax7.text(0.5, 0.3, "Total Consultations", 
                ha='center', va='center', fontsize=14, color='#7f8c8d')
        ax7.axis('off')
        ax7.set_facecolor('#ecf0f1')
        
        # Date range
        ax8 = fig.add_subplot(gs[2, 2])
        temporal = stats['temporal']
        if temporal.get('earliest_consultation') and temporal.get('latest_consultation'):
            ax8.text(0.5, 0.75, temporal['earliest_consultation'], 
                    ha='center', va='center', fontsize=14, fontweight='bold', color='#2c3e50')
            ax8.text(0.5, 0.5, "to", 
                    ha='center', va='center', fontsize=12, color='#7f8c8d')
            ax8.text(0.5, 0.25, temporal['latest_consultation'], 
                    ha='center', va='center', fontsize=14, fontweight='bold', color='#2c3e50')
        ax8.axis('off')
        ax8.set_facecolor('#ecf0f1')
        
        fig.suptitle('Dataset Processing Dashboard', fontsize=20, fontweight='bold', y=0.98)
        
        plt.savefig(output_dir / 'dashboard_summary.png', dpi=300, bbox_inches='tight')
        plt.close()
