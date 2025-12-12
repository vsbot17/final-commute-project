<script lang="ts">
  import { onMount } from 'svelte';

  // County data type
  type CountyData = {
    county: string;
    lat: number;
    lon: number;
    co2_tons: number;
    population?: number;
    co2_per_capita: number;
    total_workers?: number;
    mean_commute?: number;
  };

  // PA County data (loaded from JSON)
  let countyData: CountyData[] = [];
  let dataLoaded: boolean = false;

  let mapContainer: HTMLDivElement;
  let viewMode: 'total' | 'per_capita' = 'total';
  let selectedCounty: CountyData | null = null;

  // County coordinates mapping (for counties that might be in map data)
  const countyCoordinates: Record<string, { lat: number; lon: number }> = {
    'Allegheny': { lat: 40.4406, lon: -79.9959 },
    'Philadelphia': { lat: 40.0094, lon: -75.1333 },
    'Montgomery': { lat: 40.1688, lon: -75.3560 },
    'Bucks': { lat: 40.3154, lon: -75.1085 },
    'Delaware': { lat: 39.9167, lon: -75.4167 },
    'Chester': { lat: 39.9857, lon: -75.7499 },
    'Lancaster': { lat: 40.0379, lon: -76.3055 },
    'York': { lat: 39.9626, lon: -76.7277 },
    'Berks': { lat: 40.4167, lon: -75.9269 },
    'Dauphin': { lat: 40.3991, lon: -76.7897 },
    'Westmoreland': { lat: 40.3097, lon: -79.5181 },
    'Erie': { lat: 42.1292, lon: -80.0851 },
    'Lehigh': { lat: 40.6023, lon: -75.5964 },
    'Northampton': { lat: 40.7533, lon: -75.3082 },
    'Luzerne': { lat: 41.1843, lon: -75.8813 }
  };

  // Metro to county mapping (approximate)
  const metroToCounties: Record<string, string[]> = {
    'Philadelphia': ['Philadelphia', 'Montgomery', 'Bucks', 'Delaware', 'Chester'],
    'Pittsburgh': ['Allegheny', 'Westmoreland'],
    'Harrisburg': ['Dauphin'],
    'Allentown': ['Lehigh', 'Northampton']
  };

  $: totalEmissions = countyData.length > 0 ? countyData.reduce((sum, c) => sum + c.co2_tons, 0) : 0;
  $: top10Emissions = countyData.length > 0 ? countyData.slice(0, Math.min(10, countyData.length)).reduce((sum, c) => sum + c.co2_tons, 0) : 0;
  $: top10Percentage = totalEmissions > 0 ? (top10Emissions / totalEmissions * 100).toFixed(0) : '0';

  onMount(async () => {
    try {
      // Try to load county map data first
      const mapDataResponse = await fetch('/pa_county_map_data.json');
      const mapData = await mapDataResponse.json();
      
      // Try to load county emissions data
      const emissionsResponse = await fetch('/pa_county_emissions.json');
      const emissionsData = await emissionsResponse.json();
      
      // Try to load metro comparison data as fallback
      const metroResponse = await fetch('/pa_metro_comparison.json');
      const metroData = await metroResponse.json();

      if (mapData && mapData.length > 0) {
        // Use map data if available
        countyData = mapData.map((item: any) => ({
          county: item.county,
          lat: item.lat,
          lon: item.lon,
          co2_tons: item.co2_tons || 0,
          co2_per_capita: item.co2_per_capita || 0,
          mean_commute: item.mean_commute
        }));
      } else if (emissionsData && emissionsData.length > 0) {
        // Use emissions data and add coordinates
        countyData = emissionsData.map((item: any) => {
          const coords = countyCoordinates[item.county] || { lat: 40.0, lon: -77.0 };
          return {
            county: item.county,
            lat: coords.lat,
            lon: coords.lon,
            co2_tons: item.annual_co2_tons || 0,
            co2_per_capita: item.co2_per_capita_tons || 0,
            total_workers: item.total_workers,
            mean_commute: item.mean_commute_minutes
          };
        });
      } else if (metroData && metroData.length > 0) {
        // Use metro data as fallback - use metro names directly
        countyData = metroData.map((metro: any) => {
          // Use metro name as county name, or fallback to first county in mapping
          const counties = metroToCounties[metro.metro] || [metro.metro];
          const primaryCounty = counties[0];
          const coords = countyCoordinates[primaryCounty] || { lat: 40.0, lon: -77.0 };
          
          // Calculate total CO2 from per capita and workers
          const estimatedCO2 = metro.co2_per_capita * metro.workers;
          
          return {
            county: metro.metro, // Use metro name for clarity
            lat: coords.lat,
            lon: coords.lon,
            co2_tons: estimatedCO2,
            co2_per_capita: metro.co2_per_capita,
            total_workers: metro.workers,
            mean_commute: metro.avg_commute
          };
        });
      } else {
        // Fallback to default data structure (4 metros)
        countyData = [
          { county: 'Philadelphia', lat: 40.0094, lon: -75.1333, co2_tons: 2_345_000, co2_per_capita: 2.89, total_workers: 2100000, mean_commute: 32.5 },
          { county: 'Allegheny', lat: 40.4406, lon: -79.9959, co2_tons: 1_234_000, co2_per_capita: 2.38, total_workers: 980000, mean_commute: 26.8 },
          { county: 'Harrisburg', lat: 40.3991, lon: -76.7897, co2_tons: 630_000, co2_per_capita: 2.18, total_workers: 290000, mean_commute: 24.5 },
          { county: 'Allentown', lat: 40.6023, lon: -75.5964, co2_tons: 851_000, co2_per_capita: 2.24, total_workers: 380000, mean_commute: 25.2 }
        ];
      }

      // Sort by CO2 emissions (descending)
      countyData.sort((a, b) => b.co2_tons - a.co2_tons);
      
      dataLoaded = true;
      renderMap();
    } catch (error) {
      console.error('Error loading county data:', error);
      // Use fallback data (4 metros)
      countyData = [
        { county: 'Philadelphia', lat: 40.0094, lon: -75.1333, co2_tons: 2_345_000, co2_per_capita: 2.89, total_workers: 2100000, mean_commute: 32.5 },
        { county: 'Allegheny', lat: 40.4406, lon: -79.9959, co2_tons: 1_234_000, co2_per_capita: 2.38, total_workers: 980000, mean_commute: 26.8 },
        { county: 'Harrisburg', lat: 40.3991, lon: -76.7897, co2_tons: 630_000, co2_per_capita: 2.18, total_workers: 290000, mean_commute: 24.5 },
        { county: 'Allentown', lat: 40.6023, lon: -75.5964, co2_tons: 851_000, co2_per_capita: 2.24, total_workers: 380000, mean_commute: 25.2 }
      ];
      dataLoaded = true;
      renderMap();
    }
  });

  function renderMap() {
    if (!mapContainer || countyData.length === 0) return;

    const svgWidth = 900;
    const svgHeight = 600;
    const leftMargin = 100;
    const rightMargin = 50;
    const topMargin = 60;
    const bottomMargin = 120; // Increased to accommodate county names
    const plotWidth = svgWidth - leftMargin - rightMargin;
    const plotHeight = svgHeight - topMargin - bottomMargin;

    // Determine axes: X = Counties (categorical), Y = Emissions
    const valueKey = viewMode === 'total' ? 'co2_tons' : 'co2_per_capita';
    const yAxisLabel = viewMode === 'total' ? 'Total Annual CO₂ Emissions (tons)' : 'Per Capita CO₂ Emissions (tons/person)';
    
    // Sort counties by emissions for display
    const sortedData = [...countyData].sort((a, b) => b[valueKey] - a[valueKey]);
    
    // Get data ranges for Y-axis scaling
    const values = countyData.map(c => c[valueKey]);
    const minValue = 0; // Always start from 0 for bar chart style
    const maxValue = Math.max(...values) * 1.1; // Add 10% padding at top

    // Circle size based on total workers - calculate all worker values first
    const workerValues = countyData.map(c => c.total_workers || 0).filter(v => v > 0);
    const maxWorkers = workerValues.length > 0 ? Math.max(...workerValues) : 1;
    const minWorkers = workerValues.length > 0 ? Math.min(...workerValues) : 0;
    
    function getRadius(county: any): number {
      const workers = county.total_workers || 0;
      if (maxWorkers > 0 && workers > 0) {
        const minR = 12, maxR = 45;
        // Use square root scaling for better visual differentiation
        const normalized = Math.sqrt((workers - minWorkers) / (maxWorkers - minWorkers || 1));
        return normalized * (maxR - minR) + minR;
      }
      return 20; // Default radius when workers not available
    }

    // Calculate positions for each county (evenly spaced on x-axis)
    const countySpacing = plotWidth / (sortedData.length + 1);

    // SVG setup
    const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
    svg.setAttribute('viewBox', `0 0 ${svgWidth} ${svgHeight}`);
    svg.style.width = '100%';
    svg.style.height = `${svgHeight}px`;
    svg.style.background = 'rgba(255,255,255,0.05)';
    svg.style.borderRadius = '12px';

    // Plot area background
    const plotArea = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
    plotArea.setAttribute('x', String(leftMargin));
    plotArea.setAttribute('y', String(topMargin));
    plotArea.setAttribute('width', String(plotWidth));
    plotArea.setAttribute('height', String(plotHeight));
      plotArea.setAttribute('fill', 'rgba(255,255,255,0.02)');
      plotArea.setAttribute('stroke', 'rgba(255,255,255,0.2)');
    plotArea.setAttribute('stroke-width', '1');
    svg.appendChild(plotArea);

    // Draw X-axis (Counties)
    const xAxis = document.createElementNS('http://www.w3.org/2000/svg', 'line');
    xAxis.setAttribute('x1', String(leftMargin));
    xAxis.setAttribute('y1', String(topMargin + plotHeight));
    xAxis.setAttribute('x2', String(leftMargin + plotWidth));
    xAxis.setAttribute('y2', String(topMargin + plotHeight));
      xAxis.setAttribute('stroke', 'rgba(255,255,255,0.5)');
    xAxis.setAttribute('stroke-width', '2');
    svg.appendChild(xAxis);

    // Draw Y-axis (Emissions)
    const yAxis = document.createElementNS('http://www.w3.org/2000/svg', 'line');
    yAxis.setAttribute('x1', String(leftMargin));
    yAxis.setAttribute('y1', String(topMargin));
    yAxis.setAttribute('x2', String(leftMargin));
    yAxis.setAttribute('y2', String(topMargin + plotHeight));
      yAxis.setAttribute('stroke', 'rgba(255,255,255,0.5)');
    yAxis.setAttribute('stroke-width', '2');
    svg.appendChild(yAxis);

    // X-axis labels (County names)
    sortedData.forEach((county, index) => {
      const x = leftMargin + countySpacing * (index + 1);
      
      // Tick mark
      const tick = document.createElementNS('http://www.w3.org/2000/svg', 'line');
      tick.setAttribute('x1', String(x));
      tick.setAttribute('y1', String(topMargin + plotHeight));
      tick.setAttribute('x2', String(x));
      tick.setAttribute('y2', String(topMargin + plotHeight + 5));
            tick.setAttribute('stroke', 'rgba(255,255,255,0.4)');
      tick.setAttribute('stroke-width', '1');
      svg.appendChild(tick);
      
      // County name label (horizontal, with better spacing)
      const label = document.createElementNS('http://www.w3.org/2000/svg', 'text');
      label.setAttribute('x', String(x));
      label.setAttribute('y', String(topMargin + plotHeight + 25));
      label.setAttribute('text-anchor', 'middle');
            label.setAttribute('fill', 'rgba(255,255,255,0.9)');
      label.setAttribute('font-size', '14');
      label.setAttribute('font-weight', '600');
      label.textContent = county.county;
      svg.appendChild(label);
    });

    // Y-axis ticks and labels (Emissions)
    const yTickCount = 6;
    for (let i = 0; i <= yTickCount; i++) {
      const value = minValue + (maxValue - minValue) * (1 - i / yTickCount); // Invert for SVG coordinates
      const y = topMargin + (plotHeight * i / yTickCount);
      
      // Tick mark
      const tick = document.createElementNS('http://www.w3.org/2000/svg', 'line');
      tick.setAttribute('x1', String(leftMargin));
      tick.setAttribute('y1', String(y));
      tick.setAttribute('x2', String(leftMargin - 5));
      tick.setAttribute('y2', String(y));
            tick.setAttribute('stroke', 'rgba(255,255,255,0.4)');
      tick.setAttribute('stroke-width', '1');
      svg.appendChild(tick);
      
      // Label
      const label = document.createElementNS('http://www.w3.org/2000/svg', 'text');
      label.setAttribute('x', String(leftMargin - 10));
      label.setAttribute('y', String(y + 4));
      label.setAttribute('text-anchor', 'end');
            label.setAttribute('fill', 'rgba(255,255,255,0.85)');
      label.setAttribute('font-size', '12');
      if (viewMode === 'total') {
        label.textContent = (value / 1000).toFixed(0) + 'K';
      } else {
        label.textContent = value.toFixed(1);
      }
      svg.appendChild(label);
    }

    // X-axis title
    const xAxisTitle = document.createElementNS('http://www.w3.org/2000/svg', 'text');
    xAxisTitle.setAttribute('x', String(leftMargin + plotWidth / 2));
    xAxisTitle.setAttribute('y', String(svgHeight - 25));
    xAxisTitle.setAttribute('text-anchor', 'middle');
      xAxisTitle.setAttribute('fill', 'rgba(255,255,255,0.9)');
    xAxisTitle.setAttribute('font-size', '14');
    xAxisTitle.setAttribute('font-weight', '600');
    xAxisTitle.textContent = 'Pennsylvania Counties/Metros';
    svg.appendChild(xAxisTitle);

    // Y-axis title
    const yAxisTitle = document.createElementNS('http://www.w3.org/2000/svg', 'text');
    yAxisTitle.setAttribute('x', String(20));
    yAxisTitle.setAttribute('y', String(topMargin + plotHeight / 2));
    yAxisTitle.setAttribute('text-anchor', 'middle');
      yAxisTitle.setAttribute('fill', 'rgba(255,255,255,0.9)');
    yAxisTitle.setAttribute('font-size', '14');
    yAxisTitle.setAttribute('font-weight', '600');
    yAxisTitle.setAttribute('transform', `rotate(-90, 20, ${topMargin + plotHeight / 2})`);
    yAxisTitle.textContent = yAxisLabel;
    svg.appendChild(yAxisTitle);

    // Plot counties as circles positioned on x-axis
    const circles: Array<{ circle: SVGCircleElement; county: any }> = [];
    
    sortedData.forEach((county: any, index: number) => {
      const emissionValue = county[valueKey];
      
      // X position: evenly spaced along x-axis
      const x = leftMargin + countySpacing * (index + 1);
      
      // Y position: based on emission value (from bottom axis)
      const y = topMargin + plotHeight - ((emissionValue - minValue) / (maxValue - minValue || 1)) * plotHeight;

      const radius = getRadius(county);

      const circle = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
      circle.setAttribute('cx', String(x));
      circle.setAttribute('cy', String(y));
      circle.setAttribute('r', String(radius));
      circle.setAttribute('fill', '#ff6b6b');
      const isSelected = selectedCounty?.county === county.county;
      circle.setAttribute('fill-opacity', isSelected ? '0.9' : '0.6');
      circle.setAttribute('stroke', '#ff6b6b');
      circle.setAttribute('stroke-width', isSelected ? '3' : '2');
      circle.style.cursor = 'pointer';
      
      // Store circle reference for later updates
      circles.push({ circle, county });
      
      // Click handler to show tooltip
      circle.addEventListener('click', () => {
        // Reset all circles
        circles.forEach(({ circle: c }) => {
          c.setAttribute('fill-opacity', '0.7');
          c.setAttribute('stroke-width', '2');
        });
        // Highlight clicked circle
        circle.setAttribute('fill-opacity', '0.9');
        circle.setAttribute('stroke-width', '3');
        selectedCounty = county;
      });
      circle.addEventListener('mouseenter', () => {
        if (selectedCounty?.county !== county.county) {
          circle.setAttribute('fill-opacity', '0.8');
          circle.setAttribute('stroke-width', '2.5');
        }
      });
      circle.addEventListener('mouseleave', () => {
        if (selectedCounty?.county !== county.county) {
          circle.setAttribute('fill-opacity', '0.7');
          circle.setAttribute('stroke-width', '2');
        }
      });
      svg.appendChild(circle);

      // Add emission value label above circle
      const valueLabel = document.createElementNS('http://www.w3.org/2000/svg', 'text');
      valueLabel.setAttribute('x', String(x));
      valueLabel.setAttribute('y', String(y - radius - 10));
      valueLabel.setAttribute('text-anchor', 'middle');
      valueLabel.setAttribute('font-size', '12');
            valueLabel.setAttribute('fill', 'rgba(255,255,255,0.9)');
      valueLabel.setAttribute('font-weight', '600');
            valueLabel.setAttribute('stroke', '#000');
      valueLabel.setAttribute('stroke-width', '0.5');
      valueLabel.setAttribute('stroke-opacity', '0.5');
      if (viewMode === 'total') {
        valueLabel.textContent = (emissionValue / 1000).toFixed(0) + 'K';
      } else {
        valueLabel.textContent = emissionValue.toFixed(2);
      }
      svg.appendChild(valueLabel);

      // Draw vertical line from axis to circle center (optional visual guide)
      const guideLine = document.createElementNS('http://www.w3.org/2000/svg', 'line');
      guideLine.setAttribute('x1', String(x));
      guideLine.setAttribute('y1', String(topMargin + plotHeight));
      guideLine.setAttribute('x2', String(x));
      guideLine.setAttribute('y2', String(y));
      guideLine.setAttribute('stroke', 'rgba(255,255,255,0.15)');
      guideLine.setAttribute('stroke-width', '1');
      guideLine.setAttribute('stroke-dasharray', '3,3');
      svg.insertBefore(guideLine, circle); // Insert before circle so it's behind
    });

    mapContainer.innerHTML = '';
    mapContainer.appendChild(svg);
  }

  function toggleView() {
    viewMode = viewMode === 'total' ? 'per_capita' : 'total';
    renderMap();
  }
</script>

<div class="chapter-container">
  <div class="chapter-header">
    <h1>Where's the Problem?</h1>
    <p class="subtitle">Pennsylvania's Carbon Hotspots</p>
  </div>

  {#if !dataLoaded}
    <div class="loading-state">
      <p>Loading Pennsylvania county emissions data...</p>
    </div>
  {:else}
  <div class="content-wrapper">
    <div class="narrative-intro">
      <h2>Mapping Pennsylvania's Carbon Footprint</h2>
      <p>
        The emissions we saw in Chapter 1 aren't spread evenly across Pennsylvania. 
        Some regions bear a disproportionate share of the burden—and understanding where 
        emissions are concentrated is the first step toward targeted solutions.
      </p>
      <p>
        The data reveals a critical pattern: <strong>just {Math.min(10, countyData.length)} counties 
        account for {top10Percentage}% of Pennsylvania's total commute emissions</strong>. 
        This concentration means that strategic interventions in these areas could yield 
        outsized environmental benefits.
      </p>
    </div>

    <div class="intro-stats">
      <div class="key-stat">
        <span class="stat-number">{Math.min(10, countyData.length)}</span>
        <span class="stat-label">counties account for</span>
        <span class="stat-highlight">{top10Percentage}%</span>
        <span class="stat-label">of PA's total commute emissions</span>
      </div>
    </div>

    <div class="map-controls">
      <button 
        class="view-toggle"
        class:active={viewMode === 'total'}
        on:click={toggleView}
      >
        {viewMode === 'total' ? '📊 Total Emissions' : '👤 Per Capita'}
      </button>
      <p class="control-hint">
        {viewMode === 'total' 
          ? 'Showing total annual CO₂ emissions by county' 
          : 'Showing emissions per person - rural counties often higher!'}
      </p>
    </div>

    <!-- STORY CONTEXT & CHART TITLE -->
    <div class="graph-story-context">
      <h2>
        {viewMode === 'total'
          ? 'Total Emissions by County/Metro'
          : 'Per Capita Emissions by County/Metro'}
      </h2>
      <p class="chart-explanation">
        {viewMode === 'total'
          ? 'This visualization shows where Pennsylvania\'s commute emissions are concentrated. Each circle represents a county or metro area, positioned on the X-axis by name. The Y-axis shows total annual CO₂ emissions in tons. The size of each circle reflects the number of workers—larger circles mean more commuters. Click on any circle to explore detailed statistics for that region.'
          : 'Switching to per capita view reveals a different story. While urban areas generate the most total emissions, rural counties often have higher emissions per person due to longer commutes and limited transit options. The Y-axis now shows emissions per person (tons/person), while circle size still represents total workers. This view helps identify where individual commuters face the greatest environmental impact.'}
      </p>
      <p class="chart-interaction-hint">
        💡 <strong>Explore the data:</strong> Click on any circle to see detailed statistics including total emissions, 
        worker count, average commute time, and per capita emissions for that county or metro area.
      </p>
    </div>

    <div class="chart-and-details">
      <div class="map-container" bind:this={mapContainer}></div>

      {#if selectedCounty}
        <div class="county-detail">
          <button class="close-btn" on:click={() => selectedCounty = null} aria-label="Close details">×</button>
          <h3>{selectedCounty.county} {selectedCounty.county.includes('County') ? '' : 'Metro Area'}</h3>
          <div class="detail-grid">
            <div class="detail-item">
              <span class="detail-label">Total Annual Emissions</span>
              <span class="detail-value">{(selectedCounty.co2_tons / 1000).toFixed(0)}K tons</span>
            </div>
            {#if selectedCounty.total_workers}
              <div class="detail-item">
                <span class="detail-label">Total Workers</span>
                <span class="detail-value">{selectedCounty.total_workers.toLocaleString()}</span>
              </div>
            {/if}
            {#if selectedCounty.mean_commute}
              <div class="detail-item">
                <span class="detail-label">Avg Commute Time</span>
                <span class="detail-value">{selectedCounty.mean_commute.toFixed(1)} min</span>
              </div>
            {/if}
            <div class="detail-item">
              <span class="detail-label">Per Capita Emissions</span>
              <span class="detail-value">{selectedCounty.co2_per_capita.toFixed(2)} tons/person</span>
            </div>
          </div>
        </div>
      {/if}
    </div>

    {#if viewMode === 'total'}
      <div class="insight-box">
        <h3>🌆 Top Emitting Regions by Total</h3>
        <ul>
          {#each countyData.slice(0, 3) as c}
            <li>
              <strong>{c.county}:</strong> {(c.co2_tons/1000).toFixed(0)}K tons/year
            </li>
          {/each}
        </ul>
        <p>
          Urban regions generate the most <em>total</em> emissions, reflecting both population size and
          total driving. Policy efforts here have large aggregate benefits.
        </p>
      </div>
    {:else}
      <div class="insight-box">
        <h3>🚘 Per-Person Impact: Rural Counties Show Higher Individual Burden</h3>
        <ul>
          {#each [...countyData].sort((a, b) => b.co2_per_capita - a.co2_per_capita).slice(0, 3) as c}
            <li>
              <strong>{c.county}:</strong> {c.co2_per_capita.toFixed(2)} tons/person
            </li>
          {/each}
        </ul>
        <p>
          Here, rural and suburban areas often top the list—longer solo commutes and sparse transit.
          Targeting these counties with carpooling incentives or limited transit options could have a disproportionate impact per person.
        </p>
      </div>
    {/if}

    <div class="narrative-conclusion">
      <h2>What the Data Tells Us</h2>
      {#if viewMode === 'total'}
        <p>
          When we look at <strong>total emissions</strong>, Pennsylvania's major metropolitan areas dominate. 
          The largest circles—representing counties with the most workers—also tend to be the highest on the 
          Y-axis, showing the most emissions.
        </p>
        <p>
          This pattern makes sense: more people means more commuters, which means more cars on the road. 
          But it also reveals an opportunity: <strong>targeted transit improvements in these high-emission 
          regions could yield massive environmental benefits</strong>. A 20% reduction in Philadelphia's 
          commute emissions would prevent more CO₂ than eliminating all commute emissions in many smaller counties.
        </p>
        <p class="transition-prompt">
          But total emissions only tell part of the story. Switch to "Per Capita" view to see which regions 
          have the highest individual impact—and why.
        </p>
      {:else}
        <p>
          The <strong>per capita view</strong> reveals a different pattern entirely. While urban areas generate 
          the most total emissions, some rural and suburban counties show surprisingly high emissions per person.
        </p>
        <p>
          Why? Longer commute distances, limited public transit options, and car-dependent infrastructure 
          mean that each individual commuter in these regions has a larger carbon footprint. A commuter 
          in a rural county might drive 40 minutes each way, while a Philadelphia commuter might take 
          a 30-minute train ride—even though the Philadelphian's total commute time is longer, their 
          per-person emissions are lower.
        </p>
        <p class="key-insight">
          <strong>This reveals a critical insight:</strong> Transit infrastructure doesn't just reduce 
          total emissions—it dramatically lowers per-person impact, even in dense urban areas. 
          The next chapter explores this pattern in detail.
        </p>
      {/if}
    </div>

  </div>
  {/if}
</div>

<style>
  .chapter-container {
    min-height: 100vh;
    background: linear-gradient(180deg, #16213e 0%, #0f3460 100%);
    color: white;
    padding: 4rem 2rem;
  }

  .chapter-header {
    text-align: center;
    margin-bottom: 4rem;
  }

  .chapter-header h1 {
    font-size: 3.5rem;
    font-weight: 800;
    margin-bottom: 1rem;
  }

  .subtitle {
    font-size: 1.5rem;
    opacity: 0.9;
  }

  .content-wrapper {
    max-width: 1200px;
    margin: 0 auto;
  }

  .intro-stats {
    text-align: center;
    margin: 3rem 0;
    padding: 2rem;
    background: rgba(255, 107, 107, 0.1);
    border-radius: 15px;
    border: 2px solid #ff6b6b;
  }

  .key-stat {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 0.5rem;
  }

  .stat-number {
    font-size: 4rem;
    font-weight: 800;
    color: #ff6b6b;
  }

  .stat-highlight {
    font-size: 5rem;
    font-weight: 800;
    color: #ffd93d;
  }

  .stat-label {
    font-size: 1.3rem;
    opacity: 0.9;
  }

  .map-controls {
    text-align: center;
    margin: 2rem 0;
  }

  .view-toggle {
    padding: 1rem 2rem;
    font-size: 1.1rem;
    font-weight: 600;
    background: rgba(255, 255, 255, 0.1);
    color: white;
    border: 2px solid rgba(255, 255, 255, 0.3);
    border-radius: 8px;
    cursor: pointer;
    transition: all 0.3s;
  }

  .view-toggle:hover,
  .view-toggle.active {
    background: #4ecdc4;
    border-color: #4ecdc4;
    transform: translateY(-2px);
  }

  .control-hint {
    margin-top: 1rem;
    font-size: 1.1rem;
    opacity: 0.8;
  }

  .chart-and-details {
    display: flex;
    gap: 2rem;
    align-items: flex-start;
    margin: 3rem 0;
  }

  .map-container {
    flex: 1;
    min-height: 600px;
    margin-bottom: 0;
  }

  .county-detail {
    flex: 0 0 350px;
    padding: 2rem;
    background: rgba(78, 205, 196, 0.1);
    border-left: 4px solid #4ecdc4;
    border-radius: 12px;
    position: sticky;
    top: 2rem;
    max-height: calc(100vh - 4rem);
    overflow-y: auto;
  }

  .county-detail h3 {
    font-size: 1.8rem;
    margin-bottom: 1.5rem;
    color: #4ecdc4;
    margin-top: 0;
  }

  .close-btn {
    position: absolute;
    top: 1rem;
    right: 1rem;
    background: transparent;
    border: none;
    color: rgba(255, 255, 255, 0.7);
    font-size: 2rem;
    cursor: pointer;
    width: 32px;
    height: 32px;
    display: flex;
    align-items: center;
    justify-content: center;
    border-radius: 50%;
    transition: all 0.2s;
  }

  .close-btn:hover {
    background: rgba(255, 255, 255, 0.1);
    color: white;
  }

  .detail-grid {
    display: grid;
    grid-template-columns: 1fr;
    gap: 1.5rem;
  }

  .detail-item {
    display: flex;
    flex-direction: column;
  }

  .detail-label {
    font-size: 0.9rem;
    text-transform: uppercase;
    letter-spacing: 1px;
    opacity: 0.7;
    margin-bottom: 0.5rem;
  }

  .detail-value {
    font-size: 2rem;
    font-weight: 800;
    color: #4ecdc4;
  }

  .insight-box {
    margin: 2rem auto 2.5rem auto;
    background: rgba(255,255,255,0.13);
    border-left: 4px solid #ffd700;
    border-radius: 8px;
    padding: 1.2rem 1.5rem;
    max-width: 700px;
    box-shadow: 0 2px 18px rgba(0,0,0,0.04);
  }
  .insight-box h3 {
    color: #ffd93d;
    margin-top: 0;
  }
  .insight-box ul {
    padding-left: 1.5rem;
    margin-bottom: 0.7rem;
  }
  .insight-box li {
    font-size: 1.1rem;
    margin: 0.2em 0;
  }

  .loading-state {
    text-align: center;
    padding: 4rem 2rem;
    font-size: 1.5rem;
    opacity: 0.8;
  }

  .narrative-intro {
    margin: 3rem 0;
    padding: 2rem;
    background: rgba(255, 255, 255, 0.08);
    border-radius: 12px;
    line-height: 1.8;
  }

  .narrative-intro h2 {
    font-size: 2.5rem;
    margin-bottom: 1.5rem;
    color: #ffd93d;
    text-align: center;
  }

  .narrative-intro p {
    font-size: 1.2rem;
    margin: 1.5rem 0;
  }

  .narrative-intro strong {
    color: #4ecdc4;
    font-weight: 600;
  }

  .graph-story-context {
    margin: 2.5rem auto 1.3rem auto;
    text-align: center;
    max-width: 700px;
  }
  .graph-story-context h2 {
    color: #ffd93d;
    margin-bottom: 0.35rem;
    font-size: 2.2rem;
    font-weight: 700;
  }
  .chart-explanation {
    font-size: 1.08rem;
    opacity: 0.85;
    margin: 1rem auto;
    max-width: 800px;
    line-height: 1.7;
  }
  .chart-interaction-hint {
    font-size: 1rem;
    margin: 1.5rem auto 0;
    padding: 1rem;
    background: rgba(78, 205, 196, 0.1);
    border-left: 4px solid #4ecdc4;
    border-radius: 8px;
    max-width: 600px;
  }
  .chart-interaction-hint strong {
    color: #4ecdc4;
  }
  .graph-story-context p {
    font-size: 1.08rem;
    opacity: 0.85;
    margin: 0 auto;
  }

  .narrative-conclusion {
    margin: 4rem 0;
    padding: 3rem;
    background: rgba(255, 255, 255, 0.08);
    border-radius: 12px;
    line-height: 1.8;
  }

  .narrative-conclusion h2 {
    font-size: 2.2rem;
    margin-bottom: 2rem;
    color: #ffd93d;
    text-align: center;
  }

  .narrative-conclusion p {
    font-size: 1.2rem;
    margin: 1.5rem 0;
  }

  .narrative-conclusion strong {
    color: #4ecdc4;
    font-weight: 600;
  }

  .transition-prompt {
    font-size: 1.1rem;
    font-style: italic;
    opacity: 0.9;
    margin-top: 2rem;
    padding: 1.5rem;
    background: rgba(78, 205, 196, 0.1);
    border-left: 4px solid #4ecdc4;
    border-radius: 8px;
  }

  .key-insight {
    font-size: 1.3rem;
    font-weight: 600;
    margin-top: 2rem;
    padding: 2rem;
    background: rgba(78, 205, 196, 0.1);
    border-left: 4px solid #4ecdc4;
    border-radius: 8px;
  }

  .key-insight strong {
    color: #4ecdc4;
  }

  @media (max-width: 968px) {
    .chart-and-details {
      flex-direction: column;
    }

    .county-detail {
      flex: 1;
      position: static;
      max-height: none;
    }
  }

  @media (max-width: 768px) {
    .chapter-header h1 {
      font-size: 2rem;
    }

    .stat-number {
      font-size: 2.5rem;
    }

    .stat-highlight {
      font-size: 3rem;
    }
  }
</style>
