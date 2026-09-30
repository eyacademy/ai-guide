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
  }).catch(function(){});
}

window.addEventListener("scroll", onScroll, {passive:true});
window.addEventListener("resize", onScroll);
bindToc();
refresh();
})();
