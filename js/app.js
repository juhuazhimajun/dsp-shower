/* 两个互动图：
   ① s→z 映射（拖极点，看四种映射把它搬到哪）
   ② 双线性低通的幅频响应（改 Ωp / 阶数 / 是否预扭曲）
   纯 canvas，无外部依赖。 */
(function () {
  "use strict";

  var $ = function (s) { return document.querySelector(s); };

  /* ============================== 通用画布工具 ============================== */
  function fit(cv, h) {
    var dpr = Math.max(1, window.devicePixelRatio || 1);
    var w = cv.clientWidth || 520;
    cv.width = Math.round(w * dpr);
    cv.height = Math.round(h * dpr);
    cv.style.height = h + "px";
    var ctx = cv.getContext("2d");
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    ctx.clearRect(0, 0, w, h);
    return { ctx: ctx, w: w, h: h };
  }

  function star(ctx, x, y, r, fill) {
    ctx.save();
    ctx.beginPath();
    for (var i = 0; i < 10; i++) {
      var ang = -Math.PI / 2 + i * Math.PI / 5;
      var rr = (i % 2) ? r * 0.45 : r;
      var px = x + Math.cos(ang) * rr, py = y + Math.sin(ang) * rr;
      if (i) ctx.lineTo(px, py); else ctx.moveTo(px, py);
    }
    ctx.closePath();
    ctx.fillStyle = fill;
    ctx.fill();
    ctx.strokeStyle = "#0f172a";
    ctx.lineWidth = 1.2;
    ctx.stroke();
    ctx.restore();
  }

  function line(ctx, x1, y1, x2, y2, color, lw, dash) {
    ctx.save();
    ctx.beginPath();
    ctx.setLineDash(dash || []);
    ctx.strokeStyle = color;
    ctx.lineWidth = lw;
    ctx.moveTo(x1, y1);
    ctx.lineTo(x2, y2);
    ctx.stroke();
    ctx.restore();
  }

  /* ============================== ① s→z 映射 ============================== */
  var S = { sigma: -0.5, omega: 1.6, T: 1.0, focus: "bil" };

  var M = {
    imp: {
      name: "脉冲响应不变", color: "#d97706", expr: "z = e^{sT}",
      f: function (s, T) {
        var r = Math.exp(s.sigma * T), th = s.omega * T;
        return { re: r * Math.cos(th), im: r * Math.sin(th) };
      }
    },
    fwd: {
      name: "前向差分", color: "#dc2626", expr: "z = 1 + sT",
      f: function (s, T) { return { re: 1 + s.sigma * T, im: s.omega * T }; }
    },
    bwd: {
      name: "后向差分", color: "#7c3aed", expr: "z = 1/(1 − sT)",
      f: function (s, T) {
        var a = 1 - s.sigma * T, b = s.omega * T, d = a * a + b * b;
        return { re: a / d, im: b / d };
      }
    },
    bil: {
      name: "双线性", color: "#0f766e", expr: "z = (1 + sT/2)/(1 − sT/2)",
      f: function (s, T) {
        var a = s.sigma * T / 2, b = s.omega * T / 2;
        var d = (1 - a) * (1 - a) + b * b;
        return { re: (1 - a * a - b * b) / d, im: 2 * b / d };
      }
    }
  };
  var ORDER = ["imp", "fwd", "bwd", "bil"];

  var SDOM = { x0: -3.4, x1: 1.8, y0: -4.4, y1: 4.4 };

  function s2px(p, box) {
    return {
      x: box.ml + (p.sigma - SDOM.x0) / (SDOM.x1 - SDOM.x0) * (box.w - box.ml - box.mr),
      y: box.h - box.mb - (p.omega - SDOM.y0) / (SDOM.y1 - SDOM.y0) * (box.h - box.mt - box.mb)
    };
  }
  function px2s(px, py, box) {
    var sigma = SDOM.x0 + (px - box.ml) / (box.w - box.ml - box.mr) * (SDOM.x1 - SDOM.x0);
    var omega = SDOM.y0 + (box.h - box.mb - py) / (box.h - box.mt - box.mb) * (SDOM.y1 - SDOM.y0);
    return {
      sigma: Math.max(SDOM.x0, Math.min(SDOM.x1, sigma)),
      omega: Math.max(SDOM.y0, Math.min(SDOM.y1, omega))
    };
  }

  var sCv = $("#sPlane"), zCv = $("#zPlane");
  var sBox = null;

  function drawSPlane() {
    if (!sCv) return null;
    var c = fit(sCv, 420), ctx = c.ctx;
    var box = { w: c.w, h: c.h, ml: 44, mr: 12, mt: 14, mb: 30 };
    sBox = box;

    // 左半平面淡绿
    var p0 = s2px({ sigma: SDOM.x0, omega: SDOM.y0 }, box);
    var p1 = s2px({ sigma: 0, omega: SDOM.y1 }, box);
    ctx.fillStyle = "#f0fdf4";
    ctx.fillRect(p0.x, p1.y, p1.x - p0.x, p0.y - p1.y);
    ctx.fillStyle = "#fff5f5";
    ctx.fillRect(p1.x, p1.y, box.w - box.mr - p1.x, p0.y - p1.y);

    // 网格
    for (var gx = -3; gx <= 1; gx++) {
      var a = s2px({ sigma: gx, omega: SDOM.y0 }, box);
      var b = s2px({ sigma: gx, omega: SDOM.y1 }, box);
      line(ctx, a.x, a.y, b.x, b.y, "#e8ecf3", 1);
      ctx.fillStyle = "#94a3b8";
      ctx.font = "11px system-ui";
      ctx.textAlign = "center";
      ctx.fillText(gx.toString(), a.x, box.h - box.mb + 15);
    }
    for (var gy = -4; gy <= 4; gy++) {
      var a2 = s2px({ sigma: SDOM.x0, omega: gy }, box);
      var b2 = s2px({ sigma: SDOM.x1, omega: gy }, box);
      line(ctx, a2.x, a2.y, b2.x, b2.y, "#e8ecf3", 1);
      ctx.fillStyle = "#94a3b8";
      ctx.textAlign = "right";
      ctx.fillText(gy.toString(), box.ml - 7, a2.y + 4);
    }
    var ax = s2px({ sigma: 0, omega: 0 }, box);
    line(ctx, box.ml, ax.y, box.w - box.mr, ax.y, "#94a3b8", 1.2);
    line(ctx, ax.x, box.mt, ax.x, box.h - box.mb, "#94a3b8", 1.2);
    ctx.fillStyle = "#64748b";
    ctx.font = "12px system-ui";
    ctx.textAlign = "left";
    ctx.fillText("σ", box.w - box.mr - 12, ax.y - 7);
    ctx.fillText("jω", ax.x + 7, box.mt + 12);
    ctx.fillStyle = "#15803d";
    ctx.fillText("模拟稳定区", box.ml + 8, box.mt + 16);

    // 共轭极点（灰） + 主极点（黑星）
    var p = { sigma: S.sigma, omega: S.omega };
    var q = { sigma: S.sigma, omega: -S.omega };
    var pq = s2px(q, box);
    ctx.save();
    ctx.beginPath();
    ctx.arc(pq.x, pq.y, 5, 0, 2 * Math.PI);
    ctx.strokeStyle = "#cbd5e1";
    ctx.lineWidth = 1.6;
    ctx.stroke();
    ctx.restore();

    var pp = s2px(p, box);
    star(ctx, pp.x, pp.y, 11, "#111827");
    ctx.fillStyle = "#111827";
    ctx.font = "12px ui-monospace, Consolas, monospace";
    ctx.textAlign = "left";
    ctx.fillText("σ=" + S.sigma.toFixed(2) + ", ω=" + S.omega.toFixed(2), pp.x + 14, pp.y - 12);

    return box;
  }

  function drawZPlane() {
    if (!zCv) return null;
    var c = fit(zCv, 420), ctx = c.ctx;
    var m = 26;
    var unit = Math.min((c.w - 2 * m) / 3.9, (c.h - 2 * m) / 3.9);
    var cx = c.w / 2, cy = c.h / 2;
    var Z = function (z) { return { x: cx + z.re * unit, y: cy - z.im * unit }; };

    // 背景网格
    ctx.save();
    ctx.strokeStyle = "#eef1f6";
    ctx.lineWidth = 1;
    for (var k = -2; k <= 2; k++) {
      ctx.beginPath(); ctx.moveTo(cx + k * unit, m); ctx.lineTo(cx + k * unit, c.h - m); ctx.stroke();
      ctx.beginPath(); ctx.moveTo(m, cy + k * unit); ctx.lineTo(c.w - m, cy + k * unit); ctx.stroke();
    }
    ctx.restore();

    // 焦点方法的「左半平面去向」点云
    var f = M[S.focus].f;
    var NS = 33, NO = 47;
    var omMax = 1.15 * Math.PI / S.T;     // 扫到 ±115% 的 Nyquist，让「绕圈重叠」看得见
    for (var i = 0; i < NS; i++) {
      var sg = -3.4 + 4.6 * i / (NS - 1);
      for (var j = 0; j < NO; j++) {
        var om = -omMax + 2 * omMax * j / (NO - 1);
        var zz = f({ sigma: sg, omega: om }, S.T);
        if (!isFinite(zz.re) || !isFinite(zz.im)) continue;
        if (Math.abs(zz.re) > 3.2 || Math.abs(zz.im) > 3.2) continue;
        var q = Z(zz);
        ctx.fillStyle = sg < 0 ? "rgba(22,163,74,0.22)" : "rgba(220,38,38,0.16)";
        ctx.fillRect(q.x - 1.2, q.y - 1.2, 2.4, 2.4);
      }
    }

    // 坐标轴
    ctx.strokeStyle = "#94a3b8"; ctx.lineWidth = 1.2;
    ctx.beginPath(); ctx.moveTo(m, cy); ctx.lineTo(c.w - m, cy); ctx.stroke();
    ctx.beginPath(); ctx.moveTo(cx, m); ctx.lineTo(cx, c.h - m); ctx.stroke();

    // 单位圆
    ctx.save();
    ctx.beginPath();
    ctx.arc(cx, cy, unit, 0, 2 * Math.PI);
    ctx.fillStyle = "rgba(15,118,110,0.03)";
    ctx.fill();
    ctx.strokeStyle = "#0f172a";
    ctx.lineWidth = 1.6;
    ctx.stroke();
    ctx.restore();
    ctx.fillStyle = "#475569";
    ctx.font = "11px system-ui";
    ctx.fillText("|z| = 1", cx + unit * 0.72, cy - unit * 0.72);

    // 四个映射的落点
    var p = { sigma: S.sigma, omega: S.omega };
    var labels = [];
    for (var t = 0; t < ORDER.length; t++) {
      var key = ORDER[t], mm = M[key], z2 = mm.f(p, S.T);
      var q2 = Z(z2);
      var inside = Math.hypot(z2.re, z2.im) < 1;
      var cls = (S.sigma < 0)
        ? (inside ? "ok" : "bad")
        : (inside ? "bad" : "ok");

      ctx.save();
      ctx.beginPath();
      ctx.arc(q2.x, q2.y, 6.5, 0, 2 * Math.PI);
      ctx.fillStyle = "#fff";
      ctx.fill();
      ctx.strokeStyle = mm.color;
      ctx.lineWidth = 2.6;
      ctx.stroke();
      ctx.restore();

      labels.push({ key: key, z: z2, inside: inside, cls: cls });
    }

    // 图例：固定在左上角，避免四个标签互相压住
    var lx = 10, ly = 10, lw = Math.min(190, c.w * 0.46), lh = 4 * 18 + 12;
    ctx.save();
    ctx.beginPath();
    if (ctx.roundRect) ctx.roundRect(lx, ly, lw, lh, 9); else ctx.rect(lx, ly, lw, lh);
    ctx.fillStyle = "rgba(255,255,255,0.94)";
    ctx.fill();
    ctx.strokeStyle = "#e2e8f0";
    ctx.lineWidth = 1;
    ctx.stroke();
    ctx.restore();

    ctx.textAlign = "left";
    ctx.font = "12px system-ui, 'Microsoft YaHei'";
    for (var u = 0; u < labels.length; u++) {
      var lu = labels[u], mu = M[lu.key], yy = ly + 20 + u * 18;
      ctx.beginPath();
      ctx.arc(lx + 13, yy - 4, 4.5, 0, 2 * Math.PI);
      ctx.fillStyle = mu.color;
      ctx.fill();
      ctx.fillStyle = "#1f2937";
      ctx.fillText(mu.name, lx + 24, yy);
      ctx.fillStyle = mu.color;
      ctx.textAlign = "right";
      ctx.fillText(Math.hypot(lu.z.re, lu.z.im).toFixed(2), lx + lw - 10, yy);
      ctx.textAlign = "left";
    }
    return { labels: labels };
  }

  function refreshMap() {
    drawSPlane();
    var r = drawZPlane();
    var body = $("#mapTable").querySelector("tbody");
    if (r && body) {
      var html = "";
      for (var i = 0; i < r.labels.length; i++) {
        var l = r.labels[i], mm = M[l.key];
        var absz = Math.hypot(l.z.re, l.z.im);
        var verdict = (S.sigma < 0)
          ? (absz < 1 ? '<span class="ok">√ 稳定</span>' : '<span class="bad">× 极点在圆外</span>')
          : (absz < 1 ? '<span class="bad">× 模拟不稳→数字反而稳（假象）</span>' : '<span class="ok">√ 仍不稳定，符合预期</span>');
        html += "<tr><td><span style='color:" + mm.color + ";font-weight:700'>●</span> " + mm.name + "</td>" +
          "<td style='font-family:ui-monospace,Consolas,monospace;font-size:13px'>" + mm.expr + "</td>" +
          "<td class='num'>" + l.z.re.toFixed(3) + " " + (l.z.im >= 0 ? "+" : "−") + " j" + Math.abs(l.z.im).toFixed(3) + "</td>" +
          "<td class='num'>|z| = <b>" + absz.toFixed(3) + "</b>　" + verdict + "</td></tr>";
      }
      body.innerHTML = html;
    }
    var ro = $("#readout");
    if (ro) {
      ro.innerHTML = "当前极点 <code>s = " + S.sigma.toFixed(2) + " + j" + S.omega.toFixed(2) +
        "</code>，T = <code>" + S.T.toFixed(2) + "</code>。" +
        (S.sigma < 0
          ? " 它在模拟域是<b>稳定</b>的（左半平面）——所以只要某个方法把它搬到单位圆外，这个方法就不能用。"
          : " 它在模拟域<b>本身就不稳定</b>（右半平面）——此时双线性也会把它搬到圆外，这是等价变换，不是缺陷。");
    }
  }

  if (sCv) {
    var dragging = false;
    var pos = function (ev) {
      var r = sCv.getBoundingClientRect();
      return { x: ev.clientX - r.left, y: ev.clientY - r.top };
    };
    var moveTo = function (px, py) {
      var s = px2s(px, py, sBox || { w: sCv.clientWidth || 520, h: 420, ml: 44, mr: 12, mt: 14, mb: 30 });
      S.sigma = s.sigma; S.omega = s.omega;
      refreshMap();
    };
    sCv.addEventListener("pointerdown", function (ev) {
      dragging = true;
      sCv.setPointerCapture(ev.pointerId);
      var q = pos(ev);
      moveTo(q.x, q.y);
    });
    sCv.addEventListener("pointermove", function (ev) {
      if (!dragging) return;
      var q = pos(ev);
      moveTo(q.x, q.y);
    });
    sCv.addEventListener("pointerup", function () { dragging = false; });
    sCv.addEventListener("pointercancel", function () { dragging = false; });
  }

  if (sCv) {
    var fs_ = $("#focusSel");
    if (fs_) fs_.addEventListener("change", function () { S.focus = fs_.value; refreshMap(); });
    var ts = $("#tslider"), tv = $("#tval");
    if (ts) ts.addEventListener("input", function () {
      S.T = parseFloat(ts.value);
      if (tv) tv.textContent = S.T.toFixed(2);
      refreshMap();
    });
    Array.prototype.forEach.call(document.querySelectorAll("[data-preset]"), function (b) {
      b.addEventListener("click", function () {
        var v = b.getAttribute("data-preset").split(",");
        S.sigma = parseFloat(v[0]); S.omega = parseFloat(v[1]);
        refreshMap();
      });
    });
    window.addEventListener("resize", function () { refreshMap(); });
    refreshMap();
  }

  /* ============================== ② 滤波器频谱 ============================== */
  var respCv = $("#respCanvas");
  if (respCv) {
    var R = { Op: 0.45, n: 4, prewarp: true, showNaive: true };

    function respDb(Om, n, kAnalog) {   // |H|² = 1 / (1 + (w/ωc)^{2n})，w = 2tan(Ω/2)
      var w = 2 * Math.tan(Math.min(Om, 0.997 * Math.PI) / 2);
      return -10 * Math.log10(1 + Math.pow(w / kAnalog, 2 * n));
    }

    function drawResp() {
      var c = fit(respCv, 360), ctx = c.ctx;
      var box = { w: c.w, h: c.h, ml: 54, mr: 18, mt: 16, mb: 38 };
      var X = function (f) { return box.ml + f * (box.w - box.ml - box.mr); };
      var Y = function (db) { return box.mt + (5 - db) / 85 * (box.h - box.mt - box.mb); };

      for (var d = 0; d >= -80; d -= 20) {
        line(ctx, box.ml, Y(d), box.w - box.mr, Y(d), "#eef1f6", 1);
        ctx.fillStyle = "#94a3b8"; ctx.font = "11px system-ui"; ctx.textAlign = "right";
        ctx.fillText(d + " dB", box.ml - 6, Y(d) + 4);
      }
      for (var fq = 0; fq <= 1.0001; fq += 0.1) {
        line(ctx, X(fq), box.mt, X(fq), box.h - box.mb, "#eef1f6", 1);
        ctx.fillStyle = "#94a3b8"; ctx.textAlign = "center";
        ctx.fillText(fq.toFixed(1) + "π", X(fq), box.h - box.mb + 15);
      }
      line(ctx, X(0), Y(-3.01), X(1), Y(-3.01), "#cbd5e1", 1, [4, 4]);
      ctx.fillStyle = "#94a3b8"; ctx.textAlign = "left";
      ctx.fillText("−3 dB", X(0.62), Y(-3.01) - 5);

      // 目标截止
      line(ctx, X(R.Op), box.mt, X(R.Op), box.h - box.mb, "#334155", 1.2, [3, 3]);
      ctx.fillStyle = "#334155"; ctx.textAlign = "center";
      ctx.fillText("Ωp", X(R.Op), box.mt + 12);

      var OpRad = R.Op * Math.PI;              // 数字截止（弧度）
      var kPre = 2 * Math.tan(OpRad / 2);      // 预扭曲后的模拟截止 ωc = (2/T)tan(Ωp/2)
      var curve = function (k, color, lw, dash) {
        ctx.save();
        ctx.beginPath();
        ctx.setLineDash(dash || []);
        ctx.strokeStyle = color; ctx.lineWidth = lw; ctx.lineJoin = "round";
        for (var i = 0; i <= 700; i++) {
          var f = i / 700 * 0.999;
          var y = Y(respDb(f * Math.PI, R.n, k));
          if (i === 0) ctx.moveTo(X(f), y); else ctx.lineTo(X(f), y);
        }
        ctx.stroke();
        ctx.restore();
      };

      if (R.showNaive) curve(R.prewarp ? OpRad : kPre, "#dc2626", 2.0, [6, 4]);
      curve(R.prewarp ? kPre : OpRad, R.prewarp ? "#0f766e" : "#b45309", 2.6, []);

      var ro = $("#respReadout");
      if (ro) {
        var aPre = respDb(OpRad, R.n, kPre);
        var aNaive = respDb(OpRad, R.n, OpRad);
        var actual = 2 * Math.atan(OpRad / 2) / Math.PI;
        ro.innerHTML =
          "当前设定：<code>Ωp = " + R.Op.toFixed(3) + "π</code>，<code>n = " + R.n + "</code>。" +
          "预扭曲设计在 Ωp 处的电平是 <b>" + aPre.toFixed(1) + " dB</b>（应该正好 −3.0 dB）。" +
          "若忘了预扭曲：Ωp 处电平只剩 <b>" + aNaive.toFixed(1) + " dB</b>，" +
          "真正的 −3 dB 点被挪到 <b>" + actual.toFixed(3) + "π</b>（偏低 " +
          ((R.Op - actual) * 100).toFixed(1) + " 个百分点）。" +
          (R.Op > 0.4 ? " Ωp 越靠近 π，tan 扭得越厉害 —— 这就是「必须预扭曲」的地方。" : "");
      }
    }

    var opS = $("#opSlider"), opV = $("#opVal");
    var nS = $("#nSlider"), nV = $("#nVal");
    var pw = $("#prewarpChk"), sn = $("#showNaiveChk");
    if (opS) opS.addEventListener("input", function () {
      R.Op = parseFloat(opS.value);
      if (opV) opV.textContent = R.Op.toFixed(3).replace(/0+$/, "").replace(/\.$/, "") + "π";
      drawResp();
    });
    if (nS) nS.addEventListener("input", function () {
      R.n = parseInt(nS.value, 10);
      if (nV) nV.textContent = R.n;
      drawResp();
    });
    if (pw) pw.addEventListener("change", function () { R.prewarp = pw.checked; drawResp(); });
    if (sn) sn.addEventListener("change", function () { R.showNaive = sn.checked; drawResp(); });
    window.addEventListener("resize", drawResp);
    drawResp();
  }
})();
