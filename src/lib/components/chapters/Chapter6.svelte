<script lang="ts">
  import { onMount } from 'svelte';

  type CommuteMode = 'drive_alone' | 'transit' | 'bike_walk' | 'carpool' | 'wfh';

  // Emission factors (kg CO2 per commuter per year for average commute)
  const EMISSIONS_PER_MODE: Record<CommuteMode, number> = {
    drive_alone: 2580,  // ~10k miles at 25mpg
    transit: 580,
    bike_walk: 0,
    carpool: 1290,  // Half of drive alone (shared)
    wfh: 0
  };

  // Cost per mile (dollars)
  const COST_PER_MILE = 0.67;
  const AVG_SPEED_MPH = 30; // Average commute speed

  let dataLoaded: boolean = false;
  let paAvgCO2PerPerson: number = 2.6; // Default, will load from data

  // User inputs
  let commuteMinutes: number = 30;
  let currentMode: CommuteMode = 'drive_alone';
  let daysPerWeek: number = 5;

  // Calculated values
  $: commuteDistance = (commuteMinutes / 60) * AVG_SPEED_MPH; // miles one way
  $: dailyMiles = commuteDistance * 2; // round trip
  $: annualMiles = dailyMiles * daysPerWeek * 50; // 50 weeks per year
  $: annualCost = annualMiles * COST_PER_MILE;

  // Calculate annual CO2 based on mode and miles
  $: currentAnnualCO2 = (() => {
    const baseEmission = EMISSIONS_PER_MODE[currentMode];
    // Scale based on actual miles vs average (10k miles assumed for base)
    const avgMiles = 10000;
    return (baseEmission * (annualMiles / avgMiles)) / 1000; // Convert kg to tons
  })();

  $: vsPA = ((currentAnnualCO2 / paAvgCO2PerPerson - 1) * 100);
  $: isAboveAverage = currentAnnualCO2 > paAvgCO2PerPerson;

  // Option calculations
  $: option1 = {
    name: 'Switch to Transit',
    co2Saved: currentMode === 'drive_alone' ? ((EMISSIONS_PER_MODE.drive_alone - EMISSIONS_PER_MODE.transit) * (annualMiles / 10000)) / 1000 : 0,
    costSaved: currentMode === 'drive_alone' ? annualMiles * COST_PER_MILE * 0.7 : 0, // Transit costs ~30% of driving
    healthBenefit: commuteMinutes * 2 * 5, // 5 days, round trip
    available: true
  };

  $: option2 = {
    name: 'Go Remote 2 days/week',
    co2Saved: currentMode === 'wfh' ? 0 : ((EMISSIONS_PER_MODE[currentMode] * (annualMiles / 10000)) / 1000) * 0.4, // 2/5 days = 40%
    costSaved: annualCost * 0.4, // 40% of cost
    hoursGained: (commuteMinutes * 2 * 2 * 50) / 60, // 2 days/week, round trip, 50 weeks
    available: true
  };

  $: option3 = {
    name: 'Move Closer (15mi → 5mi)',
    newDistance: 5,
    co2Saved: currentMode === 'wfh' ? 0 : ((annualMiles - (5 * 2 * daysPerWeek * 50)) * (EMISSIONS_PER_MODE[currentMode] / 10000)) / 1000,
    costSaved: (annualMiles - (5 * 2 * daysPerWeek * 50)) * COST_PER_MILE,
    tradeoff: 'Higher rent but lower total cost',
    available: true
  };

  $: option4 = {
    name: 'Carpool/Bike 1 day/week',
    co2Saved: currentMode === 'drive_alone' ? ((EMISSIONS_PER_MODE.drive_alone - EMISSIONS_PER_MODE.carpool) * (annualMiles / 10000)) / 1000 * 0.2 : 0, // 1/5 days
    costSaved: annualCost * 0.2 * 0.5, // 1 day, half cost (carpool splits)
    bonus: 'Better fitness, meet neighbors',
    available: true
  };

  // PA collective impact
  $: totalPACommuters = 6179069;
  $: collective20pctReduction = (paAvgCO2PerPerson * totalPACommuters * 0.2) / 1000; // million tons
  $: carsEquivalent = Math.round((collective20pctReduction * 1000000) / 4.6); // 4.6 tons per car per year

  onMount(async () => {
    try {
      const summaryResponse = await fetch('/pa_summary_stats.json');
      const summaryData = await summaryResponse.json();
      
      const scenariosResponse = await fetch('/pa_scenarios.json');
      const scenariosData = await scenariosResponse.json();
      
      const totalCommuters = summaryData.total_commuters || 6179069;
      const annualCO2Tons = scenariosData.current?.emissions_tons || 0;
      paAvgCO2PerPerson = annualCO2Tons / totalCommuters;
      
      // Set default commute to PA average
      commuteMinutes = summaryData.avg_commute_minutes || 30;
      
      dataLoaded = true;
    } catch (error) {
      console.error('Error loading PA data:', error);
      dataLoaded = true;
    }
  });

  async function downloadReport() {
    try {
      // Dynamically import jsPDF
      const { jsPDF } = await import('jspdf') as any;
      const doc = new jsPDF();
      
      let yPos = 20;
      const pageWidth = doc.internal.pageSize.getWidth();
      const margin = 20;
      const maxWidth = pageWidth - 2 * margin;

      // Helper function to add text with word wrap
      const addWrappedText = (text: string, x: number, y: number, maxWidth: number, fontSize: number = 10) => {
        doc.setFontSize(fontSize);
        const lines = doc.splitTextToSize(text, maxWidth);
        doc.text(lines, x, y);
        return lines.length * (fontSize * 0.35); // Return height used
      };

      // Header
      doc.setFontSize(20);
      doc.setFont('helvetica', 'bold');
      doc.text('Pennsylvania Commute Impact Report', margin, yPos);
      yPos += 15;

      doc.setFontSize(10);
      doc.setFont('helvetica', 'normal');
      doc.text(`Generated on ${new Date().toLocaleDateString()}`, margin, yPos);
      yPos += 15;

      // Personal Impact Section
      doc.setFontSize(16);
      doc.setFont('helvetica', 'bold');
      doc.text('Your Current Impact', margin, yPos);
      yPos += 12;

      doc.setFontSize(11);
      doc.setFont('helvetica', 'normal');
      yPos += addWrappedText(`Commute: ${commuteMinutes} minutes one way`, margin, yPos, maxWidth);
      yPos += 5;
      yPos += addWrappedText(`Mode: ${currentMode.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}`, margin, yPos, maxWidth);
      yPos += 5;
      yPos += addWrappedText(`Days per week: ${daysPerWeek}`, margin, yPos, maxWidth);
      yPos += 8;

      doc.setFont('helvetica', 'bold');
      doc.text('Annual Impact:', margin, yPos);
      yPos += 8;

      doc.setFont('helvetica', 'normal');
      yPos += addWrappedText(`CO₂ Emissions: ${currentAnnualCO2.toFixed(2)} tons`, margin + 5, yPos, maxWidth);
      yPos += 5;
      yPos += addWrappedText(`Annual Cost: $${annualCost.toFixed(0)}`, margin + 5, yPos, maxWidth);
      yPos += 5;
      yPos += addWrappedText(`PA Average: ${paAvgCO2PerPerson.toFixed(2)} tons CO₂`, margin + 5, yPos, maxWidth);
      yPos += 5;
      
      doc.setFont('helvetica', 'bold');
      const comparisonText = `You're ${isAboveAverage ? '+' : ''}${vsPA.toFixed(1)}% ${isAboveAverage ? 'above' : 'below'} PA average`;
      doc.setTextColor(isAboveAverage ? 255 : 81, isAboveAverage ? 107 : 207, isAboveAverage ? 107 : 102);
      yPos += addWrappedText(comparisonText, margin + 5, yPos, maxWidth);
      doc.setTextColor(0, 0, 0);
      yPos += 15;

      // Check if we need a new page
      if (yPos > 250) {
        doc.addPage();
        yPos = 20;
      }

      // Options Section
      doc.setFontSize(16);
      doc.setFont('helvetica', 'bold');
      doc.text('Your Options to Reduce Impact', margin, yPos);
      yPos += 15;

      const options = [
        {
          title: 'Option 1: Switch to Transit',
          co2Saved: option1.co2Saved,
          costSaved: option1.costSaved,
          details: [`${option1.healthBenefit} extra walking minutes/week`]
        },
        {
          title: 'Option 2: Go Remote 2 days/week',
          co2Saved: option2.co2Saved,
          costSaved: option2.costSaved,
          details: [`${option2.hoursGained.toFixed(0)} hours gained per year`]
        },
        {
          title: 'Option 3: Move Closer',
          co2Saved: option3.co2Saved,
          costSaved: option3.costSaved,
          details: [option3.tradeoff]
        },
        {
          title: 'Option 4: Carpool/Bike 1 day/week',
          co2Saved: option4.co2Saved,
          costSaved: option4.costSaved,
          details: [option4.bonus]
        }
      ];

      options.forEach((option, index) => {
        // Check if we need a new page
        if (yPos > 240) {
          doc.addPage();
          yPos = 20;
        }

        doc.setFontSize(12);
        doc.setFont('helvetica', 'bold');
        yPos += addWrappedText(option.title, margin, yPos, maxWidth, 12);
        yPos += 5;

        doc.setFontSize(10);
        doc.setFont('helvetica', 'normal');
        yPos += addWrappedText(`CO₂ Saved: ${option.co2Saved.toFixed(2)} tons/year`, margin + 5, yPos, maxWidth);
        yPos += 5;
        yPos += addWrappedText(`Money Saved: $${option.costSaved.toFixed(0)}/year`, margin + 5, yPos, maxWidth);
        yPos += 5;

        if (option.details && option.details.length > 0) {
          option.details.forEach(detail => {
            yPos += addWrappedText(`• ${detail}`, margin + 5, yPos, maxWidth);
            yPos += 5;
          });
        }
        yPos += 8;
      });

      // Collective Impact Section
      if (yPos > 200) {
        doc.addPage();
        yPos = 20;
      }

      doc.setFontSize(16);
      doc.setFont('helvetica', 'bold');
      doc.text('Collective Impact', margin, yPos);
      yPos += 12;

      doc.setFontSize(11);
      doc.setFont('helvetica', 'normal');
      const collectiveText = `If every Pennsylvania commuter reduced their emissions by just 20%, we'd prevent ${collective20pctReduction.toFixed(1)} million tons of CO₂ annually—equivalent to taking ${carsEquivalent.toLocaleString()} cars off the road permanently.`;
      yPos += addWrappedText(collectiveText, margin, yPos, maxWidth, 11);
      yPos += 15;

      // Resources Section
      doc.setFontSize(14);
      doc.setFont('helvetica', 'bold');
      doc.text('PA-Specific Resources', margin, yPos);
      yPos += 10;

      doc.setFontSize(10);
      doc.setFont('helvetica', 'normal');
      const resources = [
        '• SEPTA Trip Planner: septa.org/trip-planner/',
        '• Port Authority Schedules: portauthority.org',
        '• PA Clean Air Act: dep.pa.gov/Business/Air',
        '• PA Carpool Programs: 511pa.com/carpool/'
      ];

      resources.forEach(resource => {
        yPos += addWrappedText(resource, margin, yPos, maxWidth);
        yPos += 5;
      });

      // Footer
      const totalPages = doc.getNumberOfPages();
      for (let i = 1; i <= totalPages; i++) {
        doc.setPage(i);
        doc.setFontSize(8);
        doc.setTextColor(128, 128, 128);
        doc.text(
          `Page ${i} of ${totalPages} - Pennsylvania Commute Impact Report`,
          pageWidth / 2,
          doc.internal.pageSize.getHeight() - 10,
          { align: 'center' }
        );
        doc.setTextColor(0, 0, 0);
      }

      // Save the PDF
      doc.save('pa-commute-impact-report.pdf');
    } catch (error) {
      console.error('Error generating PDF:', error);
      alert('Error generating PDF. Please try again.');
    }
  }
</script>

<div class="chapter-container">
  <div class="chapter-header">
    <h1>Your Choice for Pennsylvania</h1>
    <p class="subtitle">Calculate Your Personal Path to Lower Emissions</p>
  </div>

  {#if !dataLoaded}
    <div class="loading-state">
      <p>Loading Pennsylvania data...</p>
    </div>
  {:else}
  <div class="content-wrapper">
    <div class="intro-section">
      <p class="intro-text">
        Now it's your turn. Let's calculate your personal path to lower emissions and see how small changes 
        can make a big difference—for you and for Pennsylvania.
      </p>
    </div>

    <div class="calculator-section">
      <h2>Your Current Impact</h2>
      
      <div class="input-group">
        <label for="commute-minutes">Current Commute (minutes one way)</label>
        <input 
          id="commute-minutes"
          type="number" 
          bind:value={commuteMinutes} 
          min="1" 
          max="120"
          step="1"
        />
      </div>

      <div class="input-group">
        <label for="current-mode">Current Mode</label>
        <select id="current-mode" bind:value={currentMode}>
          <option value="drive_alone">Drive Alone</option>
          <option value="transit">Transit</option>
          <option value="carpool">Carpool</option>
          <option value="bike_walk">Bike/Walk</option>
          <option value="wfh">Work From Home</option>
        </select>
      </div>

      <div class="input-group">
        <label for="days-per-week">Days per Week</label>
        <input 
          id="days-per-week"
          type="number" 
          bind:value={daysPerWeek} 
          min="1" 
          max="7"
          step="1"
        />
      </div>

      <div class="results-box">
        <h3>Your Current Annual Impact</h3>
        <div class="impact-grid">
          <div class="impact-item">
            <span class="impact-label">CO₂ Emissions</span>
            <span class="impact-value">{currentAnnualCO2.toFixed(2)} tons</span>
          </div>
          <div class="impact-item">
            <span class="impact-label">Annual Cost</span>
            <span class="impact-value">${annualCost.toFixed(0)}</span>
          </div>
          <div class="impact-item">
            <span class="impact-label">PA Average</span>
            <span class="impact-value">{paAvgCO2PerPerson.toFixed(2)} tons CO₂</span>
          </div>
          <div class="impact-item comparison" class:above={isAboveAverage} class:below={!isAboveAverage}>
            <span class="impact-label">You're</span>
            <span class="impact-value">
              {isAboveAverage ? '+' : ''}{vsPA.toFixed(1)}% {isAboveAverage ? 'above' : 'below'} PA average
            </span>
          </div>
        </div>
      </div>
    </div>

    <div class="options-section">
      <h2>Your Options</h2>
      
      <div class="options-grid">
        <div class="option-card">
          <div class="option-header">
            <h3>🚇 Option 1: Switch to Transit</h3>
            {#if option1.available}
              <span class="availability-badge available">Available</span>
            {:else}
              <span class="availability-badge unavailable">Check Routes</span>
            {/if}
          </div>
          <div class="option-benefits">
            <div class="benefit-item">
              <span class="benefit-icon">🌱</span>
              <div class="benefit-content">
                <span class="benefit-label">CO₂ Saved</span>
                <span class="benefit-value">{option1.co2Saved.toFixed(2)} tons/year</span>
              </div>
            </div>
            <div class="benefit-item">
              <span class="benefit-icon">💰</span>
              <div class="benefit-content">
                <span class="benefit-label">Money Saved</span>
                <span class="benefit-value">${option1.costSaved.toFixed(0)}/year</span>
              </div>
            </div>
            <div class="benefit-item">
              <span class="benefit-icon">🏃</span>
              <div class="benefit-content">
                <span class="benefit-label">Health Benefit</span>
                <span class="benefit-value">{option1.healthBenefit} extra walking min/week</span>
              </div>
            </div>
          </div>
          <div class="option-resources">
            <a href="https://www.septa.org/trip-planner/" target="_blank" rel="noopener noreferrer" class="resource-link">
              Check SEPTA Trip Planner →
            </a>
            <a href="https://www.rideprt.org/" target="_blank" rel="noopener noreferrer" class="resource-link">
              Port Authority Schedules →
            </a>
            <a href="https://www.cattransit.com" target="_blank" rel="noopener noreferrer" class="resource-link">
              CAT Transit Routes →
            </a>
          </div>
        </div>

        <div class="option-card">
          <div class="option-header">
            <h3>🏠 Option 2: Go Remote 2 days/week</h3>
            <span class="availability-badge available">Talk to Employer</span>
          </div>
          <div class="option-benefits">
            <div class="benefit-item">
              <span class="benefit-icon">🌱</span>
              <div class="benefit-content">
                <span class="benefit-label">CO₂ Saved</span>
                <span class="benefit-value">{option2.co2Saved.toFixed(2)} tons/year</span>
              </div>
            </div>
            <div class="benefit-item">
              <span class="benefit-icon">💰</span>
              <div class="benefit-content">
                <span class="benefit-label">Money Saved</span>
                <span class="benefit-value">${option2.costSaved.toFixed(0)}/year</span>
              </div>
            </div>
            <div class="benefit-item">
              <span class="benefit-icon">⏰</span>
              <div class="benefit-content">
                <span class="benefit-label">Time Gained</span>
                <span class="benefit-value">{option2.hoursGained.toFixed(0)} hours/year</span>
              </div>
            </div>
          </div>
          <div class="option-resources">
            <a href="https://www.remote.com/resources/remote-work-policy-template" target="_blank" rel="noopener noreferrer" class="resource-link">
              Remote Work Policy Templates →
            </a>
            <a href="https://www.dol.gov/general/topic/workhours/telework" target="_blank" rel="noopener noreferrer" class="resource-link">
              PA Labor & Remote Work Guidelines →
            </a>
          </div>
        </div>

        <div class="option-card">
          <div class="option-header">
            <h3>🏘️ Option 3: Move Closer (15mi → 5mi)</h3>
            <span class="availability-badge available">Consider Trade-offs</span>
          </div>
          <div class="option-benefits">
            <div class="benefit-item">
              <span class="benefit-icon">🌱</span>
              <div class="benefit-content">
                <span class="benefit-label">CO₂ Saved</span>
                <span class="benefit-value">{option3.co2Saved.toFixed(2)} tons/year</span>
              </div>
            </div>
            <div class="benefit-item">
              <span class="benefit-icon">💰</span>
              <div class="benefit-content">
                <span class="benefit-label">Money Saved</span>
                <span class="benefit-value">${option3.costSaved.toFixed(0)}/year</span>
              </div>
            </div>
            <div class="benefit-item">
              <span class="benefit-icon">⚠️</span>
              <div class="benefit-content">
                <span class="benefit-label">Trade-off</span>
                <span class="benefit-value">{option3.tradeoff}</span>
              </div>
            </div>
          </div>
          <div class="option-resources">
            <a href="https://www.huduser.gov/portal/datasets/il.html" target="_blank" rel="noopener noreferrer" class="resource-link">
              PA Housing Affordability Calculator →
            </a>
          </div>
        </div>

        <div class="option-card">
          <div class="option-header">
            <h3>🚴 Option 4: Carpool/Bike 1 day/week</h3>
            <span class="availability-badge available">Easy Start</span>
          </div>
          <div class="option-benefits">
            <div class="benefit-item">
              <span class="benefit-icon">🌱</span>
              <div class="benefit-content">
                <span class="benefit-label">CO₂ Saved</span>
                <span class="benefit-value">{option4.co2Saved.toFixed(2)} tons/year</span>
              </div>
            </div>
            <div class="benefit-item">
              <span class="benefit-icon">💰</span>
              <div class="benefit-content">
                <span class="benefit-label">Money Saved</span>
                <span class="benefit-value">${option4.costSaved.toFixed(0)}/year</span>
              </div>
            </div>
            <div class="benefit-item">
              <span class="benefit-icon">🌟</span>
              <div class="benefit-content">
                <span class="benefit-label">Bonus</span>
                <span class="benefit-value">{option4.bonus}</span>
              </div>
            </div>
          </div>
          <div class="option-resources">
            <a href="https://www.511pa.com/carpool/" target="_blank" rel="noopener noreferrer" class="resource-link">
              PA Carpool Matching Service →
            </a>
            <a href="https://www.pennbike.org/" target="_blank" rel="noopener noreferrer" class="resource-link">
              PA Bike Resources →
            </a>
          </div>
        </div>
      </div>
    </div>

    <div class="collective-impact">
      <h2>The Bottom Line</h2>
      <div class="impact-statement">
        <p>
          If every Pennsylvania commuter reduced their emissions by just <strong>20%</strong>, we'd prevent
        </p>
        <div class="big-number">{collective20pctReduction.toFixed(1)} million tons</div>
        <p>of CO₂ annually—equivalent to taking <strong>{carsEquivalent.toLocaleString()} cars</strong> off the road permanently.</p>
      </div>
    </div>

    <div class="actions-section">
      <button class="download-btn" on:click={downloadReport}>
        📄 Download Personalized Report
      </button>
      
      <div class="pa-resources">
        <h3>PA-Specific Resources</h3>
        <div class="resources-grid">
          <a href="https://www.septa.org/trip-planner/" target="_blank" rel="noopener noreferrer" class="resource-card">
            <h4>SEPTA Trip Planner</h4>
            <p>Plan your transit route in Philadelphia</p>
          </a>
          <a href="https://www.rideprt.org/all-schedules/" target="_blank" rel="noopener noreferrer" class="resource-card">
            <h4>Port Authority Schedules</h4>
            <p>Pittsburgh transit schedules and maps</p>
          </a>
          <a href="https://www.dep.pa.gov/Business/Air/Pages/default.aspx" target="_blank" rel="noopener noreferrer" class="resource-card">
            <h4>PA Clean Air Act Incentives</h4>
            <p>Learn about clean air programs</p>
          </a>
          <a href="https://commutepa.org/carpool/" target="_blank" rel="noopener noreferrer" class="resource-card">
            <h4>PA Carpool Programs</h4>
            <p>Find carpool partners in your area</p>
          </a>
        </div>
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

  .calculator-section {
    margin: 4rem 0;
    padding: 2rem;
    background: rgba(255, 255, 255, 0.08);
    border-radius: 15px;
  }

  .calculator-section h2 {
    font-size: 2rem;
    margin-bottom: 2rem;
    color: #ffd93d;
  }

  .input-group {
    margin-bottom: 1.5rem;
  }

  .input-group label {
    display: block;
    font-size: 1.1rem;
    margin-bottom: 0.5rem;
    color: rgba(255, 255, 255, 0.9);
  }

  .input-group input,
  .input-group select {
    width: 100%;
    max-width: 300px;
    padding: 0.75rem 1rem;
    font-size: 1.1rem;
    background: rgba(255, 255, 255, 0.1);
    border: 2px solid rgba(255, 255, 255, 0.2);
    border-radius: 8px;
    color: white;
  }

  .input-group input:focus,
  .input-group select:focus {
    outline: none;
    border-color: #4ecdc4;
    background: rgba(255, 255, 255, 0.15);
  }

  .results-box {
    margin-top: 2rem;
    padding: 2rem;
    background: rgba(78, 205, 196, 0.1);
    border-radius: 12px;
    border-left: 4px solid #4ecdc4;
  }

  .results-box h3 {
    font-size: 1.5rem;
    margin-bottom: 1.5rem;
    color: #4ecdc4;
  }

  .impact-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 1.5rem;
  }

  .impact-item {
    display: flex;
    flex-direction: column;
    padding: 1rem;
    background: rgba(255, 255, 255, 0.05);
    border-radius: 8px;
  }

  .impact-item.comparison.above {
    border-left: 4px solid #ff6b6b;
  }

  .impact-item.comparison.below {
    border-left: 4px solid #51cf66;
  }

  .impact-label {
    font-size: 0.9rem;
    opacity: 0.8;
    margin-bottom: 0.5rem;
  }

  .impact-value {
    font-size: 1.5rem;
    font-weight: 700;
    color: #ffd93d;
  }

  .options-section {
    margin: 4rem 0;
  }

  .options-section h2 {
    font-size: 2.5rem;
    text-align: center;
    margin-bottom: 3rem;
    color: #ffd93d;
  }

  .options-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
    gap: 2rem;
  }

  .option-card {
    padding: 2rem;
    background: rgba(255, 255, 255, 0.08);
    border-radius: 12px;
    border: 2px solid rgba(255, 255, 255, 0.2);
    transition: transform 0.3s, box-shadow 0.3s;
  }

  .option-card:hover {
    transform: translateY(-5px);
    box-shadow: 0 8px 25px rgba(78, 205, 196, 0.3);
  }

  .option-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 1.5rem;
  }

  .option-header h3 {
    font-size: 1.5rem;
    margin: 0;
    color: #4ecdc4;
  }

  .availability-badge {
    padding: 0.4rem 0.8rem;
    border-radius: 20px;
    font-size: 0.85rem;
    font-weight: 600;
  }

  .availability-badge.available {
    background: rgba(81, 207, 102, 0.2);
    color: #51cf66;
  }

  .availability-badge.unavailable {
    background: rgba(255, 107, 107, 0.2);
    color: #ff6b6b;
  }

  .option-benefits {
    margin: 1.5rem 0;
  }

  .benefit-item {
    display: flex;
    align-items: center;
    gap: 1rem;
    padding: 1rem 0;
    border-bottom: 1px solid rgba(255, 255, 255, 0.1);
  }

  .benefit-item:last-child {
    border-bottom: none;
  }

  .benefit-icon {
    font-size: 2rem;
  }

  .benefit-content {
    display: flex;
    flex-direction: column;
    flex: 1;
  }

  .benefit-label {
    font-size: 0.9rem;
    opacity: 0.8;
    margin-bottom: 0.25rem;
  }

  .benefit-value {
    font-size: 1.2rem;
    font-weight: 700;
    color: #ffd93d;
  }

  .option-resources {
    margin-top: 1.5rem;
    padding-top: 1.5rem;
    border-top: 1px solid rgba(255, 255, 255, 0.1);
  }

  .resource-link {
    display: block;
    padding: 0.75rem 0;
    color: #4ecdc4;
    text-decoration: none;
    font-size: 0.95rem;
    transition: color 0.3s;
  }

  .resource-link:hover {
    color: #ffd93d;
    text-decoration: underline;
  }

  .collective-impact {
    margin: 4rem 0;
    padding: 3rem;
    background: rgba(255, 215, 0, 0.1);
    border-left: 4px solid #ffd93d;
    border-radius: 12px;
    text-align: center;
  }

  .collective-impact h2 {
    font-size: 2rem;
    margin-bottom: 2rem;
    color: #ffd93d;
  }

  .impact-statement {
    font-size: 1.3rem;
    line-height: 1.8;
  }

  .big-number {
    font-size: 4rem;
    font-weight: 800;
    color: #51cf66;
    margin: 1rem 0;
  }

  .actions-section {
    margin: 4rem 0;
  }

  .download-btn {
    width: 100%;
    padding: 1.5rem;
    font-size: 1.3rem;
    font-weight: 700;
    background: linear-gradient(135deg, #4ecdc4 0%, #44a08d 100%);
    color: white;
    border: none;
    border-radius: 12px;
    cursor: pointer;
    transition: transform 0.3s, box-shadow 0.3s;
    margin-bottom: 3rem;
  }

  .download-btn:hover {
    transform: translateY(-3px);
    box-shadow: 0 8px 25px rgba(78, 205, 196, 0.4);
  }

  .pa-resources h3 {
    font-size: 2rem;
    margin-bottom: 2rem;
    text-align: center;
    color: #4ecdc4;
  }

  .resources-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
    gap: 1.5rem;
  }

  .resource-card {
    padding: 1.5rem;
    background: rgba(255, 255, 255, 0.08);
    border-radius: 12px;
    border: 2px solid rgba(255, 255, 255, 0.2);
    text-decoration: none;
    color: white;
    transition: transform 0.3s, border-color 0.3s;
  }

  .resource-card:hover {
    transform: translateY(-3px);
    border-color: #4ecdc4;
  }

  .resource-card h4 {
    font-size: 1.2rem;
    margin: 0 0 0.5rem 0;
    color: #4ecdc4;
  }

  .resource-card p {
    font-size: 0.95rem;
    opacity: 0.8;
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

    .options-grid {
      grid-template-columns: 1fr;
    }

    .resources-grid {
      grid-template-columns: 1fr;
    }

    .big-number {
      font-size: 2.5rem;
    }
  }
</style>

