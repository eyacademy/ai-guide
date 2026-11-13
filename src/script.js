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

function num(v, d){ return v.toLocaleString("ru-RU", {maximumFractionDigits: d}); }
function fmt(k, v, short){
  if(v==null) return "—";
  if(k==="score") return String(v);
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
  for(var a in attrs) e.setAttribute(a, attrs[a]);
  if(parent) parent.appendChild(e);
  return e;
}

function logTicks(lo, hi, k){
  var steps = k==="time" ? [10,30,60,120,300,600,1200,1800,3600,7200,14400,28800] : null, out = [];
  if(steps){ for(var i=0;i<steps.length;i++) if(steps[i]>=lo && steps[i]<=hi) out.push(steps[i]); return out; }
  for(var p=Math.floor(Math.log10(lo)); p<=Math.ceil(Math.log10(hi)); p++)
    [1,2,5].forEach(function(m){ var v=m*Math.pow(10,p); if(v>=lo && v<=hi) out.push(v); });
  return out.length>8 ? out.filter(function(v){ return String(v).replace(/[0.]/g,"")==="1"; }) : out;
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
  var keys = ["score","cost","cost_total","time","tokens","tokens_total"], h = "<b>"+m.name+"</b><small>"+m.creator+"</small>";
  keys.forEach(function(x){ if(m[x]!=null) h += '<span'+(x===k?' class="on"':'')+'><i>'+LABEL[x]+'</i>'+fmt(x,m[x])+'</span>'; });
  return h;
}

function showTip(plot, m, k, x, y){
  var tip = plot.querySelector(".cmp-tip");
  if(!tip){ tip=document.createElement("div"); tip.className="cmp-tip"; plot.appendChild(tip); }
  tip.innerHTML = tipHtml(m, k);
  tip.style.display = "block";
  var w = tip.offsetWidth, h = tip.offsetHeight, W = plot.clientWidth;
  var left = x+14+w > W ? x-14-w : x+14;
  tip.style.left = Math.max(0, left)+"px";
  tip.style.top = Math.max(0, y-h-10)+"px";
}
function hideTip(plot){ var t=plot.querySelector(".cmp-tip"); if(t) t.style.display="none"; }

function scatter(plot, rows, k){
  rows = rows.filter(function(m){ return m[k]!=null; });
  var W = plot.clientWidth, H = Math.round(Math.max(300, Math.min(460, W*0.6)));
  var M = {l:34, r:12, t:12, b:34}, iw = W-M.l-M.r, ih = H-M.t-M.b;
  var xs = rows.map(function(m){ return m[k]; }), ys = rows.map(function(m){ return m.score; });
  var x0 = Math.log10(Math.min.apply(0,xs)/1.35), x1 = Math.log10(Math.max.apply(0,xs)*1.35);
  var y0 = Math.max(0, Math.floor((Math.min.apply(0,ys)-4)/10)*10), y1 = Math.ceil((Math.max.apply(0,ys)+3)/10)*10;
  var X = function(v){ return M.l + (Math.log10(v)-x0)/(x1-x0)*iw; }, Y = function(v){ return M.t + (1-(v-y0)/(y1-y0))*ih; };
  var svg = el("svg", {viewBox:"0 0 "+W+" "+H, height:H, role:"img", "aria-label":"Интеллект моделей против: "+LABEL[k]});
  for(var v=y0; v<=y1; v+=10){
    el("line", {x1:M.l, x2:W-M.r, y1:Y(v), y2:Y(v), "class":"gl"}, svg);
    el("text", {x:M.l-8, y:Y(v)+4, "text-anchor":"end", "class":"ax"}, svg).textContent = v;
  }
  logTicks(Math.pow(10,x0), Math.pow(10,x1), k).forEach(function(t){
    el("line", {x1:X(t), x2:X(t), y1:M.t, y2:H-M.b, "class":"gl"}, svg);
    el("text", {x:X(t), y:H-M.b+18, "text-anchor":"middle", "class":"ax"}, svg).textContent = fmt(k,t,true);
  });
  el("text", {x:W-M.r, y:H-M.b-6, "text-anchor":"end", "class":"ax"}, svg).textContent = LABEL[k]+" →";
  el("text", {x:M.l+6, y:M.t+14, "class":"ax"}, svg).textContent = "↑ Интеллект";
  var best = frontier(rows, k);
  el("polyline", {points:best.map(function(m){ return X(m[k])+","+Y(m.score); }).join(" "), fill:"none", stroke:"#2e2e38", "stroke-width":1.5, "stroke-linejoin":"round", "stroke-dasharray":"5 4"}, svg);
  var axw = LABEL[k].length*6.3+16, pts = [], boxes = [{x:W-M.r-axw, y:H-M.b-20, w:axw, h:18}, {x:M.l, y:M.t, w:90, h:18}], labels = el("g", {}, svg), dots = el("g", {}, svg);
  rows.forEach(function(m){
    var on = best.indexOf(m)>=0, p = {m:m, x:X(m[k]), y:Y(m.score)};
    p.c = el("circle", {cx:p.x, cy:p.y, r:on?6.5:5, fill:m.c, stroke:"#fff", "stroke-width":1.5, "fill-opacity":on?1:0.45, "class":"pt"}, dots);
    pts.push(p);
  });
  // Labels: best models first, then by score; skip any that would overlap.
  pts.slice().sort(function(a,b){ return (best.indexOf(b.m)>=0)-(best.indexOf(a.m)>=0) || b.m.score-a.m.score; }).forEach(function(p){
    var w = p.m.name.length*6.3+4, h = 14, right = p.x+10+w <= W-M.r;
    var bx = {x: right ? p.x+9 : p.x-9-w, y: p.y-h/2, w:w, h:h};
    var hit = boxes.some(function(b){ return bx.x<b.x+b.w && bx.x+bx.w>b.x && bx.y<b.y+b.h && bx.y+bx.h>b.y; }) ||
              pts.some(function(q){ return q!==p && q.x>bx.x-4 && q.x<bx.x+bx.w+4 && q.y>bx.y-4 && q.y<bx.y+bx.h+4; });
    if(hit || bx.x<M.l) return;
    boxes.push(bx);
    el("text", {x: right ? p.x+9 : p.x-9, y:p.y+4, "text-anchor": right?"start":"end", "class": best.indexOf(p.m)>=0 ? "lb on" : "lb"}, labels).textContent = p.m.name;
  });
  plot.innerHTML = ""; plot.appendChild(svg);
  var cur = null;
  function pick(e){
    var r = svg.getBoundingClientRect(), sx = W/r.width, mx = (e.clientX-r.left)*sx, my = (e.clientY-r.top)*sx, near = null, d = 26*26;
    pts.forEach(function(p){ var dd=(p.x-mx)*(p.x-mx)+(p.y-my)*(p.y-my); if(dd<d){ d=dd; near=p; } });
    if(near===cur) return;
    if(cur) cur.c.setAttribute("r", best.indexOf(cur.m)>=0?6.5:5);
    cur = near;
    if(!near) return hideTip(plot);
    near.c.setAttribute("r", 9);
    showTip(plot, near.m, k, near.x/sx, near.y/sx);
  }
  svg.addEventListener("pointermove", pick);
  svg.addEventListener("pointerdown", pick);
  svg.addEventListener("pointerleave", function(){ if(cur) cur.c.setAttribute("r", best.indexOf(cur.m)>=0?6.5:5); cur=null; hideTip(plot); });
  return best;
}

function niceStep(max){
  var raw = max/5, p = Math.pow(10, Math.floor(Math.log10(raw))), m = raw/p;
  return (m<=1 ? 1 : m<=2 ? 2 : m<=2.5 ? 2.5 : m<=5 ? 5 : 10)*p;
}

function columns(plot, rows, k){
  rows = rows.filter(function(m){ return m[k]!=null; }).sort(function(a,b){ return a[k]-b[k]; });
  var W = plot.clientWidth, narrow = W<600, H = narrow ? 360 : 420;
  var M = {l:narrow?40:52, r:8, t:22, b:narrow?96:120}, iw = W-M.l-M.r, ih = H-M.t-M.b;
  var max = Math.max.apply(0, rows.map(function(m){ return m[k]; })), step = niceStep(max), top = Math.ceil(max/step)*step;
  var slot = iw/rows.length, bw = Math.max(4, Math.min(44, slot*0.66));
  var Y = function(v){ return M.t + (1-v/top)*ih; };
  var svg = el("svg", {viewBox:"0 0 "+W+" "+H, height:H, role:"img", "aria-label":LABEL[k]+" по моделям"});
  for(var v=0; v<=top+step/2; v+=step){
    el("line", {x1:M.l, x2:W-M.r, y1:Y(v), y2:Y(v), "class":"gl"}, svg);
    el("text", {x:M.l-8, y:Y(v)+4, "text-anchor":"end", "class":"ax"}, svg).textContent = fmt(k, v, true);
  }
  var cols = [];
  rows.forEach(function(m, i){
    var cx = M.l + slot*(i+0.5), y = Y(m[k]);
    var g = el("g", {"class":"col"}, svg);
    el("rect", {x:M.l+slot*i, y:M.t, width:slot, height:ih, fill:"transparent"}, g);
    var r = el("rect", {x:cx-bw/2, y:y, width:bw, height:Math.max(1, M.t+ih-y), fill:m.c}, g);
    if(slot>=34) el("text", {x:cx, y:y-6, "text-anchor":"middle", "class":"vl"}, g).textContent = fmt(k, m[k], true);
    el("text", {x:cx+3, y:M.t+ih+12, "text-anchor":"end", transform:"rotate(-45 "+(cx+3)+" "+(M.t+ih+12)+")", "class":"lb"}, g).textContent = m.name;
    cols.push({g:g, r:r, m:m, cx:cx, y:y});
  });
  plot.innerHTML = ""; plot.appendChild(svg);
  var cur = null;
  function pick(e){
    var b = svg.getBoundingClientRect(), sx = W/b.width, mx = (e.clientX-b.left)*sx, i = Math.floor((mx-M.l)/slot);
    var c = cols[i] || null;
    if(c===cur) return;
    cur = c;
    cols.forEach(function(o){ o.g.setAttribute("class", "col"+(c && o!==c ? " dim" : "")); });
    if(!c) return hideTip(plot);
    showTip(plot, c.m, k, c.cx/sx, c.y/sx);
  }
  svg.addEventListener("pointermove", pick);
  svg.addEventListener("pointerdown", pick);
  svg.addEventListener("pointerleave", function(){ cur=null; cols.forEach(function(o){ o.g.setAttribute("class","col"); }); hideTip(plot); });
}

function initCompare(){
  var box = document.querySelector("#eyai .cmp");
  if(!box || box.getAttribute("data-on")) return;
  box.setAttribute("data-on", "1");
  var rows; try { rows = JSON.parse(box.getAttribute("data-models")); } catch(e){ return; }
  var plot = box.querySelector(".cmp-plot"), note = box.querySelector(".cmp-note"), subs = box.querySelector(".cmp-subs"), bestEl = box.querySelector(".cmp-best");
  var tab = box.querySelector(".cmp-tabs .on").getAttribute("data-tab"), first = subs.querySelector("button");
  var sub = first ? first.getAttribute("data-sub") : "cost";
  function draw(){
    subs.hidden = tab!=="tokens";
    bestEl.innerHTML = "";
    if(tab==="tokens") return columns(plot, rows, sub);
    var best = scatter(plot, rows, tab);
    bestEl.innerHTML = (tab==="cost" ? "Самые выгодные: " : "Самые быстрые для своего уровня: ") +
      best.map(function(m){ return "<b>"+m.name+"</b> "+fmt(tab, m[tab]); }).join(" → ");
  }
  box.addEventListener("click", function(e){
    var b = e.target.closest ? e.target.closest("button") : null;
    if(!b) return;
    var group = b.parentNode;
    for(var i=0;i<group.children.length;i++) group.children[i].classList.toggle("on", group.children[i]===b);
    if(b.getAttribute("data-tab")){ tab = b.getAttribute("data-tab"); note.textContent = b.getAttribute("data-note"); }
    if(b.getAttribute("data-sub")) sub = b.getAttribute("data-sub");
    draw();
  });
  var w = plot.clientWidth, t;
  window.addEventListener("resize", function(){ clearTimeout(t); t = setTimeout(function(){ if(plot.clientWidth!==w){ w=plot.clientWidth; draw(); } }, 150); });
  draw();
}

function refresh(){
  if(!window.fetch || !window.DOMParser) return;
  fetch(BASE+"guide.html",{cache:"no-cache"}).then(function(r){ if(!r.ok) throw 0; return r.text(); }).then(function(t){
    var doc = new DOMParser().parseFromString(t,"text/html");
    var fresh = doc.getElementById("eyai"), cur = document.getElementById("eyai");
    if(!fresh || !cur || fresh.getAttribute("data-v")===cur.getAttribute("data-v")) return;
    var st = doc.getElementById("eyai-style"), curSt = document.getElementById("eyai-style");
    if(st && curSt) curSt.textContent = st.textContent;
    cur.parentNode.replaceChild(document.importNode(fresh,true), cur);
    bindToc();
    initCompare();
  }).catch(function(){});
}

window.addEventListener("scroll", onScroll, {passive:true});
window.addEventListener("resize", onScroll);
bindToc();
initCompare();
refresh();
})();
