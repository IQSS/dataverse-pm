#!/usr/bin/env python3
"""Make the HTML charts in out/, starting with a stacked bar chart of PR merges per month by merger.

Run 'python3 merges.py report' first so out/merges.csv is current.
"""

import csv
import json
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
MERGES_CSV = HERE / "out" / "merges.csv"
OUT = HERE / "out" / "merges-per-month.html"

# git names that are the same person as a GitHub login
SAME = {"Ellen Kraffmiller": "ekraffmiller"}
DISPLAY = {
    "ofahimIQSS": "Omer Fahim",
    "pdurbin": "Philip Durbin",
    "stevenwinship": "Steven Winship",
    "sekmiller": "Stephen Kraffmiller",
    "landreev": "Leonid Andreev",
    "jp-tosca": "Juan Pablo Tosca",
    "poikilotherm": "Oliver Bertuch",
    "GPortas": "Guillermo Portas",
    "ekraffmiller": "Ellen Kraffmiller",
    "ErykKul": "Eryk Kulikowski",
}
TOP = 6
OTHER = "Other"
SQUASH = "squash merge"


def months(first, last):
    y, m = map(int, first.split("-"))
    out = []
    while f"{y:04d}-{m:02d}" <= last:
        out.append(f"{y:04d}-{m:02d}")
        m += 1
        if m == 13:
            y, m = y + 1, 1
    return out


def main():
    OUT.parent.mkdir(exist_ok=True)
    rows = list(csv.DictReader(MERGES_CSV.open()))
    for r in rows:
        r["merger"] = SAME.get(r["merger"], r["merger"])
    totals = Counter(r["merger"] for r in rows if r["merger"] != SQUASH)
    top = [name for name, _ in totals.most_common(TOP)]
    series = top + [OTHER, SQUASH]

    by_month = defaultdict(Counter)
    detail = defaultdict(Counter)
    for r in rows:
        mo = r["date"][:7]
        who = r["merger"]
        key = who if who in top or who == SQUASH else OTHER
        by_month[mo][key] += 1
        if key == OTHER:
            detail[mo][DISPLAY.get(who, who)] += 1

    ms = months(min(by_month), max(by_month))
    data = {
        "months": ms,
        "series": [{"key": s, "label": DISPLAY.get(s, s)} for s in series],
        "counts": {mo: {s: by_month[mo][s] for s in series} for mo in ms},
        "other": {mo: dict(detail[mo].most_common()) for mo in ms},
        "unknown": sum(1 for r in rows if r["merger"] == SQUASH),
        "total": len(rows),
    }
    for mode, out in (("bar", OUT), ("line", OUT.with_name("merges-per-month-line.html"))):
        html = TEMPLATE.replace("__DATA__", json.dumps(data)).replace("__MODE__", mode)
        out.write_text(html)
        print(f"Wrote {out}")

    # Small multiples: one panel per person (everyone gets their own line).
    per = defaultdict(Counter)
    for r in rows:
        per[r["merger"]][r["date"][:7]] += 1
    people = sorted((p for p in per if p != SQUASH), key=lambda p: -sum(per[p].values()))
    if SQUASH in per:
        people.append(SQUASH)
    small = {
        "months": ms,
        "panels": [{"label": DISPLAY.get(p, p),
                    "total": sum(per[p].values()), "squash": p == SQUASH,
                    "values": [per[p][mo] for mo in ms]} for p in people],
        "unknown": data["unknown"], "total": data["total"],
    }
    out = OUT.with_name("merges-per-month-people.html")
    out.write_text(SMALL.replace("__DATA__", json.dumps(small)))
    print(f"Wrote {out}")


SMALL = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Dataverse PR Mergers</title>
<style>
:root { color-scheme: light; --surface: #fcfcfb; --text-1: #0b0b0b; --text-2: #52514e; --text-3: #7a7974;
  --grid: #e6e5e1; --axis: #c9c8c2; --line: #2a78d6; --area: rgba(42,120,214,.12); --squash: #8f8e88; }
@media (prefers-color-scheme: dark) { :root:not([data-theme="light"]) { color-scheme: dark; --surface: #1a1a19;
  --text-1: #f0efec; --text-2: #c3c2b7; --text-3: #8f8e88; --grid: #2c2c2a; --axis: #4a4945; --line: #3987e5;
  --area: rgba(57,135,229,.18); --squash: #8f8e88; } }
:root[data-theme="dark"] { color-scheme: dark; --surface: #1a1a19; --text-1: #f0efec; --text-2: #c3c2b7;
  --text-3: #8f8e88; --grid: #2c2c2a; --axis: #4a4945; --line: #3987e5; --area: rgba(57,135,229,.18); --squash: #8f8e88; }
* { box-sizing: border-box; }
body { margin: 0; background: var(--surface); color: var(--text-1);
  font: 14px/1.45 -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; }
main { max-width: 1100px; margin: 0 auto; padding: 24px 16px 32px; }
h1 { font-size: 20px; margin: 0 0 4px; font-weight: 600; }
.sub { color: var(--text-2); margin: 0 0 16px; }
.grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(250px, 1fr)); gap: 18px 20px; }
.panel h2 { font-size: 13px; font-weight: 600; margin: 0; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.panel .stat { color: var(--text-3); font-size: 12px; margin: 0 0 2px; font-variant-numeric: tabular-nums; }
svg { display: block; width: 100%; height: auto; overflow: visible; }
.tick { fill: var(--text-3); font-size: 10px; }
</style>
</head>
<body>
<main>
  <h1>Who merged Dataverse pull requests, by month</h1>
  <p class="sub" id="sub"></p>
  <div class="grid" id="grid"></div>
</main>
<script>
const D = __DATA__;
const fmt = (m) => new Date(m + "-15").toLocaleString("en-US", { month: "short", year: "numeric" });
document.getElementById("sub").textContent =
  `${D.total.toLocaleString()} PRs merged into develop, ${fmt(D.months[0])} to ${fmt(D.months.at(-1))}. ` +
  `One panel per person, all on the same scale, ordered by total.` +
  (D.unknown ? ` ${D.unknown} squash merges not yet looked up are in the last panel.` : ``);
const max = Math.max(...D.panels.flatMap(p => p.values));
const yMax = Math.ceil(max / 10) * 10;
const W = 260, H = 110, m = { t: 6, r: 4, b: 18, l: 22 };
const iw = W - m.l - m.r, ih = H - m.t - m.b, n = D.months.length;
const x = i => m.l + (i / (n - 1)) * iw, y = v => m.t + ih - (v / yMax) * ih;
const grid = document.getElementById("grid");
D.panels.forEach(p => {
  let s = `<svg viewBox="0 0 ${W} ${H}" role="img" aria-label="${p.label}: ${p.total} PRs merged">`;
  [0, yMax / 2, yMax].forEach(v => {
    s += `<line x1="${m.l}" x2="${W - m.r}" y1="${y(v)}" y2="${y(v)}" stroke="${v ? 'var(--grid)' : 'var(--axis)'}"/>`;
    s += `<text class="tick" x="${m.l - 4}" y="${y(v) + 3}" text-anchor="end">${v}</text>`;
  });
  D.months.forEach((mo, i) => {
    if (mo.endsWith("-01")) s += `<text class="tick" x="${x(i)}" y="${H - 4}" text-anchor="middle">${mo.slice(0, 4)}</text>`;
  });
  const pts = p.values.map((v, i) => `${x(i).toFixed(1)},${y(v).toFixed(1)}`);
  const color = p.squash ? "var(--squash)" : "var(--line)";
  if (!p.squash) s += `<path d="M${x(0)},${y(0)} L${pts.join(" L")} L${x(n - 1)},${y(0)} Z" fill="var(--area)"/>`;
  s += `<path d="M${pts.join(" L")}" fill="none" stroke="${color}" stroke-width="2" stroke-linejoin="round"${p.squash ? ' stroke-dasharray="4 3"' : ''}/>`;
  const pk = p.values.indexOf(Math.max(...p.values));
  s += `<circle cx="${x(pk)}" cy="${y(p.values[pk])}" r="3" fill="${color}" stroke="var(--surface)" stroke-width="1.5"><title>Peak: ${p.values[pk]} in ${fmt(D.months[pk])}</title></circle>`;
  s += `</svg>`;
  grid.insertAdjacentHTML("beforeend",
    `<div class="panel"><h2>${p.label}</h2><p class="stat">${p.total} PR${p.total === 1 ? "" : "s"} · peak ${p.values[pk]} in ${fmt(D.months[pk])}</p>${s}</div>`);
});
</script>
</body>
</html>
"""


TEMPLATE = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Dataverse PR Merges</title>
<style>
:root {
  color-scheme: light;
  --surface: #fcfcfb; --text-1: #0b0b0b; --text-2: #52514e; --text-3: #7a7974;
  --grid: #e6e5e1; --axis: #c9c8c2;
  --s1: #2a78d6; --s2: #eb6834; --s3: #1baf7a; --s4: #eda100; --s5: #e87ba4; --s6: #008300;
  --other: #a3a29c; --squash: #d4d3ce; --hatch: #8f8e88;
  --tip-bg: #ffffff; --tip-border: #d9d8d3;
}
@media (prefers-color-scheme: dark) {
  :root:not([data-theme="light"]) {
    color-scheme: dark;
    --surface: #1a1a19; --text-1: #f0efec; --text-2: #c3c2b7; --text-3: #8f8e88;
    --grid: #2c2c2a; --axis: #4a4945;
    --s1: #3987e5; --s2: #d95926; --s3: #199e70; --s4: #c98500; --s5: #d55181; --s6: #008300;
    --other: #6b6a65; --squash: #3d3c39; --hatch: #8f8e88;
    --tip-bg: #252524; --tip-border: #3d3c39;
  }
}
:root[data-theme="dark"] {
  color-scheme: dark;
  --surface: #1a1a19; --text-1: #f0efec; --text-2: #c3c2b7; --text-3: #8f8e88;
  --grid: #2c2c2a; --axis: #4a4945;
  --s1: #3987e5; --s2: #d95926; --s3: #199e70; --s4: #c98500; --s5: #d55181; --s6: #008300;
  --other: #6b6a65; --squash: #3d3c39; --hatch: #8f8e88;
  --tip-bg: #252524; --tip-border: #3d3c39;
}
* { box-sizing: border-box; }
body { margin: 0; background: var(--surface); color: var(--text-1);
  font: 14px/1.45 -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; }
main { max-width: 1100px; margin: 0 auto; padding: 24px 16px 40px; }
h1 { font-size: 20px; margin: 0 0 4px; font-weight: 600; }
.sub { color: var(--text-2); margin: 0 0 16px; }
.legend { display: flex; flex-wrap: wrap; gap: 6px 16px; margin: 0 0 8px; padding: 0; list-style: none; }
.legend li { display: flex; align-items: center; gap: 6px; color: var(--text-2); font-size: 13px; }
.sw { width: 12px; height: 12px; border-radius: 3px; display: inline-block; }
.chart { position: relative; width: 100%; }
svg { display: block; width: 100%; height: auto; overflow: visible; }
.tick { fill: var(--text-3); font-size: 11px; }
.tip { position: absolute; pointer-events: none; background: var(--tip-bg); border: 1px solid var(--tip-border);
  border-radius: 8px; padding: 8px 10px; font-size: 12px; min-width: 170px; box-shadow: 0 4px 14px rgba(0,0,0,.12);
  opacity: 0; transition: opacity .1s; }
.tip b { display: block; margin-bottom: 4px; font-size: 13px; }
.tip .row { display: flex; align-items: center; gap: 6px; color: var(--text-2); }
.tip .row span:last-child { margin-left: auto; color: var(--text-1); font-variant-numeric: tabular-nums; }
.tip .note { color: var(--text-3); margin-top: 4px; }
details { margin-top: 20px; }
summary { cursor: pointer; color: var(--text-2); }
.tablewrap { overflow-x: auto; margin-top: 8px; }
table { border-collapse: collapse; font-size: 12px; font-variant-numeric: tabular-nums; }
th, td { padding: 3px 8px; text-align: right; border-bottom: 1px solid var(--grid); white-space: nowrap; }
th:first-child, td:first-child { text-align: left; }
th { color: var(--text-2); font-weight: 600; }
</style>
</head>
<body>
<main>
  <h1>Who merged Dataverse pull requests, by month</h1>
  <p class="sub" id="sub"></p>
  <ul class="legend" id="legend"></ul>
  <div class="chart" id="chart"><div class="tip" id="tip"></div></div>
  <details><summary>Show table</summary><div class="tablewrap" id="table"></div></details>
</main>
<script>
const D = __DATA__;
const colors = ["--s1","--s2","--s3","--s4","--s5","--s6","--other","--squash"];
const fill = (i) => i === 7 ? "url(#hatch)" : `var(${colors[i]})`;
const swatch = (i) => i === 7
  ? `background: var(--squash); background-image: repeating-linear-gradient(45deg, var(--hatch) 0 1px, transparent 1px 4px);`
  : `background: var(${colors[i]});`;
const fmtMonth = (m) => new Date(m + "-15").toLocaleString("en-US", { month: "short", year: "numeric" });

document.getElementById("sub").textContent =
  `${D.total.toLocaleString()} PRs merged into develop, ${fmtMonth(D.months[0])} to ${fmtMonth(D.months[D.months.length-1])}. ` +
  (D.unknown ? `${D.unknown} squash merges not yet looked up are shown as "squash merge".` : `Every squash merge has been looked up.`);

document.getElementById("legend").innerHTML = D.series.map((s, i) =>
  `<li><span class="sw" style="${swatch(i)}"></span>${s.label}</li>`).join("");

const W = 1060, H = 380, m = { t: 10, r: 8, b: 34, l: 34 };
const iw = W - m.l - m.r, ih = H - m.t - m.b;
const totals = D.months.map(mo => D.series.reduce((a, s) => a + D.counts[mo][s.key], 0));
const max = Math.max(...totals);
let step = max > 100 ? 25 : max > 40 ? 10 : 5;
let yMax = Math.ceil(max / step) * step;
const y = v => m.t + ih - (v / yMax) * ih;
const MODE = "__MODE__";
const bw = iw / D.months.length, gap = Math.max(2, bw * 0.22), barW = bw - gap;
if (MODE === "line") {
  // Lines share one scale with the busiest single series, not the stacked total.
  const lmax = Math.max(...D.months.flatMap(mo => D.series.map(s => D.counts[mo][s.key])));
  const lstep = lmax > 40 ? 10 : 5;
  window.__yMax = Math.ceil(lmax / lstep) * lstep;
  window.__step = lstep;
}

if (MODE === "line") { yMax = window.__yMax; step = window.__step; }
let s = `<svg viewBox="0 0 ${W} ${H}" role="img" aria-label="Stacked bar chart of PR merges per month by merger">
<defs><pattern id="hatch" width="5" height="5" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">
<rect width="5" height="5" fill="var(--squash)"/><line x1="0" y1="0" x2="0" y2="5" stroke="var(--hatch)" stroke-width="1.2"/></pattern></defs>`;
for (let v = 0; v <= yMax; v += step) {
  s += `<line x1="${m.l}" x2="${W - m.r}" y1="${y(v)}" y2="${y(v)}" stroke="${v ? 'var(--grid)' : 'var(--axis)'}" stroke-width="1"/>`;
  s += `<text class="tick" x="${m.l - 6}" y="${y(v) + 4}" text-anchor="end">${v}</text>`;
}
D.months.forEach((mo, i) => {
  const x = m.l + i * bw + gap / 2;
  let base = 0;
  const segs = D.series.map((ser, k) => ({ k, v: D.counts[mo][ser.key] })).filter(d => d.v > 0);
  if (MODE === "bar") segs.forEach((d, j) => {
    const top = j === segs.length - 1;
    const y0 = y(base), y1 = y(base + d.v);
    const h = Math.max(0, y0 - y1 - (j > 0 ? 2 : 0));
    const yy = y1;
    if (top && h > 4) {
      const r = Math.min(4, barW / 2);
      s += `<path d="M${x},${yy + h} V${yy + r} Q${x},${yy} ${x + r},${yy} H${x + barW - r} Q${x + barW},${yy} ${x + barW},${yy + r} V${yy + h} Z" fill="${fill(d.k)}"/>`;
    } else {
      s += `<rect x="${x}" y="${yy}" width="${barW}" height="${h}" fill="${fill(d.k)}"/>`;
    }
    base += d.v;
  });
  const [yr, mn] = mo.split("-");
  if (mn === "01" || i === 0) {
    s += `<text class="tick" x="${x + barW / 2}" y="${H - m.b + 15}" text-anchor="middle">${yr}</text>`;
  }
  if (["01","04","07","10"].includes(mn) || i === 0) {
    s += `<text class="tick" x="${x + barW / 2}" y="${H - m.b + 28}" text-anchor="middle" style="font-size:10px">${new Date(mo + "-15").toLocaleString("en-US",{month:"short"})}</text>`;
  }
  s += `<rect class="hit" data-i="${i}" x="${m.l + i * bw}" y="${m.t}" width="${bw}" height="${ih}" fill="transparent"/>`;
});
if (MODE === "line") {
  const cx = i => m.l + i * bw + bw / 2;
  // Draw "Other" and "squash merge" first so people's lines sit on top.
  const order = D.series.map((_, k) => k).sort((a, b) => (b >= 6) - (a >= 6));
  order.forEach(k => {
    const ser = D.series[k];
    const pts = D.months.map((mo, i) => `${cx(i).toFixed(1)},${y(D.counts[mo][ser.key]).toFixed(1)}`).join(" L");
    const stroke = k === 7 ? "var(--hatch)" : `var(${colors[k]})`;
    const dash = k === 7 ? ` stroke-dasharray="4 3"` : "";
    s += `<path d="M${pts}" fill="none" stroke="var(--surface)" stroke-width="5" stroke-linejoin="round"/>`;
    s += `<path d="M${pts}" fill="none" stroke="${stroke}" stroke-width="2" stroke-linejoin="round" stroke-linecap="round"${dash}/>`;
  });
  s += `<line id="cross" x1="0" x2="0" y1="${m.t}" y2="${m.t + ih}" stroke="var(--axis)" stroke-width="1" opacity="0"/>`;
}
s += `</svg>`;
const chart = document.getElementById("chart");
chart.insertAdjacentHTML("beforeend", s);

const tip = document.getElementById("tip");
chart.querySelectorAll(".hit").forEach(el => {
  el.addEventListener("mouseenter", () => {
    const i = +el.dataset.i, mo = D.months[i];
    let h = `<b>${fmtMonth(mo)} · ${totals[i]} PRs</b>`;
    D.series.forEach((ser, k) => {
      const v = D.counts[mo][ser.key];
      if (v) h += `<div class="row"><span class="sw" style="${swatch(k)}"></span><span>${ser.label}</span><span>${v}</span></div>`;
    });
    const o = D.other[mo];
    if (o && Object.keys(o).length) h += `<div class="note">Other: ${Object.entries(o).map(([n, c]) => `${n} ${c}`).join(", ")}</div>`;
    tip.innerHTML = h;
    tip.style.opacity = 1;
    const cross = document.getElementById("cross");
    if (cross) { const x = m.l + i * bw + bw / 2; cross.setAttribute("x1", x); cross.setAttribute("x2", x); cross.setAttribute("opacity", 1); }
  });
  el.addEventListener("mousemove", (e) => {
    const r = chart.getBoundingClientRect();
    let left = e.clientX - r.left + 14;
    if (left + tip.offsetWidth > r.width) left = e.clientX - r.left - tip.offsetWidth - 14;
    tip.style.left = left + "px";
    tip.style.top = Math.max(0, e.clientY - r.top - 20) + "px";
  });
  el.addEventListener("mouseleave", () => {
    tip.style.opacity = 0;
    const cross = document.getElementById("cross");
    if (cross) cross.setAttribute("opacity", 0);
  });
});

let t = `<table><thead><tr><th>Month</th>${D.series.map(s => `<th>${s.label}</th>`).join("")}<th>Total</th></tr></thead><tbody>`;
D.months.forEach((mo, i) => {
  t += `<tr><td>${fmtMonth(mo)}</td>${D.series.map(s => `<td>${D.counts[mo][s.key] || ""}</td>`).join("")}<td>${totals[i]}</td></tr>`;
});
document.getElementById("table").innerHTML = t + "</tbody></table>";
</script>
</body>
</html>
"""

if __name__ == "__main__":
    main()
