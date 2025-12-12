<script lang="ts">
  import { currentChapter, chapters } from '$lib/stores/navigation';
  
  export let onNavigate: (chapterId: number) => void = () => {};
  
  let showMenu: boolean = false;
  
  function goToChapter(chapterId: number): void {
    currentChapter.set(chapterId);
    showMenu = false;
    onNavigate(chapterId);
  }
  
  function nextChapter(): void {
    const current = $currentChapter;
    if (current < 6) {
      goToChapter(current + 1);
    }
  }
  
  function prevChapter(): void {
    const current = $currentChapter;
    if (current > 1) {
      goToChapter(current - 1);
    }
  }

  function handleKeydown(event: KeyboardEvent, chapterId: number): void {
    if (event.key === 'Enter' || event.key === ' ') {
      event.preventDefault();
      goToChapter(chapterId);
    }
  }

  function handleMenuKeydown(event: KeyboardEvent): void {
    if (event.key === 'Escape') {
      showMenu = false;
    }
  }
</script>

<nav class="navigation">
  <div class="nav-header">
    <h2>The Hidden Cost of Commutes</h2>
    <button class="menu-toggle" on:click={() => showMenu = !showMenu} aria-label="Toggle menu">
      ☰
    </button>
  </div>
  
  <div class="progress-bar">
    <div class="progress-fill" style="width: {($currentChapter / 6) * 100}%"></div>
  </div>
  
  {#if showMenu}
    <!-- svelte-ignore a11y-click-events-have-key-events -->
    <!-- svelte-ignore a11y-no-static-element-interactions -->
    <div class="menu-overlay" on:click={() => showMenu = false} on:keydown={handleMenuKeydown}>
      <!-- svelte-ignore a11y-click-events-have-key-events -->
      <!-- svelte-ignore a11y-no-static-element-interactions -->
      <div class="menu-content" on:click|stopPropagation role="dialog" aria-modal="true" aria-labelledby="menu-title">
        <div class="menu-header">
          <h3 id="menu-title">Chapters</h3>
          <button class="close-btn" on:click={() => showMenu = false} aria-label="Close menu">×</button>
        </div>
        <ul class="chapter-list">
          {#each chapters as chapter}
            <!-- svelte-ignore a11y-click-events-have-key-events -->
            <!-- svelte-ignore a11y-no-noninteractive-element-interactions -->
            <li 
              class:active={$currentChapter === chapter.id}
              on:click={() => goToChapter(chapter.id)}
              on:keydown={(e) => handleKeydown(e, chapter.id)}
              role="button"
              tabindex="0"
              aria-label={`Go to chapter ${chapter.id}: ${chapter.title}`}
            >
              <span class="chapter-number">{chapter.id}</span>
              <div class="chapter-info">
                <strong>{chapter.title}</strong>
                <span class="chapter-subtitle">{chapter.subtitle}</span>
              </div>
            </li>
          {/each}
        </ul>
      </div>
    </div>
  {/if}
  
  <div class="nav-controls">
    <button 
      class="nav-btn prev" 
      on:click={prevChapter}
      disabled={$currentChapter === 1}
      aria-label="Previous chapter"
    >
      ← Previous
    </button>
    
    <span class="chapter-indicator">
      Chapter {$currentChapter} of 6
    </span>
    
    <button 
      class="nav-btn next" 
      on:click={nextChapter}
      disabled={$currentChapter === 6}
      aria-label="Next chapter"
    >
      Next →
    </button>
  </div>
</nav>

<style>
  .navigation {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    z-index: 1000;
    background: rgba(0, 0, 0, 0.9);
    backdrop-filter: blur(10px);
    box-shadow: 0 2px 10px rgba(0, 0, 0, 0.3);
  }

  .nav-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 1rem 2rem;
    color: white;
  }

  .nav-header h2 {
    margin: 0;
    font-size: 1.5rem;
  }

  .menu-toggle {
    background: none;
    border: none;
    color: white;
    font-size: 2rem;
    cursor: pointer;
    padding: 0.5rem;
  }

  .progress-bar {
    height: 4px;
    background: rgba(255, 255, 255, 0.2);
    position: relative;
  }

  .progress-fill {
    height: 100%;
    background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
    transition: width 0.3s ease;
  }

  .nav-controls {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 1rem 2rem;
  }

  .nav-btn {
    padding: 0.75rem 1.5rem;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    border: none;
    border-radius: 8px;
    cursor: pointer;
    font-size: 1rem;
    font-weight: bold;
    transition: transform 0.2s, opacity 0.3s;
  }

  .nav-btn:hover:not(:disabled) {
    transform: translateY(-2px);
  }

  .nav-btn:disabled {
    opacity: 0.3;
    cursor: not-allowed;
  }

  .chapter-indicator {
    color: white;
    font-size: 1rem;
    font-weight: bold;
  }

  .menu-overlay {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: rgba(0, 0, 0, 0.8);
    display: flex;
    justify-content: center;
    align-items: center;
    z-index: 1001;
  }

  .menu-content {
    background: white;
    border-radius: 15px;
    max-width: 600px;
    width: 90%;
    max-height: 80vh;
    overflow-y: auto;
    box-shadow: 0 10px 40px rgba(0, 0, 0, 0.5);
  }

  .menu-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 1.5rem;
    border-bottom: 2px solid #ecf0f1;
    position: sticky;
    top: 0;
    background: white;
  }

  .menu-header h3 {
    margin: 0;
    font-size: 1.5rem;
  }

  .close-btn {
    background: none;
    border: none;
    font-size: 2rem;
    cursor: pointer;
    color: #7f8c8d;
  }

  .chapter-list {
    list-style: none;
    padding: 0;
    margin: 0;
  }

  .chapter-list li {
    display: flex;
    align-items: center;
    padding: 1.5rem;
    border-bottom: 1px solid #ecf0f1;
    cursor: pointer;
    transition: background 0.2s;
  }

  .chapter-list li:hover {
    background: #f8f9fa;
  }

  .chapter-list li.active {
    background: #e8f5e9;
    border-left: 4px solid #4CAF50;
  }

  .chapter-number {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 40px;
    height: 40px;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    border-radius: 50%;
    font-weight: bold;
    margin-right: 1rem;
    flex-shrink: 0;
  }

  .chapter-info {
    display: flex;
    flex-direction: column;
  }

  .chapter-info strong {
    font-size: 1.1rem;
    margin-bottom: 0.25rem;
    color: #2c3e50;
  }

  .chapter-subtitle {
    font-size: 0.9rem;
    color: #7f8c8d;
  }

  @media (max-width: 768px) {
    .nav-header h2 {
      font-size: 1rem;
    }

    .nav-controls {
      padding: 0.5rem 1rem;
    }

    .nav-btn {
      padding: 0.5rem 1rem;
      font-size: 0.9rem;
    }

    .chapter-indicator {
      font-size: 0.9rem;
    }
  }
</style>