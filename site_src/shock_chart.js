
  /* ---------- 5 Nov selloff: S&P after one-day drops of 3.5% or more ---------- */
  var SHOCK = JSON.parse(document.getElementById("shock-data").textContent);
  var SK = { "1m": "1 month", "3m": "3 months", "6m": "6 months", "12m": "12 months" };
  var sKey = "6m";
  var ROWS = [
    { above: true, lab: "S&P still above its 200-day average after the drop", cls: "dot-a" },
    { above: false, lab: "S&P below its 200-day average after the drop", cls: "dot-b" }
  ];
  function median(a) {
    var s = a.slice().sort(function (p, q) { return p - q; }), n = s.length;
    return n % 2 ? s[(n - 1) / 2] : (s[n / 2 - 1] + s[n / 2]) / 2;
  }
  function fmtDay(iso) {
    var p = iso.split("-");
    return +p[2] + " " + MON[+p[1] - 1] + " " + p[0];
  }

  var stb = document.querySelector("#shock-table tbody");
  SHOCK.forEach(function (e) {
    var tr = document.createElement("tr");
    tr.innerHTML = '<td class="nw">' + fmtDay(e.date) + '</td><td class="r nw">' + pct(e.ret) + "</td><td>" +
      (e.above ? "Above" : "Below") + "</td>" +
      ["1m", "3m", "6m", "12m"].map(function (k) { return '<td class="r nw">' + (e[k] == null ? "–" : pct(e[k])) + "</td>"; }).join("") +
      '<td class="r nw">' + pct(e.dd3m) + "</td>";
    stb.appendChild(tr);
  });

  function drawShock() {
    var box = document.getElementById("shock-chart");
    box.innerHTML = "";
    var W = box.clientWidth, narrow = W < 560;
    var r = 5, rowH = narrow ? 92 : 84, labH = 22;
    var m = { t: 6, r: 12, b: 28, l: 12 };
    var H = m.t + ROWS.length * (labH + rowH) + m.b;
    var iw = W - m.l - m.r;
    var vals = SHOCK.map(function (e) { return e[sKey]; }).filter(function (v) { return v != null; });
    var step = sKey === "1m" ? 5 : 10;
    var lo = Math.min(0, Math.floor(Math.min.apply(null, vals) / step) * step);
    var hi = Math.max(step, Math.ceil(Math.max.apply(null, vals) / step) * step);
    function x(v) { return m.l + (v - lo) / (hi - lo) * iw; }
    var svg = el("svg", { width: W, height: H, viewBox: "0 0 " + W + " " + H, role: "img",
      "aria-label": "S&P 500 return " + SK[sKey] + " after each one-day drop of 3.5% or more since 1950, split by the 200-day trend" }, box);
    var yAxis = H - m.b;
    var every = narrow && (hi - lo) / step > 8 ? 2 : 1;
    for (var t = lo, k = 0; t <= hi + 1e-9; t += step, k++) {
      el("line", { x1: x(t), x2: x(t), y1: m.t, y2: yAxis, "class": t === 0 ? "axis" : "grid" }, svg);
      if (k % every === 0 || t === 0) {
        el("text", { x: x(t), y: H - 8, "text-anchor": "middle", "class": "tick" }, svg, (t > 0 ? "+" : t < 0 ? "−" : "") + Math.abs(t) + "%");
      }
    }
    var sums = [];
    ROWS.forEach(function (row, ri) {
      var top = m.t + ri * (labH + rowH);
      var mid = top + labH + rowH / 2;
      el("text", { x: m.l, y: top + 15, "class": "row-lab" }, svg, row.lab);
      var pts = SHOCK.filter(function (e) { return e.above === row.above && e[sKey] != null; })
        .map(function (e) { return { e: e, x: x(e[sKey]), y: mid }; })
        .sort(function (p, q) { return p.x - q.x; });
      /* simple beeswarm: nearest free slot above or below the centre line */
      var placed = [], gap = 2 * r + 2, maxOff = rowH / 2 - r - 2;
      pts.forEach(function (p) {
        for (var j = 0; j < 40; j++) {
          var off = (j % 2 ? 1 : -1) * Math.ceil(j / 2) * (gap * 0.55);
          if (Math.abs(off) > maxOff) { off = 0; break; }
          var ok = placed.every(function (q) { var dx = q.x - p.x, dy = q.y - (mid + off); return dx * dx + dy * dy >= gap * gap; });
          if (ok) { p.y = mid + off; break; }
        }
        placed.push(p);
      });
      var md = median(pts.map(function (p) { return p.e[sKey]; }));
      el("line", { x1: x(md), x2: x(md), y1: top + labH + 2, y2: top + labH + rowH - 2, "class": "med" }, svg);
      var anchorEnd = x(md) > W - 110;
      el("text", { x: x(md) + (anchorEnd ? -6 : 6), y: top + labH + 12, "text-anchor": anchorEnd ? "end" : "start", "class": "val" }, svg,
        "median " + pct(md));
      pts.forEach(function (p) {
        p.dot = el("circle", { cx: p.x, cy: p.y, r: r, "class": row.cls }, svg);
      });
      pts.forEach(function (p) {
        var hit = el("circle", { cx: p.x, cy: p.y, r: 10, "class": "hit" }, svg);
        function show(ev) {
          p.dot.classList.add("hov");
          var e = p.e;
          showTip("<b>" + fmtDay(e.date) + "</b><span class=\"tip-sub\">S&amp;P " + pct(e.ret) + " that day · " +
            (e.above ? "still above" : "below") + " its 200-day average</span><table>" +
            [["1 month", "1m"], ["3 months", "3m"], ["6 months", "6m"], ["12 months", "12m"]].map(function (q) {
              return "<tr><td>" + q[0] + '</td><td class="r">' + (e[q[1]] == null ? "–" : pct(e[q[1]])) + "</td></tr>";
            }).join("") + "<tr><td>Further fall within 3m</td><td class=\"r\">" + pct(e.dd3m) + "</td></tr></table>", ev.clientX, ev.clientY);
        }
        hit.addEventListener("pointermove", show);
        hit.addEventListener("pointerdown", show);
        hit.addEventListener("pointerleave", function () { p.dot.classList.remove("hov"); hideTip(); });
      });
      var pos = pts.filter(function (p) { return p.e[sKey] > 0; }).length;
      var worst = Math.min.apply(null, pts.map(function (p) { return p.e[sKey]; }));
      sums.push((row.above ? "Above the 200-day: " : "Below it: ") + pos + " of " + pts.length + " higher, median " + pct(md) + ", worst " + pct(worst));
    });
    document.getElementById("shock-sum").textContent = "After " + SK[sKey] + ". " + sums.join(". ") + ".";
  }

  document.querySelectorAll("#selloff .seg button").forEach(function (b) {
    b.addEventListener("click", function () {
      sKey = b.getAttribute("data-k");
      document.querySelectorAll("#selloff .seg button").forEach(function (o) { o.setAttribute("aria-pressed", String(o === b)); });
      drawShock();
    });
  });
