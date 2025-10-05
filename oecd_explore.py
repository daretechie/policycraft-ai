import pandas as pd
import numpy as np

# Load data
df = pd.read_csv('OECD-wellbeing.csv')

print("="*60)
print("OECD WELLBEING DATASET EXPLORATION")
print("="*60)

# Basic info
print(f"\n📊 Dataset Size: {len(df)} rows")
print(f"🌍 Countries: {df['Country'].nunique()}")
print(f"📅 Years: {sorted(df['Year'].unique())}")

# Domain analysis
print("\n" + "="*60)
print("DOMAINS AVAILABLE")
print("="*60)
domains = df['Domain'].value_counts()
print(domains)

# Measures per domain
print("\n" + "="*60)
print("MEASURES BY DOMAIN")
print("="*60)
for domain in df['Domain'].unique():
    measures = df[df['Domain'] == domain]['Measure'].unique()
    print(f"\n{domain}:")
    for measure in measures:
        # Count how many countries have this measure
        count = df[(df['Domain'] == domain) & (df['Measure'] == measure)]['Country'].nunique()
        years = df[(df['Domain'] == domain) & (df['Measure'] == measure)]['Year'].unique()
        print(f"  • {measure} ({count} countries, years: {sorted(years)})")

# Year completeness analysis
print("\n" + "="*60)
print("DATA COMPLETENESS BY YEAR")
print("="*60)
year_analysis = df.groupby('Year').agg({
    'Country': 'nunique',
    'Measure': 'nunique',
    'Domain': 'nunique'
}).rename(columns={
    'Country': 'Countries',
    'Measure': 'Measures',
    'Domain': 'Domains'
})
print(year_analysis.sort_index(ascending=False))

# Find best year (most measures × countries)
year_scores = df.groupby('Year').apply(
    lambda x: x['Measure'].nunique() * x['Country'].nunique()
)
best_year = year_scores.idxmax()
print(f"\n🏆 Best Year (most complete): {best_year}")

# Sex breakdown analysis
print("\n" + "="*60)
print("SEX BREAKDOWN AVAILABILITY")
print("="*60)
sex_breakdown = df['Sex'].value_counts()
print(sex_breakdown)
print("\n⚠️  Note: You'll want Sex='Total' for country-level analysis")

# Sample countries available
print("\n" + "="*60)
print("SAMPLE COUNTRIES (first 15)")
print("="*60)
countries = sorted(df['Country'].unique())[:15]
for i, country in enumerate(countries, 1):
    code = df[df['Country'] == country]['REF_AREA'].iloc[0]
    print(f"{i:2d}. {code} - {country}")

# Identify which measures are "Total" vs broken down
print("\n" + "="*60)
print("MEASURES WITH SEX BREAKDOWN")
print("="*60)
has_breakdown = df[df['Sex'] != 'Total'].groupby('Measure')['Country'].count()
if len(has_breakdown) > 0:
    print("These measures have Male/Female breakdowns:")
    for measure in has_breakdown.index.unique():
        print(f"  • {measure}")
else:
    print("No sex breakdowns found in sample.")

print("\n" + "="*60)
print("NEXT STEPS")
print("="*60)
print("1. Review the domains and measures above")
print("2. Decide if you'll use single year or mixed years")
print("3. Select 8-10 key measures that tell a story")
print("4. Run the transformation script (coming next)")
print("="*60)