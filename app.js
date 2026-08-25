(function () {
  "use strict";

  const data = window.PRESENTATION_DATA;
  const slides = Array.from(document.querySelectorAll(".slide"));
  const dots = Array.from(document.querySelectorAll(".chapter-dot"));
  const counter = document.getElementById("current-slide");
  const fullscreenButton = document.getElementById("fullscreen-button");
  const dataModal = document.getElementById("data-modal");

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
        <strong>${metric.value}</strong>
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
        <strong>${item.value}%</strong>
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
          <ul>${ride.facts.map((fact) => `<li>${fact}</li>`).join("")}</ul>
          <dl class="ride-card__operations">
            ${ride.operations.map((item) => `<div><dt>${item.label}</dt><dd>${item.value}</dd></div>`).join("")}
          </dl>
        </div>
      </article>
    `).join("");
  }

  function activateSlide(slide) {
    const index = slides.indexOf(slide);
    if (index < 0) return;
    slides.forEach((item) => item.classList.toggle("is-active", item === slide));
    dots.forEach((dot, dotIndex) => {
      const active = dotIndex === index;
      dot.classList.toggle("is-active", active);
      if (active) dot.setAttribute("aria-current", "step");
      else dot.removeAttribute("aria-current");
    });
    counter.textContent = String(index + 1).padStart(2, "0");
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
    slides[bounded].scrollIntoView({ behavior: "smooth", block: "start" });
  }

  function setupNavigation() {
    dots.forEach((dot) => {
      dot.addEventListener("click", () => document.getElementById(dot.dataset.target).scrollIntoView({ behavior: "smooth" }));
    });

    document.addEventListener("keydown", (event) => {
      const tag = document.activeElement && document.activeElement.tagName;
      if (["INPUT", "TEXTAREA", "SELECT"].includes(tag) || dataModal.open) return;
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

  function openModal(modal) {
    if (typeof modal.showModal === "function") modal.showModal();
  }

  function setupModals() {
    document.querySelectorAll("[data-open-data]").forEach((button) => button.addEventListener("click", () => openModal(dataModal)));
    document.querySelectorAll("[data-close-modal]").forEach((button) => button.addEventListener("click", () => button.closest("dialog").close()));
    [dataModal].forEach((modal) => {
      modal.addEventListener("click", (event) => {
        const rect = modal.getBoundingClientRect();
        const outside = event.clientX < rect.left || event.clientX > rect.right || event.clientY < rect.top || event.clientY > rect.bottom;
        if (outside) modal.close();
      });
    });
  }

  function setupHeroVideo() {
    const video = document.getElementById("hero-video");
    const hero = document.getElementById("intro");
    if (!video || !hero) return;

    const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)");
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
  setupModals();
  setupHeroVideo();
  activateSlide(slides[0]);
})();
