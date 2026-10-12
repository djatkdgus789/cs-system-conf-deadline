// Submissions (bars, left axis) and acceptance rate (line, right axis) per
// year, drawn into every <div class="acc-chart" data-series="..."> on the page.
// Data: _data/acceptance.yml, embedded below as ACCEPTANCE.
//
// The rate axis is fixed at 0-60% for every conference, so lines can be
// compared across rows; only the submissions axis scales per conference.
// A missing year is a gap in both bars and line, never a zero.

var ACCEPTANCE = {{ site.data.acceptance | jsonify }};

var ACC = {
  firstYear: 2017,
  lastYear: 2026,
  rateMax: 0.6,
  height: 112,          // svg height including the year labels
  margin: { top: 8, right: 48, bottom: 18, left: 48 },
  barMax: 14,
  svgNS: "http://www.w3.org/2000/svg"
};

function accEl(tag, attrs, parent) {
  var el = document.createElementNS(ACC.svgNS, tag);
  for (var k in attrs) el.setAttribute(k, attrs[k]);
  if (parent) parent.appendChild(el);
  return el;
}

function accCompact(n) {
  if (n >= 1000) return (Math.round(n / 100) / 10).toString().replace(/\.0$/, "") + "K";
  return String(n);
}

// Round the submissions axis up to a clean value with an even midpoint tick.
function accNiceMax(v) {
  var steps = [50, 100, 200, 300, 400, 500, 600, 800, 1000, 1200, 1500, 2000, 2500, 3000, 4000, 5000, 6000, 8000, 10000];
  for (var i = 0; i < steps.length; i++) if (v <= steps[i]) return steps[i];
  return Math.ceil(v / 2000) * 2000;
}

// A column with a 4px rounded data-end and a square baseline.
function accBarPath(x, y, w, h) {
  var r = Math.min(4, w / 2, h);
  return "M" + x + "," + (y + h) +
         "V" + (y + r) +
         "Q" + x + "," + y + " " + (x + r) + "," + y +
         "H" + (x + w - r) +
         "Q" + (x + w) + "," + y + " " + (x + w) + "," + (y + r) +
         "V" + (y + h) + "Z";
}

function accTooltip() {
  var tip = document.getElementById("acc-tooltip");
  if (!tip) {
    tip = document.createElement("div");
    tip.id = "acc-tooltip";
    tip.setAttribute("role", "tooltip");
    document.body.appendChild(tip);
  }
  return tip;
}

function accShowTip(evt, d) {
  var tip = accTooltip();
  tip.textContent = "";
  var head = document.createElement("div");
  head.className = "acc-tip-year";
  head.textContent = String(d.year);
  tip.appendChild(head);
  [["acc-key-bar", d.submitted.toLocaleString(), "submitted"],
   ["acc-key-line", (100 * d.accepted / d.submitted).toFixed(1) + "%", "accepted (" + d.accepted.toLocaleString() + ")"]
  ].forEach(function (row) {
    var line = document.createElement("div");
    line.className = "acc-tip-row";
    var key = document.createElement("span");
    key.className = "acc-tip-key " + row[0];
    var val = document.createElement("strong");
    val.textContent = row[1];
    var lab = document.createElement("span");
    lab.className = "acc-tip-label";
    lab.textContent = " " + row[2];
    line.appendChild(key); line.appendChild(val); line.appendChild(lab);
    tip.appendChild(line);
  });
  tip.style.display = "block";
  var r = evt.target.getBoundingClientRect();
  var left = window.scrollX + r.left + r.width / 2 - tip.offsetWidth / 2;
  left = Math.max(window.scrollX + 4, Math.min(left, window.scrollX + document.documentElement.clientWidth - tip.offsetWidth - 4));
  tip.style.left = left + "px";
  tip.style.top = (window.scrollY + r.top - tip.offsetHeight - 6) + "px";
}

function accHideTip() {
  var tip = document.getElementById("acc-tooltip");
  if (tip) tip.style.display = "none";
}

function drawAcceptanceChart(holder) {
  var series = holder.getAttribute("data-series");
  var rows = ACCEPTANCE[series];
  holder.textContent = "";

  if (!rows || !rows.length) {
    var none = document.createElement("div");
    none.className = "acc-empty";
    none.textContent = "No public acceptance data";
    holder.appendChild(none);
    return;
  }

  var byYear = {};
  rows.forEach(function (d) { byYear[d.year] = d; });
  var years = [];
  for (var y = ACC.firstYear; y <= ACC.lastYear; y++) years.push(y);

  // Legend above the plot: two series, so it is always shown.
  var legend = document.createElement("div");
  legend.className = "acc-legend";
  [["acc-key-bar", "Submitted"], ["acc-key-line", "Acceptance rate"]].forEach(function (item) {
    var span = document.createElement("span");
    var key = document.createElement("span");
    key.className = "acc-legend-key " + item[0];
    span.appendChild(key);
    span.appendChild(document.createTextNode(item[1]));
    legend.appendChild(span);
  });
  holder.appendChild(legend);

  var width = Math.max(220, holder.clientWidth || 300);
  var m = ACC.margin;
  var plotW = width - m.left - m.right;
  var plotH = ACC.height - m.top - m.bottom;
  var band = plotW / years.length;
  var barW = Math.min(ACC.barMax, band * 0.6);

  var maxSub = 0;
  rows.forEach(function (d) { if (d.submitted > maxSub) maxSub = d.submitted; });
  var subMax = accNiceMax(maxSub);
  var ySub = function (v) { return m.top + plotH - (v / subMax) * plotH; };
  var yRate = function (v) { return m.top + plotH - (Math.min(v, ACC.rateMax) / ACC.rateMax) * plotH; };
  var xMid = function (i) { return m.left + band * i + band / 2; };

  var latest = rows[rows.length - 1];
  var svg = accEl("svg", {
    width: width, height: ACC.height, viewBox: "0 0 " + width + " " + ACC.height,
    role: "img", "class": "acc-svg",
    "aria-label": series + ": submissions and acceptance rate, " + rows[0].year + "-" + latest.year +
      ". Latest: " + latest.submitted + " submitted, " + (100 * latest.accepted / latest.submitted).toFixed(1) + "% accepted."
  }, holder);

  // Hairline grid at the three shared tick positions; both axes tick at the
  // same heights (0, half, full) so there is one grid, not two.
  [0, 0.5, 1].forEach(function (f) {
    var gy = m.top + plotH - f * plotH;
    accEl("line", { x1: m.left, x2: m.left + plotW, y1: gy, y2: gy, "class": f === 0 ? "acc-baseline" : "acc-grid" }, svg);
    var l = accEl("text", { x: m.left - 5, y: gy + 3.5, "text-anchor": "end", "class": "acc-tick" }, svg);
    l.textContent = accCompact(Math.round(subMax * f));
    var r = accEl("text", { x: m.left + plotW + 5, y: gy + 3.5, "text-anchor": "start", "class": "acc-tick" }, svg);
    r.textContent = Math.round(ACC.rateMax * f * 100) + "%";
  });

  // Axis titles, written along each axis in muted ink (never the series
  // colour). With two y-axes, these and the legend are what say which scale
  // belongs to the bars and which to the line.
  var midY = m.top + plotH / 2;
  var yl = accEl("text", { x: 0, y: 0, "text-anchor": "middle", "class": "acc-axis-title",
    transform: "translate(9," + midY + ") rotate(-90)" }, svg);
  yl.textContent = "Submitted";
  var yr2 = accEl("text", { x: 0, y: 0, "text-anchor": "middle", "class": "acc-axis-title",
    transform: "translate(" + (width - 7) + "," + midY + ") rotate(90)" }, svg);
  yr2.textContent = "Acceptance rate";

  // Year labels: every year when there is room, otherwise every other one.
  var step = band >= 24 ? 1 : 2;
  years.forEach(function (yr, i) {
    if ((years.length - 1 - i) % step !== 0) return;
    var t = accEl("text", { x: xMid(i), y: ACC.height - 4, "text-anchor": "middle", "class": "acc-tick" }, svg);
    t.textContent = "'" + String(yr).slice(2);
  });

  // Bars: submissions.
  years.forEach(function (yr, i) {
    var d = byYear[yr];
    if (!d) return;
    var top = ySub(d.submitted);
    accEl("path", { d: accBarPath(xMid(i) - barW / 2, top, barW, m.top + plotH - top), "class": "acc-bar", "data-year": yr }, svg);
  });

  // Line: acceptance rate, broken at missing years.
  var seg = [];
  var flush = function () {
    if (seg.length > 1) accEl("polyline", { points: seg.join(" "), "class": "acc-line" }, svg);
    seg = [];
  };
  years.forEach(function (yr, i) {
    var d = byYear[yr];
    if (!d) { flush(); return; }
    seg.push(xMid(i) + "," + yRate(d.accepted / d.submitted));
  });
  flush();
  years.forEach(function (yr, i) {
    var d = byYear[yr];
    if (!d) return;
    accEl("circle", { cx: xMid(i), cy: yRate(d.accepted / d.submitted), r: 3.5, "class": "acc-dot" }, svg);
  });

  // One direct label: the latest rate, at the end of the line.
  var li = years.indexOf(latest.year);
  var lr = latest.accepted / latest.submitted;
  var lab = accEl("text", { x: xMid(li), y: yRate(lr) - 7, "text-anchor": "middle", "class": "acc-direct" }, svg);
  lab.textContent = Math.round(lr * 100) + "%";

  // Hover/focus targets: the whole year column, bigger than the marks.
  years.forEach(function (yr, i) {
    var d = byYear[yr];
    if (!d) return;
    // No <title> here: the browser would show it as a second tooltip. The
    // same numbers are in the table on each conference's detail page.
    var hit = accEl("rect", {
      x: m.left + band * i, y: m.top, width: band, height: plotH, "class": "acc-hit"
    }, svg);
    hit.addEventListener("pointerenter", function (e) {
      svg.querySelectorAll('.acc-bar[data-year="' + yr + '"]').forEach(function (b) { b.classList.add("acc-active"); });
      accShowTip(e, d);
    });
    hit.addEventListener("pointerleave", function () {
      svg.querySelectorAll(".acc-active").forEach(function (b) { b.classList.remove("acc-active"); });
      accHideTip();
    });
  });
}

function drawAllAcceptanceCharts() {
  document.querySelectorAll(".acc-chart").forEach(drawAcceptanceChart);
}
