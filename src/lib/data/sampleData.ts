// Sample data for visualizations
export const cityCommuteData = [
  { city: "New York", avg_commute_minutes: 38.5, population: 8336817 },
  { city: "Los Angeles", avg_commute_minutes: 31.9, population: 3979576 },
  { city: "Chicago", avg_commute_minutes: 34.8, population: 2693976 },
  { city: "Houston", avg_commute_minutes: 28.5, population: 2320268 },
  { city: "Phoenix", avg_commute_minutes: 26.7, population: 1680992 },
  { city: "Philadelphia", avg_commute_minutes: 32.3, population: 1584064 },
  { city: "San Antonio", avg_commute_minutes: 25.8, population: 1547253 },
  { city: "San Diego", avg_commute_minutes: 24.8, population: 1423851 },
  { city: "Dallas", avg_commute_minutes: 27.4, population: 1343573 },
  { city: "San Jose", avg_commute_minutes: 28.9, population: 1021795 }
];

export const emissionFactors = {
  sedan: 0.404,
  suv: 0.645,
  electric: 0.186,
  hybrid: 0.322,
  transit: 0.14,
  train: 0.089,
  bike: 0
};

export const costData = {
  car: {
    label: "Driving Alone",
    perMile: 0.67,
    components: [
      { name: "Fuel", perMile: 0.15 },
      { name: "Insurance", fixed: 1500 },
      { name: "Registration/Fees", fixed: 200 },
      { name: "Parking", fixed: 2400 },
      { name: "Maintenance", fixed: 1200 },
      { name: "Depreciation", fixed: 3000 }
    ]
  },
  transit: {
    label: "Public Transit",
    components: [
      { name: "Monthly Pass", fixed: 1440 },
      { name: "Occasional Taxi/Uber", fixed: 600 }
    ]
  },
  bike: {
    label: "Bicycle",
    components: [
      { name: "Bike Purchase (amortized)", fixed: 200 },
      { name: "Maintenance", fixed: 150 },
      { name: "Accessories/Gear", fixed: 100 }
    ]
  }
};

export const happinessData = {
  labels: [0, 10, 20, 30, 40, 45, 50, 60, 70, 80, 90],
  values: [7.8, 7.7, 7.5, 7.3, 7.0, 6.5, 6.0, 5.5, 5.2, 5.0, 4.8]
};

export const remoteWorkTimeline = {
  labels: ['2019 Q1', '2019 Q3', '2020 Q1', '2020 Q2', '2020 Q3', 
          '2021 Q1', '2021 Q3', '2022 Q1', '2022 Q3', '2023 Q1', 
          '2023 Q3', '2024 Q1', '2024 Q3', '2025 Q1'],
  fullyRemote: [5.7, 5.9, 6.2, 42.5, 38.2, 32.5, 28.9, 25.3, 22.1, 19.8, 18.5, 17.2, 16.8, 16.5],
  hybrid: [3.2, 3.5, 3.8, 8.5, 15.2, 18.9, 19.8, 18.5, 16.2, 14.8, 13.5, 12.8, 12.2, 11.8]
};