document.addEventListener("DOMContentLoaded", () => {
  const menuButton = document.querySelector("[data-menu-button]");
  const menu = document.querySelector("[data-menu]");

  if (menuButton && menu) {
    menuButton.addEventListener("click", () => menu.classList.toggle("open"));
    menu.querySelectorAll("a").forEach(link => {
      link.addEventListener("click", () => menu.classList.remove("open"));
    });
  }

  const search = document.getElementById("product-search");
  const cards = [...document.querySelectorAll(".product-card")];
  const filters = [...document.querySelectorAll("[data-filter]")];
  const noResults = document.getElementById("no-results");
  let activeCategory = "all";

  function applyFilters() {
    if (!cards.length) return;
    const term = (search?.value || "").toLowerCase().trim();
    let visible = 0;

    cards.forEach(card => {
      const matchesName = card.dataset.name.includes(term);
      const matchesCategory =
        activeCategory === "all" || card.dataset.category === activeCategory;
      const show = matchesName && matchesCategory;
      card.hidden = !show;
      if (show) visible++;
    });

    if (noResults) noResults.hidden = visible !== 0;
  }

  search?.addEventListener("input", applyFilters);

  filters.forEach(button => {
    button.addEventListener("click", () => {
      filters.forEach(item => item.classList.remove("active"));
      button.classList.add("active");
      activeCategory = button.dataset.filter;
      applyFilters();
    });
  });

  document.querySelectorAll("[data-category-link]").forEach(link => {
    link.addEventListener("click", () => {
      activeCategory = link.dataset.categoryLink;
      filters.forEach(item => {
        item.classList.toggle("active", item.dataset.filter === activeCategory);
      });
      setTimeout(applyFilters, 50);
    });
  });
});
document.addEventListener("DOMContentLoaded", function () {
  const widget = document.querySelector("[data-whatsapp-widget]");
  const popup = document.querySelector("[data-whatsapp-popup]");
  const closeButton = document.querySelector("[data-whatsapp-close]");
  const floatingButton = document.querySelector("[data-whatsapp-button]");

  if (!widget || !popup || !closeButton || !floatingButton) {
    return;
  }

  const storageKey = "bicalhoWhatsappPopupClosedAt";
  const oneDayInMilliseconds = 24 * 60 * 60 * 1000;

  function wasClosedRecently() {
    const closedAt = localStorage.getItem(storageKey);

    if (!closedAt) {
      return false;
    }

    const elapsedTime = Date.now() - Number(closedAt);

    return elapsedTime < oneDayInMilliseconds;
  }

  function showPopup() {
    popup.classList.add("is-visible");
  }

  function hidePopup() {
    popup.classList.remove("is-visible");
  }

  if (!wasClosedRecently()) {
    window.setTimeout(showPopup, 2500);
  }

  closeButton.addEventListener("click", function () {
    hidePopup();
    localStorage.setItem(storageKey, String(Date.now()));
  });

  floatingButton.addEventListener("mouseenter", function () {
    showPopup();
  });

  floatingButton.addEventListener("focus", function () {
    showPopup();
  });

  document.addEventListener("keydown", function (event) {
    if (event.key === "Escape") {
      hidePopup();
    }
  });
});
