/* Menu lateral. As abas passaram de 7 para 9 e a barra horizontal comecou a quebrar
   por cima do conteudo em tela estreita. O #tabBar continua sendo o mesmo elemento,
   entao o handler de troca de aba do ui_extras.js segue funcionando sem alteracao. */
(function () {
  "use strict";
  const btn = document.getElementById("navToggle");
  const bar = document.getElementById("tabBar");
  const scrim = document.getElementById("navScrim");
  if (!btn || !bar) return;

  function abrir(v) {
    document.body.classList.toggle("nav-open", v);
    btn.setAttribute("aria-expanded", v ? "true" : "false");
    if (scrim) scrim.hidden = !v;
  }
  btn.addEventListener("click", () => abrir(!document.body.classList.contains("nav-open")));
  if (scrim) scrim.addEventListener("click", () => abrir(false));
  bar.addEventListener("click", (e) => { if (e.target.closest(".tab")) abrir(false); });
  document.addEventListener("keydown", (e) => { if (e.key === "Escape") abrir(false); });
})();
