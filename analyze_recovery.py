import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime

# Load the dataset
data = pd.read_csv('data/hospital_data.csv')

def analyze_recovery_metrics(data):
    """Analyze and visualize disaster recovery metrics for hospitals."""
    # Basic statistics
    print("\n=== Disaster Recovery Metrics ===")
    print(f"Total hospitals in dataset: {len(data)}")
    print(f"\nBackup Status:")
    print(data['backup_status'].value_counts())
    
    # Convert last_backup to datetime
    data['last_backup'] = pd.to_datetime(data['last_backup'])
    
    # Days since last backup
    current_time = pd.Timestamp.now()
    data['hours_since_backup'] = (current_time - data['last_backup']).dt.total_seconds() / 3600
    
    # Identify hospitals needing attention
    needs_attention = data[data['hours_since_backup'] > 24]
    
    if not needs_attention.empty:
        print("\nHOSPITALS NEEDING ATTENTION (No backup in last 24 hours):")
        print(needs_attention[['hospital_name', 'last_backup', 'hours_since_backup']])
    
    # Plot RTO and RPO metrics
    plt.figure(figsize=(12, 6))
    
    plt.subplot(1, 2, 1)
    data['recovery_time_objective'].plot(kind='bar')
    plt.title('Recovery Time Objective (hours)')
    plt.xticks(range(len(data)), data['hospital_name'], rotation=45)
    
    plt.subplot(1, 2, 2)
    data['recovery_point_objective'].plot(kind='bar', color='orange')
    plt.title('Recovery Point Objective (hours)')
    plt.xticks(range(len(data)), data['hospital_name'], rotation=45)
    
    plt.tight_layout()
    plt.savefig('recovery_metrics.png')
    print("\nRecovery metrics visualization saved as 'recovery_metrics.png'")

if __name__ == "__main__":
    analyze_recovery_metrics(data)
