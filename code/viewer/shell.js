// Shared top bar for every viewer page. No back buttons: every page is one click away here.
// Usage: <script src="/shell.js"></script>, then  TALP.ready.then(({ run }) => ...)  and
// window.addEventListener("talp:run", (e) => e.detail.run)  when the user picks another run.
(() => {
  "use strict";
  const PAGES = [
    ["/", "Panorama"],
    ["/network.html", "Haberleşme"],
    ["/algorithms.html", "Algoritma"],
  ];
  const KEY = "talp.run";
  const store = {
    get() { try { return localStorage.getItem(KEY); } catch { return null; } },
    set(v) { try { localStorage.setItem(KEY, v); } catch { /* private mode */ } },
  };
  const here = location.pathname === "/index.html" ? "/" : location.pathname;
  const bar = document.createElement("header");
  bar.id = "topbar";
  bar.innerHTML = `<span class="brand">TALP <span>· Cobalt</span></span>
    <nav>${PAGES.map(([h, t]) => `<a href="${h}" class="${h === here ? "on" : ""}">${t}</a>`).join("")}</nav>
    <span class="spacer"></span>
    <select id="runpick" title="Hangi run gösterilsin"><option>Yükleniyor…</option></select>`;
  document.body.prepend(bar);

  const TALP = { run: null, runs: [] };
  window.TALP = TALP;
  const pick = bar.querySelector("#runpick");
  const label = (r) => r.id.replace(/^(runs|experiments)\//, "") + (r.type ? ` · ${r.type}` : "");
  TALP.setRun = (id, silent = false) => {
    TALP.run = id; store.set(id); pick.value = id;
    if (!silent) window.dispatchEvent(new CustomEvent("talp:run", { detail: { run: id } }));
  };
  TALP.ready = fetch("/api/runs", { cache: "no-store" }).then((r) => r.json()).then((d) => {
    TALP.runs = d.runs || [];
    TALP.targets = d.targets;
    const official = TALP.runs.filter((r) => r.id.startsWith("runs/"));
    const other = TALP.runs.filter((r) => !r.id.startsWith("runs/"));
    const opt = (r) => `<option value="${r.id}">${label(r)}</option>`;
    pick.innerHTML = TALP.runs.length
      ? (official.length ? `<optgroup label="Resmî run'lar">${official.map(opt).join("")}</optgroup>` : "")
        + (other.length ? `<optgroup label="Deneyler">${other.map(opt).join("")}</optgroup>` : "")
      : `<option value="">Run yok</option>`;
    const want = new URLSearchParams(location.search).get("run") || store.get();
    const first = (official.find((r) => r.type === "plan") || official[0] || TALP.runs[TALP.runs.length - 1] || {}).id || "";
    TALP.setRun(TALP.runs.some((r) => r.id === want) ? want : first, true);
    return { run: TALP.run, runs: TALP.runs };
  }).catch(() => { pick.innerHTML = `<option value="">API yok</option>`; return { run: null, runs: [] }; });
  pick.addEventListener("change", () => TALP.setRun(pick.value));
})();
