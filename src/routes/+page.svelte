<script lang="ts">
  import { onMount } from 'svelte';
  import { currentChapter } from '$lib/stores/navigation';
  import Navigation from '$lib/components/Navigation.svelte';
  import Chapter1 from '$lib/components/chapters/Chapter1.svelte';
  import Chapter2 from '$lib/components/chapters/Chapter2.svelte';
  import Chapter3 from '$lib/components/chapters/Chapter3.svelte';
  import Chapter4 from '$lib/components/chapters/Chapter4.svelte';
  import Chapter5 from '$lib/components/chapters/Chapter5.svelte';
  import Chapter6 from '$lib/components/chapters/Chapter6.svelte';
  import { base } from '$app/paths';


  let chapter1Element: HTMLElement | null = null;
  let chapter2Element: HTMLElement | null = null;
  let chapter3Element: HTMLElement | null = null;
  let chapter4Element: HTMLElement | null = null;
  let chapter5Element: HTMLElement | null = null;
  let chapter6Element: HTMLElement | null = null;
  
  let scrolling: boolean = false;

  // Update chapterElements array when individual elements change
  $: chapterElements = [
    chapter1Element,
    chapter2Element,
    chapter3Element,
    chapter4Element,
    chapter5Element,
    chapter6Element
  ];

  onMount(() => {
    // Smooth scroll to chapter on load
    if ($currentChapter > 1) {
      scrollToChapter($currentChapter - 1);
    }

    // Add scroll listener to update current chapter
    const handleScroll = (): void => {
      if (scrolling) return;

      const scrollPosition = window.scrollY + window.innerHeight / 2;

      for (let i = 0; i < chapterElements.length; i++) {
        const element = chapterElements[i];
        if (element) {
          const rect = element.getBoundingClientRect();
          const elementTop = rect.top + window.scrollY;
          const elementBottom = elementTop + rect.height;

          if (scrollPosition >= elementTop && scrollPosition < elementBottom) {
            currentChapter.set(i + 1);
            break;
          }
        }
      }
    };

    window.addEventListener('scroll', handleScroll, { passive: true });
    return () => window.removeEventListener('scroll', handleScroll);
  });

  function scrollToChapter(index: number): void {
    if (chapterElements[index]) {
      scrolling = true;
      chapterElements[index]!.scrollIntoView({
        behavior: 'smooth',
        block: 'start'
      });

      setTimeout(() => {
        scrolling = false;
      }, 1000);
    }
  }

  function handleNavigate(chapterId: number): void {
    scrollToChapter(chapterId - 1);
  }
</script>

<svelte:head>
  <title>The Hidden Cost of Commutes - Interactive Visualization</title>
  <meta
    name="description"
    content="Explore how commute patterns affect well-being, productivity, and sustainability through interactive data visualizations."
  />
</svelte:head>

<div class="app">
  <Navigation onNavigate={handleNavigate} />

  <main class="main-content">
    <!-- Hero Section -->
    <section class="hero">
      <video
        class="hero-video"
        autoplay
        muted
        loop
        playsinline
        preload="metadata"
      >
        <source src={`${base}/hero.mp4`} type="video/mp4" />
      </video>

      <div class="hero-overlay"></div>

      <div class="hero-content">
        <h1 class="hero-title">The Hidden Cost of Commutes</h1>

        <p class="hero-subtitle">
          An interactive exploration of how our daily journeys shape our lives,
          our planet, and our future
        </p>


        <p class="hero-dek">

  Every weekday, Pennsylvania runs the same quiet ritual: alarms, coffee, a line of brake lights,
  a train platform, a bus that’s late. It feels like a personal problem, your schedule, your patience,
  your gas bill.

</p>
<br>
<p class="hero-dek">
  But commuting is also a climate system. It’s shaped by zoning, job geography, transit coverage, and whether
  driving alone is the default or one option among many. When millions of small trips repeat, they add up to
  something large enough to measure.
</p>
<br>
<p class="hero-dek hero-dek--emphasis">
  Start with the baseline. Then we’ll show what actually reduces the carbon.
</p>

<br>

        <button class="cta-button" on:click={() => scrollToChapter(0)}>
          Start Exploring ↓
        </button>
      </div>
    </section>

    <!-- Chapter Sections -->
    <section bind:this={chapter1Element} class="chapter-section">
      <Chapter1 />
    </section>

    <section bind:this={chapter2Element} class="chapter-section">
      <Chapter2 />
    </section>

    <section bind:this={chapter3Element} class="chapter-section">
      <Chapter3 />
    </section>

    <section bind:this={chapter4Element} class="chapter-section">
      <Chapter4 />
    </section>

    <section bind:this={chapter5Element} class="chapter-section">
      <Chapter5 />
    </section>

    <section bind:this={chapter6Element} class="chapter-section">
      <Chapter6 />
    </section>

    <!-- Footer -->
    <footer class="footer">
      <div class="footer-content">
        <h3>Take Action</h3>
        <p>
          Now that you understand the true cost of commuting, it's time to make a change.
          Small decisions can lead to big impacts on your life and the planet.
        </p>

        <div class="footer-links">
          <button on:click={() => scrollToChapter(0)}>
            Revisit the Journey
          </button>

          <a href="https://data.census.gov/" target="_blank" rel="noopener noreferrer">
            Explore the Data
          </a>
        </div>

        <p class="footer-credit">
          Data sources: U.S. Census Bureau ACS, EPA, LEHD, BLS
        </p>
      </div>
    </footer>
  </main>
</div>

<style>
  :global(body) {
    margin: 0;
    padding: 0;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
    overflow-x: hidden;
  }

  .app {
    position: relative;
  }

  .main-content {
    margin-top: 120px; /* Account for fixed navigation */
  }

  /* HERO (VIDEO BACKGROUND) */
  .hero {
    min-height: calc(100vh - 120px);
    display: flex;
    align-items: center;
    justify-content: center;
    color: white;
    text-align: center;
    padding: 2rem;
    position: relative;
    overflow: hidden;
    background: #000; /* fallback */
  }

  .hero-video {
    position: absolute;
    inset: 0;
    width: 100%;
    height: 100%;
    object-fit: cover;
    object-position: center;
    z-index: 0;
    filter: saturate(0.9) contrast(1.05);
  }

  /* Overlay for readability + emotional mood */
  .hero-overlay {
    position: absolute;
    inset: 0;
    z-index: 1;
    background:
      radial-gradient(circle at 50% 40%, rgba(0,0,0,0.10), rgba(0,0,0,0.45)),
      linear-gradient(to bottom, rgba(0,0,0,0.20), rgba(0,0,0,0.60));
  }

  .hero-content {
    position: relative;
    z-index: 2;
    max-width: 900px;
  }

  .hero-title {
    font-size: clamp(2.6rem, 5vw, 4.2rem);
    margin-bottom: 1rem;
    font-weight: 800;
    line-height: 1.1;
    text-shadow: 0 6px 24px rgba(0,0,0,0.45);
  }

  .hero-subtitle {
    font-size: clamp(1.1rem, 2vw, 1.5rem);
    margin-bottom: 1rem;
    opacity: 0.95;
    line-height: 1.6;
    text-shadow: 0 6px 18px rgba(0,0,0,0.35);
  }

  .hero-dek {
    font-size: clamp(1rem, 1.5vw, 1.2rem);
    line-height: 1.8;
    margin-bottom: 1.5rem;
    opacity: 0.9;
    text-shadow: 0 4px 12px rgba(0,0,0,0.3);
  }

  .hero-dek--emphasis {
    font-weight: 600;
    font-size: clamp(1.1rem, 1.8vw, 1.4rem);
    opacity: 0.95;
  }

  .cta-button {
    padding: 1rem 3rem;
    font-size: 1.1rem;
    background: rgba(255, 255, 255, 0.92);
    color: #222;
    border: 1px solid rgba(255, 255, 255, 0.35);
    border-radius: 50px;
    cursor: pointer;
    font-weight: 800;
    transition: transform 0.25s ease, box-shadow 0.25s ease, background 0.25s ease;
    box-shadow: 0 10px 30px rgba(0, 0, 0, 0.35);
    backdrop-filter: blur(6px);
  }

  .cta-button:hover {
    transform: translateY(-2px);
    box-shadow: 0 14px 44px rgba(0, 0, 0, 0.45);
    background: rgba(255, 255, 255, 0.98);
  }

  .chapter-section {
    scroll-margin-top: 120px;
  }

  .footer {
    background: #2c3e50;
    color: white;
    padding: 4rem 2rem;
    text-align: center;
  }

  .footer-content {
    max-width: 800px;
    margin: 0 auto;
  }

  .footer-content h3 {
    font-size: 2rem;
    margin-bottom: 1rem;
  }

  .footer-content p {
    font-size: 1.1rem;
    line-height: 1.6;
    margin-bottom: 2rem;
  }

  .footer-links {
    display: flex;
    gap: 2rem;
    justify-content: center;
    margin-bottom: 2rem;
  }

  .footer-links button,
  .footer-links a {
    color: white;
    text-decoration: none;
    padding: 0.75rem 1.5rem;
    background: rgba(255, 255, 255, 0.1);
    border: none;
    border-radius: 8px;
    transition: background 0.3s;
    cursor: pointer;
    font-size: 1rem;
  }

  .footer-links button:hover,
  .footer-links a:hover {
    background: rgba(255, 255, 255, 0.2);
  }

  .footer-credit {
    font-size: 0.9rem;
    opacity: 0.7;
    margin-top: 2rem;
  }

  /* Respect reduced-motion users */
  @media (prefers-reduced-motion: reduce) {
    .hero-video {
      display: none;
    }

    .hero {
      background: #111;
    }
  }

  @media (max-width: 768px) {
    .main-content {
      margin-top: 100px;
    }

    .hero {
      min-height: calc(100vh - 100px);
    }

    .footer-links {
      flex-direction: column;
      gap: 1rem;
    }
  }
</style>