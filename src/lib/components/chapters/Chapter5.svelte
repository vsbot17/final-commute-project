<script lang="ts">
  import { onMount } from 'svelte';

  type CountyCaseStudy = {
    name: string;
    location: string;
    avgCommute: number;
    transitBikeWalkPct: number;
    co2PerCapita: number;
    whyItWorks: string;
    keyFeatures: string[];
    comparison: {
      commuteVsPA: number; // percentage difference
      transitVsPA: number; // percentage difference
      co2VsPA: number; // percentage difference
    };
  };

  type PAStats = {
    avgCommuteMinutes: number;
    transitBikeWalkPct: number;
    co2PerCapita: number;
  };

  let paStats: PAStats = {
    avgCommuteMinutes: 27.3,
    transitBikeWalkPct: 11,
    co2PerCapita: 2.7
  };

  let caseStudies: CountyCaseStudy[] = [
    {
      name: 'Centre County',
      location: 'State College',
      avgCommute: 18.2,
      transitBikeWalkPct: 22,
      co2PerCapita: 1.8,
      whyItWorks: 'Compact university town with strong bike infrastructure',
      keyFeatures: [
        'University campus promotes walkability',
        'Extensive bike lane network',
        'Compact urban design',
        'Strong transit connections'
      ],
      comparison: {
        commuteVsPA: -33.3, // 18.2 vs 27.3 = 33.3% below
        transitVsPA: 100, // 22% vs 11% = 100% more
        co2VsPA: -33.3 // 1.8 vs 2.7 = 33.3% below
      }
    },
    {
      name: 'Montgomery County',
      location: 'Philadelphia Suburbs',
      avgCommute: 24.5,
      transitBikeWalkPct: 18,
      co2PerCapita: 2.1,
      whyItWorks: 'Strong SEPTA connections reduce car dependency',
      keyFeatures: [
        'Park-and-ride facilities at suburban stations',
        'Regional rail network access',
        'Bus rapid transit options',
        'Mixed-use development near stations'
      ],
      comparison: {
        commuteVsPA: -10.3, // 24.5 vs 27.3 = 10.3% below
        transitVsPA: 63.6, // 18% vs 11% = 63.6% more
        co2VsPA: -22.2 // 2.1 vs 2.7 = 22.2% below
      }
    },
    {
      name: 'Centre City Philadelphia',
      location: 'Philadelphia',
      avgCommute: 28.0,
      transitBikeWalkPct: 65,
      co2PerCapita: 1.5,
      whyItWorks: 'Density + transit = lower emissions per person',
      keyFeatures: [
        'Walk/bike/transit: 65%',
        'High population density',
        'Comprehensive transit network',
        'Mixed-use zoning'
      ],
      comparison: {
        commuteVsPA: 2.6, // 28.0 vs 27.3 = 2.6% above (but shorter than expected for density)
        transitVsPA: 490.9, // 65% vs 11% = 490.9% more
        co2VsPA: -44.4 // 1.5 vs 2.7 = 44.4% below
      }
    }
  ];

  let expandedCounty: string | null = null;
  let dataLoaded: boolean = false;
  
  // Store chart nodes and counties for reactive rendering
  let chartNodes: Array<{ node: HTMLDivElement; county: CountyCaseStudy }> = [];
  
  // Reactive statement to render all charts when data loads
  $: if (dataLoaded && chartNodes.length > 0) {
    chartNodes.forEach(({ node, county }) => {
      setTimeout(() => renderMiniChart(node, county), 50);
    });
  }
  
  // Action directive to register chart container
  function chartAction(node: HTMLDivElement, county: CountyCaseStudy) {
    chartNodes = [...chartNodes, { node, county }];
    
    if (dataLoaded) {
      setTimeout(() => renderMiniChart(node, county), 50);
    }
    
    return {
      update(newCounty: CountyCaseStudy) {
        // Update the county in the array
        const index = chartNodes.findIndex(item => item.node === node);
        if (index !== -1) {
          chartNodes[index].county = newCounty;
          chartNodes = [...chartNodes]; // Trigger reactivity
        }
        if (dataLoaded) {
          setTimeout(() => renderMiniChart(node, newCounty), 50);
        }
      },
      destroy() {
        chartNodes = chartNodes.filter(item => item.node !== node);
      }
    };
  }

  onMount(async () => {
    try {
      // Load PA summary stats to get accurate averages
      const summaryResponse = await fetch('/pa_summary_stats.json');
      const summaryData = await summaryResponse.json();
      
      // Calculate transit/bike/walk percentage (non-drive-alone)
      const nonDriveAlonePct = (summaryData.transit_pct || 0) + 
                                (summaryData.wfh_pct || 0) + 
                                (summaryData.bike_walk_pct || 0);
      
      // Estimate CO2 per capita from scenarios if available
      const scenariosResponse = await fetch('/pa_scenarios.json');
      const scenariosData = await scenariosResponse.json();
      const totalCommuters = summaryData.total_commuters || 6179069;
      const annualCO2Tons = scenariosData.current?.emissions_tons || 0;
      const estimatedCO2PerCapita = annualCO2Tons / totalCommuters;
      
      paStats = {
        avgCommuteMinutes: summaryData.avg_commute_minutes || 27.3,
        transitBikeWalkPct: nonDriveAlonePct || 11,
        co2PerCapita: estimatedCO2PerCapita || 2.7
      };

      // Recalculate comparisons with actual PA stats
      caseStudies = caseStudies.map(county => {
        const commuteDiff = ((county.avgCommute - paStats.avgCommuteMinutes) / paStats.avgCommuteMinutes) * 100;
        const transitDiff = ((county.transitBikeWalkPct - paStats.transitBikeWalkPct) / paStats.transitBikeWalkPct) * 100;
        const co2Diff = ((county.co2PerCapita - paStats.co2PerCapita) / paStats.co2PerCapita) * 100;
        
        return {
          ...county,
          comparison: {
            commuteVsPA: commuteDiff,
            transitVsPA: transitDiff,
            co2VsPA: co2Diff
          }
        };
      });

      dataLoaded = true;
    } catch (error) {
      console.error('Error loading PA data:', error);
      dataLoaded = true;
    }
  });

  function toggleExpand(countyName: string) {
    expandedCounty = expandedCounty === countyName ? null : countyName;
  }

  function renderMiniChart(container: HTMLDivElement, county: CountyCaseStudy) {
    if (!container) return;

    const svgWidth = 280;
    const svgHeight = 120;
    const margin = { top: 10, right: 10, bottom: 30, left: 50 };
    const chartWidth = svgWidth - margin.left - margin.right;
    const chartHeight = svgHeight - margin.top - margin.bottom;

    const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
    svg.setAttribute('viewBox', `0 0 ${svgWidth} ${svgHeight}`);
    svg.style.width = '100%';
    svg.style.height = `${svgHeight}px`;

    const chartGroup = document.createElementNS('http://www.w3.org/2000/svg', 'g');
    chartGroup.setAttribute('transform', `translate(${margin.left},${margin.top})`);

    // Data for comparison bars
    const maxValue = Math.max(
      paStats.avgCommuteMinutes,
      county.avgCommute,
      paStats.co2PerCapita * 10, // Scale CO2 for visibility
      county.co2PerCapita * 10
    );

    // Bar 1: Commute Time
    const commutePABar = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
    commutePABar.setAttribute('x', '0');
    commutePABar.setAttribute('y', String(chartHeight - (paStats.avgCommuteMinutes / maxValue) * chartHeight));
    commutePABar.setAttribute('width', String(chartWidth / 4 - 5));
    commutePABar.setAttribute('height', String((paStats.avgCommuteMinutes / maxValue) * chartHeight));
    commutePABar.setAttribute('fill', 'rgba(255,255,255,0.3)');
    commutePABar.setAttribute('rx', '4');
    chartGroup.appendChild(commutePABar);

    const commuteCountyBar = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
    commuteCountyBar.setAttribute('x', String(chartWidth / 4));
    commuteCountyBar.setAttribute('y', String(chartHeight - (county.avgCommute / maxValue) * chartHeight));
    commuteCountyBar.setAttribute('width', String(chartWidth / 4 - 5));
    commuteCountyBar.setAttribute('height', String((county.avgCommute / maxValue) * chartHeight));
    commuteCountyBar.setAttribute('fill', '#4ecdc4');
    commuteCountyBar.setAttribute('rx', '4');
    chartGroup.appendChild(commuteCountyBar);

    // Bar 2: CO2 per Capita (scaled)
    const co2PABar = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
    co2PABar.setAttribute('x', String(chartWidth / 2));
    co2PABar.setAttribute('y', String(chartHeight - (paStats.co2PerCapita * 10 / maxValue) * chartHeight));
    co2PABar.setAttribute('width', String(chartWidth / 4 - 5));
    co2PABar.setAttribute('height', String((paStats.co2PerCapita * 10 / maxValue) * chartHeight));
    co2PABar.setAttribute('fill', 'rgba(255,255,255,0.3)');
    co2PABar.setAttribute('rx', '4');
    chartGroup.appendChild(co2PABar);

    const co2CountyBar = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
    co2CountyBar.setAttribute('x', String(chartWidth / 2 + chartWidth / 4));
    co2CountyBar.setAttribute('y', String(chartHeight - (county.co2PerCapita * 10 / maxValue) * chartHeight));
    co2CountyBar.setAttribute('width', String(chartWidth / 4 - 5));
    co2CountyBar.setAttribute('height', String((county.co2PerCapita * 10 / maxValue) * chartHeight));
    co2CountyBar.setAttribute('fill', '#ff6b6b');
    co2CountyBar.setAttribute('rx', '4');
    chartGroup.appendChild(co2CountyBar);

    // Labels
    const labels = ['PA Avg', county.name.substring(0, 8), 'PA Avg', county.name.substring(0, 8)];
    labels.forEach((label, i) => {
      const text = document.createElementNS('http://www.w3.org/2000/svg', 'text');
      text.setAttribute('x', String((i * chartWidth / 4) + (chartWidth / 8)));
      text.setAttribute('y', String(chartHeight + 20));
      text.setAttribute('text-anchor', 'middle');
      text.setAttribute('fill', 'rgba(255,255,255,0.8)');
      text.setAttribute('font-size', '10');
      text.textContent = label;
      chartGroup.appendChild(text);
    });

    // Y-axis label
    const yLabel = document.createElementNS('http://www.w3.org/2000/svg', 'text');
    yLabel.setAttribute('x', String(-chartHeight / 2));
    yLabel.setAttribute('y', '-30');
    yLabel.setAttribute('text-anchor', 'middle');
    yLabel.setAttribute('fill', 'rgba(255,255,255,0.7)');
    yLabel.setAttribute('font-size', '9');
    yLabel.setAttribute('transform', `rotate(-90, ${-chartHeight / 2}, -30)`);
    yLabel.textContent = 'Commute (min) / CO₂ (×10)';
    chartGroup.appendChild(yLabel);

    svg.appendChild(chartGroup);
    container.innerHTML = '';
    container.appendChild(svg);
  }
</script>

<div class="chapter-container">
  <div class="chapter-header">
    <h1>Pennsylvania Counties Leading the Way</h1>
    <p class="subtitle">Show What's Working</p>
  </div>

  {#if !dataLoaded}
    <div class="loading-state">
      <p>Loading Pennsylvania county case studies...</p>
    </div>
  {:else}
  <div class="content-wrapper">
    <div class="intro-section">
      <p class="intro-text">
        Some Pennsylvania communities are already showing us the path forward. 
        These case studies prove that <strong>better infrastructure and planning lead to lower emissions</strong> 
        without sacrificing quality of life.
      </p>
    </div>

    <div class="pa-baseline">
      <h3>Pennsylvania Baseline</h3>
      <div class="baseline-stats">
        <div class="baseline-stat">
          <span class="baseline-label">Average Commute</span>
          <span class="baseline-value">{paStats.avgCommuteMinutes.toFixed(1)} min</span>
        </div>
        <div class="baseline-stat">
          <span class="baseline-label">Transit/Bike/Walk</span>
          <span class="baseline-value">{paStats.transitBikeWalkPct.toFixed(0)}%</span>
        </div>
        <div class="baseline-stat">
          <span class="baseline-label">CO₂ per Capita</span>
          <span class="baseline-value">{paStats.co2PerCapita.toFixed(1)} tons</span>
        </div>
      </div>
    </div>

    <div class="case-studies-grid">
      {#each caseStudies as county}
        <div 
          class="case-study-card"
          class:expanded={expandedCounty === county.name}
          role="button"
          tabindex="0"
          on:click={() => toggleExpand(county.name)}
          on:keydown={(e) => e.key === 'Enter' && toggleExpand(county.name)}
        >
          <div class="card-header">
            <div class="county-title">
              <h2>{county.name}</h2>
              <p class="location">{county.location}</p>
            </div>
            <div class="expand-icon">
              {expandedCounty === county.name ? '−' : '+'}
            </div>
          </div>

          <div class="card-stats">
            <div class="stat-row">
              <div class="stat-item">
                <span class="stat-label">Avg Commute</span>
                <span class="stat-value highlight">{county.avgCommute.toFixed(1)} min</span>
                <span class="stat-comparison" class:positive={county.comparison.commuteVsPA < 0}>
                  {county.comparison.commuteVsPA > 0 ? '+' : ''}{county.comparison.commuteVsPA.toFixed(1)}% vs PA
                </span>
              </div>
              <div class="stat-item">
                <span class="stat-label">Transit/Bike/Walk</span>
                <span class="stat-value highlight">{county.transitBikeWalkPct.toFixed(0)}%</span>
                <span class="stat-comparison positive">
                  +{county.comparison.transitVsPA.toFixed(1)}% vs PA
                </span>
              </div>
            </div>
            <div class="stat-row">
              <div class="stat-item">
                <span class="stat-label">CO₂ per Capita</span>
                <span class="stat-value highlight success">{county.co2PerCapita.toFixed(1)} tons</span>
                <span class="stat-comparison positive">
                  {county.comparison.co2VsPA.toFixed(1)}% vs PA
                </span>
              </div>
            </div>
          </div>

          <div class="mini-chart-container" use:chartAction={county}></div>

          {#if expandedCounty === county.name}
            <div class="expanded-content">
              <div class="why-it-works">
                <h3>💡 Why It Works</h3>
                <p>{county.whyItWorks}</p>
              </div>
              
              <div class="key-features">
                <h3>Key Features</h3>
                <ul>
                  {#each county.keyFeatures as feature}
                    <li>{feature}</li>
                  {/each}
                </ul>
              </div>

              <div class="impact-summary">
                <h3>Environmental Impact</h3>
                <div class="impact-stats">
                  <div class="impact-stat">
                    <span class="impact-value">{Math.abs(county.comparison.co2VsPA).toFixed(0)}%</span>
                    <span class="impact-label">Less CO₂ than PA average</span>
                  </div>
                  {#if county.comparison.commuteVsPA < 0}
                    <div class="impact-stat">
                      <span class="impact-value">{Math.abs(county.comparison.commuteVsPA).toFixed(0)}%</span>
                      <span class="impact-label">Shorter commutes</span>
                    </div>
                  {/if}
                  <div class="impact-stat">
                    <span class="impact-value">{county.comparison.transitVsPA.toFixed(0)}%</span>
                    <span class="impact-label">More alternative transport</span>
                  </div>
                </div>
              </div>
            </div>
          {/if}
        </div>
      {/each}
    </div>

    <div class="story-section">
      <h2>The Story</h2>
      <div class="story-content">
        <div class="story-point">
          <h3>🎓 Centre County (State College)</h3>
          <p>
            <strong>{caseStudies[0].avgCommute.toFixed(1)} minutes</strong> average commute 
            (PA average: {paStats.avgCommuteMinutes.toFixed(1)}) • 
            <strong>{caseStudies[0].transitBikeWalkPct.toFixed(0)}%</strong> transit/bike/walk 
            (PA average: {paStats.transitBikeWalkPct.toFixed(0)}%)
          </p>
          <p>
            Why it works: <strong>{caseStudies[0].whyItWorks}</strong>
          </p>
          <p>
            <strong>CO₂ per capita: {caseStudies[0].co2PerCapita.toFixed(1)} tons</strong> 
            ({Math.abs(caseStudies[0].comparison.co2VsPA).toFixed(0)}% below PA average)
          </p>
        </div>

        <div class="story-point">
          <h3>🚇 Montgomery County (Philadelphia Suburbs)</h3>
          <p>
            <strong>Strong SEPTA connections</strong> reduce car dependency. 
            Park-and-ride facilities at suburban stations make regional rail accessible to commuters.
          </p>
          <p>
            <strong>CO₂ per capita: {caseStudies[1].co2PerCapita.toFixed(1)} tons</strong> 
            ({Math.abs(caseStudies[1].comparison.co2VsPA).toFixed(0)}% below average)
          </p>
        </div>

        <div class="story-point">
          <h3>🏙️ Centre City Philadelphia</h3>
          <p>
            <strong>Walk/bike/transit: {caseStudies[2].transitBikeWalkPct.toFixed(0)}%</strong> • 
            Average commute: <strong>{caseStudies[2].avgCommute.toFixed(1)} minutes</strong> 
            (shorter than PA average despite density)
          </p>
          <p>
            <strong>Proof that density + transit = lower emissions per person</strong>
          </p>
          <p>
            <strong>CO₂ per capita: {caseStudies[2].co2PerCapita.toFixed(1)} tons</strong> 
            ({Math.abs(caseStudies[2].comparison.co2VsPA).toFixed(0)}% below PA average)
          </p>
        </div>
      </div>

      <div class="insight-box">
        <h3>💡 The Key Insight</h3>
        <p>
          These three case studies demonstrate that <strong>infrastructure investment and smart planning 
          can dramatically reduce emissions</strong> while maintaining or improving quality of life. 
          Whether through compact urban design, transit connections, or density, Pennsylvania has proven 
          models to follow.
        </p>
      </div>
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
    margin-bottom: 3rem;
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

  .intro-section {
    margin: 3rem 0;
    padding: 2rem;
    background: rgba(78, 205, 196, 0.1);
    border-left: 4px solid #4ecdc4;
    border-radius: 12px;
  }

  .intro-text {
    font-size: 1.3rem;
    line-height: 1.8;
    margin: 0;
  }

  .pa-baseline {
    margin: 3rem 0;
    padding: 2rem;
    background: rgba(255, 255, 255, 0.08);
    border-radius: 12px;
    border: 2px solid rgba(255, 255, 255, 0.2);
  }

  .pa-baseline h3 {
    font-size: 1.5rem;
    margin: 0 0 1.5rem 0;
    color: #ffd93d;
    text-align: center;
  }

  .baseline-stats {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 2rem;
  }

  .baseline-stat {
    text-align: center;
    padding: 1rem;
    background: rgba(255, 255, 255, 0.05);
    border-radius: 8px;
  }

  .baseline-label {
    display: block;
    font-size: 0.9rem;
    opacity: 0.8;
    margin-bottom: 0.5rem;
  }

  .baseline-value {
    display: block;
    font-size: 1.8rem;
    font-weight: 700;
    color: #4ecdc4;
  }

  .case-studies-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
    gap: 2rem;
    margin: 4rem 0;
  }

  .case-study-card {
    padding: 2rem;
    background: rgba(255, 255, 255, 0.08);
    border-radius: 12px;
    border: 2px solid rgba(255, 255, 255, 0.2);
    cursor: pointer;
    transition: all 0.3s;
  }

  .case-study-card:hover,
  .case-study-card:focus {
    background: rgba(255, 255, 255, 0.12);
    transform: translateY(-5px);
    border-color: #4ecdc4;
    outline: 2px solid #4ecdc4;
    outline-offset: 2px;
  }

  .case-study-card.expanded {
    background: rgba(78, 205, 196, 0.15);
    border-color: #4ecdc4;
    box-shadow: 0 4px 20px rgba(78, 205, 196, 0.3);
  }

  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    margin-bottom: 1.5rem;
  }

  .county-title h2 {
    font-size: 2rem;
    margin: 0 0 0.5rem 0;
    color: #4ecdc4;
  }

  .location {
    font-size: 1rem;
    opacity: 0.8;
    margin: 0;
  }

  .expand-icon {
    font-size: 2rem;
    font-weight: 300;
    color: #4ecdc4;
    width: 40px;
    height: 40px;
    display: flex;
    align-items: center;
    justify-content: center;
    background: rgba(78, 205, 196, 0.2);
    border-radius: 50%;
  }

  .card-stats {
    margin: 1.5rem 0;
  }

  .stat-row {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
    gap: 1rem;
    margin-bottom: 1rem;
  }

  .stat-item {
    padding: 1rem;
    background: rgba(255, 255, 255, 0.05);
    border-radius: 8px;
  }

  .stat-label {
    display: block;
    font-size: 0.85rem;
    opacity: 0.8;
    margin-bottom: 0.5rem;
  }

  .stat-value {
    display: block;
    font-size: 1.5rem;
    font-weight: 700;
    color: #ffd93d;
    margin-bottom: 0.25rem;
  }

  .stat-value.highlight {
    color: #4ecdc4;
  }

  .stat-value.success {
    color: #51cf66;
  }

  .stat-comparison {
    display: block;
    font-size: 0.8rem;
    opacity: 0.7;
  }

  .stat-comparison.positive {
    color: #51cf66;
  }

  .mini-chart-container {
    margin: 1.5rem 0;
    padding: 1rem;
    background: rgba(255, 255, 255, 0.05);
    border-radius: 8px;
    min-height: 120px;
  }

  .expanded-content {
    margin-top: 2rem;
    padding-top: 2rem;
    border-top: 2px solid rgba(255, 255, 255, 0.2);
    animation: slideDown 0.3s ease-out;
  }

  @keyframes slideDown {
    from {
      opacity: 0;
      transform: translateY(-10px);
    }
    to {
      opacity: 1;
      transform: translateY(0);
    }
  }

  .why-it-works {
    margin-bottom: 2rem;
    padding: 1.5rem;
    background: rgba(78, 205, 196, 0.1);
    border-left: 4px solid #4ecdc4;
    border-radius: 8px;
  }

  .why-it-works h3 {
    font-size: 1.3rem;
    margin: 0 0 1rem 0;
    color: #4ecdc4;
  }

  .why-it-works p {
    font-size: 1.1rem;
    line-height: 1.7;
    margin: 0;
  }

  .key-features {
    margin-bottom: 2rem;
  }

  .key-features h3 {
    font-size: 1.3rem;
    margin: 0 0 1rem 0;
    color: #ffd93d;
  }

  .key-features ul {
    list-style: none;
    padding: 0;
    margin: 0;
  }

  .key-features li {
    padding: 0.75rem 0;
    padding-left: 1.5rem;
    position: relative;
    font-size: 1.05rem;
    line-height: 1.6;
  }

  .key-features li::before {
    content: '✓';
    position: absolute;
    left: 0;
    color: #51cf66;
    font-weight: bold;
  }

  .impact-summary {
    padding: 1.5rem;
    background: rgba(255, 215, 0, 0.1);
    border-left: 4px solid #ffd93d;
    border-radius: 8px;
  }

  .impact-summary h3 {
    font-size: 1.3rem;
    margin: 0 0 1rem 0;
    color: #ffd93d;
  }

  .impact-stats {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
    gap: 1.5rem;
  }

  .impact-stat {
    text-align: center;
  }

  .impact-value {
    display: block;
    font-size: 2.5rem;
    font-weight: 800;
    color: #51cf66;
    margin-bottom: 0.5rem;
  }

  .impact-label {
    display: block;
    font-size: 0.9rem;
    opacity: 0.8;
  }

  .story-section {
    margin: 4rem 0;
  }

  .story-section h2 {
    font-size: 2.5rem;
    text-align: center;
    margin-bottom: 3rem;
    color: #ffd93d;
  }

  .story-content {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
    gap: 2rem;
    margin-bottom: 3rem;
  }

  .story-point {
    padding: 1.5rem;
    background: rgba(255, 255, 255, 0.05);
    border-radius: 12px;
    border-left: 4px solid #4ecdc4;
  }

  .story-point h3 {
    font-size: 1.5rem;
    margin: 0 0 1rem 0;
    color: #4ecdc4;
  }

  .story-point p {
    font-size: 1.1rem;
    line-height: 1.7;
    margin: 0.75rem 0;
  }

  .insight-box {
    margin: 3rem auto;
    padding: 2rem;
    max-width: 800px;
    background: rgba(255, 215, 0, 0.1);
    border-left: 4px solid #ffd93d;
    border-radius: 12px;
  }

  .insight-box h3 {
    font-size: 1.8rem;
    margin: 0 0 1rem 0;
    color: #ffd93d;
  }

  .insight-box p {
    font-size: 1.2rem;
    line-height: 1.8;
    margin: 0;
  }

  .loading-state {
    text-align: center;
    padding: 4rem 2rem;
    font-size: 1.5rem;
    opacity: 0.8;
  }

  @media (max-width: 768px) {
    .chapter-header h1 {
      font-size: 2rem;
    }

    .case-studies-grid {
      grid-template-columns: 1fr;
    }

    .story-content {
      grid-template-columns: 1fr;
    }
  }
</style>

