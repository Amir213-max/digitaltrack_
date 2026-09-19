import { t as initReveal } from "./section-reveal-zVdRusEw.js";

var sections = [".about-hero", ".industries-grid", ".industries-deep", ".contact-cta"];

function boot() {
  sections.forEach((sel) => initReveal(sel));
}

document.addEventListener("DOMContentLoaded", boot);
