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
        // Use metro data as fallback - convert metros to representative counties
        countyData = metroData.map((metro: any) => {
          const counties = metroToCounties[metro.metro] || [metro.metro];
          const primaryCounty = counties[0];
          const coords = countyCoordinates[primaryCounty] || { lat: 40.0, lon: -77.0 };
          
          // Estimate total CO2 from per capita and workers
          const estimatedCO2 = metro.co2_per_capita * metro.workers;
          
          return {
            county: primaryCounty,
            lat: coords.lat,
            lon: coords.lon,
            co2_tons: estimatedCO2,
            co2_per_capita: metro.co2_per_capita,
            total_workers: metro.workers,
            mean_commute: metro.avg_commute
          };
        });
      } else {
        // Fallback to default data structure
        countyData = [
          { county: 'Philadelphia', lat: 40.0094, lon: -75.1333, co2_tons: 2_345_000, co2_per_capita: 1.48 },
          { county: 'Allegheny', lat: 40.4406, lon: -79.9959, co2_tons: 1_234_000, co2_per_capita: 0.99 },
          { county: 'Montgomery', lat: 40.1688, lon: -75.3560, co2_tons: 987_000, co2_per_capita: 1.15 },
          { county: 'Bucks', lat: 40.3154, lon: -75.1085, co2_tons: 765_000, co2_per_capita: 1.22 },
          { county: 'Delaware', lat: 39.9167, lon: -75.4167, co2_tons: 654_000, co2_per_capita: 1.16 }
        ];
      }

      // Sort by CO2 emissions (descending)
      countyData.sort((a, b) => b.co2_tons - a.co2_tons);
      
      dataLoaded = true;
      renderMap();
    } catch (error) {
      console.error('Error loading county data:', error);
      // Use fallback data
      countyData = [
        { county: 'Philadelphia', lat: 40.0094, lon: -75.1333, co2_tons: 2_345_000, co2_per_capita: 1.48 },
        { county: 'Allegheny', lat: 40.4406, lon: -79.9959, co2_tons: 1_234_000, co2_per_capita: 0.99 },
        { county: 'Montgomery', lat: 40.1688, lon: -75.3560, co2_tons: 987_000, co2_per_capita: 1.15 }
      ];
      dataLoaded = true;
      renderMap();
    }
  });

  function renderMap() {
    if (!mapContainer || countyData.length === 0) return;

    const svgWidth = 800;
    const svgHeight = 600;
    const leftMargin = 80;
    const rightMargin = 50;
    const topMargin = 50;
    const bottomMargin = 80;
    const plotWidth = svgWidth - leftMargin - rightMargin;
    const plotHeight = svgHeight - topMargin - bottomMargin;

    // Determine axes: X = Average Commute Time, Y = Emissions
    const valueKey = viewMode === 'total' ? 'co2_tons' : 'co2_per_capita';
    const yAxisLabel = viewMode === 'total' ? 'Total Annual CO₂ Emissions (tons)' : 'Per Capita CO₂ Emissions (tons/person)';
    
    // Get data ranges for scaling
    const commuteTimes = countyData.map(c => c.mean_commute || 0).filter(v => v > 0);
    const minCommute = commuteTimes.length > 0 ? Math.min(...commuteTimes) : 0;
    const maxCommute = commuteTimes.length > 0 ? Math.max(...commuteTimes) : 50;
    
    const values = countyData.map(c => c[valueKey]);
    const minValue = Math.min(...values);
    const maxValue = Math.max(...values);

    // Circle size based on total workers (if available) or fixed size
    function getRadius(county: any) {
      if (county.total_workers) {
        const maxWorkers = Math.max(...countyData.map(c => c.total_workers || 0));
        const minR = 8, maxR = 35;
        return Math.sqrt((county.total_workers || 0) / (maxWorkers || 1)) * (maxR - minR) + minR;
      }
      return 12; // Default radius
    }

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

    // Draw X-axis (Commute Time)
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

    // X-axis ticks and labels (Commute Time)
    const xTickCount = 6;
    for (let i = 0; i <= xTickCount; i++) {
      const value = minCommute + (maxCommute - minCommute) * (i / xTickCount);
      const x = leftMargin + (plotWidth * i / xTickCount);
      
      // Tick mark
      const tick = document.createElementNS('http://www.w3.org/2000/svg', 'line');
      tick.setAttribute('x1', String(x));
      tick.setAttribute('y1', String(topMargin + plotHeight));
      tick.setAttribute('x2', String(x));
      tick.setAttribute('y2', String(topMargin + plotHeight + 5));
      tick.setAttribute('stroke', 'rgba(255,255,255,0.4)');
      tick.setAttribute('stroke-width', '1');
      svg.appendChild(tick);
      
      // Label
      const label = document.createElementNS('http://www.w3.org/2000/svg', 'text');
      label.setAttribute('x', String(x));
      label.setAttribute('y', String(topMargin + plotHeight + 22));
      label.setAttribute('text-anchor', 'middle');
      label.setAttribute('fill', 'rgba(255,255,255,0.8)');
      label.setAttribute('font-size', '12');
      label.textContent = value.toFixed(0);
      svg.appendChild(label);
    }

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
      label.setAttribute('fill', 'rgba(255,255,255,0.8)');
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
    xAxisTitle.setAttribute('y', String(svgHeight - 20));
    xAxisTitle.setAttribute('text-anchor', 'middle');
    xAxisTitle.setAttribute('fill', 'rgba(255,255,255,0.9)');
    xAxisTitle.setAttribute('font-size', '14');
    xAxisTitle.setAttribute('font-weight', '600');
    xAxisTitle.textContent = 'Average Commute Time (minutes)';
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

    // Plot counties as circles
    countyData.forEach((county: any) => {
      const commuteTime = county.mean_commute || (minCommute + maxCommute) / 2;
      const emissionValue = county[valueKey];
      
      // Map to plot coordinates
      const x = leftMargin + ((commuteTime - minCommute) / (maxCommute - minCommute || 1)) * plotWidth;
      const y = topMargin + plotHeight - ((emissionValue - minValue) / (maxValue - minValue || 1)) * plotHeight;

      const radius = getRadius(county);

      const circle = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
      circle.setAttribute('cx', String(x));
      circle.setAttribute('cy', String(y));
      circle.setAttribute('r', String(radius));
      circle.setAttribute('fill', '#ff6b6b');
      circle.setAttribute('fill-opacity', '0.6');
      circle.setAttribute('stroke', '#ff6b6b');
      circle.setAttribute('stroke-width', '2');
      circle.style.cursor = 'pointer';
      circle.addEventListener('mouseenter', () => {
        circle.setAttribute('fill-opacity', '0.9');
        circle.setAttribute('stroke-width', '3');
        selectedCounty = county;
      });
      circle.addEventListener('mouseleave', () => {
        circle.setAttribute('fill-opacity', '0.6');
        circle.setAttribute('stroke-width', '2');
      });
      svg.appendChild(circle);

      // Add county name label
      const nameLabel = document.createElementNS('http://www.w3.org/2000/svg', 'text');
      nameLabel.setAttribute('x', String(x));
      nameLabel.setAttribute('y', String(y - radius - 8));
      nameLabel.setAttribute('text-anchor', 'middle');
      nameLabel.setAttribute('font-size', '11');
      nameLabel.setAttribute('fill', '#ffffff');
      nameLabel.setAttribute('font-weight', '600');
      nameLabel.setAttribute('stroke', '#000000');
      nameLabel.setAttribute('stroke-width', '0.5');
      nameLabel.setAttribute('stroke-opacity', '0.7');
      nameLabel.textContent = county.county;
      svg.appendChild(nameLabel);

      // Annotate top emitter
      const isTop = emissionValue === maxValue;
      if (isTop) {
        const labelX = x + radius + 25;
        const labelY = y - 5;
        const line = document.createElementNS('http://www.w3.org/2000/svg', 'line');
        line.setAttribute('x1', String(x + radius));
        line.setAttribute('y1', String(y));
        line.setAttribute('x2', String(labelX - 4));
        line.setAttribute('y2', String(labelY));
        line.setAttribute('stroke', '#ffd93d');
        line.setAttribute('stroke-width', '1.5');
        svg.appendChild(line);
        const text = document.createElementNS('http://www.w3.org/2000/svg', 'text');
        text.setAttribute('x', String(labelX));
        text.setAttribute('y', String(labelY));
        text.setAttribute('fill', '#ffd93d');
        text.setAttribute('font-size', '13');
        text.setAttribute('font-weight', 'bold');
        text.setAttribute('stroke', '#333');
        text.setAttribute('stroke-width', '0.7');
        text.textContent = viewMode === 'total' ? 'Top Emitter' : 'Highest per Capita';
        svg.appendChild(text);
      }
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
          ? 'Click to Show total annual CO₂ emissions by county' 
          : 'Click to Show emissions per person - rural counties often higher!'}
      </p>
    </div>

    <!-- STORY CONTEXT & CHART TITLE -->
    <div class="graph-story-context">
      <h2>
        {viewMode === 'total'
          ? 'Commute Time vs. Total Emissions'
          : 'Commute Time vs. Per Capita Emissions'}
      </h2>
      <p>
        {viewMode === 'total'
          ? 'Each circle represents a county. The X-axis shows average commute time; the Y-axis shows total annual CO₂ emissions. Circle size represents number of workers. Higher and further right = more emissions and longer commutes.'
          : 'Each circle represents a county. The X-axis shows average commute time; the Y-axis shows per capita emissions. Circle size represents number of workers. Higher and further right = higher individual impact and longer commutes.'}
      </p>
    </div>

    <!-- BUBBLE LEGEND / KEY (above map) -->
    <div class="key-card">
      <div class="legend-row">
        <svg width="32" height="32"><circle cx="16" cy="16" r="15" fill="#ff6b6b" fill-opacity="0.6"/></svg>
        <span>{viewMode === 'total' ? 'Highest Total (tons)' : 'Highest per Capita (tons/person)'}</span>
        <strong>
          {viewMode === 'total'
            ? Math.round(Math.max(...countyData.map(c => c.co2_tons))/1000) + 'K'
            : Math.max(...countyData.map(c => c.co2_per_capita)).toFixed(2)}
        </strong>
      </div>
      <div class="legend-row">
        <svg width="20" height="20"><circle cx="10" cy="10" r="9" fill="#ff6b6b" fill-opacity="0.6"/></svg>
        <span>Median Value</span>
        <strong>
          {viewMode === 'total'
            ? Math.round(countyData.map(c=>c.co2_tons/1000).sort((a,b)=>a-b)[Math.floor(countyData.length/2)]) + 'K'
            : countyData.map(c=>c.co2_per_capita).sort((a,b)=>a-b)[Math.floor(countyData.length/2)].toFixed(2)}
        </strong>
      </div>
      <div class="legend-row">
        <svg width="12" height="12"><circle cx="6" cy="6" r="5" fill="#ff6b6b" fill-opacity="0.6"/></svg>
        <span>{viewMode === 'total' ? 'Lowest Total' : 'Lowest per Capita'}</span>
        <strong>
          {viewMode === 'total'
            ? Math.round(Math.min(...countyData.map(c => c.co2_tons))/1000) + 'K'
            : Math.min(...countyData.map(c => c.co2_per_capita)).toFixed(2)}
        </strong>
      </div>
    </div>

    <div class="map-container" bind:this={mapContainer}></div>

    {#if viewMode === 'total'}
      <div class="insight-box">
        <h3>🌆 Most emissions? Big cities by total, but ...</h3>
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
        <h3>🚘 Per-person: Rural counties, big outliers</h3>
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

    {#if selectedCounty}
      <div class="county-detail">
        <h3>{selectedCounty.county} County</h3>
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

    <div class="top-counties">
      <h2>Top {Math.min(5, countyData.length)} Emitting {countyData.length > 0 ? 'Counties' : 'Areas'}</h2>
      <div class="counties-list">
        {#each countyData.slice(0, Math.min(5, countyData.length)) as county, i}
          <div 
            class="county-row" 
            role="button"
            tabindex="0"
            on:click={() => selectedCounty = county}
            on:keydown={(e) => e.key === 'Enter' && (selectedCounty = county)}
          >
            <span class="rank">#{i + 1}</span>
            <span class="county-name">{county.county}</span>
            <span class="emissions">{(county.co2_tons / 1000).toFixed(0)}K tons</span>
            <div class="bar" style="width: {countyData[0] ? (county.co2_tons / countyData[0].co2_tons * 100) : 0}%"></div>
          </div>
        {/each}
      </div>
    </div>

  </div>
  {/if}
</div>

<style>
  .chapter-container {
    min-height: 100vh;
    background: linear-gradient(180deg, #0f3460 0%, #16213e 100%);
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

  .map-container {
    margin: 3rem 0;
    min-height: 600px;
  }

  .county-detail {
    margin: 3rem auto;
    padding: 2rem;
    max-width: 800px;
    background: rgba(78, 205, 196, 0.1);
    border-left: 4px solid #4ecdc4;
    border-radius: 12px;
  }

  .county-detail h3 {
    font-size: 2rem;
    margin-bottom: 1.5rem;
    color: #4ecdc4;
  }

  .detail-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 2rem;
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

  .top-counties {
    margin: 4rem 0;
  }

  .top-counties h2 {
    font-size: 2rem;
    margin-bottom: 2rem;
    text-align: center;
  }

  .counties-list {
    display: flex;
    flex-direction: column;
    gap: 1rem;
  }

  .county-row {
    padding: 1.5rem;
    background: rgba(255, 255, 255, 0.05);
    border-radius: 12px;
    display: grid;
    grid-template-columns: 60px 1fr 150px;
    align-items: center;
    position: relative;
    cursor: pointer;
    transition: all 0.3s;
  }

  .county-row:hover,
  .county-row:focus {
    background: rgba(255, 255, 255, 0.1);
    transform: translateX(10px);
    outline: 2px solid #4ecdc4;
    outline-offset: 2px;
  }

  .rank {
    font-size: 2rem;
    font-weight: 800;
    color: #ffd93d;
  }

  .county-name {
    font-size: 1.3rem;
    font-weight: 600;
  }

  .emissions {
    font-size: 1.3rem;
    font-weight: 700;
    color: #ff6b6b;
    text-align: right;
  }

  .bar {
    position: absolute;
    bottom: 0;
    left: 0;
    height: 4px;
    background: linear-gradient(90deg, #ff6b6b, #ffd93d);
    border-radius: 0 0 12px 12px;
    transition: width 0.5s ease;
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
  .graph-story-context p {
    font-size: 1.08rem;
    opacity: 0.85;
    margin: 0 auto;
  }
  .key-card {
    background: rgba(30,30,40,0.85);
    color: #fff;
    border-radius: 8px;
    padding: 1.3em 2em;
    margin: 1em auto 1.2em auto;
    max-width: 350px;
    font-size: 1em;
    box-shadow: 0 2px 20px rgba(0,0,0,0.08);
  }
  .key-card .legend-row {
    display: flex;
    align-items: center;
    margin-bottom: 0.3em;
    gap: 0.8em;
  }
  .key-card strong {
    margin-left: auto;
    color: #ffd700;
  }
  .key-card svg {
    vertical-align: middle;
    display: inline-block;
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

    .county-row {
      grid-template-columns: 50px 1fr;
      gap: 0.5rem;
    }

    .emissions {
      grid-column: 1 / -1;
      text-align: left;
      margin-top: 0.5rem;
    }
  }
</style>
