(function(){
var BASE = "https://eyacademy.github.io/ai-guide/";

function headBottom(){
  var head = 0, menus = document.querySelectorAll(".t228, .t-menu__fixed, [class*='positionfixed']");
  for(var k=0;k<menus.length;k++){
    var r = menus[k].getBoundingClientRect();
    if(r.top<=0 && r.bottom>head && r.height<200 && r.bottom<window.innerHeight/2) head = r.bottom;
  }
  return Math.max(0, Math.round(head));
}

function update(){
  var root = document.getElementById("eyai"), toc = root && root.querySelector(".toc");
  if(!toc) return;
  var head = headBottom();
  root.style.setProperty("--eyai-head", head+"px");
  var line = head + toc.offsetHeight + 40, links = toc.querySelectorAll("a"), active = null;
  for(var i=0;i<links.length;i++){
    var sec = document.getElementById(links[i].getAttribute("href").slice(1));
    if(sec && sec.getBoundingClientRect().top <= line) active = links[i];
  }
  for(i=0;i<links.length;i++){
    var on = links[i]===active;
    if(on && !links[i].classList.contains("on")){
      var w = links[i].parentNode;
      w.scrollTo({left: links[i].offsetLeft - (w.clientWidth-links[i].offsetWidth)/2, behavior:"smooth"});
    }
    links[i].classList.toggle("on", on);
  }
}

var ticking = false;
function onScroll(){ if(ticking) return; ticking = true; requestAnimationFrame(function(){ ticking = false; update(); }); }

function bindToc(){
  var toc = document.querySelector("#eyai .toc");
  if(!toc) return;
  toc.addEventListener("click", function(e){
    var a = e.target.closest ? e.target.closest("a") : null;
    if(!a) return;
    var el = document.getElementById(a.getAttribute("href").slice(1));
    if(!el) return;
    e.preventDefault(); e.stopPropagation();
    var y = el.getBoundingClientRect().top + window.pageYOffset - headBottom() - toc.offsetHeight + 16;
    window.scrollTo({top: y, behavior: "smooth"});
  });
  update();
}

/* model comparison */
var NS = "http://www.w3.org/2000/svg";
var S = {locale:"ru-RU", sec:" с", min:" мин", hour:" ч", k:" тыс.", M:" млн", B:" млрд", level:"уровень ",
  score:"Индекс интеллекта", cost:"Стоимость задачи", time:"Время на задачу",
  tokens:"Токены на задачу", axisY:"↑ Индекс интеллекта",
  speed:"Скорость вывода", ttft:"Задержка", tps:" ток/с", subCost:"Стоимость задачи по тарифу", bestCost:"Граница эффективности: ",
  plan:"Тариф", apiPrice:"нет данных по тарифу; расчёт по ценам API", notInPlan:"не входит в тариф; расчёт по ценам API", nearFree:"≈ 0",
  pick:"Выберите модели в списке справа.", noData:"Не удалось загрузить данные. Обновите страницу.",
  capScore:"Топ-{n} моделей, баллы из 100", capOmni:"Итоговый балл от −100 до 100", capAcc:"Доля верных ответов",
  capHall:"Доля галлюцинаций, меньше — лучше", capField:"Баллы из 100",
  noteOmni:"За верный ответ балл начисляется, за выдуманный — вычитается, за ответ «не знаю» — ноль. Значение ниже нуля означает, что модель чаще выдумывает ответ, чем отвечает верно.",
  noteAcc:"Сколько вопросов на знания модель ответила верно. Больше — лучше.",
  noteHall:"Как часто модель выдумывает ответ вместо ответа «не знаю». Меньше — лучше.",
  of:" из ", showAll:"Показать все ", collapse:"Свернуть", preparing:"Подготовка…",
  ratingTitle:"Рейтинг моделей", valueTitle:"Стоимость и эффективность моделей",
  credit1:"Источник: Artificial Analysis · artificialanalysis.ai",
  credit2:"Гид по ИИ-инструментам Академии бизнеса EY · eyacademyeurasia.com/ai-guide",
  nothing:"Ничего не найдено", knowledgeNote:""};
var GUIDE = "guide.html";
function readI18n(){
  // The Tilda loader carries only data-lang; the wording arrives with the page it pulls in.
  var r = document.getElementById("eyai");
  if(!r) return;
  var lang = r.getAttribute("data-lang"), raw = r.getAttribute("data-i18n");
  if(lang && lang !== "ru") GUIDE = lang + "/guide.html";
  if(raw) try { var o = JSON.parse(raw); for(var k in o) S[k] = o[k]; } catch(e){}
}
readI18n();
var LABEL = S;
var EFF = ["non-reasoning","minimal","low","medium","default","high","xhigh","max"];

function esc(t){ return String(t).replace(/[&<>"]/g, function(c){ return {"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]; }); }
function num(v, d){ return v.toLocaleString(S.locale, {maximumFractionDigits: d}); }
function fmt(k, v, short){
  if(v==null) return "—";
  if(k==="score") return num(v, 1);
  if(k==="speed") return num(v, 0)+S.tps;
  if(k==="ttft") return num(v, v<10 ? 1 : 0)+S.sec;
  if(k==="cost"||k==="cost_total") return "$" + num(v, v<1 ? (short?2:3) : v<100 ? (short?1:2) : 0);
  if(k==="time"){
    if(v<60) return Math.round(v)+S.sec;
    if(v<3600) return short ? num(v/60,1)+S.min : Math.floor(v/60)+S.min+" "+Math.round(v%60)+S.sec;
    return short ? num(v/3600,1)+S.hour : Math.floor(v/3600)+S.hour+" "+Math.round(v%3600/60)+S.min;
  }
  if(v>=1e9) return num(v/1e9,1)+S.B;
  if(v>=1e6) return num(v/1e6,1)+S.M;
  if(v>=1e3) return num(v/1e3,short?0:1)+S.k;
  return num(v,0);
}

function el(name, attrs, parent){
  var e = document.createElementNS(NS, name);
  for(var a in attrs) if(attrs[a]!=null) e.setAttribute(a, attrs[a]);
  if(parent) parent.appendChild(e);
  return e;
}

var LOGOS = {};
function logoFile(creator){
  var k = creator.toLowerCase();
  for(var n in LOGOS) if(k.indexOf(n)>=0) return LOGOS[n];
  return null;
}
function logo(parent, cx, y, size, creator, color){
  var f = logoFile(creator);
  if(f) return el("image", {href:BASE+"logos/"+f, x:cx-size/2, y:y, width:size, height:size}, parent);
  el("circle", {cx:cx, cy:y+size/2, r:size/2, fill:color}, parent);
  el("text", {x:cx, y:y+size/2+4, "text-anchor":"middle", "class":"lgt"}, parent).textContent = creator.charAt(0).toUpperCase();
}

function logTicks(lo, hi, k){
  var steps = k==="time" ? [10,30,60,120,300,600,1200,1800,3600,7200,14400,28800] : null, out = [];
  if(steps){ for(var i=0;i<steps.length;i++) if(steps[i]>=lo && steps[i]<=hi) out.push(steps[i]); return out; }
  for(var p=Math.floor(Math.log10(lo)); p<=Math.ceil(Math.log10(hi)); p++)
    [1,2,5].forEach(function(m){ var v=m*Math.pow(10,p); if(v>=lo && v<=hi) out.push(v); });
  return out.length>8 ? out.filter(function(v){ return String(v).replace(/[0.]/g,"")==="1"; }) : out;
}

function niceStep(max){
  var raw = max/5, p = Math.pow(10, Math.floor(Math.log10(raw))), m = raw/p;
  return (m<=1 ? 1 : m<=2 ? 2 : m<=2.5 ? 2.5 : m<=5 ? 5 : 10)*p;
}

// Models nobody beats: no other model is both better on the metric and smarter.
function frontier(rows, k){
  var best = -1, out = [];
  rows.slice().sort(function(a,b){ return a[k]-b[k] || b.score-a.score; }).forEach(function(m){
    if(m.score>best){ best=m.score; out.push(m); }
  });
  return out;
}

function tipHtml(m, k){
  var keys = ["score","cost","time","tokens","speed","ttft"];   // per-task figures only
  var h = "<b>"+esc(m.family)+"</b><small>"+esc(m.creator)+(m.effort ? " · "+S.level+esc(m.effort) : "")+"</small>";
  keys.forEach(function(x){
    if(m[x]==null) return;
    var label = x==="cost" && m.sub && !m.api ? S.subCost : LABEL[x], v = x==="cost" && m.sub && !m[x] ? S.nearFree : fmt(x,m[x]);
    h += '<span'+(x===k?' class="on"':'')+'><i>'+label+'</i>'+v+'</span>';
    if(x==="cost" && m.sub) h += '<span><i>'+S.plan+'</i>'+(m.plan ? esc(m.plan)+(m.api ? " · "+S.notInPlan : "") : S.apiPrice)+'</span>';
  });
  return h;
}

function showTip(plot, m, k, x, y){
  var tip = plot.querySelector(".cmp-tip");
  if(!tip){ tip=document.createElement("div"); tip.className="cmp-tip"; plot.appendChild(tip); }
  tip.innerHTML = tipHtml(m, k);
  tip.style.display = "block";
  var w = tip.offsetWidth, h = tip.offsetHeight, W = plot.clientWidth;
  tip.style.left = Math.max(0, x+14+w > W ? x-14-w : x+14)+"px";
  tip.style.top = Math.max(0, y-h-10)+"px";
}
function hideTip(plot){ var t=plot.querySelector(".cmp-tip"); if(t) t.style.display="none"; }
function empty(plot, text){ plot.innerHTML = '<p class="cmp-load">'+text+'</p>'; }

function scatter(plot, rows, k, opt){
  rows = rows.filter(function(m){ return m[k]!=null; });
  if(!rows.length){ empty(plot, S.pick); return []; }
  var W = plot.clientWidth, H = Math.round(Math.max(300, Math.min(480, W*0.62)));
  var M = {l:34, r:12, t:12, b:34}, iw = W-M.l-M.r, ih = H-M.t-M.b;
  var pos = rows.map(function(m){ return m[k]; }).filter(function(v){ return v>0; });
  var zero = opt.log && pos.length<rows.length ? (pos.length ? Math.min.apply(0,pos) : 1)/4 : 0;
  var xv = function(m){ return m[k]>0 || !opt.log ? m[k] : zero; }, lab = opt.label || LABEL[k];
  var xs = rows.map(xv), ys = rows.map(function(m){ return m.score; });
  var y0 = Math.max(0, Math.floor((Math.min.apply(0,ys)-4)/10)*10), y1 = Math.ceil((Math.max.apply(0,ys)+3)/10)*10;
  var Y = function(v){ return M.t + (1-(v-y0)/(y1-y0))*ih; }, X, xt = [];
  if(opt.log){
    var x0 = Math.log10(Math.min.apply(0,xs)/1.35), x1 = Math.log10(Math.max.apply(0,xs)*1.35);
    X = function(v){ return M.l + (Math.log10(v)-x0)/(x1-x0)*iw; };
    xt = logTicks(zero ? zero*2 : Math.pow(10,x0), Math.pow(10,x1), k);
  } else {
    var xmax = Math.max.apply(0,xs), st = niceStep(xmax), xtop = Math.ceil(xmax*1.04/st)*st;
    X = function(v){ return M.l + v/xtop*iw; };
    for(var t0=0; t0<=xtop+st/2; t0+=st) xt.push(t0);
  }
  var svg = el("svg", {viewBox:"0 0 "+W+" "+H, height:H, role:"img", "aria-label":S.score+" / "+lab});
  for(var v=y0; v<=y1; v+=10){
    el("line", {x1:M.l, x2:W-M.r, y1:Y(v), y2:Y(v), "class":"gl", "stroke-dasharray":"2 4"}, svg);
    el("text", {x:M.l-8, y:Y(v)+4, "text-anchor":"end", "class":"ax"}, svg).textContent = v;
  }
  xt.forEach(function(t){
    el("line", {x1:X(t), x2:X(t), y1:M.t, y2:H-M.b, "class":"gl", "stroke-dasharray":"2 4"}, svg);
    el("text", {x:X(t), y:H-M.b+18, "text-anchor":"middle", "class":"ax"}, svg).textContent = fmt(k,t,true);
  });
  if(zero){
    el("line", {x1:X(zero), x2:X(zero), y1:M.t, y2:H-M.b, "class":"gl", "stroke-dasharray":"2 4"}, svg);
    el("text", {x:X(zero), y:H-M.b+18, "text-anchor":"middle", "class":"ax"}, svg).textContent = S.nearFree;
  }
  el("text", {x:W-M.r, y:H-M.b-6, "text-anchor":"end", "class":"ax"}, svg).textContent = lab+" →";
  el("text", {x:M.l+6, y:M.t+14, "class":"ax"}, svg).textContent = S.axisY;
  // Reasoning levels of one model share a thin line in its colour.
  var fams = {};
  rows.forEach(function(m){ (fams[m.family] = fams[m.family] || []).push(m); });
  for(var f in fams) if(fams[f].length>1){
    var line = fams[f].slice().sort(function(a,b){ return a.eo-b.eo || a[k]-b[k]; });
    el("polyline", {points:line.map(function(m){ return X(xv(m))+","+Y(m.score); }).join(" "), fill:"none", stroke:line[0].c, "stroke-width":1.2, "stroke-opacity":.5}, svg);
  }
  var best = opt.pareto ? frontier(rows, k) : [];
  if(best.length>1) el("polyline", {points:best.map(function(m){ return X(xv(m))+","+Y(m.score); }).join(" "), fill:"none", stroke:"#2e2e38", "stroke-width":1.5, "stroke-linejoin":"round", "stroke-dasharray":"5 4"}, svg);
  var pts = [], axw = lab.length*6.3+16, boxes = [{x:W-M.r-axw, y:H-M.b-20, w:axw, h:18}, {x:M.l, y:M.t, w:90, h:18}];
  var labels = el("g", {}, svg), dots = el("g", {}, svg);
  rows.forEach(function(m){
    var on = best.indexOf(m)>=0, p = {m:m, on:on, x:X(xv(m)), y:Y(m.score)};
    p.r = on ? 6.5 : 5;
    p.c = m.api   // no subscription data: drawn hollow, at the API price
      ? el("circle", {cx:p.x, cy:p.y, r:p.r-0.75, fill:"#fff", stroke:m.c, "stroke-width":1.5, "class":"pt"}, dots)
      : el("circle", {cx:p.x, cy:p.y, r:p.r, fill:m.c, stroke:"#fff", "stroke-width":1.5, "fill-opacity":on?1:0.5, "class":"pt"}, dots);
    pts.push(p);
  });
  // One label per model, at its smartest level; best models first, skip overlaps.
  var top = {};
  pts.forEach(function(p){ var t = top[p.m.family]; if(!t || p.m.score>t.m.score) top[p.m.family] = p; });
  pts.filter(function(p){ return top[p.m.family]===p || p.on; }).sort(function(a,b){ return b.on-a.on || b.m.score-a.m.score; }).forEach(function(p){
    var text = p.on && fams[p.m.family].length>1 && p.m.effort ? p.m.family+" · "+p.m.effort : p.m.family;
    var w = text.length*6.4+4, h = 14, right = p.x+10+w <= W-M.r;
    var bx = {x: right ? p.x+9 : p.x-9-w, y: p.y-h/2, w:w, h:h};
    var hit = boxes.some(function(b){ return bx.x<b.x+b.w && bx.x+bx.w>b.x && bx.y<b.y+b.h && bx.y+bx.h>b.y; }) ||
              pts.some(function(q){ return q!==p && q.x>bx.x-4 && q.x<bx.x+bx.w+4 && q.y>bx.y-4 && q.y<bx.y+bx.h+4; });
    if(hit || bx.x<M.l) return;
    boxes.push(bx);
    el("text", {x: right ? p.x+9 : p.x-9, y:p.y+4, "text-anchor": right?"start":"end", "class": p.on ? "lb on" : "lb"}, labels).textContent = text;
  });
  plot.innerHTML = ""; plot.appendChild(svg);
  var cur = null;
  function pick(e){
    var r = svg.getBoundingClientRect(), sx = W/r.width, mx = (e.clientX-r.left)*sx, my = (e.clientY-r.top)*sx, near = null, d = 26*26;
    pts.forEach(function(p){ var dd=(p.x-mx)*(p.x-mx)+(p.y-my)*(p.y-my); if(dd<d){ d=dd; near=p; } });
    if(near===cur) return;
    if(cur) cur.c.setAttribute("r", cur.r);
    cur = near;
    if(!near) return hideTip(plot);
    near.c.setAttribute("r", 9);
    showTip(plot, near.m, k, near.x/sx, near.y/sx);
  }
  svg.addEventListener("pointermove", pick);
  svg.addEventListener("pointerdown", pick);
  svg.addEventListener("pointerleave", function(){ if(cur) cur.c.setAttribute("r", cur.r); cur=null; hideTip(plot); });
  return best;
}

var ABBR = {"non-reasoning":"N","minimal":"Min","low":"L","medium":"M","default":"D","high":"H","xhigh":"X","max":"Mx","reasoning":"R"};
function abbr(e){ return e ? (ABBR[e] || e.slice(0,3)) : ""; }

// Two balanced lines for a group caption.
function wrap2(text, max){
  if(text.length*6.6 <= max) return [text];
  var w = text.split(" "), best = [text], diff = 1e9;
  for(var i=1;i<w.length;i++){
    var a = w.slice(0,i).join(" "), b = w.slice(i).join(" "), d = Math.abs(a.length-b.length);
    if(d<diff){ diff=d; best=[a,b]; }
  }
  return best;
}

// Bars grouped by model, one bar per reasoning level, like the Artificial Analysis cost charts.
function columns(plot, rows, k){
  rows = rows.filter(function(m){ return m[k]!=null; });
  if(!rows.length){ empty(plot, S.pick); return; }
  var byF = {};
  rows.forEach(function(m){ (byF[m.family] = byF[m.family] || []).push(m); });
  var groups = Object.keys(byF).map(function(f){
    var r = byF[f].sort(function(a,b){ return a.eo-b.eo || a[k]-b[k]; });
    return {f:f, rows:r, c:r[0].c, max:Math.max.apply(0, r.map(function(x){ return x[k]; }))};
  }).sort(function(a,b){ return k==="speed" ? b.max-a.max : a.max-b.max; });
  var W = plot.clientWidth, narrow = W<600, n = rows.length, G = groups.length;
  var gap = narrow ? 8 : 18, M = {l:narrow?40:54, r:6, t:26};
  var unit = (W-M.l-M.r-gap*(G-1))/n, bw = Math.max(2, unit*0.8);
  var minGroup = Math.min.apply(0, groups.map(function(g){ return g.rows.length*unit; }));
  var rotate = minGroup < 58;
  M.b = rotate ? (narrow?124:140) : 84;
  var H = (narrow ? 340 : 460) + M.b - 84, ih = H-M.t-M.b, base = M.t+ih;
  var max = Math.max.apply(0, rows.map(function(m){ return m[k]; }));
  var step = k==="time" && max>=120 ? niceStep(max/60)*60 : niceStep(max), top = Math.ceil(max/step)*step;   // time: whole minutes
  var Y = function(v){ return M.t + (1-v/top)*ih; };
  var svg = el("svg", {viewBox:"0 0 "+W+" "+H, height:H, role:"img", "aria-label":LABEL[k]});
  for(var v=0; v<=top+step/2; v+=step){
    el("line", {x1:M.l, x2:W-M.r, y1:Y(v), y2:Y(v), "class":"gl", "stroke-dasharray": v ? "2 4" : null}, svg);
    el("text", {x:M.l-8, y:Y(v)+4, "text-anchor":"end", "class":"ax"}, svg).textContent = v ? fmt(k, v, true) : "0";
  }
  var bars = [], x = M.l;
  groups.forEach(function(g){
    var gx = x, cnt = g.rows.length;
    g.rows.forEach(function(m, i){
      var cx = x + unit*(i+0.5), y = Y(m[k]), grp = el("g", {"class":"col"}, svg);
      el("rect", {x:cx-bw/2, y:y, width:bw, height:Math.max(1, base-y), fill:g.c, "fill-opacity": cnt>1 ? 0.42+0.58*i/(cnt-1) : 1}, grp);
      if(unit>=24) el("text", {x:cx, y:y-6, "text-anchor":"middle", "class":"vl"}, grp).textContent = fmt(k, m[k], true);
      if(unit>=13 && m.effort) el("text", {x:cx, y:base+14, "text-anchor":"middle", "class":"ef"}, grp).textContent = abbr(m.effort);
      bars.push({g:grp, m:m, cx:cx, y:y});
    });
    x += cnt*unit;
    var mid = (gx+x)/2, ly = base + (unit>=13 ? 50 : 36);
    logo(svg, mid, ly-31, 16, g.rows[0].creator, g.c);
    if(rotate){
      el("text", {x:mid+3, y:ly-6, "text-anchor":"end", transform:"rotate(-40 "+(mid+3)+" "+(ly-6)+")", fill:g.c, "class":"gn"}, svg).textContent = g.f;
    } else {
      wrap2(g.f, x-gx+gap-4).forEach(function(line, i){
        el("text", {x:mid, y:ly+i*14, "text-anchor":"middle", fill:g.c, "class":"gn"}, svg).textContent = line;
      });
    }
    x += gap;
  });
  plot.innerHTML = ""; plot.appendChild(svg);
  var cur = null;
  function pick(e){
    var b = svg.getBoundingClientRect(), sx = W/b.width, mx = (e.clientX-b.left)*sx, c = null, d = unit/2+gap/2+1;
    bars.forEach(function(o){ var dd = Math.abs(o.cx-mx); if(dd<d){ d=dd; c=o; } });
    if(c===cur) return;
    cur = c;
    bars.forEach(function(o){ o.g.setAttribute("class", "col"+(c && o!==c ? " dim" : "")); });
    if(!c) return hideTip(plot);
    showTip(plot, c.m, k, c.cx/sx, c.y/sx);
  }
  svg.addEventListener("pointermove", pick);
  svg.addEventListener("pointerdown", pick);
  svg.addEventListener("pointerleave", function(){ cur=null; bars.forEach(function(o){ o.g.setAttribute("class","col"); }); hideTip(plot); });
}

var dataP = null;
function loadData(){
  if(!dataP) dataP = fetch(BASE+"data/aa-index.json", {cache:"no-cache"})
    .then(function(r){ if(!r.ok) throw 0; return r.json(); })
    .catch(function(e){ dataP = null; throw e; });
  return dataP;
}

function colorFrom(colors, creator){
  var k = creator.toLowerCase();
  for(var n in colors) if(k.indexOf(n)>=0) return colors[n];
  return "#9a9aa6";
}

/* saving a chart as a picture; the source is named once, at the top */
function credit(desc){
  // The description above most charts already names Artificial Analysis; then only the guide is credited.
  var src = String(S.credit1).split(" \u00b7 ")[0];
  return (/Artificial Analysis/i.test(desc || "") ? "" : src + " \u00b7 ") + S.credit2;
}

// The short description that sits above a chart, taken from the section it belongs to.
function secLead(node){
  var s = node && node.closest ? node.closest("section") : null, p = s && s.querySelector(".sec-lead");
  return p ? p.textContent.trim() : "";
}

// Break the description into a few lines that fit the picture.
function wrapText(text, perLine, maxLines){
  var words = String(text || "").trim().split(/\s+/), lines = [], cur = "";
  if(!words[0]) return [];
  words.forEach(function(w){
    if(!cur) cur = w;
    else if((cur + " " + w).length <= perLine) cur += " " + w;
    else { lines.push(cur); cur = w; }
  });
  if(cur) lines.push(cur);
  if(lines.length > maxLines){
    lines = lines.slice(0, maxLines);
    lines[maxLines - 1] = lines[maxLines - 1].replace(/[\s,;:.\u2014-]+$/, "") + "\u2026";
  }
  return lines;
}

// Values for the dotted scale behind the columns: a round step around the zero line.
function scaleTicks(pos, neg){
  var step = niceStep(pos + neg) || 1, out = [];
  for(var v = -Math.ceil(neg / step) * step; v <= pos + step / 2; v += step) out.push(Math.round(v * 1e6) / 1e6);
  return out;
}

function dataUri(url){
  return fetch(url, {cache:"force-cache"}).then(function(r){ return r.blob(); }).then(function(b){
    return new Promise(function(ok){ var f = new FileReader(); f.onload = function(){ ok(f.result); }; f.readAsDataURL(b); });
  }).catch(function(){ return null; });
}

function svgText(parent, x, y, text, opt){
  var t = el("text", {x:x, y:y, "font-family":"Arial, sans-serif", "font-size":opt.size || 13,
    fill:opt.fill || "#2e2e38", "text-anchor":opt.anchor || "start", "font-weight":opt.bold ? "700" : "400"}, parent);
  if(opt.rotate) t.setAttribute("transform", "rotate("+opt.rotate+" "+x+" "+y+")");
  t.textContent = text;
  return t;
}

// The rating is drawn as HTML on the page, so the picture is built from the same numbers.
function ratingSvg(list, caption, pct, colors, desc){
  var W = Math.max(1100, 60 + list.length * 46), M = {l:64, r:28};
  var lines = wrapText(desc, Math.floor((W - M.l - M.r) / 7.1), 3);
  var capY = 74 + (lines.length ? lines.length * 18 + 14 : 0);
  var longest = Math.max.apply(0, list.map(function(m){ return String(m.name).length; }));
  M.t = capY + 40;                                       // air between the caption and the top of the scale
  M.b = 46 + Math.ceil(longest * 6.6 * 0.71) + 28;       // room for the slanted names, nothing under them
  var ih = 290, H = M.t + ih + M.b, iw = W - M.l - M.r, slot = iw / list.length;
  var vals = list.map(function(m){ return m.v; });
  var pos = Math.max(0, Math.max.apply(0, vals)), neg = Math.max(0, -Math.min.apply(0, vals));
  // The scale runs to the next round value above the tallest column, as on Artificial Analysis.
  var step = niceStep(pos + neg) || 1;
  var hi = pos ? Math.ceil(pos * 1.06 / step) * step : 0, lo = neg ? Math.ceil(neg * 1.06 / step) * step : 0;
  if(pos <= 100 && hi > 100) hi = 100;
  var max = (hi + lo) || 1, zero = M.t + ih * hi / max;
  var svg = el("svg", {xmlns:NS, width:W, height:H, viewBox:"0 0 "+W+" "+H});
  el("rect", {x:0, y:0, width:W, height:H, fill:"#fff"}, svg);
  el("rect", {x:0.5, y:0.5, width:W - 1, height:H - 1, fill:"none", stroke:"#e1e1e6"}, svg);
  svgText(svg, M.l, 46, S.ratingTitle, {size:26, bold:true});
  lines.forEach(function(t, i){ svgText(svg, M.l, 74 + i * 18, t, {size:13, fill:"#747480"}); });
  svgText(svg, M.l, capY, caption, {size:13, fill:"#747480"});
  svgText(svg, W - M.r, capY, credit(desc), {size:12, fill:"#9a9aa6", anchor:"end"});
  // Dotted scale with a line at the top as the upper bound; a solid zero line only when columns go below it.
  for(var v = -lo; v <= hi + step / 2; v += step){
    var gy = zero - v / max * ih;
    if(!v && !neg) continue;
    el("line", {x1:M.l, x2:W - M.r, y1:gy, y2:gy, stroke:v ? "#dcdce2" : "#c4c4cc", "stroke-dasharray": v ? "2 4" : null}, svg);
    svgText(svg, M.l - 10, gy + 4, Math.round(v) + (pct ? "%" : ""), {size:11, fill:"#747480", anchor:"end"});
  }
  list.forEach(function(m, i){
    var cx = M.l + slot * (i + 0.5), bw = Math.min(30, slot * 0.66);
    var h = Math.max(2, Math.abs(m.v) / max * ih), top = m.v < 0 ? zero : zero - h;
    el("rect", {x:cx - bw / 2, y:top, width:bw, height:h, fill:m.c}, svg);
    var r = Math.round(m.v), label = (r < 0 ? "−" : "") + Math.abs(r) + (pct ? "%" : "");
    svgText(svg, cx, m.v < 0 ? top + h + 15 : top - 6, label, {size:12, bold:true, anchor:"middle"});
    if(m.file) el("image", {href:BASE + "logos/" + m.file, x:cx - 10, y:M.t + ih + 10, width:20, height:20}, svg);
    svgText(svg, cx + 4, M.t + ih + 42, m.name, {size:12, anchor:"end", rotate:-45});
  });
  return svg;
}

function framed(svg, title, desc, foot){
  // Put the title, the description and the credit above a chart that is already drawn as SVG.
  var box = svg.viewBox.baseVal, w = box && box.width || svg.clientWidth, h = box && box.height || svg.clientHeight;
  var p = 24, lines = wrapText(desc, Math.floor(w / 7.1), 3), cr = credit(desc);
  var side = title.length * 11.5 + cr.length * 6.3 + 40 < w;   // the credit fits on the title line
  var feet = wrapText(foot, Math.floor(w / 7.4), 3);
  var head = 44 + (lines.length ? lines.length * 17 + 12 : 0) + (side ? 0 : 18), W = w + p * 2;
  var H = head + h + (feet.length ? 24 + feet.length * 18 : 20);
  var out = el("svg", {xmlns:NS, width:Math.round(W), height:Math.round(H), viewBox:"0 0 "+W+" "+H});
  el("rect", {x:0, y:0, width:W, height:H, fill:"#fff"}, out);
  el("rect", {x:0.5, y:0.5, width:W - 1, height:H - 1, fill:"none", stroke:"#e1e1e6"}, out);
  var st = el("style", {}, out);
  st.textContent = "text{font-family:Arial,sans-serif}.gl{stroke:#e1e1e6}.ax{fill:#747480;font-size:12px}" +
    ".ef{fill:#747480;font-size:10px}.lb{fill:#747480;font-size:12px}.lb.on{fill:#2e2e38;font-weight:700}" +
    ".vl{fill:#2e2e38;font-size:11px;font-weight:700}.gn{font-size:12px;font-weight:700}";
  var copy = svg.cloneNode(true);
  copy.setAttribute("x", p); copy.setAttribute("y", head);
  copy.setAttribute("width", w); copy.setAttribute("height", h);
  out.appendChild(copy);
  svgText(out, p, 34, title, {size:20, bold:true});
  lines.forEach(function(t, i){ svgText(out, p, 56 + i * 17, t, {size:12.5, fill:"#747480"}); });
  feet.forEach(function(t, i){ svgText(out, p, head + h + 26 + i * 18, t, {size:13}); });
  if(side) svgText(out, W - p, 34, cr, {size:12, fill:"#9a9aa6", anchor:"end"});
  else svgText(out, p, 56 + lines.length * 17, cr, {size:12, fill:"#9a9aa6"});
  return out;
}

function savePng(svg, name){
  var imgs = Array.prototype.slice.call(svg.querySelectorAll("image"));
  return Promise.all(imgs.map(function(el){
    var href = el.getAttribute("href") || el.getAttribute("xlink:href");
    return href && href.indexOf("data:") !== 0 ? dataUri(href).then(function(d){
      if(d) el.setAttribute("href", d); else el.remove();
    }) : null;
  })).then(function(){
    var w = +svg.getAttribute("width"), h = +svg.getAttribute("height"), scale = 2;
    var src = "data:image/svg+xml;charset=utf-8," + encodeURIComponent(new XMLSerializer().serializeToString(svg));
    return new Promise(function(ok, no){
      var im = new Image();
      im.onload = function(){
        var c = document.createElement("canvas");
        c.width = w * scale; c.height = h * scale;
        var g = c.getContext("2d");
        g.fillStyle = "#fff"; g.fillRect(0, 0, c.width, c.height);
        g.drawImage(im, 0, 0, c.width, c.height);
        c.toBlob(function(b){
          var a = document.createElement("a");
          a.href = URL.createObjectURL(b); a.download = name;
          document.body.appendChild(a); a.click(); a.remove();
          setTimeout(function(){ URL.revokeObjectURL(a.href); }, 5000);
          ok();
        }, "image/png");
      };
      im.onerror = no;
      im.src = src;
    });
  });
}

/* rating tabs: intelligence, knowledge reliability, fields */
function rtCap(metric, n){
  if(metric === "score") return S.capScore.replace("{n}", n);
  return {omni:S.capOmni, acc:S.capAcc, hall:S.capHall}[metric] || S.capField;
}
function rtNote(metric){ return {omni:S.noteOmni, acc:S.noteAcc, hall:S.noteHall}[metric] || ""; }

function initRating(){
  var rt = document.querySelector("#eyai .rt");
  if(!rt || rt.getAttribute("data-on")) return;
  rt.setAttribute("data-on", "1");
  var chart = rt.parentNode, ol = chart.querySelector(".bars"), grid = chart.querySelector(".rt-grid"), legend = chart.querySelector(".legend"), cap = chart.querySelector(".rt-cap");
  var dateEl = chart.querySelector(".rt-date"), dateText = dateEl ? dateEl.textContent : "";
  var note = rt.querySelector(".rt-note"), colors = {};
  try { colors = JSON.parse(rt.getAttribute("data-colors")); } catch(e){}
  var tab = "score", metric = "score", tabNote = note.textContent, shown = null;

  function render(d){
    var pct = metric==="acc" || metric==="hall", asc = metric==="hall";
    var list = (metric==="score" ? d.models.map(function(m){ return {name:m.name, creator:m.creator, effort:m.effort, v:m.score}; })
      : (d.bench||[]).filter(function(m){ return m[metric]!=null; }).map(function(m){ return {name:m.name, creator:m.creator, effort:m.effort, v:m[metric]}; }))
      .sort(function(a,b){ return asc ? a.v-b.v : b.v-a.v; }).slice(0, 30);
    // Zero line sits above the bottom when some values are negative; bars below it hang down.
    shown = list;
    var vals = list.map(function(m){ return m.v; }), pos = Math.max(0, Math.max.apply(0, vals)), neg = Math.max(0, -Math.min.apply(0, vals));
    var pad = neg ? (pos + neg)*0.09 : 0, max = (pos + neg + pad) || 1, seen = {}, leg = [];
    ol.style.setProperty("--z", ((neg + pad)/max*100).toFixed(2)+"%");
    if(grid) grid.innerHTML = scaleTicks(pos, neg + pad).map(function(v){
      var y = ((neg + pad + v)/max*100);
      return (!v && !neg) || y < -0.5 || y > 100.5 ? "" :
        '<i class="'+(v ? "" : "z")+'" style="--g:'+y.toFixed(2)+'%"><b>'+(Math.round(v)+(pct ? "%" : ""))+'</b></i>';
    }).join("");
    ol.innerHTML = list.map(function(m, i){
      var c = colorFrom(colors, m.creator), f = logoFile(m.creator), w = Math.max(m.v ? 2 : 0.6, Math.abs(m.v)/max*100).toFixed(2);
      m.c = c; m.file = f;
      var name = esc(m.name + (m.effort ? " ("+m.effort+")" : "")), r = Math.round(m.v), val = (r<0 ? "−" : "") + Math.abs(r) + (pct ? "%" : "");
      if(!seen[m.creator]){ seen[m.creator] = 1; leg.push('<span><i style="background:'+c+'"></i>'+esc(m.creator)+'</span>'); }
      var lo = f ? '<img src="'+BASE+'logos/'+f+'" width="20" height="20" alt="">' : '<b class="lgl" style="--c:'+c+'">'+esc(m.creator.charAt(0).toUpperCase())+'</b>';
      return '<li class="bar'+(m.v<0 ? " neg" : "")+'" title="'+name+' · '+esc(m.creator)+' · '+val+'"><span class="i">'+(i+1)+'</span><span class="lo">'+lo+'</span>'+
        '<span class="n"><span>'+name+'</span><small>'+esc(m.creator)+'</small></span><span class="t"><span class="f'+(w<14 || m.v<0 ? " sm" : "")+'" style="--c:'+c+';--w:'+w+'%"><em>'+val+'</em></span></span></li>';
    }).join("");
    legend.innerHTML = leg.join("");
    cap.textContent = rtCap(metric, list.length);
    note.textContent = rtNote(metric) || tabNote;
    if(dateEl) dateEl.textContent = tab==="know" ? (S.knowledgeNote || d.knowledge_note || dateText) : dateText;
  }
  var main = chart.querySelector(".rt-main"), value = chart.querySelector(".rt-value");
  function show(){
    var subs = rt.querySelectorAll(".rt-subs");
    for(var i=0;i<subs.length;i++) subs[i].hidden = subs[i].getAttribute("data-for")!==tab;
    if(value){ value.hidden = tab!=="value"; main.hidden = tab==="value"; }
    if(tab==="value"){ note.textContent = tabNote; window.dispatchEvent(new Event("resize")); return; }
    loadData().then(function(d){ LOGOS = d.logos || LOGOS; render(d); }).catch(function(){});
  }
  rt.addEventListener("click", function(e){
    var b = e.target.closest ? e.target.closest("button") : null;
    if(!b) return;
    if(b.classList.contains("rt-dl")){
      var busy = b.textContent;
      b.textContent = S.preparing; b.disabled = true;
      var plot = value && !value.hidden ? value.querySelector(".cmp-plot svg") : null;
      var cn = plot && value.querySelector(".cmp-note");   // the open tab's own explanation, not the hover hint
      var desc = plot ? (cn ? cn.textContent : note.textContent) : secLead(chart);
      var be = plot && value.querySelector(".cmp-best");
      var svg = plot ? framed(plot, S.valueTitle, desc, be ? be.textContent : "")
        : (shown ? ratingSvg(shown, cap.textContent, metric === "acc" || metric === "hall", colors, desc) : null);
      var done = function(){ b.textContent = busy; b.disabled = false; };
      if(svg) savePng(svg, "ey-ai-guide-" + (plot ? "value" : metric) + ".png").then(done, done); else done();
      return;
    }
    var g = b.parentNode;
    for(var i=0;i<g.children.length;i++) g.children[i].classList.toggle("on", g.children[i]===b);
    if(b.getAttribute("data-rt")){
      tab = b.getAttribute("data-rt"); tabNote = b.getAttribute("data-note");
      var s = rt.querySelector('.rt-subs[data-for="'+tab+'"] .on');
      metric = s ? s.getAttribute("data-m") : tab;
    }
    if(b.getAttribute("data-m")) metric = b.getAttribute("data-m");
    show();
  });
  show();   // the page ships the bars as HTML; this also hands the numbers to the picture export
}

/* phones: the rating list starts collapsed */
function initMore(){
  var btn = document.querySelector("#eyai .rt-more");
  if(!btn || btn.getAttribute("data-on")) return;
  btn.setAttribute("data-on", "1");
  var ol = btn.parentNode.querySelector(".bars");
  function label(){ var n = ol.children.length; btn.hidden = n <= 10; btn.textContent = ol.classList.contains("cut") ? S.showAll + n : S.collapse; }
  btn.addEventListener("click", function(){ ol.classList.toggle("cut"); label(); });
  new MutationObserver(label).observe(ol, {childList:true});
  label();
}

/* tabs for the subscription tables */
function initPlans(){
  var boxes = document.querySelectorAll("#eyai .pl-box");
  for(var n=0;n<boxes.length;n++) (function(box){
    if(box.getAttribute("data-on")) return;
    box.setAttribute("data-on", "1");
    var bar = box.querySelector(".pl-tabs");
    bar.addEventListener("click", function(e){
      var b = e.target.closest ? e.target.closest("button") : null;
      if(!b) return;
      var btns = bar.querySelectorAll("button"), panels = box.querySelectorAll(":scope > .pl-panel"), k = Array.prototype.indexOf.call(btns, b);
      for(var i=0;i<btns.length;i++){ btns[i].classList.toggle("on", i===k); panels[i].hidden = i!==k; }
    });
  })(boxes[n]);
}

function initCompare(){
  var box = document.querySelector("#eyai .cmp");
  if(!box || box.getAttribute("data-on") || !window.fetch) return;
  box.setAttribute("data-on", "1");
  var plot = box.querySelector(".cmp-plot");
  loadData().then(function(d){ setupCompare(box, d); })
    .catch(function(){ empty(plot, S.noData); });
}

function setupCompare(box, d){
  var colors = {}; try { colors = JSON.parse(box.getAttribute("data-colors")); } catch(e){}
  function colorOf(creator){ var k = creator.toLowerCase(); for(var n in colors) if(k.indexOf(n)>=0) return colors[n]; return "#9a9aa6"; }
  LOGOS = d.logos || {};
  var rows = (d.variants || []).map(function(v){ v.c = colorOf(v.creator); v.eo = EFF.indexOf(v.effort); return v; });
  var fams = {};
  rows.forEach(function(r){
    var f = fams[r.family] || (fams[r.family] = {name:r.family, creator:r.creator, c:r.c, best:r});
    if(r.score>f.best.score) f.best = r;
  });
  var defaults = (d["default"] || []).filter(function(n){ return fams[n]; }), sel = {}, allEff = true, logX = true, pareto = true;
  defaults.forEach(function(n){ sel[n] = 1; });
  var plot = box.querySelector(".cmp-plot"), note = box.querySelector(".cmp-note"), subs = box.querySelector(".cmp-subs"), bestEl = box.querySelector(".cmp-best");
  var ctl = box.querySelector(".cmp-ctl"), par = box.querySelector(".cmp-par input");
  var list = box.querySelector(".cmp-list"), q = box.querySelector(".cmp-q"), count = box.querySelector(".cmp-count"), eff = box.querySelector(".cmp-eff input");
  var tab = box.querySelector(".cmp-tabs .on").getAttribute("data-tab"), subOf = {}, barOf = {};
  [].forEach.call(box.querySelectorAll(".cmp-tabs [data-k]"), function(b){ barOf[b.getAttribute("data-tab")] = b.getAttribute("data-k"); });
  [].forEach.call(subs.querySelectorAll("button.on"), function(b){ subOf[b.getAttribute("data-for")] = b.getAttribute("data-sub"); });
  var on = box.querySelector(".cmp-price .on"), price = on ? on.getAttribute("data-price") : "api", tier = "basic", plans = d.subs || {}, tabNote = note.textContent;
  var priceEl = box.querySelector(".cmp-price"), tierEl = box.querySelector(".cmp-tier");

  // Cost of a task inside a subscription: API cost × the plan's share of the API price.
  function priced(rows){
    if(tab!=="cost" || price!=="sub") return rows;
    return rows.map(function(r){
      var p = (plans[r.family] || {})[tier], o = {};
      for(var x in r) o[x] = r[x];
      o.sub = true;
      if(p && p[0]!=null){ o.cost = r.cost*p[0]; o.plan = p[1]; }
      else { o.api = true; o.plan = p ? p[1] : ""; }
      return o;
    });
  }

  function visible(){ return rows.filter(function(r){ return sel[r.family] && (allEff || fams[r.family].best===r); }); }
  function renderList(){
    var text = q.value.trim().toLowerCase(), groups = {}, order = [];
    Object.keys(fams).map(function(n){ return fams[n]; }).sort(function(a,b){ return b.best.score-a.best.score; }).forEach(function(f){
      if(text && (f.name+" "+f.creator).toLowerCase().indexOf(text)<0) return;
      if(!groups[f.creator]){ groups[f.creator] = []; order.push(f.creator); }
      groups[f.creator].push(f);
    });
    list.innerHTML = order.map(function(c){
      var lf = logoFile(c), lg = lf ? '<img src="'+BASE+'logos/'+lf+'" alt="">' : '<i class="lgd" style="background:'+groups[c][0].c+'"></i>';
      return '<div class="cmp-grp"><span>'+lg+esc(c)+'</span>'+groups[c].map(function(f){
        return '<label><input type="checkbox" data-f="'+esc(f.name)+'"'+(sel[f.name]?" checked":"")+'><i style="background:'+f.c+'"></i><em>'+esc(f.name)+'</em><small>'+fmt("score", f.best.score)+'</small></label>';
      }).join("")+'</div>';
    }).join("") || '<p class="cmp-empty">'+S.nothing+'</p>';
    count.textContent = Object.keys(sel).length+S.of+Object.keys(fams).length;
  }
  function draw(){
    var sub = subOf[tab] || barOf[tab], bars = !!sub;
    [].forEach.call(subs.children, function(b){ b.hidden = b.getAttribute("data-for")!==tab; });
    subs.hidden = !subOf[tab];
    if(ctl) ctl.hidden = bars;
    if(priceEl) priceEl.hidden = tab!=="cost";
    if(tierEl) tierEl.hidden = tab!=="cost" || price!=="sub";
    note.textContent = tab==="cost" && price==="sub" ? note.getAttribute("data-sub-note") : tabNote;
    if(bestEl) bestEl.innerHTML = "";
    var vis = priced(visible());
    if(bars) return columns(plot, vis, sub);
    var best = scatter(plot, vis, tab, {log:logX, pareto:pareto, label: tab==="cost" && price==="sub" ? S.subCost : null});
    // The models on the frontier, cheapest first: easier to read than the crowded chart.
    if(bestEl && pareto && best.length) bestEl.innerHTML = S.bestCost + best.filter(function(m, i){
      return best.map(function(x){ return x.family; }).indexOf(m.family)===i;
    }).map(function(m){ return "<b>"+esc(m.family)+"</b>"; }).join(" \u2192 ");
  }
  box.addEventListener("click", function(e){
    var b = e.target.closest ? e.target.closest("button") : null;
    if(!b) return;
    if(b.getAttribute("data-q")){
      sel = {};
      if(b.getAttribute("data-q")==="top") defaults.forEach(function(n){ sel[n] = 1; });
      renderList(); return draw();
    }
    var group = b.parentNode;
    var fr = b.getAttribute("data-for");   // sub-tabs of different tabs share one row
    for(var i=0;i<group.children.length;i++){
      var c = group.children[i];
      if(!fr || c.getAttribute("data-for")===fr) c.classList.toggle("on", c===b);
    }
    if(b.getAttribute("data-tab")){ tab = b.getAttribute("data-tab"); tabNote = b.getAttribute("data-note"); }
    if(b.getAttribute("data-sub")) subOf[b.getAttribute("data-for")] = b.getAttribute("data-sub");
    if(b.getAttribute("data-price")) price = b.getAttribute("data-price");
    if(b.getAttribute("data-tier")) tier = b.getAttribute("data-tier");
    if(b.getAttribute("data-scale")) logX = b.getAttribute("data-scale")==="log";
    draw();
  });
  list.addEventListener("change", function(e){
    var n = e.target.getAttribute("data-f");
    if(n==null) return;
    if(e.target.checked) sel[n] = 1; else delete sel[n];
    count.textContent = Object.keys(sel).length+S.of+Object.keys(fams).length;
    draw();
  });
  q.addEventListener("input", renderList);
  eff.addEventListener("change", function(){ allEff = eff.checked; draw(); });
  if(par) par.addEventListener("change", function(){ pareto = par.checked; draw(); });
  var w = plot.clientWidth, t;
  window.addEventListener("resize", function(){ clearTimeout(t); t = setTimeout(function(){ if(plot.clientWidth!==w){ w=plot.clientWidth; draw(); } }, 150); });
  renderList();
  draw();
}

function ready(){ var r = document.getElementById("eyai"); if(r) r.classList.remove("eyai-wait"); }

function refresh(){
  if(!window.fetch || !window.DOMParser) return ready();
  fetch(BASE+GUIDE,{cache:"no-cache"}).then(function(r){ if(!r.ok) throw 0; return r.text(); }).then(function(t){
    var doc = new DOMParser().parseFromString(t,"text/html");
    var fresh = doc.getElementById("eyai"), cur = document.getElementById("eyai");
    if(!fresh || !cur || fresh.getAttribute("data-v")===cur.getAttribute("data-v")) return ready();
    var st = doc.getElementById("eyai-style"), curSt = document.getElementById("eyai-style");
    if(st && curSt) curSt.textContent = st.textContent;
    cur.parentNode.replaceChild(document.importNode(fresh,true), cur);
    readI18n();
    bindToc();
    initCompare();
    initRating();
    initPlans();
    initMore();
    ready();
  }).catch(ready);
}

window.addEventListener("scroll", onScroll, {passive:true});
window.addEventListener("resize", onScroll);
bindToc();
initCompare();
initRating();
initPlans();
initMore();
refresh();
})();
