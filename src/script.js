(function(){
var BASE = "https://eyacademy.github.io/ai-guide/";

function bindToc(){
  var toc = document.querySelector("#eyai .toc");
  if(!toc) return;
  toc.addEventListener("click", function(e){
    var a = e.target.closest ? e.target.closest("a") : null;
    if(!a) return;
    var el = document.getElementById(a.getAttribute("href").slice(1));
    if(!el) return;
    e.preventDefault(); e.stopPropagation();
    var head = 0, menus = document.querySelectorAll(".t228, .t-menu__fixed, [class*='positionfixed']");
    for(var k=0;k<menus.length;k++){ var r=menus[k].getBoundingClientRect(); if(r.top<=0 && r.bottom>head && r.height<200) head=r.bottom; }
    window.scrollTo({top: el.getBoundingClientRect().top + window.pageYOffset - head + 24, behavior: "smooth"});
  });
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

bindToc();
refresh();
})();
