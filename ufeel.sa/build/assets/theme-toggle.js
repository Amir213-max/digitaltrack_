(function () {
  var root = document.documentElement;
  function apply(theme) {
    root.setAttribute("data-theme", theme);
    document.querySelectorAll("[data-theme-toggle]").forEach(function (btn) {
      var toDark = theme === "light";
      btn.setAttribute("aria-label", toDark ? "الوضع الداكن" : "الوضع الفاتح");
      btn.setAttribute("title", toDark ? "الوضع الداكن" : "الوضع الفاتح");
    });
    document.querySelectorAll('img[src*="digital-track-mark"], img[src*="digital-track-logo"]').forEach(function (img) {
      if (!img.dataset.logoBase) {
        img.dataset.logoBase = img.getAttribute("src").replace("digital-track-mark-lime.png", "digital-track-mark.png");
      }
      var base = img.dataset.logoBase;
      img.setAttribute(
        "src",
        theme === "dark"
          ? base.replace(/digital-track-(mark|logo)\.png/, "digital-track-mark-lime.png")
          : base
      );
    });
  }
  document.addEventListener("click", function (event) {
    var btn = event.target.closest("[data-theme-toggle]");
    if (!btn) return;
    var next = root.getAttribute("data-theme") === "dark" ? "light" : "dark";
    localStorage.setItem("dt-theme", next);
    apply(next);
  });
  apply(root.getAttribute("data-theme") || "light");
})();
