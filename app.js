(function () {
  "use strict";

  const data = window.PRESENTATION_DATA;
  const slides = Array.from(document.querySelectorAll(".slide"));
  const dots = Array.from(document.querySelectorAll(".chapter-dot"));
  const counter = document.getElementById("current-slide");
  const fullscreenButton = document.getElementById("fullscreen-button");
  const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)");

  function statusLabel(type, label) {
    const className = type === "verified"
      ? "data-status--verified"
      : type === "forecast"
        ? "data-status--forecast"
        : "data-status--pending";
    return `<span class="data-status ${className}">${label}</span>`;
  }

  function renderMetrics() {
    const grid = document.getElementById("metric-grid");
    grid.innerHTML = data.metrics.map((metric, index) => `
      <article class="metric-card reveal ${metric.type !== "pending" ? `metric-card--${metric.type}` : ""}">
        <div class="metric-card__top">${statusLabel(metric.type, metric.status)}<span>0${index + 1}</span></div>
        <strong data-countup>${metric.value}</strong>
        <p>${metric.label}</p>
        <small>${metric.source}</small>
      </article>
    `).join("");
  }

  function renderSeasonality() {
    const chart = document.getElementById("season-chart");
    chart.setAttribute("aria-label", data.seasonality.map((item) => `${item.label}: ${item.value}%`).join("; "));
    chart.innerHTML = data.seasonality.map((item) => `
      <div class="season-share season-share--${item.type}" style="--share:${item.value}" aria-label="${item.label}: ${item.value}%">
        <strong data-countup>${item.value}%</strong>
        <span>${item.label}</span>
      </div>
    `).join("");
  }

  function renderRides() {
    const grid = document.getElementById("ride-grid");
    grid.innerHTML = data.rides.map((ride) => `
      <article class="ride-card reveal">
        <div class="ride-card__media"><img src="${ride.image}" alt="${ride.alt}" loading="eager"><span>${ride.routeLabel}</span></div>
        <div class="ride-card__body">
          <h3>${ride.name}</h3>
          <p>${ride.summary}</p>
          <ul>${ride.facts.map((fact) => `<li data-countup>${fact}</li>`).join("")}</ul>
          <dl class="ride-card__operations">
            ${ride.operations.map((item) => `<div><dt>${item.label}</dt><dd data-countup>${item.value}</dd></div>`).join("")}
          </dl>
        </div>
      </article>
    `).join("");
  }

  function activateSlide(slide) {
    const index = slides.indexOf(slide);
    if (index < 0) return;
    slide.classList.add("has-entered");
    slides.forEach((item) => item.classList.toggle("is-active", item === slide));
    dots.forEach((dot, dotIndex) => {
      const active = dotIndex === index;
      dot.classList.toggle("is-active", active);
      if (active) dot.setAttribute("aria-current", "step");
      else dot.removeAttribute("aria-current");
    });
    counter.textContent = String(index + 1).padStart(2, "0");
    counter.classList.remove("is-changing");
    requestAnimationFrame(() => counter.classList.add("is-changing"));
    document.documentElement.style.setProperty("--deck-progress", `${((index + 1) / slides.length) * 100}%`);
  }

  function setupSlideObserver() {
    const observer = new IntersectionObserver((entries) => {
      const visible = entries
        .filter((entry) => entry.isIntersecting)
        .sort((a, b) => b.intersectionRatio - a.intersectionRatio)[0];
      if (visible) activateSlide(visible.target);
    }, { threshold: [0.08, 0.2, 0.35, 0.55, 0.75] });
    slides.forEach((slide) => observer.observe(slide));
  }

  function goToSlide(index) {
    const bounded = Math.max(0, Math.min(index, slides.length - 1));
    slides[bounded].scrollIntoView({ behavior: reducedMotion.matches ? "auto" : "smooth", block: "start" });
  }

  function setupNavigation() {
    dots.forEach((dot, index) => {
      dot.addEventListener("click", () => goToSlide(index));
    });

    document.addEventListener("keydown", (event) => {
      const tag = document.activeElement && document.activeElement.tagName;
      if (["INPUT", "TEXTAREA", "SELECT"].includes(tag)) return;
      const currentIndex = slides.findIndex((slide) => slide.classList.contains("is-active"));
      if (["ArrowDown", "ArrowRight", "PageDown", " "].includes(event.key)) {
        event.preventDefault();
        goToSlide(currentIndex + 1);
      }
      if (["ArrowUp", "ArrowLeft", "PageUp"].includes(event.key)) {
        event.preventDefault();
        goToSlide(currentIndex - 1);
      }
      if (event.key === "Home") goToSlide(0);
      if (event.key === "End") goToSlide(slides.length - 1);
      if (event.key.toLowerCase() === "f") toggleFullscreen();
    });
  }

  async function toggleFullscreen() {
    try {
      if (!document.fullscreenElement) await document.documentElement.requestFullscreen();
      else await document.exitFullscreen();
    } catch (error) {
      fullscreenButton.title = "Полноэкранный режим недоступен в этом браузере";
    }
  }

  function setupFullscreen() {
    fullscreenButton.addEventListener("click", toggleFullscreen);
    document.addEventListener("fullscreenchange", () => {
      const active = Boolean(document.fullscreenElement);
      fullscreenButton.setAttribute("aria-label", active ? "Выйти из полноэкранного режима" : "Открыть на весь экран");
      fullscreenButton.title = active ? "Выйти из полноэкранного режима" : "На весь экран";
      fullscreenButton.classList.toggle("is-active", active);
    });
  }

  function getCountDescriptor(element) {
    const finalText = element.textContent.trim();
    const match = finalText.match(/-?\d+(?:[ \u00a0]\d{3})*(?:[,.]\d+)?/u);
    if (!match) return null;

    const raw = match[0];
    const decimalSeparator = raw.includes(",") ? "," : raw.includes(".") ? "." : "";
    const decimalPlaces = decimalSeparator ? raw.split(decimalSeparator)[1].length : 0;
    const normalized = raw.replace(/[ \u00a0]/g, "").replace(",", ".");
    const target = Number(normalized);
    if (!Number.isFinite(target)) return null;

    return {
      finalText,
      target,
      prefix: finalText.slice(0, match.index),
      suffix: finalText.slice(match.index + raw.length),
      decimalSeparator,
      decimalPlaces,
      grouped: /[ \u00a0]/.test(raw),
      padded: decimalPlaces === 0 && /^0\d+/.test(raw),
      width: raw.length,
    };
  }

  function formatCount(value, descriptor) {
    if (descriptor.decimalPlaces) {
      const fixed = value.toFixed(descriptor.decimalPlaces);
      return descriptor.decimalSeparator === "," ? fixed.replace(".", ",") : fixed;
    }

    let formatted = String(Math.round(value));
    if (descriptor.grouped) formatted = formatted.replace(/\B(?=(\d{3})+(?!\d))/g, " ");
    if (descriptor.padded) formatted = formatted.padStart(descriptor.width, "0");
    return formatted;
  }

  function animateCount(element) {
    if (element.dataset.counted === "true") return;
    const descriptor = getCountDescriptor(element);
    if (!descriptor) return;

    element.dataset.counted = "true";
    element.setAttribute("aria-label", descriptor.finalText);
    if (reducedMotion.matches) {
      element.textContent = descriptor.finalText;
      return;
    }

    const startedAt = performance.now();
    const duration = 950;
    const render = (now) => {
      const progress = Math.min((now - startedAt) / duration, 1);
      const eased = 1 - Math.pow(1 - progress, 3);
      element.textContent = `${descriptor.prefix}${formatCount(descriptor.target * eased, descriptor)}${descriptor.suffix}`;
      if (progress < 1) requestAnimationFrame(render);
      else element.textContent = descriptor.finalText;
    };
    requestAnimationFrame(render);
  }

  function setupCountUps() {
    const targets = Array.from(document.querySelectorAll("[data-countup]"));
    if (reducedMotion.matches) {
      targets.forEach((element) => animateCount(element));
      return;
    }

    const observer = new IntersectionObserver((entries) => {
      entries.forEach((entry) => {
        if (!entry.isIntersecting) return;
        animateCount(entry.target);
        observer.unobserve(entry.target);
      });
    }, { threshold: 0.38, rootMargin: "0px 0px -7% 0px" });
    targets.forEach((element) => observer.observe(element));
  }

  function setupHeroVideo() {
    const video = document.getElementById("hero-video");
    const hero = document.getElementById("intro");
    if (!video || !hero) return;

    let heroIsVisible = true;

    const syncPlayback = () => {
      if (reducedMotion.matches || document.hidden || !heroIsVisible) {
        video.pause();
        return;
      }
      video.play().catch(() => {
        // The poster remains visible if a browser blocks autoplay.
      });
    };

    video.addEventListener("loadeddata", () => {
      video.classList.add("is-ready");
      syncPlayback();
    });

    const observer = new IntersectionObserver((entries) => {
      heroIsVisible = entries[0].isIntersecting;
      syncPlayback();
    }, { threshold: 0.2 });
    observer.observe(hero);

    document.addEventListener("visibilitychange", syncPlayback);
    if (typeof reducedMotion.addEventListener === "function") reducedMotion.addEventListener("change", syncPlayback);
    syncPlayback();
  }

  renderMetrics();
  renderSeasonality();
  renderRides();
  setupSlideObserver();
  setupNavigation();
  setupFullscreen();
  setupCountUps();
  setupHeroVideo();
  activateSlide(slides[0]);
})();
