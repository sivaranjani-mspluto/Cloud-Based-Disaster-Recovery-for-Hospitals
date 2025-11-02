import os
import math
import random
from datetime import datetime, timedelta
import pandas as pd

"""
Transforms district-level health infrastructure data (pc_hospitals_dist.csv)
into a hospital-level dataset compatible with the analysis script/notebook.

Input (default): data/pc_hospitals_dist.csv
Output: data/hospital_data.csv

Schema produced:
- hospital_id
- hospital_name
- location (Urban/Rural)
- beds_available
- backup_status (Active/Inactive)
- last_backup (YYYY-mm-dd HH:MM:SS)
- recovery_time_objective (hours)
- recovery_point_objective (hours)
- data_volume_gb

Usage:
  python scripts/transform_pc_hospitals_dist.py
  python scripts/transform_pc_hospitals_dist.py <input_csv> <output_csv>
"""

RANDOM_SEED = 42
random.seed(RANDOM_SEED)


def safe_div(a, b, default=0.0):
    return float(a) / float(b) if b not in (0, None) else float(default)


def choose_location(p_urban):
    return "Urban" if random.random() < p_urban else "Rural"


def estimate_beds(row, loc):
    # Estimate average beds per hospital by location using available district metrics
    u_hosp = row.get('pc_hospitals_u', 0) or 0
    r_hosp = row.get('pc_hospitals_r', 0) or 0
    u_beds_total = row.get('pc_hosp_beds_u', None)

    # Urban: direct ratio if available; Rural: assume 60% of urban avg as proxy
    urban_avg = safe_div(u_beds_total, u_hosp, default=30) if u_beds_total not in (None, "") else 30
    rural_avg = max(10, int(0.6 * urban_avg))

    base = urban_avg if loc == "Urban" else rural_avg
    # Add small variance
    return max(5, int(round(random.normalvariate(base, base * 0.15))))


def estimate_backup_status(row, loc):
    # Heuristic: higher density of doctors or paramedics => more likely Active
    doc_u = row.get('pc_docs_pos_u', 0) or 0
    doc_r = row.get('pc_docs_pos_r', 0) or 0
    pmed_u = row.get('pc_pmed_pos_u', 0) or 0
    pmed_r = row.get('pc_pmed_pos_r', 0) or 0

    score = (doc_u + pmed_u) if loc == "Urban" else (doc_r + pmed_r)
    # Normalize and map to probability range
    prob_active = min(0.9, 0.3 + 0.0008 * score)
    return "Active" if random.random() < prob_active else "Inactive"


def estimate_backups_and_objectives(is_active):
    now = datetime.now()
    if is_active:
        hours_ago = random.randint(1, 72)   # backed up within last 3 days
        rto = random.choice([2, 3, 4, 5, 6])
        rpo = random.choice([0.5, 1, 1, 2])
    else:
        hours_ago = random.randint(24, 720)  # 1–30 days
        rto = random.choice([6, 8, 10, 12])
        rpo = random.choice([2, 4, 6])

    last_backup = (now - timedelta(hours=hours_ago)).strftime('%Y-%m-%d %H:%M:%S')
    return last_backup, float(rto), float(rpo)


def estimate_data_volume_gb(beds):
    # Approximate clinical + imaging + EHR storage footprint
    # 4 GB per bed is a conservative rolling figure
    base = 4.0 * beds
    # Add modest variance
    return round(max(20.0, random.normalvariate(base, base * 0.2)), 1)


def transform(input_csv: str, output_csv: str):
    df = pd.read_csv(input_csv)

    required_cols = ['lgd_state_id','lgd_district_id','pc_hospitals_r','pc_hospitals_u','pc_hosp_beds_u','pc_pmed_pos_r','pc_pmed_pos_u','pc_docs_pos_r','pc_docs_pos_u','pc_num_hospitals']
    for c in required_cols:
        if c not in df.columns:
            raise ValueError(f"Missing required column '{c}' in {input_csv}")

    rows = []
    for _, row in df.iterrows():
        dist_id = str(row['lgd_district_id']).zfill(3)
        total_hosp = int(row.get('pc_num_hospitals', 0) or 0)
        u = int(row.get('pc_hospitals_u', 0) or 0)
        r = int(row.get('pc_hospitals_r', 0) or 0)
        total = max(1, u + r) if total_hosp == 0 else total_hosp

        # Use proportion of urban hospitals to sample location
        p_urban = safe_div(u, (u + r) if (u + r) > 0 else total, default=0.5)

        # Cap number synthesized per district to avoid explosion, but keep proportions
        synth_n = min(total, 50)
        for i in range(1, synth_n + 1):
            loc = choose_location(p_urban)
            beds = estimate_beds(row, loc)
            backup_status = estimate_backup_status(row, loc)
            last_backup, rto, rpo = estimate_backups_and_objectives(backup_status == "Active")
            data_gb = estimate_data_volume_gb(beds)

            hospital_id = f"D{dist_id}-{i:03d}"
            hospital_name = f"District {dist_id} Hospital {i}"

            rows.append({
                'hospital_id': hospital_id,
                'hospital_name': hospital_name,
                'location': loc,
                'beds_available': beds,
                'backup_status': backup_status,
                'last_backup': last_backup,
                'recovery_time_objective': rto,
                'recovery_point_objective': rpo,
                'data_volume_gb': data_gb
            })

    out_df = pd.DataFrame(rows)
    os.makedirs(os.path.dirname(output_csv), exist_ok=True)
    out_df.to_csv(output_csv, index=False)
    print(f"Wrote {len(out_df)} rows to {output_csv}")


if __name__ == "__main__":
    import sys
    in_path = sys.argv[1] if len(sys.argv) > 1 else os.path.join('data','pc_hospitals_dist.csv')
    out_path = sys.argv[2] if len(sys.argv) > 2 else os.path.join('data','hospital_data.csv')
    transform(in_path, out_path)
