<script lang="ts">
  import { onMount, tick, onDestroy } from 'svelte';
  import { base } from '$app/paths';

  type MetroData = {
    metro: string;
    avg_commute: number;
    workers: number;
    co2_per_capita: number;
    transit_pct: number;
    median_income: number;
    commute_burden_score: number;
  };

  let metroData: MetroData[] = [];
  let dataLoaded = false;
  let selectedMetro: MetroData | null = null;
  let chartContainer: HTMLDivElement;

  // Keep a reference so we can remove old SVG safely (prevents HMR glitches)
  let currentSvg: SVGSVGElement | null = null;

  onMount(async () => {
    try {
      // IMPORTANT: use base so it works in /FinalViz on GitHub Pages
      const metroResponse = await fetch(`${base}/pa_metro_comparison.json`);
      const json = await metroResponse.json();

      metroData = (json || []) as MetroData[];

      // pick a default metro so the narrative never shows "undefined"
      if (metroData.length) selectedMetro = metroData[0];

      dataLoaded = true;

      // wait for DOM binding so chartContainer exists
      await tick();
      renderChart();
    } catch (error) {
      console.error('Error loading metro data:', error);
      dataLoaded = true;
    }
  });

  onDestroy(() => {
    if (currentSvg && currentSvg.parentNode) currentSvg.parentNode.removeChild(currentSvg);
    currentSvg = null;
  });

  function selectMetro(metro: MetroData) {
    selectedMetro = selectedMetro?.metro === metro.metro ? null : metro;
    renderChart();
  }

  function safe(n: any, digits = 1) {
    if (typeof n !== 'number' || !Number.isFinite(n)) return '—';
    return n.toFixed(digits);
  }

  function renderChart() {
    if (!chartContainer || metroData.length === 0) return;

    // clear old chart
    chartContainer.innerHTML = '';
    currentSvg = null;

    const svgWidth = 920;
    const svgHeight = 520;
    const margin = { top: 90, right: 40, bottom: 110, left: 80 };
    const chartWidth = svgWidth - margin.left - margin.right;
    const chartHeight = svgHeight - margin.top - margin.bottom;

    const groupWidth = chartWidth / metroData.length;
    const barWidth = groupWidth * 0.28;
    const gap = groupWidth * 0.10;

    const maxCommute = Math.max(...metroData.map((m) => m.avg_commute || 0), 1);
    const maxCO2 = Math.max(...metroData.map((m) => m.co2_per_capita || 0), 1);

    // svg
    const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
    svg.setAttribute('viewBox', `0 0 ${svgWidth} ${svgHeight}`);
    svg.style.width = '100%';
    svg.style.height = `${svgHeight}px`;
    svg.style.background = 'rgba(255,255,255,0.05)';
    svg.style.borderRadius = '14px';

    const g = document.createElementNS('http://www.w3.org/2000/svg', 'g');
    g.setAttribute('transform', `translate(${margin.left},${margin.top})`);

    // axes
    const xAxis = document.createElementNS('http://www.w3.org/2000/svg', 'line');
    xAxis.setAttribute('x1', '0');
    xAxis.setAttribute('y1', String(chartHeight));
    xAxis.setAttribute('x2', String(chartWidth));
    xAxis.setAttribute('y2', String(chartHeight));
    xAxis.setAttribute('stroke', 'rgba(255,255,255,0.35)');
    xAxis.setAttribute('stroke-width', '2');
    g.appendChild(xAxis);

    const yAxis = document.createElementNS('http://www.w3.org/2000/svg', 'line');
    yAxis.setAttribute('x1', '0');
    yAxis.setAttribute('y1', '0');
    yAxis.setAttribute('x2', '0');
    yAxis.setAttribute('y2', String(chartHeight));
    yAxis.setAttribute('stroke', 'rgba(255,255,255,0.35)');
    yAxis.setAttribute('stroke-width', '2');
    g.appendChild(yAxis);

    // ticks (commute minutes)
    const tickCount = 5;
    for (let i = 0; i <= tickCount; i++) {
      const v = (maxCommute / tickCount) * i;
      const y = chartHeight - (v / maxCommute) * chartHeight;

      const t = document.createElementNS('http://www.w3.org/2000/svg', 'line');
      t.setAttribute('x1', '-6');
      t.setAttribute('y1', String(y));
      t.setAttribute('x2', '0');
      t.setAttribute('y2', String(y));
      t.setAttribute('stroke', 'rgba(255,255,255,0.25)');
      g.appendChild(t);

      const label = document.createElementNS('http://www.w3.org/2000/svg', 'text');
      label.setAttribute('x', '-12');
      label.setAttribute('y', String(y + 4));
      label.setAttribute('text-anchor', 'end');
      label.setAttribute('fill', 'rgba(255,255,255,0.75)');
      label.setAttribute('font-size', '12');
      label.textContent = v.toFixed(0);
      g.appendChild(label);

      const grid = document.createElementNS('http://www.w3.org/2000/svg', 'line');
      grid.setAttribute('x1', '0');
      grid.setAttribute('y1', String(y));
      grid.setAttribute('x2', String(chartWidth));
      grid.setAttribute('y2', String(y));
      grid.setAttribute('stroke', 'rgba(255,255,255,0.05)');
      g.appendChild(grid);
    }

    // title
    const title = document.createElementNS('http://www.w3.org/2000/svg', 'text');
    title.setAttribute('x', String(chartWidth / 2));
    title.setAttribute('y', '-55');
    title.setAttribute('text-anchor', 'middle');
    title.setAttribute('fill', 'rgba(255,255,255,0.92)');
    title.setAttribute('font-size', '16');
    title.setAttribute('font-weight', '650');
    title.textContent = 'Commute time vs CO₂ per person (click a metro to highlight)';
    g.appendChild(title);

    // legend
   // legend (top-right)
const legendItems = [
  { color: '#4ecdc4', label: 'Commute (minutes)' },
  { color: '#ff6b6b', label: 'CO₂ per person (tons)' }
];

const legendX = chartWidth - 36;
const legendY = -62;

legendItems.forEach((item, idx) => {
  const x = legendX;
  const y = legendY + idx * 18;

  const rect = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
  rect.setAttribute('x', String(x));
  rect.setAttribute('y', String(y - 10));
  rect.setAttribute('width', '12');
  rect.setAttribute('height', '12');
  rect.setAttribute('fill', item.color);
  rect.setAttribute('rx', '2');
  g.appendChild(rect);

  const text = document.createElementNS('http://www.w3.org/2000/svg', 'text');
  text.setAttribute('x', String(x + 18));
  text.setAttribute('y', String(y));
  text.setAttribute('fill', 'rgba(255,255,255,0.75)');
  text.setAttribute('font-size', '12');
  text.setAttribute('font-weight', '500');
  text.textContent = item.label;
  g.appendChild(text);
});

    // bars
    metroData.forEach((m, i) => {
      const isSelected = selectedMetro?.metro === m.metro;

      const xCenter = i * groupWidth + groupWidth / 2;
      const x1 = xCenter - barWidth - gap / 2;
      const x2 = xCenter + gap / 2;

      const commuteH = (m.avg_commute / maxCommute) * chartHeight;
      const co2H = (m.co2_per_capita / maxCO2) * chartHeight;

      const commuteBar = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
      commuteBar.setAttribute('x', String(x1));
      commuteBar.setAttribute('y', String(chartHeight - commuteH));
      commuteBar.setAttribute('width', String(barWidth));
      commuteBar.setAttribute('height', String(commuteH));
      commuteBar.setAttribute('fill', '#4ecdc4');
      commuteBar.setAttribute('fill-opacity', isSelected ? '0.95' : '0.65');
      commuteBar.setAttribute('stroke', '#4ecdc4');
      commuteBar.setAttribute('stroke-width', isSelected ? '3' : '1');
      commuteBar.style.cursor = 'pointer';
      commuteBar.addEventListener('click', () => selectMetro(m));
      g.appendChild(commuteBar);

      const co2Bar = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
      co2Bar.setAttribute('x', String(x2));
      co2Bar.setAttribute('y', String(chartHeight - co2H));
      co2Bar.setAttribute('width', String(barWidth));
      co2Bar.setAttribute('height', String(co2H));
      co2Bar.setAttribute('fill', '#ff6b6b');
      co2Bar.setAttribute('fill-opacity', isSelected ? '0.95' : '0.65');
      co2Bar.setAttribute('stroke', '#ff6b6b');
      co2Bar.setAttribute('stroke-width', isSelected ? '3' : '1');
      co2Bar.style.cursor = 'pointer';
      co2Bar.addEventListener('click', () => selectMetro(m));
      g.appendChild(co2Bar);

      // metro label
      const name = document.createElementNS('http://www.w3.org/2000/svg', 'text');
      name.setAttribute('x', String(xCenter));
      name.setAttribute('y', String(chartHeight + 30));
      name.setAttribute('text-anchor', 'middle');
      name.setAttribute('fill', isSelected ? '#ffd93d' : 'rgba(255,255,255,0.9)');
      name.setAttribute('font-size', '14');
      name.setAttribute('font-weight', isSelected ? '700' : '600');
      name.style.cursor = 'pointer';
      name.addEventListener('click', () => selectMetro(m));
      name.textContent = m.metro;
      g.appendChild(name);

      // bar values
      const cLab = document.createElementNS('http://www.w3.org/2000/svg', 'text');
      cLab.setAttribute('x', String(x1 + barWidth / 2));
      cLab.setAttribute('y', String(chartHeight - commuteH - 8));
      cLab.setAttribute('text-anchor', 'middle');
      cLab.setAttribute('fill', 'rgba(255,255,255,0.9)');
      cLab.setAttribute('font-size', '11');
      cLab.textContent = safe(m.avg_commute, 1);
      g.appendChild(cLab);

      const eLab = document.createElementNS('http://www.w3.org/2000/svg', 'text');
      eLab.setAttribute('x', String(x2 + barWidth / 2));
      eLab.setAttribute('y', String(chartHeight - co2H - 8));
      eLab.setAttribute('text-anchor', 'middle');
      eLab.setAttribute('fill', 'rgba(255,255,255,0.9)');
      eLab.setAttribute('font-size', '11');
      eLab.textContent = safe(m.co2_per_capita, 2);
      g.appendChild(eLab);
    });

    // y-axis title
    const yTitle = document.createElementNS('http://www.w3.org/2000/svg', 'text');
    const yX = -55;
    const yY = chartHeight / 2;
    yTitle.setAttribute('x', String(yX));
    yTitle.setAttribute('y', String(yY));
    yTitle.setAttribute('text-anchor', 'middle');
    yTitle.setAttribute('fill', 'rgba(255,255,255,0.85)');
    yTitle.setAttribute('font-size', '13');
    yTitle.setAttribute('font-weight', '600');
    yTitle.setAttribute('transform', `rotate(-90, ${yX}, ${yY})`);
    yTitle.textContent = 'Commute (minutes) and CO₂ (tons)';
    g.appendChild(yTitle);

    svg.appendChild(g);
    chartContainer.appendChild(svg);
    currentSvg = svg;
  }

  $: if (dataLoaded && chartContainer && metroData.length) {
    renderChart();
  }

  // Key insight text (computed)
  $: lowestCO2 =
    metroData.length ? metroData.reduce((a, b) => (a.co2_per_capita < b.co2_per_capita ? a : b)) : null;

  $: highestCommute =
    metroData.length ? metroData.reduce((a, b) => (a.avg_commute > b.avg_commute ? a : b)) : null;
</script>

<div class="chapter-container">
  <div class="chapter-header">
    <h1>The Metro Divide</h1>
    <p class="subtitle">Why commute length isn’t the whole carbon story</p>
  </div>

  {#if !dataLoaded}
    <div class="loading-state">
      <p>Loading Pennsylvania metro comparison data...</p>
    </div>
  {:else if metroData.length === 0}
    <div class="loading-state">
      <p>Couldn’t load metro data. Check that <code>pa_metro_comparison.json</code> is in <code>static/</code> and refresh.</p>
      <p style="opacity:0.8; margin-top:1rem;">(On GitHub Pages the correct path is <code>/FinalViz/pa_metro_comparison.json</code>.)</p>
    </div>
  {:else}
    <div class="content-wrapper">
      <div class="intro-section">
  <h2 class="kicker">The assumption</h2>
  <p class="intro-text">
    Most people treat commute emissions like a simple math problem: longer drive = more carbon.
    It’s intuitive, it’s tidy, and it’s often wrong.
  </p>

  <h2 class="kicker">What the data actually says</h2>
  <p class="intro-text">
    Pennsylvania’s major metros show why. Two places can have similar commute times and end up with very different
    carbon footprints, not because residents care more or less about the environment, but because the system around
    them gives different choices.
  </p>

  <h2 class="kicker">The core issue</h2>
  <p class="intro-text">
    The real driver here is <strong>mode</strong>: whether people can realistically avoid driving alone.
    Transit access, land use, job density, and the way a region is built determine whether a commute becomes
    one tailpipe per worker, or a shared ride that spreads emissions across many people.
  </p>

  <p class="intro-text subtle">
    Read the chart as a story about infrastructure. Commute time is the surface. Carbon is the consequence.
  </p>
</div>


      <div class="chart-section">
        <div class="chart-container" bind:this={chartContainer}></div>
      </div>

      <div class="metro-comparison-grid">
        {#each metroData as metro}
          <div
            class="metro-card"
            class:selected={selectedMetro?.metro === metro.metro}
            on:click={() => selectMetro(metro)}
            role="button"
            tabindex="0"
            on:keydown={(e) => e.key === 'Enter' && selectMetro(metro)}
          >
            <h3>{metro.metro}</h3>

            <div class="metro-stats">
              <div class="stat-item">
                <span class="stat-label">Avg Commute</span>
                <span class="stat-value">{safe(metro.avg_commute, 1)} min</span>
              </div>
              <div class="stat-item">
                <span class="stat-label">Transit Use</span>
                <span class="stat-value">{safe(metro.transit_pct, 1)}%</span>
              </div>
              <div class="stat-item">
                <span class="stat-label">CO₂ per Person</span>
                <span class="stat-value">{safe(metro.co2_per_capita, 2)} tons</span>
              </div>
              <div class="stat-item">
                <span class="stat-label">Median Income</span>
                <span class="stat-value">${Math.round(metro.median_income).toLocaleString()}</span>
              </div>
            </div>

            {#if selectedMetro?.metro === metro.metro}
              <div class="burden-score">
                <span class="burden-label">Commute Burden Score</span>
                <span class="burden-value">{safe(metro.commute_burden_score, 1)}</span>
                <p class="burden-note">Time vs income ratio (lower is better)</p>
              </div>
            {/if}
          </div>
        {/each}
      </div>

      <div class="story-section">
  <h2>What’s really happening</h2>

  <div class="story-lead">
    <p>
      Click a metro above. Don’t just compare the numbers — ask what the numbers imply about daily life.
      A commute isn’t only a personal choice. It’s a design outcome.
    </p>
  </div>

  {#if selectedMetro}
    <div class="selected-narrative">
      <h3>{selectedMetro.metro}: the commute you inherit</h3>

      <p>
        In <strong>{selectedMetro.metro}</strong>, the average commute is
        <strong>{safe(selectedMetro.avg_commute, 1)} minutes</strong>.
        About <strong>{safe(selectedMetro.transit_pct, 1)}%</strong> of commuters use public transit, and
        emissions come out to roughly <strong>{safe(selectedMetro.co2_per_capita, 2)} tons of CO₂ per person</strong>.
      </p>

      <p>
        This is what climate policy looks like on an ordinary morning. If transit is frequent and reliable,
        fewer commutes require a car. If it isn’t, even short trips become carbon-intensive — repeated
        thousands of times across a metro.
      </p>

      <p class="soft">
        The more important question isn’t “How long is the commute?” —
        it’s <strong>how many single-occupancy miles are locked in by design.</strong>
      </p>
    </div>
  {/if}

  <div class="insight-box">
    <h3>The key insight</h3>
    <p>
      The metro with the longest average commute is not the one with the highest emissions per person.
      When those don’t match, it’s evidence that <strong>infrastructure and mode choice</strong> —
      not just minutes — shape the carbon cost of daily life.
    </p>

    <p class="soft">
      Emissions aren’t only produced by engines. They’re produced by the absence of alternatives.
    </p>
  </div>

  <div class="takeaway">
    <h3>So what?</h3>
    <p>
      Reducing commute emissions isn’t about asking people to make heroic choices.
      It’s about changing what’s normal through transit investment, land use,
      and giving people a real way to get to work without a car.
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
    margin-bottom: 2.5rem;
  }

  .chapter-header h1 {
    font-size: 3rem;
    font-weight: 700;
    margin-bottom: 0.5rem;
  }

  .subtitle {
    font-size: 1.2rem;
    opacity: 0.9;
  }

  .content-wrapper {
    max-width: 1200px;
    margin: 0 auto;
  }

  .intro-section {
    margin: 2.5rem 0;
    padding: 1.75rem;
    background: rgba(78, 205, 196, 0.1);
    border-left: 4px solid #4ecdc4;
    border-radius: 12px;
  }

  .intro-text {
    font-size: 1.15rem;
    line-height: 1.8;
    margin: 0;
  }

  .chart-section {
    margin: 2.5rem 0 3rem 0;
    padding: 1.5rem;
    background: rgba(255, 255, 255, 0.05);
    border-radius: 15px;
  }

  .chart-container {
    min-height: 520px;
    display: flex;
    align-items: center;
    justify-content: center;
  }

  .metro-comparison-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
    gap: 1.5rem;
    margin: 2.5rem 0 3.5rem 0;
  }

  .metro-card {
    padding: 1.5rem;
    background: rgba(255, 255, 255, 0.08);
    border-radius: 12px;
    border: 2px solid rgba(255, 255, 255, 0.18);
    cursor: pointer;
    transition: all 0.25s;
  }

  .metro-card:hover,
  .metro-card:focus {
    background: rgba(255, 255, 255, 0.12);
    transform: translateY(-3px);
    border-color: #4ecdc4;
    outline: none;
  }

  .metro-card.selected {
    background: rgba(78, 205, 196, 0.15);
    border-color: #4ecdc4;
    box-shadow: 0 4px 18px rgba(78, 205, 196, 0.25);
  }

  .metro-card h3 {
    font-size: 1.4rem;
    margin: 0 0 1rem 0;
    color: #4ecdc4;
    text-align: center;
    font-weight: 700;
  }

  .metro-stats {
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
  }

  .stat-item {
    display: flex;
    justify-content: space-between;
    padding: 0.6rem 0;
    border-bottom: 1px solid rgba(255, 255, 255, 0.1);
  }

  .stat-item:last-child {
    border-bottom: none;
  }

  .stat-label {
    font-size: 0.9rem;
    opacity: 0.8;
  }

  .stat-value {
    font-size: 1rem;
    font-weight: 700;
    color: #ffd93d;
  }

  .burden-score {
    margin-top: 1rem;
    padding: 1rem;
    background: rgba(255, 215, 0, 0.12);
    border-radius: 10px;
    text-align: center;
  }

  .burden-label {
    display: block;
    font-size: 0.85rem;
    opacity: 0.85;
    margin-bottom: 0.35rem;
  }

  .burden-value {
    display: block;
    font-size: 1.8rem;
    font-weight: 800;
    color: #ffd93d;
    margin-bottom: 0.25rem;
  }

  .burden-note {
    font-size: 0.8rem;
    opacity: 0.75;
    margin: 0;
  }

  .story-section {
    margin: 3rem 0 0 0;
  }

  .story-section h2 {
    font-size: 2rem;
    text-align: center;
    margin-bottom: 1.25rem;
    color: #ffd93d;
  }

  .story-lead {
    max-width: 900px;
    margin: 0 auto 1.5rem auto;
    opacity: 0.9;
    line-height: 1.8;
    text-align: center;
  }

  .selected-narrative {
    max-width: 900px;
    margin: 0 auto 1.5rem auto;
    padding: 1.5rem;
    background: rgba(255, 255, 255, 0.05);
    border-radius: 12px;
    border-left: 4px solid #4ecdc4;
  }

  .selected-narrative h3 {
    margin: 0 0 0.75rem 0;
    color: #4ecdc4;
    font-size: 1.3rem;
  }

  .selected-narrative p {
    margin: 0.75rem 0;
    line-height: 1.8;
  }

  .selected-narrative p.soft {
    opacity: 0.9;
  }

  .insight-box {
    margin: 1.75rem auto 0 auto;
    padding: 1.75rem;
    max-width: 900px;
    background: rgba(255, 215, 0, 0.1);
    border-left: 4px solid #ffd93d;
    border-radius: 12px;
  }

  .insight-box h3 {
    font-size: 1.5rem;
    margin: 0 0 0.75rem 0;
    color: #ffd93d;
  }

  .insight-box p {
    font-size: 1.1rem;
    line-height: 1.85;
    margin: 0;
  }

  .loading-state {
    text-align: center;
    padding: 4rem 2rem;
    font-size: 1.2rem;
    opacity: 0.85;
  }

  .kicker {
  font-size: 0.85rem;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  opacity: 0.75;
  margin: 1.5rem 0 0.4rem 0;
}

.subtle,
.soft {
  opacity: 0.85;
}

.takeaway {
  max-width: 900px;
  margin: 3rem auto 0 auto;
  padding: 1.5rem;
  background: rgba(255,255,255,0.04);
  border-radius: 12px;
  border-left: 4px solid rgba(255, 217, 61, 0.65);
}


  @media (max-width: 768px) {
    .chapter-header h1 {
      font-size: 2rem;
    }

    .chart-container {
      min-height: 420px;
    }
  }
</style>