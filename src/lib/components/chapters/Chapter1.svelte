<script lang="ts">
  import { fade, fly } from 'svelte/transition';
  import { onMount } from 'svelte';

  // PA-specific data (loaded from processed JSON)
  let PA_STATS = {
    totalCommuters: 0,
    avgCommuteMinutes: 0,
    annualHoursLost: 0,
    annualCO2Tons: 0,
    carsEquivalent: 0,
    avgCO2PerPerson: 0
  };

  let userCommuteMinutes: number = 27;
  let animationStep: number = 0;
  let dataLoaded: boolean = false;

  // Load data from JSON files
  onMount(async () => {
    try {
      // Load summary stats
      const summaryResponse = await fetch('/pa_summary_stats.json');
      const summaryData = await summaryResponse.json();
      
      // Load scenarios to get CO2 emissions
      const scenariosResponse = await fetch('/pa_scenarios.json');
      const scenariosData = await scenariosResponse.json();
      
      // Calculate CO2 per person (tons per commuter per year)
      const totalCommuters = summaryData.total_commuters;
      const annualCO2Tons = scenariosData.current.emissions_tons;
      const avgCO2PerPerson = annualCO2Tons / totalCommuters;
      
      // Calculate cars equivalent (assuming average car emits ~4.6 tons CO2 per year)
      const carsEquivalent = Math.round(annualCO2Tons / 4.6);
      
      PA_STATS = {
        totalCommuters: summaryData.total_commuters,
        avgCommuteMinutes: summaryData.avg_commute_minutes,
        annualHoursLost: summaryData.annual_hours_lost,
        annualCO2Tons: annualCO2Tons,
        carsEquivalent: carsEquivalent,
        avgCO2PerPerson: avgCO2PerPerson
      };
      
      // Set default user commute to match PA average
      userCommuteMinutes = Math.round(PA_STATS.avgCommuteMinutes);
      dataLoaded = true;
      
      // Start animation sequence after data loads
      setTimeout(() => animationStep = 1, 500);
      setTimeout(() => animationStep = 2, 2000);
      setTimeout(() => animationStep = 3, 4000);
      setTimeout(() => animationStep = 4, 6000);
    } catch (error) {
      console.error('Error loading PA data:', error);
      // Fallback to default values if loading fails
      PA_STATS = {
        totalCommuters: 6_179_069,
        avgCommuteMinutes: 9.9,
        annualHoursLost: 509_773_192,
        annualCO2Tons: 2_166_258,
        carsEquivalent: 470_000,
        avgCO2PerPerson: 0.35
      };
      dataLoaded = true;
      
      // Start animation sequence even with fallback data
      setTimeout(() => animationStep = 1, 500);
      setTimeout(() => animationStep = 2, 2000);
      setTimeout(() => animationStep = 3, 4000);
      setTimeout(() => animationStep = 4, 6000);
    }
  });

  $: userAnnualHours = (userCommuteMinutes * 2 * 5 * 50) / 60;
  $: userAnnualCO2 = (userCommuteMinutes * 0.5 * 2 * 250 * 8.887 / 25) / 1000;
  $: comparisonToPAAvg = ((userAnnualCO2 / PA_STATS.avgCO2PerPerson - 1) * 100).toFixed(1);
</script>

<div class="chapter-container">
  <div class="hero-section">
    <h1 class="chapter-title">The Pennsylvania Commute</h1>
    <p class="subtitle">The Hidden Climate Cost of Getting to Work</p>
  </div>

  {#if !dataLoaded}
    <div class="loading-state">
      <p>Loading Pennsylvania commute data...</p>
    </div>
  {:else}
  <!-- Animation Sequence -->
  <div class="story-sequence">
    {#if animationStep >= 1}
      <div class="stat-reveal" in:fly={{ y: 50, duration: 800 }}>
        <div class="big-stat">
          <span class="number">{PA_STATS.totalCommuters.toLocaleString()}</span>
          <span class="label">Pennsylvanians commute to work every day</span>
        </div>
      </div>
    {/if}

    {#if animationStep >= 2}
      <div class="stat-reveal" in:fly={{ y: 50, duration: 800 }}>
        <div class="big-stat">
          <span class="number">{PA_STATS.avgCommuteMinutes}</span>
          <span class="unit">minutes</span>
          <span class="label">average commute time (each way)</span>
        </div>
        <p class="stat-context">
          That's <strong>{(PA_STATS.annualHoursLost / 1_000_000).toFixed(0)} million hours</strong> lost annually
        </p>
      </div>
    {/if}

    {#if animationStep >= 3}
      <div class="stat-reveal impact-highlight" in:fly={{ y: 50, duration: 800 }}>
        <p class="emphasis">But there's a bigger cost we don't see:</p>
        <div class="big-stat climate">
          <span class="number">{(PA_STATS.annualCO2Tons / 1_000_000).toFixed(1)}M</span>
          <span class="unit">tons</span>
          <span class="label">of CO₂ released into the atmosphere every year</span>
        </div>
        <p class="stat-context">
          That's equivalent to <strong>{PA_STATS.carsEquivalent.toLocaleString()} cars</strong> running year-round
        </p>
      </div>
    {/if}

    {#if animationStep >= 4}
      <div class="callout" in:fade={{ duration: 800 }}>
        <p class="callout-text">
          This is Pennsylvania's hidden climate burden
        </p>
      </div>
    {/if}
  </div>

  <!-- Personal Calculator -->
  <div class="calculator-section">
    <h2>What's Your Carbon Footprint?</h2>
    <p class="calculator-intro">
      Enter your one-way commute time to see your personal impact
    </p>

    <div class="input-group">
      <label for="commute-input">Your commute (minutes):</label>
      <input
        id="commute-input"
        type="range"
        bind:value={userCommuteMinutes}
        min="5"
        max="90"
        step="1"
      />
      <div class="input-display">{userCommuteMinutes} minutes</div>
    </div>

    <div class="results-grid">
      <div class="result-card">
        <div class="result-label">Your Annual Hours</div>
        <div class="result-value">{userAnnualHours.toFixed(0)}</div>
        <div class="result-unit">hours commuting</div>
      </div>

      <div class="result-card highlight">
        <div class="result-label">Your Annual CO₂</div>
        <div class="result-value">{userAnnualCO2.toFixed(2)}</div>
        <div class="result-unit">tons of carbon</div>
      </div>

      <div class="result-card">
        <div class="result-label">vs. PA Average</div>
        <div class="result-value" class:positive={parseFloat(comparisonToPAAvg) < 0} class:negative={parseFloat(comparisonToPAAvg) > 0}>
          {parseFloat(comparisonToPAAvg) > 0 ? '+' : ''}{comparisonToPAAvg}%
        </div>
        <div class="result-unit">
          {parseFloat(comparisonToPAAvg) > 0 ? 'above' : 'below'} PA average
        </div>
      </div>
    </div>

    <div class="insight-box">
      <p>
        💡 <strong>Quick comparison:</strong> Your {userAnnualCO2.toFixed(2)} tons of CO₂ is equivalent to:
      </p>
      <ul>
        <li>{(userAnnualCO2 * 1000 / 400).toFixed(1)} round-trip flights from NYC to LA</li>
        <li>{(userAnnualCO2 * 1000 / 8.89).toFixed(0)} gallons of gasoline burned</li>
        <li>{(userAnnualCO2 / 0.021).toFixed(0)} trees needed to offset it</li>
      </ul>
    </div>
  </div>

  <div class="transition-text">
    <p>But this burden isn't shared equally across Pennsylvania...</p>
    <div class="scroll-indicator">↓ Keep scrolling to see where emissions are highest</div>
  </div>
  {/if}
</div>

<style>
  .chapter-container {
    min-height: 100vh;
    background: linear-gradient(180deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
    color: white;
    padding: 4rem 2rem;
  }

  .hero-section {
    text-align: center;
    padding: 4rem 0;
    max-width: 900px;
    margin: 0 auto;
  }

  .chapter-title {
    font-size: 4rem;
    font-weight: 800;
    margin-bottom: 1rem;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
  }

  .subtitle {
    font-size: 1.8rem;
    opacity: 0.9;
    font-weight: 300;
  }

  .story-sequence {
    max-width: 1000px;
    margin: 6rem auto;
    padding: 0 2rem;
  }

  .stat-reveal {
    margin: 4rem 0;
    padding: 3rem;
    background: rgba(255, 255, 255, 0.05);
    border-radius: 15px;
    backdrop-filter: blur(10px);
  }

  .big-stat {
    text-align: center;
    margin: 2rem 0;
  }

  .big-stat .number {
    display: block;
    font-size: 6rem;
    font-weight: 800;
    color: #4ecdc4;
    line-height: 1;
  }

  .big-stat .unit {
    font-size: 2.5rem;
    color: #4ecdc4;
    margin-left: 0.5rem;
  }

  .big-stat .label {
    display: block;
    font-size: 1.5rem;
    margin-top: 1rem;
    opacity: 0.9;
  }

  .big-stat.climate .number {
    color: #ff6b6b;
  }

  .big-stat.climate .unit {
    color: #ff6b6b;
  }

  .stat-context {
    text-align: center;
    font-size: 1.3rem;
    margin-top: 1.5rem;
    opacity: 0.85;
  }

  .stat-context strong {
    color: #ffd93d;
  }

  .impact-highlight {
    background: rgba(255, 107, 107, 0.1);
    border-left: 4px solid #ff6b6b;
  }

  .emphasis {
    font-size: 1.5rem;
    text-align: center;
    margin-bottom: 2rem;
    font-weight: 600;
  }

  .callout {
    margin: 4rem auto;
    padding: 2rem;
    background: rgba(255, 215, 0, 0.1);
    border: 2px solid #ffd700;
    border-radius: 12px;
    text-align: center;
  }

  .callout-text {
    font-size: 2rem;
    font-weight: 600;
    margin: 0;
  }

  .calculator-section {
    max-width: 1000px;
    margin: 6rem auto;
    padding: 3rem;
    background: rgba(255, 255, 255, 0.08);
    border-radius: 20px;
  }

  .calculator-section h2 {
    text-align: center;
    font-size: 2.5rem;
    margin-bottom: 1rem;
  }

  .calculator-intro {
    text-align: center;
    font-size: 1.2rem;
    opacity: 0.9;
    margin-bottom: 3rem;
  }

  .input-group {
    margin: 3rem 0;
  }

  .input-group label {
    display: block;
    font-size: 1.2rem;
    margin-bottom: 1rem;
    font-weight: 600;
  }

  input[type="range"] {
    width: 100%;
    height: 8px;
    background: rgba(255, 255, 255, 0.2);
    border-radius: 5px;
    outline: none;
  }

  input[type="range"]::-webkit-slider-thumb {
    appearance: none;
    width: 24px;
    height: 24px;
    background: #4ecdc4;
    border-radius: 50%;
    cursor: pointer;
  }

  .input-display {
    text-align: center;
    font-size: 3rem;
    font-weight: 800;
    color: #4ecdc4;
    margin-top: 1rem;
  }

  .results-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
    gap: 2rem;
    margin: 3rem 0;
  }

  .result-card {
    padding: 2rem;
    background: rgba(255, 255, 255, 0.05);
    border-radius: 12px;
    text-align: center;
    transition: transform 0.3s;
  }

  .result-card:hover {
    transform: translateY(-5px);
  }

  .result-card.highlight {
    background: rgba(255, 107, 107, 0.15);
    border: 2px solid #ff6b6b;
  }

  .result-label {
    font-size: 1rem;
    text-transform: uppercase;
    letter-spacing: 1px;
    opacity: 0.7;
    margin-bottom: 1rem;
  }

  .result-value {
    font-size: 3rem;
    font-weight: 800;
    color: #4ecdc4;
  }

  .result-value.positive {
    color: #51cf66;
  }

  .result-value.negative {
    color: #ff6b6b;
  }

  .result-unit {
    font-size: 1rem;
    opacity: 0.8;
    margin-top: 0.5rem;
  }

  .insight-box {
    margin-top: 3rem;
    padding: 2rem;
    background: rgba(78, 205, 196, 0.1);
    border-left: 4px solid #4ecdc4;
    border-radius: 8px;
  }

  .insight-box p {
    margin: 0 0 1rem 0;
    font-size: 1.1rem;
  }

  .insight-box ul {
    list-style: none;
    padding: 0;
    margin: 0;
  }

  .insight-box li {
    padding: 0.5rem 0;
    font-size: 1.1rem;
  }

  .transition-text {
    text-align: center;
    margin: 6rem 0 3rem;
    font-size: 1.5rem;
    opacity: 0.9;
  }

  .scroll-indicator {
    margin-top: 2rem;
    font-size: 1.2rem;
    animation: bounce 2s infinite;
    opacity: 0.6;
  }

  .loading-state {
    text-align: center;
    padding: 4rem 2rem;
    font-size: 1.5rem;
    opacity: 0.8;
  }

  @keyframes bounce {
    0%, 100% { transform: translateY(0); }
    50% { transform: translateY(10px); }
  }

  @media (max-width: 768px) {
    .chapter-title {
      font-size: 2.5rem;
    }

    .subtitle {
      font-size: 1.2rem;
    }

    .big-stat .number {
      font-size: 3.5rem;
    }

    .results-grid {
      grid-template-columns: 1fr;
    }

    .calculator-section {
      padding: 2rem 1rem;
    }
  }
</style>