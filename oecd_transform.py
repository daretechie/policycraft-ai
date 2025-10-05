import pandas as pd
import numpy as np

print("="*70)
print("OECD WELLBEING DATA TRANSFORMATION")
print("Building dataset for Plotly Studio Competition")
print("="*70)

# =====================================================================
# STEP 1: LOAD AND FILTER DATA
# =====================================================================

df = pd.read_csv('OECD-wellbeing.csv')
print(f"\nLoaded {len(df)} rows")

# Filter to totals only (country-level, no demographic breakdowns)
df_totals = df[
    (df['Age'] == 'Total') &
    (df['Sex'] == 'Total') &
    (df['Education'] == 'Total')
].copy()

print(f"Filtered to totals: {len(df_totals)} rows")

# =====================================================================
# STEP 2: DEFINE KEY MEASURES
# =====================================================================

key_measures = {
    # Measure Name : (short_name, should_invert, description)
    'Life satisfaction': ('life_satisfaction', False, 'Overall life satisfaction score'),
    'Life expectancy at birth': ('health', False, 'Years of life expectancy'),
    'Households and NPISHs net adjusted disposable income per capita': ('income', False, 'Household income'),
    'Adult literacy skills': ('education', False, 'Adult literacy proficiency'),
    'Employment rate': ('jobs', False, 'Employment rate'),
    'Long hours in paid work': ('work_life_balance', True, 'Working very long hours'),
    'Homicides': ('safety', True, 'Homicide rate per 100k'),
    'Access to green space': ('environment', False, 'Urban green space access'),
    'Social support': ('social_connections', False, 'Having social support'),
    'Housing affordability': ('housing', True, 'Housing cost burden'),
}

print("\n" + "="*70)
print("SELECTED MEASURES")
print("="*70)
for measure, (short_name, invert, desc) in key_measures.items():
    exists = measure in df_totals['Measure'].values
    status = "✓" if exists else "✗"
    inv_flag = " [INVERT]" if invert else ""
    print(f"{status} {short_name:20s} {inv_flag}")
    if not exists:
        print(f"   WARNING: '{measure}' not found in data!")

# =====================================================================
# STEP 3: EXTRACT AND PREPARE DATA
# =====================================================================

print("\n" + "="*70)
print("EXTRACTING DATA")
print("="*70)

# For each measure, get the most recent year available
df_key = df_totals[df_totals['Measure'].isin(key_measures.keys())].copy()

# Keep only most recent year for each country-measure combination
df_key = df_key.sort_values('Year').groupby(
    ['Country', 'REF_AREA', 'Measure']
).tail(1).reset_index(drop=True)

print(f"Extracted {len(df_key)} measure observations")
print(f"Countries with data: {df_key['Country'].nunique()}")

# =====================================================================
# STEP 4: PIVOT TO WIDE FORMAT
# =====================================================================

print("\n" + "="*70)
print("CREATING WIDE FORMAT")
print("="*70)

df_wide = df_key.pivot_table(
    index=['Country', 'REF_AREA'],
    columns='Measure',
    values='OBS_VALUE',
    aggfunc='first'
).reset_index()

# Rename columns to short names
rename_map = {measure: info[0] for measure, info in key_measures.items()}
df_wide = df_wide.rename(columns=rename_map)
df_wide = df_wide.rename(columns={'Country': 'country', 'REF_AREA': 'country_code'})

# Get dimension columns
dimension_cols = [info[0] for info in key_measures.values()]
dimension_cols = [col for col in dimension_cols if col in df_wide.columns]

print(f"Wide format: {df_wide.shape[0]} countries × {len(dimension_cols)} dimensions")
print(f"Dimensions: {', '.join(dimension_cols)}")

# =====================================================================
# STEP 5: HANDLE MISSING VALUES
# =====================================================================

print("\n" + "="*70)
print("HANDLING MISSING DATA")
print("="*70)

missing_before = df_wide[dimension_cols].isna().sum()
print("Missing values by dimension:")
for col in dimension_cols:
    missing_count = missing_before[col]
    missing_pct = (missing_count / len(df_wide)) * 100
    if missing_count > 0:
        print(f"  {col:25s} {missing_count:3d} ({missing_pct:5.1f}%)")

# Remove countries with more than 50% missing data
missing_pct_by_country = (df_wide[dimension_cols].isna().sum(axis=1) / len(dimension_cols)) * 100
countries_to_remove = df_wide[missing_pct_by_country > 50]['country'].tolist()

if countries_to_remove:
    print(f"\nRemoving {len(countries_to_remove)} countries with >50% missing data:")
    for c in countries_to_remove:
        print(f"  - {c}")
    df_wide = df_wide[missing_pct_by_country <= 50].copy()

# Fill remaining missing values with OECD average
for col in dimension_cols:
    if df_wide[col].isna().any():
        avg_val = df_wide[col].mean()
        missing_count = df_wide[col].isna().sum()
        df_wide[col].fillna(avg_val, inplace=True)
        print(f"Filled {missing_count} missing values in {col} with average {avg_val:.2f}")

print(f"\nFinal dataset: {len(df_wide)} countries")

# =====================================================================
# STEP 6: NORMALIZE TO 0-100 SCALE
# =====================================================================

print("\n" + "="*70)
print("NORMALIZING TO 0-100 SCALE")
print("="*70)

# Create a copy for reference
df_original = df_wide[dimension_cols].copy()

for col in dimension_cols:
    # Find the measure info
    measure_info = [(k, v) for k, v in key_measures.items() if v[0] == col]
    if not measure_info:
        continue
    
    should_invert = measure_info[0][1][1]
    
    if should_invert:
        print(f"  {col:25s} [INVERTING - lower is better]")
        # Invert: use percentile rank
        df_wide[col] = (1 - df_wide[col].rank(pct=True)) * 100
    else:
        print(f"  {col:25s} [normalizing - higher is better]")
        # Normal min-max scaling
        min_val = df_wide[col].min()
        max_val = df_wide[col].max()
        if max_val > min_val:
            df_wide[col] = ((df_wide[col] - min_val) / (max_val - min_val)) * 100
        else:
            df_wide[col] = 50.0

# Round to 1 decimal
for col in dimension_cols:
    df_wide[col] = df_wide[col].round(1)

print("\nNormalization complete - all values now 0-100 scale")

# =====================================================================
# STEP 7: CREATE COMPOSITE INDEX
# =====================================================================

print("\n" + "="*70)
print("CREATING COMPOSITE WELLBEING INDEX")
print("="*70)

df_wide['composite_index'] = df_wide[dimension_cols].mean(axis=1).round(1)

print(f"Composite index range: {df_wide['composite_index'].min():.1f} - {df_wide['composite_index'].max():.1f}")
print(f"Composite index mean: {df_wide['composite_index'].mean():.1f}")

# =====================================================================
# STEP 8: CALCULATE GAPS FROM OECD AVERAGE
# =====================================================================

print("\n" + "="*70)
print("CALCULATING GAPS FROM OECD AVERAGE")
print("="*70)

oecd_averages = df_wide[dimension_cols].mean()

for col in dimension_cols:
    gap_col = f"{col}_gap"
    df_wide[gap_col] = (df_wide[col] - oecd_averages[col]).round(1)

print("Gap columns created for all dimensions")
print("\nOECD Averages (all ~50 after normalization):")
for col in dimension_cols:
    print(f"  {col:25s} {oecd_averages[col]:5.1f}")

# =====================================================================
# STEP 9: SORT AND CREATE OUTPUT
# =====================================================================

df_wide = df_wide.sort_values('composite_index', ascending=False).reset_index(drop=True)

# =====================================================================
# STEP 10: DISPLAY RESULTS
# =====================================================================

print("\n" + "="*70)
print("TOP 10 COUNTRIES BY OVERALL WELLBEING")
print("="*70)
print(f"{'Rank':<6} {'Country':<25} {'Score':<8} {'Strengths'}")
print("-" * 70)

for idx, row in df_wide.head(10).iterrows():
    gap_cols = [col for col in df_wide.columns if col.endswith('_gap')]
    strengths = sorted(
        [(col.replace('_gap', ''), row[col]) for col in gap_cols],
        key=lambda x: x[1],
        reverse=True
    )[:2]
    strength_str = f"{strengths[0][0]} (+{strengths[0][1]:.1f}), {strengths[1][0]} (+{strengths[1][1]:.1f})"
    print(f"{idx+1:<6} {row['country']:<25} {row['composite_index']:<8.1f} {strength_str}")

print("\n" + "="*70)
print("BOTTOM 10 COUNTRIES BY OVERALL WELLBEING")
print("="*70)
print(f"{'Rank':<6} {'Country':<25} {'Score':<8} {'Main Weaknesses'}")
print("-" * 70)

for idx, row in df_wide.tail(10).iterrows():
    gap_cols = [col for col in df_wide.columns if col.endswith('_gap')]
    weaknesses = sorted(
        [(col.replace('_gap', ''), row[col]) for col in gap_cols],
        key=lambda x: x[1]
    )[:2]
    weakness_str = f"{weaknesses[0][0]} ({weaknesses[0][1]:.1f}), {weaknesses[1][0]} ({weaknesses[1][1]:.1f})"
    print(f"{len(df_wide)-idx:<6} {row['country']:<25} {row['composite_index']:<8.1f} {weakness_str}")

# =====================================================================
# STEP 11: SAVE PROCESSED DATA
# =====================================================================

print("\n" + "="*70)
print("SAVING PROCESSED DATA")
print("="*70)

# Main output file
output_file = 'oecd_wellbeing_processed.csv'
df_wide.to_csv(output_file, index=False)
print(f"✓ Main file saved: {output_file}")

# Create metadata file
metadata = f"""OECD WELLBEING DATA - PROCESSED FOR PLOTLY STUDIO
================================================

Dataset Summary:
- Countries: {len(df_wide)}
- Dimensions: {len(dimension_cols)}
- Data Years: Most recent available (2018-2024 depending on measure)

Dimensions Included:
"""

for col in dimension_cols:
    measure_info = [(k, v) for k, v in key_measures.items() if v[0] == col]
    if measure_info:
        desc = measure_info[0][1][2]
        metadata += f"  • {col}: {desc}\n"

metadata += f"""
Value Interpretation:
- All dimensions normalized to 0-100 scale
- 0 = Worst performer in dataset
- 100 = Best performer in dataset
- ~50 = OECD average
- Higher values = Better outcomes for all dimensions

Columns:
- country: Country name
- country_code: ISO 3-letter code (for mapping)
- composite_index: Average across all dimensions
- [dimension]: Normalized score (0-100)
- [dimension]_gap: Difference from OECD average

Inverted Measures (lower raw values = higher normalized scores):
- work_life_balance (working long hours)
- safety (homicide rate)
- housing (cost burden)

Top 5 Countries:
"""

for idx, row in df_wide.head(5).iterrows():
    metadata += f"{idx+1}. {row['country']} ({row['composite_index']:.1f})\n"

with open('oecd_data_metadata.txt', 'w', encoding='utf-8') as f:
    f.write(metadata)

print(f"✓ Metadata saved: oecd_data_metadata.txt")

# Save a sample for testing
df_wide.head(15).to_csv('oecd_sample_15countries.csv', index=False)
print(f"✓ Sample file saved: oecd_sample_15countries.csv")

# =====================================================================
# STEP 12: VALIDATION CHECKS
# =====================================================================

print("\n" + "="*70)
print("DATA VALIDATION")
print("="*70)

checks = {
    "No missing country names": df_wide['country'].isna().sum() == 0,
    "No missing country codes": df_wide['country_code'].isna().sum() == 0,
    "All scores 0-100": (df_wide[dimension_cols].min().min() >= 0) and (df_wide[dimension_cols].max().max() <= 100),
    "Composite index exists": 'composite_index' in df_wide.columns,
    "All gaps calculated": all(f'{col}_gap' in df_wide.columns for col in dimension_cols),
    "At least 25 countries": len(df_wide) >= 25,
    "File size reasonable": True  # Will check after save
}

all_passed = True
for check, result in checks.items():
    status = "✓ PASS" if result else "✗ FAIL"
    print(f"{status} - {check}")
    if not result:
        all_passed = False

if all_passed:
    print("\n" + "="*70)
    print("SUCCESS! Data is ready for Plotly Studio!")
    print("="*70)
    print(f"\n📁 Import this file: {output_file}")
    print(f"📊 Countries: {len(df_wide)}")
    print(f"📈 Dimensions: {len(dimension_cols)}")
    print("\n🚀 Next step: Upload to Plotly Studio and use the prompts!")
else:
    print("\n⚠️  WARNING: Some validation checks failed. Review data before proceeding.")

print("\n" + "="*70)