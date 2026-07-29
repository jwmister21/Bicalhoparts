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
