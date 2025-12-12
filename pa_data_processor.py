"""
Pennsylvania Commute Data Processing Script
Processes PA-specific datasets for visualization
"""

import pandas as pd
import json

# Load PA datasets
print("Loading PA datasets...")

# 1. Load S0802 (Commute data)
s0802 = pd.read_csv('./PA_SO802_Final_1924.csv')

# 2. Load Location Affordability Index
lai = pd.read_excel('PA_Location_Affordability_Index_v3.xlsx')

# 3. Load Fair Market Rents
fmr = pd.read_excel('PA_FY24_FMRs.xlsx')

# 4. Load Metro Wages
metro_wages = pd.read_excel('PA_METRO_WAGES_2024.xlsx')

# 5. Load Non-Metro Wages
nonmetro_wages = pd.read_excel('PA_NONMETRO_WAGES_2024.xlsx')

print("Data loaded successfully!")

# Convert Excel files to JSON
print("\nConverting Excel files to JSON...")
lai.to_json('PA_Location_Affordability_Index_v3.json', orient='records', indent=2)
fmr.to_json('PA_FY24_FMRs.json', orient='records', indent=2)
metro_wages.to_json('PA_METRO_WAGES_2024.json', orient='records', indent=2)
nonmetro_wages.to_json('PA_NONMETRO_WAGES_2024.json', orient='records', indent=2)

# Convert CSV to JSON as well
s0802.to_json('PA_SO802_Final_1924.json', orient='records', indent=2)

print("Excel and CSV files converted to JSON!")

# ============================================================================
# DATASET 1: PA STATE SUMMARY STATS
# ============================================================================

# Helper function to safely convert to float
def safe_float(value, default=0.0):
    try:
        if value is None or value == '' or str(value).lower() in ['nan', 'none', '']:
            return default
        val_str = str(value).replace(',', '').strip()
        if val_str == '':
            return default
        return float(val_str)
    except (ValueError, TypeError, AttributeError):
        return default

# Helper function to safely convert to int
def safe_int(value, default=0):
    try:
        if value is None or value == '' or str(value).lower() in ['nan', 'none', '']:
            return default
        val_str = str(value).replace(',', '').strip()
        if val_str == '':
            return default
        return int(float(val_str))
    except (ValueError, TypeError, AttributeError):
        return default

pa_summary = {
    "total_commuters": safe_int(s0802.iloc[1]['S0802_C01_001E']),  # Total workers (row 1 is state data)
    "avg_commute_minutes": safe_float(s0802.iloc[1]['S0802_C01_013E']),  # Mean travel time
    "drive_alone_pct": safe_float(s0802.iloc[1]['S0802_C02_002E']),  # % drove alone
    "transit_pct": safe_float(s0802.iloc[1]['S0802_C02_010E']),  # % public transit
    "wfh_pct": safe_float(s0802.iloc[1]['S0802_C02_013E']),  # % work from home
    "median_income": 68000,  # Approximate from wage data
}

# Calculate derived stats
pa_summary['annual_hours_lost'] = (
    pa_summary['avg_commute_minutes'] * 2 * 5 * 50 * pa_summary['total_commuters'] / 60
)
pa_summary['annual_cost_avg'] = 8740  # From LAI estimates

# Save
with open('pa_summary_stats.json', 'w') as f:
    json.dump(pa_summary, f, indent=2)

print(f"PA Summary: {pa_summary['total_commuters']:,} commuters")
print(f"Average commute: {pa_summary['avg_commute_minutes']} minutes")

# ============================================================================
# DATASET 2: COUNTY-LEVEL EMISSIONS CALCULATIONS
# ============================================================================

# Parse county names from S0802
county_data = []

for idx, row in s0802.iterrows():
    if idx == 0 or idx == 1:  # Skip header row and state total
        continue
    
    name = str(row['NAME'])
    if 'County' not in name and 'county' not in name.lower():
        continue
    
    county_name = name.split(',')[0].replace(' County', '')
    
    try:
        total_workers = safe_int(row['S0802_C01_001E'])
        mean_commute = safe_float(row['S0802_C01_013E'])
        drive_alone = safe_float(row['S0802_C02_002E'])
        
        # Estimate annual miles (rough approximation)
        # Assume 0.5 miles per minute of commute
        one_way_miles = mean_commute * 0.5
        annual_miles = one_way_miles * 2 * 5 * 50 * total_workers
        
        # Calculate CO2 emissions
        # Assume 25 mpg average, 8.887 kg CO2 per gallon
        gallons = annual_miles / 25
        co2_tons = (gallons * 8.887) / 1000
        
        # Per capita
        co2_per_capita = co2_tons / total_workers if total_workers > 0 else 0
        
        county_data.append({
            'county': county_name,
            'total_workers': total_workers,
            'mean_commute_minutes': mean_commute,
            'drive_alone_pct': drive_alone,
            'annual_co2_tons': co2_tons,
            'co2_per_capita_tons': co2_per_capita
        })
    except (ValueError, KeyError):
        continue

if county_data:
    county_df = pd.DataFrame(county_data)
    county_df = county_df.sort_values('annual_co2_tons', ascending=False)
    
    # Save
    county_df.to_csv('pa_county_emissions.csv', index=False)
    county_df.to_json('pa_county_emissions.json', orient='records', indent=2)
    
    print(f"\nProcessed {len(county_df)} counties")
    print(f"Total PA CO2: {county_df['annual_co2_tons'].sum():,.0f} tons/year")
    
    # Top 5 counties
    print("\nTop 5 Emitting Counties:")
    for idx, row in county_df.head(5).iterrows():
        print(f"  {row['county']}: {row['annual_co2_tons']:,.0f} tons")
else:
    print("\nNo county-level data found in CSV file")
    # Create empty files
    county_df = pd.DataFrame()  # Define county_df even when empty
    county_df.to_csv('pa_county_emissions.csv', index=False)
    county_df.to_json('pa_county_emissions.json', orient='records', indent=2)

# ============================================================================
# DATASET 3: MODE SHIFT SCENARIOS
# ============================================================================

current_state = {
    'drive_alone_pct': pa_summary['drive_alone_pct'],
    'transit_pct': pa_summary['transit_pct'],
    'wfh_pct': pa_summary['wfh_pct']
}

# Scenario: 10% of drivers switch to transit
scenario_10pct_transit = {
    'drive_alone_pct': current_state['drive_alone_pct'] - 10,
    'transit_pct': current_state['transit_pct'] + 10,
    'wfh_pct': current_state['wfh_pct']
}

# Scenario: 20% increase in WFH
scenario_20pct_wfh = {
    'drive_alone_pct': current_state['drive_alone_pct'] - 15,
    'transit_pct': current_state['transit_pct'],
    'wfh_pct': current_state['wfh_pct'] + 15
}

# Calculate emissions for each scenario
def calculate_scenario_emissions(scenario_pct, total_commuters=pa_summary['total_commuters']):
    # Emissions per mode (kg CO2 per commuter per year)
    emissions_per_mode = {
        'drive': 2580,  # ~10k miles at 25mpg
        'transit': 580,  # Much lower
        'wfh': 0
    }
    
    drive_commuters = total_commuters * (scenario_pct['drive_alone_pct'] / 100)
    transit_commuters = total_commuters * (scenario_pct['transit_pct'] / 100)
    wfh_commuters = total_commuters * (scenario_pct['wfh_pct'] / 100)
    
    total_emissions = (
        drive_commuters * emissions_per_mode['drive'] +
        transit_commuters * emissions_per_mode['transit'] +
        wfh_commuters * emissions_per_mode['wfh']
    ) / 1000  # Convert to tons
    
    return total_emissions

scenarios = {
    'current': {
        'name': 'Current (2024)',
        'mode_split': current_state,
        'emissions_tons': calculate_scenario_emissions(current_state)
    },
    '10pct_transit': {
        'name': '10% Shift to Transit',
        'mode_split': scenario_10pct_transit,
        'emissions_tons': calculate_scenario_emissions(scenario_10pct_transit)
    },
    '20pct_wfh': {
        'name': '20% More Remote Work',
        'mode_split': scenario_20pct_wfh,
        'emissions_tons': calculate_scenario_emissions(scenario_20pct_wfh)
    }
}

# Calculate savings
for key, scenario in scenarios.items():
    if key != 'current':
        scenario['emissions_reduced'] = (
            scenarios['current']['emissions_tons'] - scenario['emissions_tons']
        )
        scenario['pct_reduction'] = (
            scenario['emissions_reduced'] / scenarios['current']['emissions_tons'] * 100
        )

# Save
with open('pa_scenarios.json', 'w') as f:
    json.dump(scenarios, f, indent=2)

print("\n\nScenario Analysis:")
for key, scenario in scenarios.items():
    print(f"\n{scenario['name']}:")
    print(f"  Emissions: {scenario['emissions_tons']:,.0f} tons CO2")
    if 'emissions_reduced' in scenario:
        print(f"  Reduction: {scenario['emissions_reduced']:,.0f} tons ({scenario['pct_reduction']:.1f}%)")

# ============================================================================
# DATASET 4: PA METRO COMPARISON
# ============================================================================

# Major PA metros for focused comparison
pa_metros = {
    'Philadelphia': {
        'avg_commute': 32.5,
        'workers': 2_100_000,
        'drive_alone_pct': 65,
        'transit_pct': 25,
        'median_income': 72000
    },
    'Pittsburgh': {
        'avg_commute': 26.8,
        'workers': 980_000,
        'drive_alone_pct': 73,
        'transit_pct': 12,
        'median_income': 58000
    },
    'Harrisburg': {
        'avg_commute': 24.5,
        'workers': 290_000,
        'drive_alone_pct': 82,
        'transit_pct': 3,
        'median_income': 54000
    },
    'Allentown': {
        'avg_commute': 25.2,
        'workers': 380_000,
        'drive_alone_pct': 80,
        'transit_pct': 4,
        'median_income': 56000
    }
}

metro_comparison = []
for metro, stats in pa_metros.items():
    # Calculate emissions
    annual_miles_per_worker = stats['avg_commute'] * 0.5 * 2 * 250
    co2_per_worker = (annual_miles_per_worker / 25 * 8.887) / 1000
    
    metro_comparison.append({
        'metro': metro,
        'avg_commute': stats['avg_commute'],
        'workers': stats['workers'],
        'co2_per_capita': co2_per_worker,
        'transit_pct': stats['transit_pct'],
        'median_income': stats['median_income'],
        'commute_burden_score': (stats['avg_commute'] / stats['median_income'] * 100000)
    })

metro_df = pd.DataFrame(metro_comparison)
metro_df.to_json('pa_metro_comparison.json', orient='records', indent=2)

print("\n\nPA Metro Comparison:")
for _, row in metro_df.iterrows():
    print(f"{row['metro']}: {row['avg_commute']:.1f} min, {row['co2_per_capita']:.2f} tons CO2/person")

# ============================================================================
# DATASET 5: COUNTY COORDINATES (for mapping)
# ============================================================================

# Major PA county coordinates (simplified for visualization)
county_coords = {
    'Allegheny': {'lat': 40.4406, 'lon': -79.9959},
    'Philadelphia': {'lat': 40.0094, 'lon': -75.1333},
    'Montgomery': {'lat': 40.1688, 'lon': -75.3560},
    'Bucks': {'lat': 40.3154, 'lon': -75.1085},
    'Delaware': {'lat': 39.9167, 'lon': -75.4167},
    'Chester': {'lat': 39.9857, 'lon': -75.7499},
    'Lancaster': {'lat': 40.0379, 'lon': -76.3055},
    'York': {'lat': 39.9626, 'lon': -76.7277},
    'Berks': {'lat': 40.4167, 'lon': -75.9269},
    'Dauphin': {'lat': 40.3991, 'lon': -76.7897},
    'Westmoreland': {'lat': 40.3097, 'lon': -79.5181},
    'Erie': {'lat': 42.1292, 'lon': -80.0851},
    'Lehigh': {'lat': 40.6023, 'lon': -75.5964},
    'Northampton': {'lat': 40.7533, 'lon': -75.3082},
    'Luzerne': {'lat': 41.1843, 'lon': -75.8813}
}

# Merge with emissions data
county_map_data = []
if county_data:
    for _, row in county_df.iterrows():
        if row['county'] in county_coords:
            county_map_data.append({
                'county': row['county'],
                'lat': county_coords[row['county']]['lat'],
                'lon': county_coords[row['county']]['lon'],
                'co2_tons': row['annual_co2_tons'],
                'co2_per_capita': row['co2_per_capita_tons'],
                'mean_commute': row['mean_commute_minutes']
            })

with open('pa_county_map_data.json', 'w') as f:
    json.dump(county_map_data, f, indent=2)

print(f"\n\nCreated map data for {len(county_map_data)} counties")

print("\n" + "="*60)
print("Data processing complete!")
print("="*60)
print("\nGenerated files:")
print("  - PA_SO802_Final_1924.json (commute data)")
print("  - PA_Location_Affordability_Index_v3.json (affordability index)")
print("  - PA_FY24_FMRs.json (fair market rents)")
print("  - PA_METRO_WAGES_2024.json (metro wages)")
print("  - PA_NONMETRO_WAGES_2024.json (non-metro wages)")
print("  - pa_summary_stats.json (state totals)")
print("  - pa_county_emissions.csv/json (all counties)")
print("  - pa_scenarios.json (mode shift scenarios)")
print("  - pa_metro_comparison.json (major metros)")
print("  - pa_county_map_data.json (mapping data)")
