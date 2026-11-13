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
var LABEL = {score:"Интеллект", cost:"Цена задачи", cost_total:"Общая стоимость", time:"Время на задачу", tokens:"Токены на задачу", tokens_total:"Всего токенов"};
var EFF = ["non-reasoning","minimal","low","medium","default","high","xhigh","max"];

function esc(t){ return String(t).replace(/[&<>"]/g, function(c){ return {"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]; }); }
function num(v, d){ return v.toLocaleString("ru-RU", {maximumFractionDigits: d}); }
function fmt(k, v, short){
  if(v==null) return "—";
  if(k==="score") return num(v, 1);
  if(k==="cost"||k==="cost_total") return "$" + num(v, v<1 ? (short?2:3) : v<100 ? (short?1:2) : 0);
  if(k==="time"){
    if(v<60) return Math.round(v)+" с";
    if(v<3600) return short ? num(v/60,1)+" мин" : Math.floor(v/60)+" мин "+Math.round(v%60)+" с";
    return short ? num(v/3600,1)+" ч" : Math.floor(v/3600)+" ч "+Math.round(v%3600/60)+" мин";
  }
  if(v>=1e9) return num(v/1e9,1)+" млрд";
  if(v>=1e6) return num(v/1e6,1)+" млн";
  if(v>=1e3) return num(v/1e3,short?0:1)+" тыс.";
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
  var keys = ["score","cost","cost_total","time","tokens","tokens_total"];
  var h = "<b>"+esc(m.family)+"</b><small>"+esc(m.creator)+(m.effort ? " · уровень "+esc(m.effort) : "")+"</small>";
  keys.forEach(function(x){ if(m[x]!=null) h += '<span'+(x===k?' class="on"':'')+'><i>'+LABEL[x]+'</i>'+fmt(x,m[x])+'</span>'; });
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
  if(!rows.length){ empty(plot, "Выберите модели в списке справа."); return []; }
  var W = plot.clientWidth, H = Math.round(Math.max(300, Math.min(480, W*0.62)));
  var M = {l:34, r:12, t:12, b:34}, iw = W-M.l-M.r, ih = H-M.t-M.b;
  var xs = rows.map(function(m){ return m[k]; }), ys = rows.map(function(m){ return m.score; });
  var y0 = Math.max(0, Math.floor((Math.min.apply(0,ys)-4)/10)*10), y1 = Math.ceil((Math.max.apply(0,ys)+3)/10)*10;
  var Y = function(v){ return M.t + (1-(v-y0)/(y1-y0))*ih; }, X, xt = [];
  if(opt.log){
    var x0 = Math.log10(Math.min.apply(0,xs)/1.35), x1 = Math.log10(Math.max.apply(0,xs)*1.35);
    X = function(v){ return M.l + (Math.log10(v)-x0)/(x1-x0)*iw; };
    xt = logTicks(Math.pow(10,x0), Math.pow(10,x1), k);
  } else {
    var xmax = Math.max.apply(0,xs), st = niceStep(xmax), xtop = Math.ceil(xmax*1.04/st)*st;
    X = function(v){ return M.l + v/xtop*iw; };
    for(var t0=0; t0<=xtop+st/2; t0+=st) xt.push(t0);
  }
  var svg = el("svg", {viewBox:"0 0 "+W+" "+H, height:H, role:"img", "aria-label":"Интеллект моделей против: "+LABEL[k]});
  for(var v=y0; v<=y1; v+=10){
    el("line", {x1:M.l, x2:W-M.r, y1:Y(v), y2:Y(v), "class":"gl"}, svg);
    el("text", {x:M.l-8, y:Y(v)+4, "text-anchor":"end", "class":"ax"}, svg).textContent = v;
  }
  xt.forEach(function(t){
    el("line", {x1:X(t), x2:X(t), y1:M.t, y2:H-M.b, "class":"gl"}, svg);
    el("text", {x:X(t), y:H-M.b+18, "text-anchor":"middle", "class":"ax"}, svg).textContent = fmt(k,t,true);
  });
  el("text", {x:W-M.r, y:H-M.b-6, "text-anchor":"end", "class":"ax"}, svg).textContent = LABEL[k]+" →";
  el("text", {x:M.l+6, y:M.t+14, "class":"ax"}, svg).textContent = "↑ Интеллект";
  // Reasoning levels of one model share a thin line in its colour.
  var fams = {};
  rows.forEach(function(m){ (fams[m.family] = fams[m.family] || []).push(m); });
  for(var f in fams) if(fams[f].length>1){
    var line = fams[f].slice().sort(function(a,b){ return a.eo-b.eo || a[k]-b[k]; });
    el("polyline", {points:line.map(function(m){ return X(m[k])+","+Y(m.score); }).join(" "), fill:"none", stroke:line[0].c, "stroke-width":1.2, "stroke-opacity":.5}, svg);
  }
  var best = opt.pareto ? frontier(rows, k) : [];
  if(best.length>1) el("polyline", {points:best.map(function(m){ return X(m[k])+","+Y(m.score); }).join(" "), fill:"none", stroke:"#2e2e38", "stroke-width":1.5, "stroke-linejoin":"round", "stroke-dasharray":"5 4"}, svg);
  var pts = [], axw = LABEL[k].length*6.3+16, boxes = [{x:W-M.r-axw, y:H-M.b-20, w:axw, h:18}, {x:M.l, y:M.t, w:90, h:18}];
  var labels = el("g", {}, svg), dots = el("g", {}, svg);
  rows.forEach(function(m){
    var on = best.indexOf(m)>=0, p = {m:m, on:on, x:X(m[k]), y:Y(m.score)};
    p.r = on ? 6.5 : 5;
    p.c = el("circle", {cx:p.x, cy:p.y, r:p.r, fill:m.c, stroke:"#fff", "stroke-width":1.5, "fill-opacity":on?1:0.5, "class":"pt"}, dots);
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
  if(!rows.length){ empty(plot, "Выберите модели в списке справа."); return; }
  var byF = {};
  rows.forEach(function(m){ (byF[m.family] = byF[m.family] || []).push(m); });
  var groups = Object.keys(byF).map(function(f){
    var r = byF[f].sort(function(a,b){ return a.eo-b.eo || a[k]-b[k]; });
    return {f:f, rows:r, c:r[0].c, max:Math.max.apply(0, r.map(function(x){ return x[k]; }))};
  }).sort(function(a,b){ return a.max-b.max; });
  var W = plot.clientWidth, narrow = W<600, n = rows.length, G = groups.length;
  var gap = narrow ? 8 : 18, M = {l:narrow?40:54, r:6, t:26};
  var unit = (W-M.l-M.r-gap*(G-1))/n, bw = Math.max(2, unit*0.8);
  var minGroup = Math.min.apply(0, groups.map(function(g){ return g.rows.length*unit; }));
  var rotate = minGroup < 58;
  M.b = rotate ? (narrow?124:140) : 84;
  var H = (narrow ? 340 : 460) + M.b - 84, ih = H-M.t-M.b, base = M.t+ih;
  var max = Math.max.apply(0, rows.map(function(m){ return m[k]; })), step = niceStep(max), top = Math.ceil(max/step)*step;
  var Y = function(v){ return M.t + (1-v/top)*ih; };
  var svg = el("svg", {viewBox:"0 0 "+W+" "+H, height:H, role:"img", "aria-label":LABEL[k]+" по моделям и уровням размышлений"});
  for(var v=0; v<=top+step/2; v+=step){
    el("line", {x1:M.l, x2:W-M.r, y1:Y(v), y2:Y(v), "class":"gl", "stroke-dasharray": v ? "2 4" : null}, svg);
    el("text", {x:M.l-8, y:Y(v)+4, "text-anchor":"end", "class":"ax"}, svg).textContent = fmt(k, v, true);
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

/* rating tabs: intelligence, knowledge reliability, fields */
var RT_CAP = {score:"Топ-30 моделей, баллы из 100", omni:"Итоговый балл от −100 до 100", acc:"Доля верных ответов",
  hall:"Доля выдуманных ответов, меньше — лучше", fin:"Баллы из 100", ops:"Баллы из 100", law:"Баллы из 100",
  med:"Баллы из 100", eng:"Баллы из 100", eco:"Баллы из 100"};
var RT_NOTE = {omni:"За верный ответ плюс, за выдуманный минус, за честное «не знаю» ноль. Ниже нуля — модель чаще выдумывает, чем знает.",
  acc:"Сколько вопросов на знания модель ответила верно. Больше — лучше.",
  hall:"Как часто модель выдумывает ответ, когда должна была сказать «не знаю». Меньше — лучше."};

function initRating(){
  var rt = document.querySelector("#eyai .rt");
  if(!rt || rt.getAttribute("data-on")) return;
  rt.setAttribute("data-on", "1");
  var chart = rt.parentNode, ol = chart.querySelector(".bars"), legend = chart.querySelector(".legend"), cap = chart.querySelector(".rt-cap");
  var note = rt.querySelector(".rt-note"), colors = {};
  try { colors = JSON.parse(rt.getAttribute("data-colors")); } catch(e){}
  var tab = "score", metric = "score", tabNote = note.textContent;

  function render(d){
    var pct = metric==="acc" || metric==="hall", asc = metric==="hall";
    var list = (metric==="score" ? d.models.map(function(m){ return {name:m.name, creator:m.creator, effort:m.effort, v:m.score}; })
      : (d.bench||[]).filter(function(m){ return m[metric]!=null; }).map(function(m){ return {name:m.name, creator:m.creator, effort:m.effort, v:m[metric]}; }))
      .sort(function(a,b){ return asc ? a.v-b.v : b.v-a.v; }).slice(0, 30);
    var max = Math.max.apply(0, list.map(function(m){ return Math.abs(m.v); })) || 1, seen = {}, leg = [];
    ol.innerHTML = list.map(function(m, i){
      var c = colorFrom(colors, m.creator), f = logoFile(m.creator), w = Math.max(3, Math.round(Math.abs(m.v)/max*100));
      var name = esc(m.name + (m.effort ? " ("+m.effort+")" : "")), r = Math.round(m.v), val = (r<0 ? "−" : "") + Math.abs(r) + (pct ? "%" : "");
      if(!seen[m.creator]){ seen[m.creator] = 1; leg.push('<span><i style="background:'+c+'"></i>'+esc(m.creator)+'</span>'); }
      var lo = f ? '<img src="'+BASE+'logos/'+f+'" width="20" height="20" alt="">' : '<b class="lgl" style="--c:'+c+'">'+esc(m.creator.charAt(0).toUpperCase())+'</b>';
      return '<li class="bar'+(m.v<0 ? " neg" : "")+'" title="'+name+' · '+esc(m.creator)+' · '+val+'"><span class="i">'+(i+1)+'</span><span class="lo">'+lo+'</span>'+
        '<span class="n"><span>'+name+'</span><small>'+esc(m.creator)+'</small></span><span class="t"><span class="f'+(w<14 ? " sm" : "")+'" style="--c:'+c+';--w:'+w+'%"><em>'+val+'</em></span></span></li>';
    }).join("");
    legend.innerHTML = leg.join("");
    cap.textContent = metric==="score" ? "Топ-"+list.length+" моделей, баллы из 100" : RT_CAP[metric];
    note.textContent = RT_NOTE[metric] || tabNote;
  }
  function show(){
    var subs = rt.querySelectorAll(".rt-subs");
    for(var i=0;i<subs.length;i++) subs[i].hidden = subs[i].getAttribute("data-for")!==tab;
    loadData().then(function(d){ LOGOS = d.logos || LOGOS; render(d); }).catch(function(){});
  }
  rt.addEventListener("click", function(e){
    var b = e.target.closest ? e.target.closest("button") : null;
    if(!b) return;
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
}

/* tabs for the subscription tables */
function initPlans(){
  var box = document.querySelector("#eyai .pl-box");
  if(!box || box.getAttribute("data-on")) return;
  box.setAttribute("data-on", "1");
  box.querySelector(".pl-tabs").addEventListener("click", function(e){
    var b = e.target.closest ? e.target.closest("button") : null;
    if(!b) return;
    var btns = box.querySelectorAll(".pl-tabs button"), panels = box.querySelectorAll(".pl-panel"), k = Array.prototype.indexOf.call(btns, b);
    for(var i=0;i<btns.length;i++){ btns[i].classList.toggle("on", i===k); panels[i].hidden = i!==k; }
  });
}

function initCompare(){
  var box = document.querySelector("#eyai .cmp");
  if(!box || box.getAttribute("data-on") || !window.fetch) return;
  box.setAttribute("data-on", "1");
  var plot = box.querySelector(".cmp-plot");
  loadData().then(function(d){ setupCompare(box, d); })
    .catch(function(){ empty(plot, "Не удалось загрузить данные. Обновите страницу."); });
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
  var tab = box.querySelector(".cmp-tabs .on").getAttribute("data-tab"), first = subs.querySelector("button"), sub = first ? first.getAttribute("data-sub") : "cost";

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
    }).join("") || '<p class="cmp-empty">Ничего не найдено</p>';
    count.textContent = Object.keys(sel).length+" из "+Object.keys(fams).length;
  }
  function draw(){
    subs.hidden = tab!=="tokens";
    if(ctl) ctl.hidden = tab==="tokens";
    bestEl.innerHTML = "";
    var vis = visible();
    if(tab==="tokens") return columns(plot, vis, sub);
    var best = scatter(plot, vis, tab, {log:logX, pareto:pareto});
    if(best.length) bestEl.innerHTML = (tab==="cost" ? "Самые выгодные: " : "Самые быстрые для своего уровня: ") +
      best.filter(function(m, i){ return best.map(function(x){ return x.family; }).indexOf(m.family)===i; })
        .map(function(m){ return "<b>"+esc(m.family)+"</b>"; }).join(" → ") + ". Наведите на точку, чтобы увидеть цену и уровень размышлений.";
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
    for(var i=0;i<group.children.length;i++) group.children[i].classList.toggle("on", group.children[i]===b);
    if(b.getAttribute("data-tab")){ tab = b.getAttribute("data-tab"); note.textContent = b.getAttribute("data-note"); }
    if(b.getAttribute("data-sub")) sub = b.getAttribute("data-sub");
    if(b.getAttribute("data-scale")) logX = b.getAttribute("data-scale")==="log";
    draw();
  });
  list.addEventListener("change", function(e){
    var n = e.target.getAttribute("data-f");
    if(n==null) return;
    if(e.target.checked) sel[n] = 1; else delete sel[n];
    count.textContent = Object.keys(sel).length+" из "+Object.keys(fams).length;
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
  fetch(BASE+"guide.html",{cache:"no-cache"}).then(function(r){ if(!r.ok) throw 0; return r.text(); }).then(function(t){
    var doc = new DOMParser().parseFromString(t,"text/html");
    var fresh = doc.getElementById("eyai"), cur = document.getElementById("eyai");
    if(!fresh || !cur || fresh.getAttribute("data-v")===cur.getAttribute("data-v")) return ready();
    var st = doc.getElementById("eyai-style"), curSt = document.getElementById("eyai-style");
    if(st && curSt) curSt.textContent = st.textContent;
    cur.parentNode.replaceChild(document.importNode(fresh,true), cur);
    bindToc();
    initCompare();
    initRating();
    initPlans();
    ready();
  }).catch(ready);
}

window.addEventListener("scroll", onScroll, {passive:true});
window.addEventListener("resize", onScroll);
bindToc();
initCompare();
initRating();
initPlans();
refresh();
})();
