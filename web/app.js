/* IKKI · frontend — API နှင့် တကယ် ချိတ်ထားသည် (mock မဟုတ်) */
(function(){
'use strict';
var $=function(i){return document.getElementById(i)};
var TOKEN = localStorage.getItem('ikki_token') || '';
var cur   = localStorage.getItem('ikki_lang') || 'my';
var STAGE_MY=["ဗီဒီယို ဖတ်နေသည်","စကားသံ နားထောင်နေသည်","တိတ်ဆိတ်မှု တိုင်းပြီး ဖြတ်နေသည်",
  "မြန်မာစာတန်း ရေးနေသည်","ဂရပ်ဖစ် တပ်နေသည်","အသံနဲ့ သီချင်း ချိန်နေသည်","အရောင် ချိန်ပြီး ထုတ်နေသည်"];
var STAGE_EN=["Reading your footage","Listening to the speech","Measuring silence, then cutting",
  "Writing the Burmese captions","Laying in the graphics","Balancing sound and music","Grading and rendering"];
// ⚠️ ဖော်ပြချက်ကို **ဘာသာစကား ၂ မျိုး** ထားရမည် — အရင်က မြန်မာတစ်မျိုးတည်း
//    ဖြစ်ပြီး `.my` class နဲ့ ထားသဖြင့် EN mode မှာလည်း မြန်မာအတိုင်း ကျန်ခဲ့သည်
//    (English သုံးစွဲသူအတွက် ဖတ်မရ)。 [id, label, my, en, font, meta]
var STYLES={creator:[
  ["cinematic-vlog","Cinematic Vlog","ရုပ်ရှင်ဆန် · အသက်ရှုသံ ချန်",
   "Cinematic · keeps the breaths","Pyidaungsu Regular","24fps"],
  ["vlog","Vlog","သွက် · karaoke စာတန်း",
   "Brisk · karaoke captions","MyanmarYinmar","30fps"],
  ["podcast","Podcast","စကား အဓိက · ထပ်နေတာ ဖြုတ်",
   "Talk first · repeats removed","Pyidaungsu","30fps"],
  ["knowledge","Knowledge Sharing","infographic များများ",
   "Heavy on infographics","MyanmarSansPro","30fps"],
  /* ⚠️ style ထည့်တိုင်း **နှစ်နေရာ** ထည့်ရမည်: `core/recipes.py` + ဒီစာရင်း。
     ⚠️ အောက်က ၃ ခုက **reference ၃ ပုဒ် တိုင်းပြီး** ဆောက်ထားသည်
        (`assets/calib/ref_hype_2026.json`) — ပုံစံ ၃ မျိုး ကွဲသဖြင့်
        ပျမ်းမျှ မယူဘဲ သီးသန့် ခွဲထားသည် (Zin ၂၀၂၆-၀၉-၂၀)。 */
  /* ⚠️ **Headtop** — plan-driven。 ကျန်ပုံစံတွေက worker က ဆုံးဖြတ်ပြီး
        ဒီတစ်ခုကတော့ **AI plan ကို အကောင်အထည်ဖော်**သည် ⇒ event တိုင်း
        သုံးစွဲသူ ပြင်နိုင်သည် (Zin ၂၀၂၆-၀၉-၂၀ spec)。 */
  /* ⚠️ ၇ ခုမြောက်က **နမူနာပုံ ဘယ်ဟာ သုံးမလဲ** — `prev/headtop.jpg` မရှိသေး၍
        `ref-talk` ကို ချေးသည်。 မထည့်လျှင် ပုံ ပျက်နေသည် (၂၀၂၆-၀၉-၂၁ တွေ့)。 */
  ["headtop","Headtop · Motion Edit","စာတန်း ဖတ်လွယ် · အဓိပ္ပာယ်အလိုက် ဂရပ်ဖစ် · ပြင်လို့ရ",
   "Readable captions · semantic graphics · editable","MasterpieceUniRound","plan","ref-talk"],
  /* ⚠️ "Fast Cut" ကို ဤပုံစံထဲ **ပေါင်းထားသည်** (Zin ၂၀၂၆-၀၉-၂၀) —
        ကွာတာက ဖြတ်နှုန်းတစ်ခုတည်း ဖြစ်၍ ပုံစံ သီးသန့် မလို。
        ပုံစံ ဆက်တင်ထဲက 「အရှိန်」 ကနေ မြန်/ပုံမှန် ရွေးပါ。 */
  ["ref-talk","Talking Head Motion Edit","စာသား ၃၅% · အောက်တန်း အခြေခံ · အရှိန် ရွေးလို့ရ",
   "Text 35% · lower-third led · pace selectable","MasterpieceUniRound","ref 1+3"],
  /* ⚠️ "· ZAE" ကို ဖယ်ထားသည် — brand စာရင်းမှာ **ZAE ဟု နာမည်ပေးထားသော
     သီးသန့် brand** ရှိပြီး (id b_94ad…) ဤ style ရဲ့ theme `zae` နှင့် မတူ。
     နာမည် တူနေသဖြင့် ဘယ်ဟာ ရွေးမှန်း မသိရခဲ့သည်。 */
  ["short-video","Short Video","3:4 · စာတန်းကြီး + navy အနားသတ်",
   "3:4 · big captions, navy outline","Pyidaungsu Bold","3:4"]],
 biz:[["promotional","Promotional","logo sting · CTA · ဈေးနှုန်း",
   "Logo sting · CTA · pricing","Noto Sans Myanmar","30–90s"],
  ["brand-review","Brand Review","နှိုင်းယှဉ်တန်း · ကြယ် အဆင့်",
   "Comparison rows · star ratings","Padauk Book","16:9"],
  /* ⚠️ အရင်က label "Short Video" ဖြစ်ပြီး Creator ရဲ့ "Short Video · ZAE" နဲ့
     **တိုက်နေ**ခဲ့သည် — dropdown မှာ အတူတူ ၂ ခု ပေါ်ကာ ဘယ်ဟာလဲ မသိရ
     (Zin ၂၀၂၆-၀၉-၂၀)。 ⇒ စီးပွားရေး ဟာကို ခွဲ နာမည် ပေးသည်。 */
  ["short-biz","Business Short","CTA · ဆက်သွယ်ရန် ကတ်",
   "CTA · contact card","Archivo Black","9:16"]],
 edu:[["course","Course","အခန်းလိုက် · အနားယူချိန် ချန်",
   "Chaptered · keeps the pauses","Padauk Book Bold","16:9"]]};

/* ⚠️ Zin ၂၀၂၆-၀၉-၂၀ (က): 「style ရွေးလိုက်တာနဲ့ brand + size အလိုလို ကိုက်」
   ⇒ ရွေးချယ်မှု ၃ ခု → ၁ ခု。 style တိုင်းမှာ `theme` ရှိပြီးသား ဖြစ်၍
   အဲဒါကို brand အဖြစ် သုံးသည် (built-in brand id = theme id)。
   size ကို **မသတ်မှတ်ပါ** — `state.fmt` ဗလာဆိုလျှင် brand ရဲ့ native
   (`FM.NATIVE`: zjl→16:9 · zae→3:4) အလိုလို သုံးသည်。
   ⚠️ သုံးစွဲသူ ကိုယ်တိုင် ရွေးလိုက်လျှင် **အဲဒါကို အနိုင်ပေးရမည်** — မဟုတ်လျှင်
   style ပြောင်းတိုင်း သူ့ ရွေးချယ်မှု ပျက်မည်。 ⇒ `ovr` အလံ。 */
var STHEME={'cinematic-vlog':'zjl','vlog':'zjl','podcast':'zjl',
  /* ⚠️ `ref-slides` · `ref-fast` က ပေါင်းပြီးသား — စာရင်းမှာ မပြတော့。
     ဒါပေမယ့် **အဟောင်း job တွေရဲ့ recipe အမည်** အဖြစ် ကျန်နိုင်သဖြင့်
     theme map မှာတော့ ထားရမည် — မရှိလျှင် ပုံစံ ပြန်ဖွင့်တဲ့အခါ ပျက်မည်。 */
  'headtop':'ikki','ref-talk':'ikki','ref-slides':'zjl','ref-fast':'zjl',
  'knowledge':'zjl','brand-review':'zjl','course':'zjl',
  'short-video':'zae','promotional':'zae','short-biz':'zae'};
/* ⚠️ style အချို့မှာ brand ရဲ့ native အရွယ်နဲ့ **မတူ**。 `short-biz` က
   CTA/ဆက်သွယ်ရန် ကတ် အတွက် 9:16 (TikTok/Reels) ဖြစ်ပြီး zae ရဲ့ native
   က 3:4 — ဒါကြောင့် သီးသန့် သတ်မှတ်ပေးရသည်。 */
var SSIZE={'short-biz':'9:16'};
function styleDefaults(){
  var want=STHEME[state.style];
  if(!want) return false;
  var hit=false;
  if(!state.ovrBrand && state.brand!==want){ state.brand=want; hit=true; }
  var ws=SSIZE[state.style]||'';
  if(!state.ovrFmt && state.fmt!==ws){ state.fmt=ws; hit=true; }  // ws ဗလာ ⇒ brand native
  return hit;
}
var NATIVE={};
var BRANDS=[];
var FONTS=[];
var FMTS=[];
/* ⚠️ Zin ၂၀၂၆-၀၉-၁၉: 「တစ်ပုဒ်ပြီးတာနဲ့ နောက်တစ်ပုဒ် တန်း edit လုပ်လို့ရအောင်」
   ⇒ ရွေးချယ်မှုကို **မှတ်ထား**သည် — နောက်ဗီဒီယိုမှာ အစကနေ ပြန်ရွေးစရာ မလို。 */
var SKEY='ikki_prefs';
var state={style:'short-video', family:'', brand:'zae', font:'', fmt:'', cap:'', vfmt:'', job:null, poll:null, up:null,
  ovrBrand:false, ovrFmt:false};
try{ var _p=JSON.parse(localStorage.getItem(SKEY)||'{}');
  ['style','brand','font','fmt','cap','vfmt'].forEach(function(k){ if(_p[k]!=null) state[k]=_p[k] });
}catch(e){}
function savePrefs(){
  try{ localStorage.setItem(SKEY, JSON.stringify({style:state.style,brand:state.brand,
    font:state.font,fmt:state.fmt,cap:state.cap,vfmt:state.vfmt})) }catch(e){}
}

/* ── API ── */
function askToken(){
  /* ⚠️ အစမ်းအဆင့်မှာ login မရှိသေး — token တစ်ခုတည်းဖြင့် ဝင်သည်。
     localStorage မှာ သိမ်းထားသဖြင့် တစ်ကြိမ်ပဲ ထည့်ရသည်。 */
  var t=window.prompt(cur==='my'
    ? 'ဝင်ရောက်ရန် token ထည့်ပါ'
    : 'Enter your access token');
  if(t){ TOKEN=t.trim(); localStorage.setItem('ikki_token',TOKEN); location.reload(); }
}
function api(path,opt){
  opt=opt||{}; opt.headers=Object.assign({'Authorization':'Bearer '+TOKEN},opt.headers||{});
  return fetch('/api'+path,opt).then(function(r){
    if(r.status===401){ askToken(); throw new Error('auth'); }
    if(r.status===402) {scene('s-quota'); throw new Error('quota');}
    if(!r.ok) return r.text().then(function(t){throw new Error(t||r.status)});
    return r.json();
  });
}

/* ── ဘာသာစကား ── */
function lang(c){
  cur=c; localStorage.setItem('ikki_lang',c);
  $('l-my').setAttribute('aria-pressed',c==='my'?'true':'false');
  $('l-en').setAttribute('aria-pressed',c==='en'?'true':'false');
  document.documentElement.lang=c;
  [].forEach.call(document.querySelectorAll('[data-my]'),function(el){
    var v=el.getAttribute('data-'+c); if(v!=null) el.innerHTML=v;
  });
  // ⚠️ placeholder · title · aria-label တွေက **innerHTML မဟုတ်** ⇒
  //    အထက်က loop က မထိ、EN mode မှာ မြန်မာလို ကျန်နေသည် (တကယ် ဖြစ်ခဲ့:
  //    ရှာဖွေကွက်ရဲ့ placeholder နဲ့ ဖိုင်လုံခြုံရေး ခလုပ်ရဲ့ title)。
  [].forEach.call(document.querySelectorAll('[data-my-ph],[data-my-tt]'),function(el){
    var ph=el.getAttribute('data-'+c+'-ph'); if(ph!=null) el.setAttribute('placeholder',ph);
    var tt=el.getAttribute('data-'+c+'-tt');
    if(tt!=null){ el.setAttribute('title',tt); el.setAttribute('aria-label',tt); }
  });
  /* ⚠️ .my က သုံးစွဲသူ၏ စာသား — UI ဘာသာစကား ပြောင်းလည်း မြန်မာအတိုင်း ကျန်ရမည် */
  paintStyles(); if(state.job) paintSteps();
}

/* ── section ── */
var VIEWS=['v-new','v-lib','v-sty','v-acc'];
function go(id){
  VIEWS.forEach(function(v){var e=$(v); if(e) e.hidden=v!==id});
  [].forEach.call(document.querySelectorAll('[data-go]'),function(n){
    n.setAttribute('aria-current',n.getAttribute('data-go')===id?'page':'false')});
  if(id==='v-lib') loadJobs();
  if(id==='v-acc'||id==='v-sty') loadMeta();
  if(id==='v-sty') loadStyles();
  window.scrollTo({top:0,behavior:'smooth'});
}
var scenes=['s-ready','s-up','s-work','s-done','s-err','s-quota'];
function scene(id){scenes.forEach(function(s){var e=$(s); if(e) e.hidden=s!==id})}
/* Keep keyboard, screen-reader and visual order identical: Brand → Style → Video. */
function orderProjectFlow(){
  var root=$('s-ready'), style=root&&root.querySelector('.project-style');
  var video=root&&root.querySelector('.project-video');
  if(root&&style&&video) root.insertBefore(video,style.nextSibling);
}

function nice(t){
  t=String(t||'').replace(/\.(mp4|mov|m4v|mkv|webm|avi)$/i,'');
  return t.length>44 ? t.slice(0,41)+'…' : t;
}

/* ── ပုံစံ စာရင်း — **dropdown တစ်ခုတည်း** (Zin ၂၀၂၆-၀၉-၁၉: 「dropdown လေးနဲ့ ရွေးလို့ရတာက ပိုရှင်း」)
      ⚠️ category tab (Creator/Business/Education) **ဖျောက်ပြီး** — အားလုံး တစ်နေရာ、
         optgroup နဲ့ ခွဲပြသည် ⇒ နှိပ်ရမယ့် အကြိမ် ၂ → ၁。 */
var CATN={creator:['Creator','Creator'],biz:['Business','Business'],edu:['Education','Education']};
var STYLE_FAMILY={creator:'creator',biz:'business',edu:'business'};
function familyForStyle(id){
  var found='creator';
  Object.keys(STYLES).forEach(function(group){
    STYLES[group].forEach(function(style){ if(style[0]===id) found=STYLE_FAMILY[group]||'creator' });
  });
  return found;
}
function markPick(){
  document.querySelectorAll('[data-pick]').forEach(function(c){
    var on=c.getAttribute('data-pick')===state.style;
    c.style.outline = on ? '2.5px solid var(--ac)' : '';
    c.style.outlineOffset = on ? '2px' : '';
  });
}
/* ⚠️ style က brand/size ကို အလိုလို ရွေးပေးသဖြင့် **ဘာ သုံးမလဲ မြင်ရရမည်** —
   မမြင်ရလျှင် "အလိုလို" က ဖုံးကွယ်မှု ဖြစ်သည် (Zin ၂၀၂၆-၀၉-၂၀)。 */
/* ⚠️ `esc` က အရင်က function **၂ ခု အတွင်းမှာပဲ** `var esc` ဟု ကြေညာထားခဲ့
   (line ~1064 · ~1128) ⇒ အခြား scope မှာ **မရှိ**。 picker ကုဒ်မှာ သုံးမိ၍
   `esc is not defined` နဲ့ ပျက်မည် ဖြစ်ခဲ့သည် (deploy မလုပ်ခင် စမ်းစဉ် ဖမ်းမိ ·
   ၂၀၂၆-၀၉-၂၀)。 ⇒ module အဆင့် helper。 အတွင်းက local တွေကို မထိပါ。 */
function esc(x){ return String(x==null?'':x)
  .replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;')
  .replace(/"/g,'&quot;'); }
function paintAdv(){
  var el=$('advsum'); if(!el) return;
  var bn=(BRANDS.find?BRANDS.find(function(b){return b.id===state.brand}):null);
  var nat=NATIVE[state.brand]||'16:9';
  var sz=state.fmt||nat;
  el.textContent='— '+((bn&&bn.name)||state.brand)+' · '+sz
    + (state.ovrBrand||state.ovrFmt ? ' (ကိုယ်တိုင် ရွေးထား)' : '');
}
function paintProjectBrand(){
  var el=$('projectbrand'); if(!el) return;
  var brand=BRANDS.filter(function(b){return b.id===state.brand})[0]||BRANDS[0];
  if(!brand){
    el.innerHTML='<span class="brand-loading">'+(cur==='my'?'ဘရန်းကို ဖွင့်နေသည်…':'Loading your brand…')+'</span>';
    return;
  }
  var colors=(brand.colors||[]).slice(0,5);
  var logo=brand.logo ? ' style="background-image:url(/api/brands/'+esc(brand.id)+'/logo?t='+encodeURIComponent(TOKEN)+'&v='+Date.now()+')"' : '';
  el.innerHTML='<div class="brand-summary">'
    +'<div class="brand-mark"'+logo+'>'+(!brand.logo?esc((brand.name||'I').slice(0,1).toUpperCase()):'')+'</div>'
    +'<div class="brand-detail"><span class="eyebrow">'+(cur==='my'?'ACTIVE BRAND':'ACTIVE BRAND')+'</span>'
    +'<b>'+esc(brand.name)+'</b><small>'+esc(brand.mmf||'')+' · '+esc(brand.aspect||'')+'</small></div>'
    +'<div class="brand-swatches">'+colors.map(function(color){return '<i style="background:'+esc(color)+'"></i>'}).join('')+'</div></div>'
    +'<div class="brand-quick">'+BRANDS.map(function(b){return '<button class="bp" data-b="'+esc(b.id)+'"'
      +(b.id===state.brand?' aria-pressed="true"':'')+'>'+esc(b.name)+'</button>'}).join('')+'</div>';
}
function paintStyles(){
  var el=$('styles'); if(!el) return;
  /* ⚠️ Zin ၂၀၂၆-၀၉-၂၀: 「dropdown ပုံစံကြီးက မမိုက်ဘူး — နမူနာ ဗီဒီယို
     animation လေးတွေ ပါပြထားတဲ့ ပုံစံ ပိုကြိုက်」 ⇒ dropdown ဖြုတ်ပြီး ကတ်。
     ⚠️ နမူနာက **ဂရပ်ဖစ် ပုံစံ**ကို ပြသည် — ဖြတ်ချက်/စာတန်း အပြည့် မဟုတ်。
     ⚠️ preview clip တစ်ခုစီက အရွယ်သေး · silent ဖြစ်လို့ card မှာ တိုက်ရိုက် လှုပ်ရှားပြသည်။ */
  var cur_=state.style, pick=null;
  Object.keys(STYLES).forEach(function(c){
    STYLES[c].forEach(function(t){ if(t[0]===cur_) pick=t });
  });
  if(!pick){ pick=STYLES[Object.keys(STYLES)[0]][0]; cur_=state.style=pick[0]; }
  function dsc(t){ return cur==='my'?t[2]:t[3]; }

  var family=state.family||familyForStyle(cur_);
  if(family!=='creator'&&family!=='business') family='creator';
  state.family=family;
  var groups=family==='creator'?['creator']:['biz','edu'];
  var h='<div class="audience-tabs" role="tablist" aria-label="Audience">'
    +'<button type="button" data-family="creator" role="tab" aria-selected="'+(family==='creator')+'">'
    +(cur==='my'?'Creator':'Creator')+'</button>'
    +'<button type="button" data-family="business" role="tab" aria-selected="'+(family==='business')+'">'
    +(cur==='my'?'Business / Education':'Business / Education')+'</button></div>';
  h+='<div class="style-spotlight"><span class="eyebrow">'+(cur==='my'?'SELECTED DIRECTION':'SELECTED DIRECTION')+'</span>'
    +'<b>'+esc(pick[1])+'</b><p>'+esc(dsc(pick))+'</p></div>';
  h+='<div class="sgal">';
  groups.forEach(function(c){
    h+='<div class="sgal-h">'+esc(CATN[c][0])+'</div>';
    STYLES[c].forEach(function(t){
      var id=t[0];
      var preview=t[6]||id;
      h+='<button type="button" class="scard" data-sv="'+esc(id)+'"'
       + ' aria-pressed="'+(id===cur_?'true':'false')+'">'
       + '<span class="thumb">'
       +   '<img src="prev/'+esc(preview)+'.jpg" alt="" loading="lazy" decoding="async">'
       +   '<video src="prev/'+esc(preview)+'.mp4" muted autoplay loop playsinline preload="metadata"'
       +   ' disablepictureinpicture></video>'
       +   '<span class="tick" aria-hidden="true">✓</span>'
       + '</span>'
       + '<span class="meta"><b>'+esc(t[1])+'</b><s>'+esc(dsc(t))+'</s></span>'
       + '</button>';
    });
  });
  h+='</div>';
  h+='<p class="lede" style="font-size:12.5px;margin:10px 0 0">'
   + esc(pick[4])+' · '+esc(pick[5])+'</p>';
  el.innerHTML=h;
  paintAdv();

  var cards=[].slice.call(el.querySelectorAll('.scard'));
  function play(card,on){
    var v=card.querySelector('video'); if(!v) return;
    card.classList.toggle('play', on);
    if(on){ var q=v.play(); q&&q.catch&&q.catch(function(){}); }
    else { try{ v.pause(); v.currentTime=0 }catch(e){} }
  }
  cards.forEach(function(card){
    card.onmouseenter=function(){ play(card,true) };
    card.onmouseleave=function(){ play(card,false) };
    card.onfocus=function(){ play(card,true) };
    card.onblur=function(){ play(card,false) };
    card.onclick=function(){
      var v=card.getAttribute('data-sv');
      if(v===state.style) return;
      state.style=v;
      state.family=familyForStyle(v);
      if(styleDefaults()) loadMeta();
      paintStyles();
    };
  });
  /* ⚠️ ဖုန်းမှာ hover မရှိ ⇒ မြင်ကွင်းထဲ ရောက်တာနဲ့ ဖွင့်ပေးသည်。
     ⚠️ တစ်ချိန်တည်း အားလုံး ဖွင့်လျှင် ဖုန်း နှေးမည် — **တစ်ခုတည်း**သာ。 */
  if(window.matchMedia&&window.matchMedia('(hover:none)').matches&&window.IntersectionObserver){
    var io=new IntersectionObserver(function(es){
      es.forEach(function(e){
        if(e.isIntersecting&&e.intersectionRatio>0.6){
          cards.forEach(function(c){ play(c, c===e.target) });
        }
      });
    },{threshold:[0,0.6,1]});
    cards.forEach(function(c){ io.observe(c) });
  }
  markPick();
}

/* ── brand ── */
function loadMeta(){
  api('/brands').then(function(d){
    BRANDS=d.brands;
    // ⚠️ chip မှာ အရွယ် မပြတော့ဘူး — အရွယ်က သီးသန့် ရွေးတာ ဖြစ်သဖြင့်
    //    ဒီမှာ ပြလျှင် "ဘရန်းက အရွယ် သတ်မှတ်တယ်" ဟု အထင်မှားသည်。
    /* ⚠️ Zin ၂၀၂၆-၀၉-၂၀: 「brand နာမည်တွေ ဖြုတ်ပေးပါ · Default တစ်ခုစီ ထားပေး」
       တိုင်းချက်: job ၃၉ ခုလုံး `zjl`(၂၄) / `zae`(၁၅) ကိုပဲ သုံးပြီး —
       သုံးစွဲသူ brand ကို **တစ်ခါမှ ကိုယ်တိုင် မရွေးဖူး** (style ကနေ အလိုလို)。
       ⇒ နာမည်ရှည် မလို · ဘယ်ဟာက ပုံသေလဲ **အမှတ်အသား** သာ လိုသည်。 */
    var _dflt=(typeof STHEME!=='undefined')?STHEME[state.style]:null;
    $('brandpick').innerHTML=d.brands.map(function(b){
      return '<button class="chip bp" data-b="'+b.id+'"'+(b.id===state.brand?' aria-pressed="true"':'')+'>'+
        b.name+(b.id===_dflt?'<em class="dflt">'+(cur==='my'?'ပုံသေ':'default')+'</em>':'')+'<small>'+(b.colors||[]).slice(0,4).map(function(c){
          return '<i style="display:inline-block;width:8px;height:8px;border-radius:2px;margin-right:2px;background:'+c+'"></i>'
        }).join('')+'</small></button>';
    }).join('');
    var k=$('kits'); if(k) k.innerHTML=d.brands.map(function(b){
      return '<div class="card"'+(b.id===state.brand?' style="outline:2px solid var(--ac)"':'')+'>'+
        '<div style="display:flex;justify-content:space-between;align-items:baseline;margin-bottom:13px">'+
        '<b style="font-size:18px;font-weight:700;letter-spacing:-.03em">'+b.name+'</b>'+
        '<span class="mono" style="font-size:11px;color:var(--tx3)">'+b.aspect+'</span></div>'+
        '<div class="sws">'+b.colors.map(function(c){return '<i style="background:'+c+'" data-h="'+c.slice(1)+'"></i>'}).join('')+'</div>'+
        '<div class="opt" style="padding-top:12px;border:0"><div class="txt"><span>'+(cur==='my'?'မြန်မာ ဖောင့်':'Burmese type')+'</span></div><span class="mono" style="font-size:12px">'+b.mmf+'</span></div>'+
        '<div class="opt"><div class="txt"><span>Latin</span></div><span class="mono" style="font-size:12px">'+b.latin+'</span></div>'+
        '<div class="opt"><div class="txt"><span>'+(cur==='my'?'ပုံသေ အရွယ်':'Default size')+'</span></div><span class="mono" style="font-size:12px">'+b.aspect+'</span></div>'+
        // ⚠️ logo တင်လိုက်တာနဲ့ **ဗီဒီယိုရဲ့ theme ပါ ပြောင်း**သည် —
        //    logo ထဲက အရောင်ကို ထုတ်ပြီး brand.colors ထဲ ထည့်သည်。
        //    နောက်ခံကိုတော့ logo အရောင်အတိုင်း **မထားရ** — အဝါ/အဖြူ logo ဆိုလျှင်
        //    အဖြူစာတန်း လုံးဝ မမြင်ရ ⇒ အဆင်းယူပြီး အလင်း အတင်း ချသည်。
        '<div class="logobox">'+
          '<div class="logoprev" id="lp_'+b.id+'"'+(b.logo
            ? ' style="background-image:url(/api/brands/'+b.id+'/logo?t='+
              encodeURIComponent(TOKEN)+'&v='+Date.now()+')"' : '')+'></div>'+
          '<div style="flex:1;min-width:150px">'+
            '<label class="btn" style="display:inline-block;cursor:pointer">'+
              (cur==='my'?'Logo တင်မယ်':'Upload logo')+
              '<input type="file" accept="image/png,image/jpeg,image/webp" hidden data-logo="'+b.id+'"></label>'+
            (b.logo?'<button class="more" data-logodel="'+b.id+'" style="margin-left:10px">'+
              (cur==='my'?'ဖယ်မယ်':'Remove')+'</button>':'')+
            '<p class="lede" style="font-size:12px;margin:7px 0 0;color:var(--tx3)">'+
              (cur==='my'?'တင်လိုက်တာနဲ့ အရောင် ထုတ်ပြီး ဗီဒီယိုက သင့် theme အတိုင်း ဖြစ်သွားမယ်'
                         :'The palette is read from it and the video follows your theme')+'</p>'+
          '</div></div>'+
        '<button class="btn kit-e" data-edit="'+b.id+'">'+(cur==='my'?'ပြင်မယ်':'Edit')+'</button></div>';
    }).join('');
    paintProjectBrand();
  }).catch(function(){});
  paintBroll();
  api('/capsizes').then(function(d){
    var el=$('cappick'); if(!el) return;
    el.innerHTML=d.sizes.map(function(c){
      return '<button class="chip cp" data-cap="'+c.id+'"'+
        (c.id===state.cap?' aria-pressed="true"':'')+'>'+
        (cur==='my'?c.my:c.en)+'<small>'+Math.round(c.pct*1440)+'px</small></button>';
    }).join('');
  }).catch(function(){});
  api('/formats').then(function(d){
    var el=$('fmtpick'); if(!el) return;
    NATIVE=d.native||{}; FMTS=d.formats||[];
    var native=NATIVE[state.brand]||'';
    var G={vertical:[cur==='my'?'ဒေါင်လိုက်':'Vertical'],
           square:[cur==='my'?'စတုရန်း':'Square'],
           horizontal:[cur==='my'?'အလျားလိုက်':'Horizontal']};
    var by={};
    d.formats.forEach(function(f){ (by[f.group]=by[f.group]||[]).push(f) });
    el.innerHTML=Object.keys(G).filter(function(g){return by[g]}).map(function(g){
      return '<div class="fmtg"><span>'+G[g][0]+'</span><div class="fmts">'+
        by[g].map(function(f){
          // ⚠️ ပုံသေ (brand ရဲ့ native) ကို **မြင်သာစေရမည်** — မရွေးဘဲ
          //    ထားလျှင် ဘယ်အရွယ် ထွက်မလဲ သုံးစွဲသူ သိရမည်。
          var on = state.fmt ? (state.fmt===f.key) : (f.key===native);
          var ar = f.w/f.h, bw = ar>=1 ? 22 : Math.round(22*ar), bh = ar>=1 ? Math.round(22/ar) : 22;
          return '<button class="fmt" data-fmt="'+f.key+'"'+(on?' aria-pressed="true"':'')+'>'+
            '<i style="width:'+bw+'px;height:'+bh+'px"></i>'+
            '<span><b>'+f.key.replace('4K16:9','4K 16:9')+'</b>'+
            '<small>'+f.w+'×'+f.h+' · '+f.label+'</small></span>'+
            (f.key===native?'<span class="dflt">'+(cur==='my'?'ပုံသေ':'default')+'</span>':'')+
            '</button>';
        }).join('')+'</div></div>';
    }).join('');
  }).catch(function(){});
  api('/fonts').then(function(d){
    FONTS=d.fonts||[];
    var el=$('fontpick'); if(!el) return;
    el.innerHTML=d.fonts.map(function(f){
      // ⚠️ နာမည်တစ်ခုတည်း ပြလျှင် ဘယ်ဟာ ဘယ်လိုလဲ မသိဘူး — **ပုံစံ ပြရမည်**。
      //    ပုံက အဖြူ alpha ဖြစ်၍ CSS mask နဲ့ theme ရဲ့ စာအရောင် ယူသည် —
      //    မဟုတ်လျှင် light theme မှာ အဖြူပေါ်အဖြူ ဖြစ်ပြီး မမြင်ရ。
      return '<div class="lrow'+(f.id===state.font?' sel':'')+'" data-font="'+f.id+'">'+
        '<span class="fprev" style="-webkit-mask-image:url(/img/fonts/'+f.id+'.png);'+
          'mask-image:url(/img/fonts/'+f.id+'.png)" aria-hidden="true"></span>'+
        '<div class="lname"><b>'+f.name+'</b><span class="my">'+f.look+'</span></div>'+
        '<div class="lmeta hidesm">'+f.good+'</div>'+
        '<div class="ldur hidesm mono">'+f.id+'</div><div class="wave hidesm"></div>'+
        '<div class="lacts">'+(f.id===state.font
          ? '<span class="pill p-ac">'+(cur==='my'?'ရွေးထား':'Selected')+'</span>' : '')+'</div></div>';
    }).join('');
    FONTS = d.fonts;
    paintFontWhy();
  }).catch(function(){});
  api('/settings').then(function(st){
    var a=$('tgchat'); if(a && st.tg_chat) a.value=st.tg_chat;
    var b=$('tgtok');  if(b && st.tg_token) b.placeholder='သိမ်းထားပြီး';
  }).catch(function(){});
  paintMe(); paintPlan(); paintPay();
  api('/usage').then(function(u){
    var pc=Math.min(100,Math.round(u.minutes/u.quota*100));
    $('umeter').style.width=pc+'%';
    $('utext').textContent=Math.round(u.minutes)+' / '+u.quota+' min';
    var g=$('usage'); if(g) g.innerHTML=
      '<div class="card"><div class="stat ac">'+Math.round(u.minutes)+'</div><p style="font-size:12.5px;color:var(--tx2);margin-top:7px">'+
        (cur==='my'?'သုံးပြီး မိနစ် / '+u.quota:'Minutes used of '+u.quota)+'</p><div class="meter" style="margin-top:12px"><i style="width:'+pc+'%"></i></div></div>'+
      '<div class="card"><div class="stat">'+(u.quota-Math.round(u.minutes))+'</div><p style="font-size:12.5px;color:var(--tx2);margin-top:7px">'+
        (cur==='my'?'ကျန် မိနစ်':'Minutes left')+'</p></div>';
  }).catch(function(){});
}

/* ── တင်ခြင်း — ပြတ်လျှင် ဆက်တင်သည် ──
   ⚠️ offset ကို server က ဖိုင်အရွယ်နဲ့ တိုင်းသည်။ 409 ပြန်လာလျှင်
      server ပြောတဲ့ offset ကနေ ဆက်ရမည် — client ရဲ့ ကိန်းကို မယုံရ。 */
function upload(f){
  scene('s-up'); $('upname').textContent=f.name;
  var CH=8*1024*1024, sent=0, id=null, dead=false;
  $('upcancel').onclick=function(){dead=true; scene('s-ready')};
  function bar(){
    var pc=Math.min(100,Math.round(sent/f.size*100));
    $('upbar').style.width=pc+'%';
    $('upnum').textContent=(sent/1e9).toFixed(2)+' GB / '+(f.size/1e9).toFixed(2)+' GB · '+pc+'%';
  }
  return api('/upload/init',{method:'POST',headers:{'Content-Type':'application/json'},
      body:JSON.stringify({name:f.name,size:f.size})})
    .then(function(d){ id=d.upload_id; state.up=id; CH=d.chunk||CH;
      // ⚠️ R2 mode — browser က R2 ကို တိုက်ရိုက် တင်သည်。 VPS မဖြတ်သဖြင့်
      //    Cloudflare ရဲ့ အနီးဆုံး edge ကို သွားပြီး အများကြီး မြန်သည်。
      // ⚠️ ဖိုင်က worker ရဲ့ စက်ထဲ ရှိပြီးသားဆို **တစ် byte မှ မတင်ရ**
      if(d.mode==='have'){ sent=f.size; bar();
        $('upname').textContent=f.name+' — စက်ထဲ ရှိပြီးသား · တင်စရာ မလို ⚡';
        return {upload_id:id}; }
      if(d.mode==='r2') return r2up();
      function next(){
        if(dead) return Promise.reject(new Error('cancelled'));
        if(sent>=f.size) return {upload_id:id};
        var end=Math.min(f.size,sent+CH);
        return fetch('/api/upload/'+id+'/chunk?offset='+sent,{method:'PUT',
            headers:{'Authorization':'Bearer '+TOKEN,'Content-Type':'application/octet-stream'},
            body:f.slice(sent,end)})
          .then(function(r){return r.json().then(function(j){return {r:r,j:j}})})
          .then(function(x){
            if(x.r.status===409){ sent=x.j.received; bar(); return next(); }  /* server ကို ယုံ */
            sent=x.j.received; bar(); return next();
          })
          .catch(function(e){
            if(dead) throw e;
            return new Promise(function(res){setTimeout(res,2500)}).then(next);  /* ပြတ်လျှင် ပြန်ကြိုး */
          });
      }
      bar(); return next();
    });

  function r2up(){
    // ⚠️ အရင်က အပိုင်း **တစ်ခုပြီးမှ တစ်ခု** တင်ပြီး အပိုင်းတိုင်းအတွက်
    //    presigned URL ကို သီးသန့် သွားတောင်းခဲ့သည်。 တိုင်းချက် (၂၀၂၆-၀၉-၁၉):
    //      · presign အသွားအပြန် အလယ်တန်း ၂၀၀ ms (အများဆုံး ၆၇၆)
    //        ⇒ ၄.၅ GB (၈ MB အပိုင်း ၅၆၂ ခု) = **၁၁၂ စက္ကန့် စောင့်ရုံ**
    //      · Zin ရဲ့ လိုင်းမှာ parallel က **ပိုနှေး** (4.1 → 3.2 MB/s) —
    //        လိုင်း ကိုယ်တိုင် ပြည့်နေ၍。 ဒါပေမယ့် လိုင်း မြန်သော customer
    //        မှာ parallel က အများကြီး ကူသည် ⇒ **ပုံသေ မထားရ · တိုင်းပြီး ချိန်ရ**。
    var parts=[], next=1, inflight=0, urls={}, uNext=1, err=null, doneB=0;
    var CONC=1, best=0, bestC=1, probe=0, tMark=performance.now(), bMark=0;
    var NP=Math.ceil(f.size/CH);

    function grab(){           // presigned URL များ **အစုလိုက်** ကြိုတောင်း
      if(uNext>NP) return Promise.resolve();
      var k=Math.min(50, NP-uNext+1), from=uNext; uNext+=k;
      return api('/upload/'+id+'/parts?frm='+from+'&n='+k,{method:'POST'})
        .then(function(d){ (d.urls||[]).forEach(function(u,i){ urls[d.from+i]=u }) });
    }

    function tune(bytes){      // ⚠️ concurrency ကို **တိုင်းပြီး** ချိန်သည်
      doneB+=bytes;
      var el=(performance.now()-tMark)/1000;
      if(el<4) return;
      var mbps=(doneB-bMark)/1048576/el;
      if(mbps>best*1.08){ best=mbps; bestC=CONC; if(CONC<6) CONC++; }
      else if(CONC>bestC){ CONC=bestC; }
      else if(probe++%4===3 && CONC<6){ CONC++; }
      tMark=performance.now(); bMark=doneB;
    }

    function put(pn){
      var from=(pn-1)*CH, to=Math.min(f.size, from+CH), size=to-from;
      var tries=0;
      function go(){
        var u=urls[pn];
        if(!u) return grab().then(go);
        return fetch(u,{method:'PUT',body:f.slice(from,to)}).then(function(r){
          if(!r.ok) throw new Error('r2 '+r.status);
          var et=r.headers.get('ETag');
          // ⚠️ ETag မရလျှင် complete ကျမည် — bucket CORS ရဲ့ ExposeHeaders
          if(!et) throw new Error('ETag မရ — bucket CORS ကို စစ်ပါ');
          parts.push({n:pn, etag:et}); sent+=size; bar(); tune(size);
        }).catch(function(e){
          if(dead || String(e.message).indexOf('ETag')===0) throw e;
          if(++tries>4) throw e;
          delete urls[pn];      // URL သက်တမ်း ကုန်နိုင် — ပြန်တောင်း
          return new Promise(function(res){setTimeout(res,1500*tries)}).then(go);
        });
      }
      return go();
    }

    function pump(){
      if(err) return Promise.reject(err);
      if(dead) return Promise.reject(new Error('cancelled'));
      if(next>NP && inflight===0){
        // ⚠️ complete က အပိုင်း နံပါတ် **အစဉ်လိုက်** လိုသည် — အပြိုင် တင်၍ ရောနေ
        parts.sort(function(x,y){return x.n-y.n});
        return api('/upload/'+id+'/complete',{method:'POST',
            headers:{'Content-Type':'application/json'},
            body:JSON.stringify({parts:parts})})
          .then(function(){ return {upload_id:id} });
      }
      var jobs=[];
      while(inflight<CONC && next<=NP){
        var pn=next++; inflight++;
        jobs.push(put(pn).then(function(){inflight--},
                               function(e){inflight--; err=err||e}));
      }
      if(!jobs.length) jobs.push(new Promise(function(r){setTimeout(r,60)}));
      return Promise.race(jobs).then(pump);
    }
    bar(); return grab().then(pump);
  }
}

function start(f){
  // ⚠️ ပုံစံ မရွေးဘဲ မတင်ရ — ပြန်စ ရှာဖွေမှုက «ကင်မရာကို ပြောတာ» မှသာ အလုပ်ဖြစ်သည်
  //    (vlog ၅/၅ အောင် · podcast ကျ ၇၉.၆%)。 မရွေးလျှင် server က ပိတ်ထားမည်。
  if(!state.vfmt){
    alert(cur==='my'?'ဒီဗီဒီယိုက ဘယ်ပုံစံလဲ ရွေးပေးပါ':'Please pick what kind of video this is');
    var vb=$('vfmtbox'); if(vb&&vb.scrollIntoView) vb.scrollIntoView({behavior:'smooth',block:'center'});
    return;
  }
  upload(f).then(function(d){
    // ⚠️ အသံ ရှိလျှင် **ဗီဒီယို ပြီးမှ** တင်သည် — တစ်ပြိုင်တည်း တင်လျှင်
    //    လိုင်း မျှပြီး နှစ်ခုလုံး နှေးသည်。
    if(!AUD) return {upload_id:d.upload_id, audio:null};
    return upload(AUD).then(function(a){ return {upload_id:d.upload_id, audio:a.upload_id} });
  }).then(function(d){
    return api('/jobs',{method:'POST',headers:{'Content-Type':'application/json'},
      body:JSON.stringify({upload_id:d.upload_id,audio_upload_id:d.audio||'',
                           recipe:state.style,brand_id:state.brand,fmt:state.fmt,cap:state.cap,
                           font:state.font,title:f.name,vfmt:state.vfmt})});
  }).then(function(j){ savePrefs(); watch(j.job_id) })
    .catch(function(e){ if(String(e.message)!=='cancelled'&&String(e.message)!=='quota') fail(e.message) });
}

/* ── dual-system အသံ ── */
var AUD=null;
document.addEventListener('DOMContentLoaded',function(){
  var f=$('audfile'); if(!f) return;
  f.onchange=function(){
    AUD=this.files[0]||null;
    var n=$('audnote'), c=$('audclr');
    if(AUD){ n.textContent=(cur==='my'?'ရွေးထား: ':'Selected: ')+AUD.name+
      ' ('+(AUD.size/1e6).toFixed(1)+' MB)'; if(c) c.hidden=false; }
  };
  var c=$('audclr');
  if(c) c.onclick=function(){ AUD=null; f.value=''; c.hidden=true;
    $('audnote').textContent=(cur==='my'?'recorder ဖိုင် တင်ပါ — အလိုအလျောက် ချိန်ညှိပြီး ပေါင်းပါမယ်'
                                       :'Upload the recorder file — we align and merge it'); };
});

/* ── job စောင့်ကြည့်ခြင်း ── */
function paintSteps(){
  var names=cur==='my'?STAGE_MY:STAGE_EN, st=state.job?state.job.stage:0;
  $('steps').innerHTML=names.map(function(n,i){
    var c=i<st?'fin':(i===st?'on':'');
    return '<li class="'+c+'"><i></i><span>'+n+'</span></li>';
  }).join('');
}
function watch(jid){
  scene('s-work'); clearInterval(state.poll);
  function tick(){
    api('/jobs/'+jid).then(function(j){
      state.job=j;
      var st=j.stage||0, pc=Math.round(st/7*100);
      $('arc').style.strokeDashoffset=628-628*st/7;
      $('pct').textContent=pc+'%';
      $('eta').textContent = j.stage_name ? j.stage_name
        : (cur==='my' ? 'အဆင့် '+st+' / ၇' : 'stage '+st+' of 7');
      paintSteps(); dock(j);
      // ⚠️ queued အနေနဲ့ ရပ်နေရင် **အကြောင်းရင်း ပြရမည်** — render server
      //    (Mac) ပိတ်နေလျှင် ဘာမှ မပြဘဲ ရပ်နေခဲ့သည်。
      if(j.status==='queued') checkWorker();
      // ⚠️ **review မှာ ရပ်ရမည်** — မရပ်လျှင် ၃ စက္ကန့်တိုင်း ဆက်မေးပြီး
      //    dock က "2/7 လုပ်နေဆဲ" ဟု ထာဝရ ပြနေမည်。 တကယ်က သုံးစွဲသူကို
      //    စောင့်နေတာ — ဗီဒီယို မဖြတ်ရသေး。
      if(j.status==='review'){
        clearInterval(state.poll); $('dock').hidden=true;
        // ⚠️ **done(j) ခေါ်ရမည်** — အရင်က ဘောက်စ်တွေ ဖွင့်ပေးရုံသာ လုပ်ခဲ့သဖြင့်
        //    ဝါကျစာရင်း (#tx) က **ဗလာ** ဖြစ်နေပြီး "ဒီအတိုင်း ဖြတ်မယ်" နှိပ်လျှင်
        //    revApprove က ဝါကျ ၀ ကြောင်း = "အားလုံး ဖျက်ထားသည်" ဟု ယူဆကာ
        //    ရပ်ပစ်သည် ⇒ သုံးစွဲသူ **ဘာမှ ဆက်လုပ်လို့ မရ** (၂၀၂၆-၀၉-၁၆ Zin တွေ့)。
        //    job စာရင်းကနေ ဖွင့်တဲ့ လမ်းကြောင်း (data-play) က done(j) ခေါ်လို့
        //    အဆင်ပြေခဲ့သည် — ဒီတစ်ခုတည်းသာ ကျန်ခဲ့တာ。
        done(j);
        var tb=$('txbox');
        if(tb && tb.scrollIntoView) tb.scrollIntoView({behavior:'smooth',block:'start'});
      }
      if(j.status==='done'){ clearInterval(state.poll); done(j) }
      if(j.status==='failed'){ clearInterval(state.poll); fail(j.err||'') }
      if(j.status==='cancelled'){ clearInterval(state.poll); scene('s-ready'); $('dock').hidden=true }
    }).catch(function(){});
  }
  tick(); state.poll=setInterval(tick,3000);
  $('jcancel').onclick=function(){
    api('/jobs/'+jid+'/cancel',{method:'POST'}).then(function(){
      clearInterval(state.poll); scene('s-ready'); $('dock').hidden=true; loadMeta();
    });
  };
}
function dock(j){
  if(!j||['done','failed','cancelled','review'].indexOf(j.status)>-1){$('dock').hidden=true;return}
  $('dock').hidden=false;
  $('dkname').textContent=j.title||j.id;
  $('dkstage').textContent=(cur==='my'?STAGE_MY:STAGE_EN)[Math.min(6,j.stage||0)];
  $('dkn').textContent=(j.stage||0)+'/7';
  $('dkbar').style.width=Math.round((j.stage||0)/7*100)+'%';
}
function done(j){
  // ⚠️ Zin ၂၀၂၆-၀၉-၁၉: 「ဗီဒီယို upload ပြီးတာနဲ့ Script Editor အော်တို ပေါ်မှ」
  //    ⇒ `review` (ASR ပြီး · ဗီဒီယို မထုတ်ရသေး) ရောက်တာနဲ့ **တန်း ခေါ်သွားသည်**。
  //    `?old=1` ထည့်လျှင် ယခင် စာမျက်နှာ ဆက်ကြည့်လို့ ရသည် (လုံးဝ မပိတ်ရ)。
  if(j && j.status==='review' && !/[?&]old=1/.test(location.search)){
    location.href='/script.html?job='+encodeURIComponent(j.id); return;
  }
  scene('s-done'); $('dock').hidden=true;
  var cut=Math.max(0,(j.src_dur||0)-(j.out_dur||0));
  function mmss(s){s=Math.round(s);return Math.floor(s/60)+':'+('0'+(s%60)).slice(-2)}
  // ⚠️ review မှာ **ဗီဒီယို မထုတ်ရသေး** ⇒ "ပြီးသွားပြီ" ဟု ခေါင်းစဉ်တပ်ခြင်း၊
  //    ဖိုင်မရှိသေးသော player/download ပြခြင်းက လိမ်ညာရာ ကျသည်。
  var _rev = (j.status==='review');
  var _h1 = document.querySelector('#s-done h1.t');
  if(_h1){
    var hm = _rev ? 'စစ်ပြီး အတည်ပြုပါ။' : 'ပြီးသွားပြီ။';
    var he = _rev ? 'Review and approve.' : 'Done.';
    _h1.setAttribute('data-my',hm); _h1.setAttribute('data-en',he);
    _h1.innerHTML = (cur==='my'?hm:he);
  }
  var _ck = document.querySelector('#s-done .check'); if(_ck) _ck.hidden=_rev;
  $('donesum').innerHTML = _rev
    ? (cur==='my'
        ? 'ဗီဒီယို <b class="ac">မဖြတ်ရသေးပါ</b> — '+mmss(j.src_dur||0)+
          '။ အကြံပြု ဖြတ်ချက် '+(j.cuts||0)+' ခု။ အောက်မှာ စစ်ပြီး အတည်ပြုပါ။'
        : 'Nothing is cut yet — '+mmss(j.src_dur||0)+'. '+(j.cuts||0)+
          ' suggested cuts. Review below, then approve.')
    : (cur==='my'
      ? '<b class="ac">'+mmss(cut)+'</b> ဖြတ်လိုက်တယ် — '+mmss(j.src_dur||0)+' ကနေ '+mmss(j.out_dur||0)+
        '။ ဖြတ်ချက် '+(j.cuts||0)+' ခု · စာတန်း '+(j.captions||0)+' ကြောင်း'
      : '<b class="ac">'+mmss(cut)+' removed</b> — '+mmss(j.src_dur||0)+' down to '+mmss(j.out_dur||0)+
        '. '+(j.cuts||0)+' cuts · '+(j.captions||0)+' captions');
  var url='/api/jobs/'+j.id+'/file?t='+encodeURIComponent(TOKEN);
  var dl=$('dl'); if(dl){ dl.href=url; dl.hidden=_rev; }
  var v=$('prev');
  if(v){
    v.hidden=_rev;
    if(_rev){ v.removeAttribute('src'); v.load(); }
    else { v.src=url; v.load(); }
  }
  // ⚠️ ညွှန်ပြချက်တွေကို **ပြရမည်** — Zin ရဲ့ spec: ဖြတ်စာရင်း ပြပြီး
  //    သူ အတည်ပြုမှ ဖြတ်ရမယ်။ မပြလျှင် ကတိ ပျက်သည်。
  var K={restart:['ပြန်စ','restart'],repeat:['ထပ်နေတာ','repeat'],
         cough:['ချောင်းဆိုး','cough'],filler:['ဖြည့်စကား','filler'],
         // ⚠️ ဖျက်ခိုင်းထားတာ ၁၀၀% မဖျက်ဖြစ်ခဲ့ — **အမြဲ ပြရမည်**
         drop_left:['⚠️ မဖျက်နိုင်','⚠️ not cut'],
         // ⚠️ ဒီမှာ မထည့်လျှင် raw အမည် (`flash_shot`) အတိုင်း ပေါ်သည် —
         //    Zin က 「ဘာအတွက်လဲ」 မေးခဲ့သည် (၂၀၂၆-၀၉-၂၀)。 kind အသစ်
         //    ထည့်တိုင်း **ဒီစာရင်းထဲ ပါရမည်**。
         flash_shot:['⚠️ ဖျပ်ခနဲ မြင်ကွင်း','⚠️ flash shot'],
         // ⚠️ `clean.plan()` က `retake` ကိုပါ ထုတ်သည် — စက်က အုပ်စု ဖွဲ့ရုံသာ၊
         //    ဘယ်ဟာ ကောင်းလဲကို **လူက ရွေးရမည်** (တိုင်းထားသော precision
         //    ၈၈.၉% က ၉၀% ဂိတ် မမီ)。
         retake:['ပြန်ရိုက်ထားတာ — ရွေးပါ','retake — you pick']};
  var fl=j.flag_list||[];
  if(fl.length){
    $('flagbox').hidden=false;
    $('flagn').textContent=(cur==='my'?fl.length+' ခု':fl.length+' items');
    $('flags').innerHTML=fl.map(function(f){
      var k=K[f.kind]||[f.kind,f.kind];
      var mm=Math.floor(f.at/60), ss=('0'+Math.floor(f.at%60)).slice(-2);
      return '<div class="row fl"><span class="tc">'+mm+':'+ss+'</span>'+
        '<span class="tx my">'+(f.text||'')+
        (f.keep?' <ins>→ '+f.keep+'</ins>':'')+'</span>'+
        '<span class="rt lo">'+(cur==='my'?k[0]:k[1])+
        (f.score?' · '+f.score:'')+'</span></div>';
    }).join('');
  } else { $('flagbox').hidden=true; }
  // ── စာသား ပြင်ကွက် ──
  var segs=j.segs||[];
  if(typeof segs==='string'){ try{segs=JSON.parse(segs)}catch(e){segs=[]} }
  state.segs=segs; state.jobid=j.id; state.recipe=j.recipe;
  // ── ပြင်ကွက် ──
  ADJ={};
  var ab=$('adjbox');
  if(ab && segs.length){
    ab.hidden=false;
    api('/styles').then(function(sd){
      var row=(sd.styles||[]).filter(function(x){return x.id===j.recipe})[0];
      STYDEF = row ? Object.assign({}, row) : {};
      CUTOPT = sd.cuts || [];
      if(sd.over && sd.over[j.recipe]) STYDEF=Object.assign({},STYDEF,sd.over[j.recipe]);
      // ⚠️ အရောင် မသတ်မှတ်ထားလျှင် theme ရဲ့ ပုံသေကို ပြရမည် — ဗလာပြလျှင်
      //    သုံးစွဲသူက "အရောင် မရှိဘူး" ထင်မည်。
      if(!STYDEF.cap_fill) STYDEF.cap_fill='#FFFFFF';
      if(!STYDEF.cap_stroke) STYDEF.cap_stroke='#1E3B5A';
      if(STYDEF.cap_cover===null||STYDEF.cap_cover===undefined) STYDEF.cap_cover=1;
      adjPaint();
    }).catch(function(){ adjPaint(); });
  } else if(ab) ab.hidden=true;
  if(segs.length){
    $('txbox').hidden=false;
    $('tx').innerHTML=segs.map(function(sg,i){
      var mm=Math.floor(sg.start/60), ss=('0'+Math.floor(sg.start%60)).slice(-2);
      return '<div class="row" data-i="'+i+'"><span class="tc">'+mm+':'+ss+'</span>'+
        '<span class="tx my" contenteditable="true" data-ed="'+i+'" spellcheck="false">'+
          String(sg.text||'').replace(/</g,'&lt;')+'</span>'+
        '<span class="rt"><span class="pill p-ac tflag" hidden></span>'+
        '<button class="iact" data-del="'+i+'" aria-label="Delete">✕</button></span></div>';
    }).join('');
    // ⚠️ **review = ဗီဒီယို မဖြတ်ရသေး**。 ဒီအဆင့်မှာ "ပြန်ထုတ်မယ်" ခလုပ်ကို
    //    ဖျောက်ပြီး "ဒီအတိုင်း ဖြတ်ပြီး Edit လုပ်မယ်" ကို ပြရသည် — မတူသော
    //    လုပ်ဆောင်ချက် နှစ်ခုကို ခလုပ်တစ်ခုတည်းနဲ့ ပြလျှင် ရှုပ်သည်。
    var _rev = (j.status === 'review');
    var _rb = $('revbar'), _re = $('txre');
    if(_rb) _rb.hidden = !_rev;
    if(_re) _re.hidden = _rev;
    var _h3 = $('txbox') && $('txbox').querySelector('h3');
    if(_h3) _h3.textContent = _rev
      ? (cur==='my' ? 'ဘယ်အပိုင်း ကျန်မလဲ ရွေးပါ' : 'Choose what stays')
      : (cur==='my' ? 'စာသား ပြင်ရန်' : 'Edit the transcript');
    var _ts=$('tosed'); if(_ts){ _ts.hidden=!_rev; _ts.href='/script.html?job='+j.id; }
    if(_rev){
      var pl=j.plan; if(typeof pl==='string'){ try{pl=JSON.parse(pl)}catch(e){pl=null} }
      state.plan = pl || null;
      rtPaint(); clPaint();
      revSum();
    }
    txstat(); rrSum(); livePreview();
    // ⚠️ ဘယ်ဟာက "ဖြတ်" ဘယ်ဟာက "စာတန်း ပြင်" ဆိုတာ **ချက်ချင်း ပြရမည်** —
    //    မပြလျှင် သုံးစွဲသူက စာလုံး ပြင်လိုက်ရင် အသံပါ ပြောင်းမယ် ထင်နေမည်。
    [].forEach.call(document.querySelectorAll('#tx [data-ed]'),function(el){
      el.oninput=function(){
        rrSum();
        var r=el.closest('.row'), i=parseInt(r.getAttribute('data-i'),10);
        var o=((state.segs[i]||{}).text||'').trim(), t=(el.textContent||'').trim();
        var fl=r.querySelector('.tflag');
        if(!fl) return;
        // ⚠️ **စာလုံး ပြင်တာက ဘယ်တော့မှ မဖြတ်ဘူး** — ဖြတ်ဖို့က စကားလုံး
        //    အဆင့် အချိန်မှတ် လိုပြီး ASR က အဲဒါကို ယုံကြည်လောက်အောင် မပေးဘူး。
        //    ⇒ ဖြတ်ချင်ရင် **✕ နဲ့ တစ်ကြောင်းလုံး ဖျက်**ရမည်。
        if(t===o){ fl.hidden=true; }
        else {
          fl.hidden=false; fl.className='pill p-ac tflag';
          fl.textContent = cur==='my' ? 'စာတန်းပဲ ပြောင်းမယ်' : 'caption only';
        }
      };
    });
  } else { $('txbox').hidden=true; }
  // ── ဗားရှင်း ──
  var vs=j.versions||[];
  if(vs.length>1){
    $('verbox').hidden=false;
    $('vers').innerHTML=vs.map(function(v){
      var d=new Date((v.created||0)*1000);
      return '<div class="row"><span class="tc mono">v'+v.n+'</span>'+
        '<span class="tx">'+(v.note||'')+' · '+d.toLocaleString()+'</span>'+
        '<span class="rt"><a class="iact" href="/api/jobs/'+j.id+'/file?t='+
          encodeURIComponent(TOKEN)+'" aria-label="Download">↓</a></span></div>';
    }).join('');
  } else { $('verbox').hidden=true; }
  var ds=$('dlsrt'); if(ds) ds.href='/api/jobs/'+j.id+'/srt?t='+encodeURIComponent(TOKEN);
  planLoad(j.id);
  loadMeta();
}
function txstat(){
  var rows=[].slice.call(document.querySelectorAll('#tx .row'));
  var gone=rows.filter(function(r){return r.classList.contains('gone')}).length;
  $('txstat').textContent = cur==='my'
    ? rows.length+' ကြောင်း · ဖျက်ထား '+gone+' ခု'
    : rows.length+' lines · '+gone+' removed';
}
function fail(msg){
  scene('s-err'); $('dock').hidden=true;
  $('errwhy').textContent = msg || (cur==='my'?'အကြောင်းရင်း မသိရသေးပါ':'Reason unknown');
  loadMeta();
}

/* ── ဗီဒီယို စာရင်း ── */
var ALL=[]; var FONTS=[];
// ⚠️ AI ရဲ့ အကြောင်းပြချက်ကို **ဆက်ပြရမည်** — ဘာလို့ ဒီဖောင့် ရွေးလဲ
//    မမြင်ရလျှင် သုံးစွဲသူက ယုံရခက်သည်。
function paintFontWhy(){
  var w=document.getElementById('fontwhy'); if(!w) return;
  if(state.fontwhy){ w.hidden=false; w.textContent=state.fontwhy; }
  else w.hidden=true;
}
function loadJobs(){
  paintTrash();
  api('/jobs').then(function(d){ ALL=d.jobs; paintJobs();
    var run=ALL.filter(function(j){return ['queued','running'].indexOf(j.status)>-1});
    $('nrun').textContent=run.length; $('nrun').style.display=run.length?'':'none';
    if(run.length) dock(run[0]); else $('dock').hidden=true;
  }).catch(function(){});
}
function paintJobs(){
  var q=($('q').value||'').trim().toLowerCase();
  var f=document.querySelector('.stf[aria-pressed="true"]');
  f=f?f.getAttribute('data-st'):'all';
  var P={queued:['p-dim','တန်းစီ','Queued'],running:['p-dim','လုပ်နေဆဲ','Running'],
         review:['p-ac','စာတမ်း စစ်ရန်','Review transcript'],
         done:['p-ok','ပြီး','Done'],failed:['p-no','ပျက်သွား','Failed'],cancelled:['p-dim','ရပ်ထား','Stopped']};
  var rows=ALL.filter(function(j){
    var okF = f==='all' || (f==='running'? ['queued','running'].indexOf(j.status)>-1 : j.status===f);
    var okQ = !q || ((j.title||'')+' '+(j.recipe||'')+' '+(j.brand_id||'')).toLowerCase().indexOf(q)>-1;
    return okF&&okQ;
  });
  // ⚠️ ဘာမှ မရှိတာ (အသစ်) နဲ့ ရှာလို့ မတွေ့တာ **ခွဲပြရမည်**
  var noAny = (ALL||[]).length===0;
  $('nojobs').hidden = !(noAny);
  $('noq').hidden = rows.length>0 || noAny;
  $('jobs').innerHTML=rows.map(function(j){
    var p=P[j.status]||P.queued;
    // ⚠️ ပုံငယ်က **ဗီဒီယိုထဲက frame အစစ်** ဖြစ်ရမည် — gradient အတုက
    //    ဘယ်ဟာ ဘယ်ဟာလဲ ခွဲလို့ မရ (ဗီဒီယို ၂၀ ခုရှိရင် အကုန် တူနေသည်)。
    var th = j.status==='done'
      ? '<img class="thumb" loading="lazy" alt="" src="/api/jobs/'+j.id+'/thumb?t='+
        encodeURIComponent(TOKEN)+'" onerror="this.className=\'thumb im'+
        ((j.id.charCodeAt(3)%5)+1)+'\';this.removeAttribute(\'src\')">'
      : '<div class="thumb im'+((j.id.charCodeAt(3)%5)+1)+'"></div>';
    return '<div class="lrow">'+th+
      // ⚠️ ခေါင်းစဉ်က R2 key (pYoIvgBmehsq…) ဖြစ်တတ်၍ **ဖတ်လို့ မရ** ⇒
      //    extension ဖြုတ် · ရှည်လျှင် ဖြတ် (**ပြဖို့သာ** — DB မထိ)。
      '<div class="lname"><b class="my">'+nice(j.title||j.id)+'</b><span>'+(j.brand_id||'')+'</span></div>'+
      '<div class="lmeta hidesm">'+(j.recipe||'')+'</div>'+
      '<div class="ldur hidesm mono">'+(j.out_dur?Math.round(j.out_dur)+'s':'—')+'</div>'+
      '<div class="wave hidesm"></div><div class="lacts">'+
      '<span class="pill '+p[0]+'">'+(cur==='my'?p[1]:p[2])+'</span>'+
      // ⚠️ ဖိုင် ပျောက်နေလျှင် **ဒေါင်းလုပ် မပြရ** — နှိပ်ပြီး ကျရင် ယုံကြည်မှု ပျက်သည်
      (j.gone? '<span class="pill p-no">'+(cur==='my'?'ဖိုင် ပျောက်':'file gone')+'</span>' : '')+
      (j.status==='done' && !j.gone?'<button class="iact" data-play="'+j.id+'" aria-label="Play">▶</button>'+
        '<a class="iact" href="/api/jobs/'+j.id+'/file?t='+encodeURIComponent(TOKEN)+'" aria-label="Download">↓</a>':'')+
      // ⚠️ Script Editor — စာသား ရှိပြီးသား job တိုင်းမှာ ပြရမည်。 ဖိုင် ပျောက်နေလည်း
      //    စာသား တည်းဖြတ်လို့ ရသည် (ထွက်ဖိုင် မလို · segs ကိုသာ သုံး)。
      //    token က `ikki_token` အတူတူမို့ ပြန် login စရာ မလို。
      // ⚠️ `review` = **သင် လုပ်ရန် ကျန်နေတာ** ⇒ icon သေးသေး မဟုတ်ဘဲ
      //    ခလုတ် ရှင်းရှင်း ပြရမည် (၂၀၂၆-၀၉-၁၉ — icon ချည်း ဖြစ်နေ၍ ဘာလုပ်ရမှန်း မသိ)。
      (j.status==='review'
        ? '<a class="btn" style="text-decoration:none;padding:7px 14px;font-size:12.5px" '+
          'href="/script.html?job='+j.id+'">'+(cur==='my'?'✂️ ဖြတ်ရန်':'✂️ Edit')+'</a>' : '')+
      (j.status==='done'
        ? '<a class="iact" href="/script.html?job='+j.id+'" aria-label="'+
          (cur==='my'?'စာသား တည်းဖြတ်':'Script editor')+'" title="'+
          (cur==='my'?'စာသား တည်းဖြတ်':'Script editor')+'">📝</a>' : '')+
      // ⚠️ ဖျက်ခလုပ် — ပြီးသွားတာ/ပျက်သွားတာမှာသာ。 လုပ်နေဆဲကို ဖျက်လျှင်
      //    worker က ဆက်ရေးနေပြီး ဖိုင် ကျန်နေမည် ⇒ အရင် ရပ်ခိုင်းရသည်。
      (['done','failed','cancelled'].indexOf(j.status)>-1
        ? '<button class="iact idel" data-del-job="'+j.id+'" aria-label="'+
          (cur==='my'?'ဖျက်မယ်':'Delete')+'">🗑</button>' : '')+
      // ⚠️ လုပ်နေဆဲ/တန်းစီ job ကို **ပြန်ဖွင့်ကြည့်လို့ ရရမည်** —
      //    မရလျှင် render လုပ်ရင်း tab ပိတ်မိတာနဲ့ တိုးတက်မှု ပျောက်သည်
      //    (Pro app မှာ လက်ခံလို့ မရသော အားနည်းချက်)。
      (['queued','running'].indexOf(j.status)>-1
        ? '<button class="iact" data-open="'+j.id+'" aria-label="'+
          (cur==='my'?'တိုးတက်မှု ကြည့်':'View progress')+'">↗</button>' : '')+
      (j.status==='failed'
        ? '<button class="iact" data-open="'+j.id+'" aria-label="'+
          (cur==='my'?'အမှား ကြည့်':'View error')+'">↗</button>' : '')+
      // ⚠️ ကျဘမ်းဖြစ်သွားလျှင် **ပြန်စလို့ ရရမည်** — မရလျှင် disk ပြည့်တာမျိုး
      //    ယာယီ ပြဿနာတစ်ခုအတွက် GB ချီတဲ့ ဗီဒီယို ပြန်တင်ရမည်。
      //    upload က R2 ပေါ် ရှိပြီးသား。
      (['failed','cancelled'].indexOf(j.status)>-1
        ? '<button class="iact" data-retry="'+j.id+'" aria-label="'+
          (cur==='my'?'ပြန်စမယ်':'Retry')+'">↻</button>' : '')+
      '</div></div>';
  }).join('');
}

/* ── ချိတ်ဆက်မှုများ ── */
document.addEventListener('click',function(e){
  var rt=e.target.closest&&e.target.closest('[data-retry]');
  if(rt){
    var rid=rt.getAttribute('data-retry'), rmy=(cur==='my');
    rt.disabled=true;
    api('/jobs/'+rid+'/retry',{method:'POST'})
     .then(function(d){
       alert(rmy?('ပြန်စလိုက်ပါပြီ။'+(d.refunded?' မိနစ် '+d.refunded+' ပြန်ထည့်ပေးပြီး။':''))
                :('Restarted.'+(d.refunded?' '+d.refunded+' min refunded.':'')));
       loadJobs(); })
     .catch(function(err){ rt.disabled=false;
       console.error('retry',err); alert(String(err.message||err).slice(0,200)); });
    return;
  }
  var op=e.target.closest&&e.target.closest('[data-open]');
  if(op){ go('v-new'); watch(op.getAttribute('data-open')); return }
  var n=e.target.closest&&e.target.closest('[data-go]'); if(n) go(n.getAttribute('data-go'));
  var audience=e.target.closest&&e.target.closest('[data-family]');
  if(audience){
    state.family=audience.getAttribute('data-family');
    if(familyForStyle(state.style)!==state.family){
      state.style=(state.family==='creator'?STYLES.creator[0]:STYLES.biz[0])[0];
      if(styleDefaults()) loadMeta();
    }
    paintStyles(); return;
  }
  // ⚠️ category chip ဖယ်ပြီး (dropdown ထဲ optgroup နဲ့ ပါပြီးသား) — handler မလိုတော့
  // ⚠️ hero ကတ် ၃ ခုက ယခင်က **နှိပ်လို့ရပုံ ပေါ်နေပြီး ဘာမှ မဖြစ်**ခဲ့ (၂၀၂၆-၀၉-၁၉ တိုင်းစစ်ပြီး)
  //    ⇒ recipe ရွေးပေးပြီး dropdown ကိုပါ ညှိသည် (နှစ်နေရာ မကွဲစေရန်)。
  var hp=e.target.closest&&e.target.closest('[data-pick]');
  if(hp){ state.style=hp.getAttribute('data-pick'); state.family=familyForStyle(state.style); styleDefaults(); paintStyles(); markPick();
    var el=document.getElementById('styles'); if(el&&el.scrollIntoView)
      el.scrollIntoView({behavior:'smooth',block:'center'}); return }
  var s=e.target.closest&&e.target.closest('[data-style]');
  if(s){state.style=s.getAttribute('data-style'); state.family=familyForStyle(state.style); styleDefaults(); paintStyles()}
  var dl=e.target.closest&&e.target.closest('[data-del]');
  if(dl){
    var row=dl.closest('.row');
    if(row.classList.contains('rtcut')){
      alert(cur==='my'?'ဒီစာကြောင်းက လက်ခံထားတဲ့ ပြန်စ ထဲ ပါပါတယ် — အပေါ်က ✗ နဲ့ ပြန်ပြင်ပါ'
                      :'This line belongs to an accepted retake — change it with ✗ above');
      return;
    }
    row.classList.toggle('gone');
    // ⚠️ ဖျက်ထားတာကို မြင်ရစေရန် — အရောင်တစ်ခုတည်းနဲ့ မပြောရ
    var t=row.querySelector('[data-ed]');
    t.style.textDecoration = row.classList.contains('gone') ? 'line-through' : '';
    t.style.opacity = row.classList.contains('gone') ? '0.45' : '';
    txstat(); rrSum(); livePreview(); return;
  }
  // ── ဗီဒီယို ဖျက်ခြင်း ──
  // ⚠️ အတည်ပြုချက် **မဖြစ်မနေ** — ဖျက်ပြီးရင် ပြန်မရ (R2 ကပါ ဖျက်သည်)。
  var dj=e.target.closest&&e.target.closest('[data-del-job]');
  if(dj){
    var did=dj.getAttribute('data-del-job');
    var _jb=(ALL.filter(function(x){return x.id===did})[0])||{};
    var nm=_jb.title||did;
    // ⚠️ `window.confirm` ကို **မမှီခိုရ** — browser အချို့ (webview · dialog
    //    ပိတ်ထားသူ) မှာ မပေါ်ဘဲ `false` ပြန်သဖြင့် ခလုပ်က သေနေသလို ဖြစ်သည်
    //    (Zin: "Delete button တွေ နှိပ်လို့ မရဘူး" — တကယ် ဖြစ်ခဲ့)。
    //    ⇒ စာမျက်နှာထဲမှာပဲ **နှစ်ဆင့်** အတည်ပြုသည်。
    if(dj.getAttribute('data-arm')!=='1'){
      [].forEach.call(document.querySelectorAll('[data-del-job][data-arm="1"]'),
        function(o){ o.removeAttribute('data-arm'); o.textContent='🗑';
                     o.style.color=''; o.style.borderColor=''; });
      dj.setAttribute('data-arm','1');
      dj.textContent = (cur==='my' ? 'ဖျက်?' : 'Sure?');
      dj.style.color='#E5484D'; dj.style.borderColor='#E5484D';
      dj.__t = setTimeout(function(){
        dj.removeAttribute('data-arm'); dj.textContent='🗑';
        dj.style.color=''; dj.style.borderColor='';
      }, 4000);
      return;
    }
    clearTimeout(dj.__t);
    dj.disabled=true; dj.textContent = (cur==='my' ? 'ဖျက်နေ…' : 'Deleting…');
    api('/jobs/'+did,{method:'DELETE'})
      .then(function(){
        // ⚠️ undo bar ကို **paintJobs() မတိုင်ခင်** ပြရမည် — paintJobs က
        //    ကျဘမ်းဖြစ်လျှင် catch သို့ ခုန်ပြီး undo က ဘယ်တော့မှ မပေါ်ဘူး。
        showUndo(did, nm);
        ALL=ALL.filter(function(x){return x.id!==did}); paintJobs();
        // ⚠️ **ပြန်ယူခွင့် ပေးရမည်** — ဗီဒီယို ၂၆ ခု တစ်ပြိုင်နက် ပျောက်ခဲ့ပြီး
        //    ဘယ်သူ ဖျက်လဲ log ကနေ ခွဲလို့ မရခဲ့သည်。 ယခု ၂၄ နာရီ ကျန်သည်。
      })
      .catch(function(err){ dj.disabled=false; dj.textContent='🗑';
        dj.removeAttribute('data-arm'); dj.style.color=''; dj.style.borderColor='';
        console.error('delete failed', err);
        alert(String(err.message||err).slice(0,300)); });
    return;
  }
  var pl=e.target.closest&&e.target.closest('[data-play]');
  if(pl){
    var id=pl.getAttribute('data-play');
    api('/jobs/'+id).then(function(j){ go('v-new'); scene('s-done'); done(j); });
    return;
  }
  var ff=e.target.closest&&e.target.closest('[data-font]');
  if(ff){ state.font=ff.getAttribute('data-font'); loadMeta(); }
  var b=e.target.closest&&e.target.closest('.bp');
  if(b){state.brand=b.getAttribute('data-b'); state.ovrBrand=true;
    [].forEach.call(document.querySelectorAll('.bp'),function(o){o.setAttribute('aria-pressed',o===b?'true':'false')});
    // ⚠️ brand ပြောင်းလျှင် ပုံသေ အရွယ်လည်း ပြောင်းသည် — ပြန်ဆွဲရမည်
    loadMeta();}
  var cp=e.target.closest&&e.target.closest('.cp');
  if(cp){state.cap=cp.getAttribute('data-cap');
    [].forEach.call(document.querySelectorAll('.cp'),function(o){o.setAttribute('aria-pressed',o===cp?'true':'false')})}
  var fm=e.target.closest&&e.target.closest('.fmt');
  if(fm){state.fmt=fm.getAttribute('data-fmt'); state.ovrFmt=true;
    [].forEach.call(document.querySelectorAll('.fmt'),function(o){o.setAttribute('aria-pressed',o===fm?'true':'false')})}
  var fd=e.target.closest&&e.target.closest('.stf');
  if(fd){[].forEach.call(document.querySelectorAll('.stf'),function(o){o.setAttribute('aria-pressed',o===fd?'true':'false')}); paintJobs()}
});
document.addEventListener('keydown',function(e){
  if(e.target.matches('input,textarea,select')) return;
  if(e.metaKey||e.ctrlKey||e.altKey) return;
  if(e.key==='/'){e.preventDefault(); go('v-lib'); $('q').focus(); return}
  var btns=[].slice.call(document.querySelectorAll('.pillnav button')), i=-1;
  btns.forEach(function(b,k){if(b.getAttribute('aria-current')==='page') i=k});
  if(i<0) return;
  if(e.key==='ArrowRight'&&i<btns.length-1){e.preventDefault();btns[i+1].click();btns[i+1].focus()}
  if(e.key==='ArrowLeft'&&i>0){e.preventDefault();btns[i-1].click();btns[i-1].focus()}
});
$('l-my').onclick=function(){lang('my')}; $('l-en').onclick=function(){lang('en')};
$('thm').onclick=function(){
  var r=document.documentElement,c=r.getAttribute('data-theme');
  var dark=c?c==='dark':!window.matchMedia('(prefers-color-scheme: light)').matches;
  r.setAttribute('data-theme',dark?'light':'dark');
  localStorage.setItem('ikki_theme',dark?'light':'dark');
};
$('priv').onclick=function(){go('v-acc');setTimeout(function(){$('privacy').scrollIntoView({behavior:'smooth'})},120)};
$('drop').onclick=function(){$('file').click()};
$('file').onchange=function(){ if(this.files[0]) start(this.files[0]) };
$('again').onclick=function(){scene('s-ready'); loadJobs()};
var fr=$('fontreset'); if(fr) fr.onclick=function(){state.font=''; loadMeta()};
var fmr=$('fmtreset'); if(fmr) fmr.onclick=function(){state.fmt=''; state.ovrFmt=false; loadMeta()};
var cpr=$('capreset'); if(cpr) cpr.onclick=function(){state.cap=''; loadMeta()};
// ⚠️ "ရွေးတာ" နှင့် "ပြင်တာ" ကို ခွဲထားသည် — Create မှာ ရွေးရုံ၊
//    ပြင်ချင်လျှင် Style & brand စာမျက်နှာ သွားရမည်。
var gs=$('gostyle'); if(gs) gs.onclick=function(){ go('v-sty') };

// ── ပြင်ချက်နဲ့ ပြန်ထုတ် ──
var tr=$('txre');
if(tr) tr.onclick=function(){
  // ⚠️ ဖျက်တာနဲ့ ပြင်တာ **မတူ** —
  //    · ဖျက်/တိုအောင်လုပ် (မူရင်းထဲ ရှိသေးရင်) → `text` · အသံပါ ဖြတ်သည်
  //    · စာလုံး ပြောင်း (မူရင်းထဲ မရှိတော့ရင်) → `fix` · **စာတန်းပဲ** ပြောင်း၊
  //      အသံနဲ့ ဖြတ်မှတ် မထိ (အသံထဲ မရှိတဲ့ စာလုံးကို ဖြတ်လို့ မရ)
  var out=[], nfix=0, ncut=0;
  [].forEach.call(document.querySelectorAll('#tx .row'),function(r){
    var i=parseInt(r.getAttribute('data-i'),10);
    if(r.classList.contains('gone')) { out.push({i:i,text:''}); ncut++; return; }
    var o=((state.segs[i]||{}).text||'');
    var t=(r.querySelector('[data-ed]').textContent||'').trim();
    if(t===o.trim()){ out.push({i:i, text:o}); return; }
    out.push({i:i, text:o, fix:t}); nfix++;
  });
  tr.disabled=true;
  api('/jobs/'+state.jobid+'/reedit',{method:'POST',
      headers:{'Content-Type':'application/json'},
      body:JSON.stringify({segs:out, recipe:state.recipe,
                           over:ADJ, font:(ADJ.mmf||undefined)})})
   .then(function(d){ tr.disabled=false; watch(d.job_id); })
   .catch(function(e){ tr.disabled=false; alert(String(e.message||e).slice(0,300)); });
};


// ══ စာတမ်း အတည်ပြုခြင်း (Edit မလုပ်ခင်) ═══════════════════
// ⚠️ Zin: "ဗီဒီယိုထည့်လိုက်တာနဲ့ အရင်ဆုံး Edit မလုပ်ခင် user ကို transcript ပြ။
//    အဲဒီ transcript click တစ်ချက်နှိပ်လိုက်တာနဲ့ Transcript ထဲကပါတဲ့ စာလုံး
//    တွေကိုပဲ … Cut ဖြတ်ပေးတဲ့ပုံစံ" — ဖြတ်ချက်ကို **app က မဆုံးဖြတ်ရ**。
function revSum(){
  var el=$('revsum'); if(!el) return;
  var tot=(state.segs||[]).length, gone=0, sec=0;
  [].forEach.call(document.querySelectorAll('#tx .row'),function(r){
    if(r.classList.contains('gone')){
      gone++;
      var i=parseInt(r.getAttribute('data-i'),10), sg=(state.segs||[])[i];
      if(sg) sec += Math.max(0,(+sg.end||0)-(+sg.start||0));
    }
  });
  var p=state.plan||{}, src=+p.src_dur||0;
  var left = src ? Math.max(0, src - sec) : 0;
  function mmss(x){ var m=Math.floor(x/60),ss=('0'+Math.round(x%60)).slice(-2); return m+':'+ss; }
  el.innerHTML = cur==='my'
    ? ('စာကြောင်း <b>'+tot+'</b> · ဖျက်ထား <b>'+gone+'</b>'
       + (src? ' · မူရင်း '+mmss(src)+' → ခန့်မှန်း <b>'+mmss(left)+'</b>' : '')
       + (p.cuts? '<br>တိတ်ဆိတ်မှု ဖြတ်ချက် '+p.cuts+' ခု ကို အလိုအလျောက် ထည့်ပေးပါမယ်' : ''))
    : ('<b>'+tot+'</b> lines · <b>'+gone+'</b> marked for cutting'
       + (src? ' · '+mmss(src)+' → about <b>'+mmss(left)+'</b>' : '')
       + (p.cuts? '<br>'+p.cuts+' silence cuts will also be applied' : ''));
}

// ⚠️ Script ကိုက်ညှိခြင်း — **ဖျက်ရုံသာ**。 script ထဲ ပါတဲ့ စာပိုဒ်နဲ့
//    ကိုက်တဲ့ စာကြောင်းကို ချန်ပြီး ကျန်တာကို ဖျက်မှတ် တပ်သည်。
//    အသံထဲ မရှိတဲ့ စာလုံးကို ထည့်လို့ မရ၍ script ကို **အတိအကျ မကူးနိုင်**。
function scrMatch(){
  var box=$('scr'), st=$('scrst'); if(!box) return;
  var norm=function(x){ return String(x||'').replace(/[\s\u200b-\u200d]+/g,'')
                          .replace(/[။၊,.!?"'()\[\]{}—–-]/g,''); };
  var script=norm(box.value);
  if(script.length<8){ if(st) st.textContent = cur==='my'?'Script က တိုလွန်းသည်':'Script is too short'; return; }
  var kept=0, cutn=0;
  [].forEach.call(document.querySelectorAll('#tx .row'),function(r){
    if(r.classList.contains('rtcut')) return;
    var i=parseInt(r.getAttribute('data-i'),10);
    var t=norm(((state.segs||[])[i]||{}).text||'');
    if(t.length<4){ return; }
    // စာကြောင်းရဲ့ အလယ်ပိုင်း ခုနစ်လုံးက script ထဲ ရှိလား
    var probe=t.slice(Math.max(0,Math.floor(t.length/2)-4), Math.floor(t.length/2)+4);
    var hit = probe.length>=4 && script.indexOf(probe)>-1;
    if(hit){ r.classList.remove('gone'); kept++; }
    else   { r.classList.add('gone');   cutn++; }
  });
  rrSum(); revSum(); txstat();
  if(st) st.textContent = cur==='my'
    ? ('ကိုက်ညီ '+kept+' ကြောင်း · ဖျက်မှတ် '+cutn+' ကြောင်း။ စစ်ပြီးမှ အောက်က ခလုပ် နှိပ်ပါ။')
    : (kept+' matched · '+cutn+' marked for cutting. Check them, then use the button below.');
}

// ══ ပြန်စ (retake) review ═══════════════════════════════════
// ⚠️ **စက်က မဖြတ်** — တစ်ခုချင်း လူ ဆုံးဖြတ်ပြီး server က မှတ်တမ်းတင်သည်。
//    detection ကို C0736 တစ်ခုတည်း (FP ၃ ခု) နဲ့ ချိန်လျှင် overfit ⇒ ဒီ
//    ဆုံးဖြတ်ချက်တွေက ground truth ဖြစ်လာမည် (၂၀၂၆-၀၉-၁၆)。
var RT={};
var RTR=[['not_retake','ပြန်စ မဟုတ်','Not a retake'],
         ['keeps_content','ချန်ချင်တာ ပါနေ','Cuts something I want'],
         ['bad_boundary','ဖြတ်မှတ် မမှန်','Wrong boundary'],
         ['other','အခြား','Other']];
function rtList(){ var p=state.plan||{}; return p.retakes||[]; }
function rtRows(r){
  return (r.sentences||[]).map(function(x){
    return document.querySelector('#tx .row[data-i="'+(x-1)+'"]'); }).filter(Boolean);
}
function rtMark(r, on){
  rtRows(r).forEach(function(row){
    row.classList.toggle('gone', on); row.classList.toggle('rtcut', on);
    var t=row.querySelector('[data-ed]');
    if(t){ t.style.textDecoration=on?'line-through':''; t.style.opacity=on?'0.45':''; }
  });
}
function rtCount(){
  var L=rtList(), n=L.filter(function(r){return RT[r.id]}).length, el=$('rtn');
  if(el) el.textContent = cur==='my' ? (n+' / '+L.length+' ဆုံးဖြတ်ပြီး') : (n+' / '+L.length+' decided');
}
function rtPaint(){
  var box=$('rtbox'); if(!box) return;
  var L=rtList(); RT={};
  if(!L.length){ box.hidden=true; return; }
  box.hidden=false;
  var esc=function(x){ return String(x||'').replace(/</g,'&lt;'); };
  var mmss=function(x){ var m=Math.floor(x/60), q=('0'+Math.floor(x%60)).slice(-2); return m+':'+q; };
  $('rts').innerHTML=L.map(function(r){
    return '<div class="row" data-rt="'+esc(r.id)+'"><span class="tc">'+mmss(+r.at||0)+'–'+mmss(+r.to||0)+
      '<br>'+(+r.removed||0).toFixed(1)+'s</span>'+
      '<span class="tx my"><del>'+esc(r.text)+'</del>'+(r.keep?'<br><ins>→ '+esc(r.keep)+'</ins>':'')+
      '<select class="rtwhy" hidden><option value="">'+
        (cur==='my'?'မဖြတ်တဲ့ အကြောင်း (မဖြစ်မနေ မဟုတ်)':'Why keep? (optional)')+'</option>'+
        RTR.map(function(o){ return '<option value="'+o[0]+'">'+(cur==='my'?o[1]:o[2])+'</option>'; }).join('')+
      '</select></span>'+
      '<span class="rt"><button class="iact rtok" data-rtd="accept" aria-pressed="false" '+
        'aria-label="'+(cur==='my'?'ဖြတ်':'Cut')+'">✓</button> '+
      '<button class="iact rtno" data-rtd="reject" aria-pressed="false" '+
        'aria-label="'+(cur==='my'?'မဖြတ်':'Keep')+'">✗</button></span></div>';
  }).join('');
  rtCount();
}
function rtDecide(btn){
  var it=btn.closest('[data-rt]'); if(!it) return;
  var id=it.getAttribute('data-rt'), r=rtList().filter(function(x){return x.id===id})[0];
  if(!r) return;
  var dec=btn.getAttribute('data-rtd');
  RT[id]={decision:dec, reason:''};
  rtMark(r, dec==='accept');
  it.querySelector('.rtok').setAttribute('aria-pressed', dec==='accept'?'true':'false');
  it.querySelector('.rtno').setAttribute('aria-pressed', dec==='reject'?'true':'false');
  var sel=it.querySelector('.rtwhy'); if(sel){ sel.hidden=(dec!=='reject'); if(dec!=='reject') sel.value=''; }
  rtCount(); txstat(); rrSum(); revSum(); livePreview();
}
document.addEventListener('change',function(e){
  var sl=e.target; if(!sl || !sl.classList || !sl.classList.contains('rtwhy')) return;
  var it=sl.closest('[data-rt]'), id=it && it.getAttribute('data-rt');
  if(id && RT[id]) RT[id].reason=sl.value;
});

// ══ review v2 — အုပ်စု တစ်ခုချင်း **ဘယ် take ချန်မလဲ** (၂၀၂၆-၀၉-၁၆) ══
// ⚠️ စက်က ဘယ် take ချန်မလဲ **မဆုံးဖြတ်ရ** — ချန်သော take က ရှေ့မှာ ဖြစ်တာ ၃၄%
//    (podcast ၅၂%) ⇒ လူသာ ရွေးရမည်。 ပုံသေ = **ဘာမှ မဖျက်**。
var CL={};
function clList(){ var p=state.plan||{}; return p.clusters||[]; }
function clRow(t){ return document.querySelector('#tx .row[data-i="'+((t.i|0)-1)+'"]'); }
function clMark(c){
  var pick=CL[c.id];
  (c.takes||[]).forEach(function(t){
    var row=clRow(t); if(!row) return;
    var cut = pick && pick!=='none' && String(t.n)!==String(pick);
    row.classList.toggle('gone', !!cut); row.classList.toggle('rtcut', !!cut);
    var tx=row.querySelector('[data-ed]');
    if(tx){ tx.style.textDecoration=cut?'line-through':''; tx.style.opacity=cut?'0.45':''; }
  });
}
function clCount(){
  var L=clList(), n=L.filter(function(c){return CL[c.id]}).length, el=$('cln');
  if(el) el.textContent = cur==='my' ? (n+' / '+L.length+' ရွေးပြီး') : (n+' / '+L.length+' chosen');
}
function clPaint(){
  var box=$('clbox'), off=$('rtoff'); if(!box) return;
  var p=state.plan||{}, L=clList(); CL={};
  if(off){
    var msg=p.retake_off||''; off.hidden=!msg;
    if(msg) off.textContent='ⓘ '+msg;
  }
  if(!L.length){ box.hidden=true; return; }
  box.hidden=false;
  var esc=function(x){ return String(x||'').replace(/</g,'&lt;'); };
  var mmss=function(x){ var m=Math.floor(x/60), q=('0'+Math.floor(x%60)).slice(-2); return m+':'+q; };
  $('cls').innerHTML=L.map(function(c){
    var opts=c.options||{}, blocked=c.blocked||{};
    var takes=(c.takes||[]).map(function(t){
      var ok = Object.prototype.hasOwnProperty.call(opts, String(t.n));
      return '<div class="row" data-ctk="'+esc(t.n)+'"><span class="tc">'+mmss(+t.start||0)+
        '<br>'+((+t.end||0)-(+t.start||0)).toFixed(1)+'s</span>'+
        '<span class="tx my">'+esc(t.text)+'</span>'+
        '<span class="rt"><button class="iact" data-clk="'+esc(c.id)+'" data-cln="'+esc(t.n)+'"'+
          (ok?'':' disabled title="'+esc(blocked[String(t.n)]||'')+'"')+' aria-pressed="false">'+
          (cur==='my'?('take '+t.n+' ချန်'):('keep take '+t.n))+'</button></span></div>';
    }).join('');
    return '<div class="clus" data-cl="'+esc(c.id)+'" style="border:1px solid var(--ln);border-radius:10px;'+
      'padding:8px 10px;margin:0 0 9px">'+
      '<p style="font-size:12px;color:var(--tx3);margin:0 0 6px">'+mmss(+(c.span||[0])[0])+'–'+
        mmss(+(c.span||[0,0])[1])+' · take '+(c.takes||[]).length+'</p>'+
      '<div class="rows">'+takes+'</div>'+
      '<div style="margin-top:6px"><button class="iact" data-clk="'+esc(c.id)+'" data-cln="none" '+
        'aria-pressed="false">'+(cur==='my'?'ဘာမှ မဖျက်':'Cut nothing')+'</button></div></div>';
  }).join('');
  clCount();
}
function clPick(btn){
  var id=btn.getAttribute('data-clk'), n=btn.getAttribute('data-cln');
  var c=clList().filter(function(x){return x.id===id})[0]; if(!c) return;
  CL[id]=n;
  var wrap=btn.closest('[data-cl]')||document;
  [].forEach.call(wrap.querySelectorAll('[data-clk="'+id+'"]'),function(b){
    b.setAttribute('aria-pressed', b.getAttribute('data-cln')===n ? 'true':'false');
  });
  clMark(c); clCount(); txstat(); rrSum(); revSum(); livePreview();
}

function revApprove(){
  var btn=$('revgo'); if(!btn) return;
  var RL=rtList(), und=RL.filter(function(r){return !RT[r.id]});
  if(und.length){
    alert(cur==='my'?('ပြန်စ အကြံပြုချက် '+und.length+' ခု မဆုံးဖြတ်ရသေးပါ — ✓ ဖြတ် / ✗ မဖြတ် ရွေးပါ')
                    :(und.length+' possible retakes still need ✓ cut or ✗ keep'));
    var bx=$('rtbox'); if(bx&&bx.scrollIntoView) bx.scrollIntoView({behavior:'smooth',block:'center'});
    return;
  }
  // ⚠️ အုပ်စု တစ်ခုချင်း ရွေးမှ ဆက်ရ — «ဘာမှ မဖျက်» လည်း ရွေးချယ်မှု တစ်ခု
  var CLL=clList(), cund=CLL.filter(function(c){return !CL[c.id]});
  if(cund.length){
    alert(cur==='my'?('ပြန်စ အုပ်စု '+cund.length+' ခု မရွေးရသေးပါ — ချန်မယ့် take (သို့) «ဘာမှ မဖျက်» ရွေးပါ')
                    :(cund.length+' retake groups still need a take (or “cut nothing”)'));
    var cb=$('clbox'); if(cb&&cb.scrollIntoView) cb.scrollIntoView({behavior:'smooth',block:'center'});
    return;
  }
  var out=[], ncut=0;
  [].forEach.call(document.querySelectorAll('#tx .row'),function(r){
    var i=parseInt(r.getAttribute('data-i'),10);
    if(r.classList.contains('gone')){ out.push({i:i,text:''}); ncut++; return; }
    var o=((state.segs[i]||{}).text||'');
    var t=(r.querySelector('[data-ed]').textContent||'').trim();
    if(t===o.trim()){ out.push({i:i,text:o}); return; }
    out.push({i:i,text:o,fix:t});
  });
  if(out.length===ncut){
    alert(cur==='my'?'အားလုံး ဖျက်ထားပါတယ်':'Everything is marked for cutting'); return; }
  btn.disabled=true;
  api('/jobs/'+state.jobid+'/approve',{method:'POST',
      headers:{'Content-Type':'application/json'},
      body:JSON.stringify({segs:out, retakes:RL.map(function(r){
        return {id:r.id, decision:RT[r.id].decision, reason:RT[r.id].reason||''}; }),
        clusters:CLL.map(function(c){ return {id:c.id, keep:CL[c.id]}; })})})
   .then(function(d){
     btn.disabled=false;
     var rb=$('revbar'); if(rb) rb.hidden=true;
     watch(state.jobid);
   })
   .catch(function(e){ btn.disabled=false; alert(String(e.message||e).slice(0,300)); });
}

document.addEventListener('click',function(e){
  var t=e.target;
  if(t && t.id==='revgo'){ revApprove(); return; }
  var rd=t && t.closest && t.closest('[data-rtd]');
  if(rd){ rtDecide(rd); return; }
  var ck=t && t.closest && t.closest('[data-clk]');
  if(ck && !ck.disabled){ clPick(ck); return; }
  var vf=t && t.closest && t.closest('[data-vfmt]');
  if(vf){
    state.vfmt=vf.getAttribute('data-vfmt');
    [].forEach.call(document.querySelectorAll('[data-vfmt]'),function(b){
      b.setAttribute('aria-pressed', b===vf ? 'true':'false'); });
    return;
  }
  if(t && t.id==='scrgo'){ scrMatch(); return; }
});


// ══ အကောင့် · ထွက်ခြင်း ═══════════════════════════════════
// ⚠️ အရင်က **ဘယ်သူ ဝင်နေလဲ မမြင်ရ · ထွက်လို့ မရ**。 token တစ်ခုတည်းဖြစ်၍
//    link ရသူတိုင်း ဖျက်ခွင့်အပါ အပြည့် ရခဲ့သည်。 ယခု အကောင့်တစ်ခုချင်း
//    token ရှိပြီး data ခွဲထားသည်。
var ME=null;
function paintMe(){
  api('/me').then(function(a){
    ME=a;
    var own=!!a.owner;
    var anew=$('acctnew'); if(anew) anew.hidden=!own;
    ['tgchat','tgtok','tgsave'].forEach(function(id){
      var node=$(id); if(node) node.disabled=!own;
    });
    var c=$('acctchip'); if(c) c.textContent=a.name||'';
    var el=$('acctcard'); if(!el) return;
    var my=(cur==='my');
    el.innerHTML =
      '<div class="opt" style="padding-top:0;border:0"><div class="txt"><span>'+
        (my?'ဝင်နေသူ':'Signed in as')+'</span></div>'+
        '<b style="font-size:15px">'+(a.name||'—')+'</b></div>'+
      '<div class="opt"><div class="txt"><span>'+(my?'ဗီဒီယို':'Videos')+
        '</span></div><span class="mono" style="font-size:12px">'+(a.videos||0)+'</span></div>'+
      '<div class="btns" style="margin-top:14px">'+
        '<button class="btn" id="logout2">'+(my?'ထွက်မယ်':'Log out')+'</button></div>'+
      '<div class="rows" id="acctlist" style="margin-top:16px"></div>';
    api('/accounts').then(function(d){
      var l=$('acctlist'); if(!l||!(d.accounts||[]).length) return;
      l.innerHTML='<p class="lede" style="font-size:12.5px;color:var(--tx3);margin:0 0 8px">'+
        (my?'အကောင့်များ — တစ်ခုချင်းရဲ့ ဗီဒီယို · ဘရန်း သီးသန့်':'Accounts — each has its own videos and brands')+'</p>'+
        d.accounts.map(function(x){
        return '<div class="row"><div class="lname"><b>'+x.name+'</b><span class="mono">'+x.id+'</span></div>'+
          '<span class="rt">'+(x.id===a.id?'<span class="pill p-ac">'+(my?'ဝင်နေ':'current')+'</span>':
          '<button class="iact idel" data-adel="'+x.id+'">🗑</button>')+'</span></div>';
      }).join('');
    }).catch(function(){});
  }).catch(function(){});
}
function doLogout(){
  var my=(cur==='my');
  if(!confirmTwo(this, my?'တကယ် ထွက်မှာလား? နောက်တစ်ခါ နှိပ်ပါ':'Log out? Click again')) return;
  localStorage.removeItem('ikki_token'); location.reload();
}
// ⚠️ `confirm()` ကို မမှီခို — browser အချို့မှာ တိတ်တဆိတ် false ပြန်သည်
function confirmTwo(btn, msg){
  if(!btn) return true;
  if(btn.getAttribute('data-arm')==='1'){ clearTimeout(btn.__t); return true; }
  btn.setAttribute('data-arm','1'); btn.__txt=btn.textContent; btn.textContent=msg;
  btn.style.color='#E5484D'; btn.style.borderColor='#E5484D';
  btn.__t=setTimeout(function(){ btn.removeAttribute('data-arm');
    btn.textContent=btn.__txt; btn.style.color=''; btn.style.borderColor=''; },4000);
  return false;
}
document.addEventListener('click', function(e){
  if(e.target && (e.target.id==='logout'||e.target.id==='logout2')) doLogout.call(e.target);
  if(e.target && e.target.id==='acctnew'){
    var my=(cur==='my');
    var nm=window.prompt(my?'အကောင့် အမည်?':'Account name?','');
    if(!nm) return;
    api('/accounts',{method:'POST',headers:{'Content-Type':'application/json'},
        body:JSON.stringify({name:nm})})
     .then(function(d){
       // ⚠️ token ကို **တစ်ခါပဲ** ပြသည် — server မှာ ပြန်မပေးတော့。
       window.prompt(my?'ဒီ token ကို ကူးယူထားပါ — နောက်တစ်ခါ မပြတော့ပါ:'
                       :'Copy this token — it is shown only once:', d.token);
       paintMe();
     }).catch(function(err){ alert(String(err.message||err).slice(0,200)); });
  }
  var ad=e.target.closest&&e.target.closest('[data-adel]');
  if(ad){ if(!confirmTwo(ad,'?')) return;
    api('/accounts/'+ad.getAttribute('data-adel'),{method:'DELETE'})
      .then(paintMe).catch(function(err){ alert(String(err.message||err).slice(0,200)); }); }
});

// ══ Plan · မိနစ် ═══════════════════════════════════════════
// ⚠️ **ငွေပေးချေမှု စနစ် မတပ်ရသေး** — ဒါကြောင့် "ဝယ်မယ်" ဆိုပြီး card
//    တောင်းလို့ မရ。 မိနစ် ကုန်လျှင် ဘာလုပ်ရမလဲ ရှင်းရှင်း ပြပြီး
//    တောင်းဆိုချက်ကို Telegram ကနေ ပို့ပေးသည်。 လိမ်ရာ မကျစေရန်。
var PLAN=null;
function paintPlan(){
  var el=$('plancard'); if(!el) return;
  api('/plan').then(function(d){
    PLAN=d; var my=(cur==='my'), p=d.plan||{};
    var low = d.left <= Math.max(10, d.quota*0.1);
    el.innerHTML =
      '<div style="display:flex;justify-content:space-between;align-items:baseline;flex-wrap:wrap;gap:10px">'+
        '<b style="font-size:19px;font-weight:700">'+(p.name||'—')+'</b>'+
        '<span class="mono" style="font-size:12px;color:var(--tx3)">'+(p.price||'')+'</span></div>'+
      '<div class="meter" style="margin:14px 0 8px"><i style="width:'+Math.round(d.pct*100)+'%"></i></div>'+
      '<p class="mono" style="font-size:12.5px;color:var(--tx2)">'+
        d.used+' / '+d.quota+' '+(my?'မိနစ်':'min')+' · '+
        (my?'ကျန် ':'left ')+d.left+'</p>'+
      (p.renews?'<div class="opt"><div class="txt"><span>'+(my?'သက်တမ်း':'Renews')+
        '</span></div><span class="mono" style="font-size:12px">'+p.renews+'</span></div>':'')+
      (p.contact?'<div class="opt"><div class="txt"><span>'+(my?'ဆက်သွယ်ရန်':'Contact')+
        '</span></div><span class="mono" style="font-size:12px">'+p.contact+'</span></div>':'')+
      (low?'<p class="lede" style="font-size:13px;color:var(--ac);margin-top:12px">'+
        (my?'မိနစ် နည်းနေပါပြီ — ကုန်သွားရင် ဗီဒီယို ထပ်မထုတ်နိုင်တော့ပါဘူး။'
           :'Running low — rendering stops when it hits zero.')+'</p>':'')+
      '<div class="btns" style="margin-top:16px">'+
        '<button class="cta" id="topup">'+(my?'မိနစ် ထပ်တောင်းမယ်':'Ask for more minutes')+'</button>'+
      '</div>'+
      '<p class="lede" style="font-size:12px;color:var(--tx3);margin-top:10px">'+
        (my?'မိနစ် ဝယ်ချင်ရင် အောက်က <b>ငွေပေးချေမှု</b> မှာ KBZPay / Wave Pay / CB Pay နဲ့ လွှဲပြီး ငွေလွှဲနံပါတ် တင်ပါ။'
           :'To buy minutes, use <b>Payment</b> below — KBZPay / Wave Pay / CB Pay, then submit the transaction ID.')+'</p>';
  }).catch(function(){});
}
document.addEventListener('click', function(e){
  if(e.target && e.target.id==='topup'){
    var my=(cur==='my');
    var n=window.prompt(my?'ဘယ်နှစ်မိနစ် လိုချင်လဲ?':'How many minutes?','300');
    if(n===null) return;
    e.target.disabled=true;
    api('/plan/topup',{method:'POST',headers:{'Content-Type':'application/json'},
        body:JSON.stringify({minutes:n})})
     .then(function(d){ e.target.disabled=false;
       alert((d.sent? (my?'တောင်းဆိုချက် ပို့ပြီးပါပြီ။':'Request sent.')
                    : (my?'Telegram မသတ်မှတ်ရသေးလို့ မပို့နိုင်ပါ — အောက်မှာ ထည့်ပါ။'
                        :'Telegram is not set up yet — add it below.'))
             + (d.contact? '\n'+d.contact : '')); })
     .catch(function(err){ e.target.disabled=false; alert(String(err.message||err).slice(0,200)); });
  }
  if(e.target && e.target.id==='planedit'){
    var f=$('planform'); if(!f) return;
    if(!f.hidden){ f.hidden=true; return; }
    var p=(PLAN&&PLAN.plan)||{}, my=(cur==='my');
    f.innerHTML=['name','quota','price','renews','contact'].map(function(k){
      var lab={name:my?'အမည်':'Name',quota:my?'မိနစ် ကန့်သတ်':'Monthly minutes',
               price:my?'ဈေးနှုန်း':'Price',renews:my?'သက်တမ်း':'Renews',
               contact:my?'ဆက်သွယ်ရန်':'Contact'}[k];
      return '<div class="opt"><div class="txt"><span>'+lab+'</span></div>'+
        '<input class="inp planf" data-k="'+k+'" value="'+(p[k]==null?'':p[k])+'" style="width:200px"></div>';
    }).join('')+'<div class="btns" style="margin-top:14px"><button class="btn" id="plansave">'+
      (my?'သိမ်းမယ်':'Save')+'</button></div>';
    f.hidden=false;
  }
  if(e.target && e.target.id==='plansave'){
    var body={};
    [].forEach.call(document.querySelectorAll('.planf'),function(i){ body[i.getAttribute('data-k')]=i.value; });
    e.target.disabled=true;
    api('/plan',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)})
     .then(function(){ e.target.disabled=false; $('planform').hidden=true; paintPlan(); loadMeta&&loadMeta(); })
     .catch(function(err){ e.target.disabled=false; alert(String(err.message||err).slice(0,200)); });
  }
});

// ══ ငွေပေးချေမှု · KBZPay / Wave / CB Pay ═══════════════════
// ⚠️ ဒါက card gateway **မဟုတ်**。 server က ငွေရပြီးမပြီး မသိနိုင်သဖြင့် —
//    ၁။ တင်ပြပြီးတာနဲ့ "ငွေရပြီးပါပြီ" ဟု မပြရ ⇒ "စစ်ဆေးနေဆဲ" ဟုသာ ပြသည်
//    ၂။ ဆက်တင်/အတည်ပြု ခလုပ်များကို ပိုင်ရှင်မဟုတ်လျှင် **မပြရ**
//    ၃။ QR ပုံ မရှိလျှင် နံပါတ်ကို ကူးယူနိုင်အောင် copy ခလုပ် ထားရမည် —
//       ဖုန်းထဲက app ကနေ နံပါတ် လက်နဲ့ ကူးရတာ မှားလွယ်သည်。
var PAY=null;
function eh(s){ return String(s==null?'':s)
  .replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;'); }
function payStat(st,my){
  if(st==='ok')  return '<span class="pill p-ok">'+(my?'အတည်ပြုပြီး':'Approved')+'</span>';
  if(st==='no')  return '<span class="pill p-no">'+(my?'လက်မခံပါ':'Declined')+'</span>';
  return '<span class="pill">'+(my?'စစ်ဆေးနေဆဲ':'Checking')+'</span>';
}
function paintPay(){
  var el=$('paycard'); if(!el) return;
  api('/pay').then(function(d){
    PAY=d; var my=(cur==='my');
    var eb=$('payedit'); if(eb) eb.hidden=!d.owner;
    var on=(d.methods||[]).filter(function(m){return m.on && (m.num||m.qr)});
    var h='';
    if(!on.length){
      h+='<p class="lede" style="font-size:13.5px;color:var(--tx2)">'+
        (my?(d.owner?'ငွေလက်ခံမယ့် နည်းလမ်း မဖွင့်ရသေးပါဘူး။ <b>ဆက်တင်</b> ကနှိပ်ပြီး KBZPay / Wave Pay / CB Pay နံပါတ်နဲ့ QR ထည့်ပါ။'
                     :'ငွေပေးချေမှု နည်းလမ်း မဖွင့်ရသေးပါဘူး — မိနစ် လိုရင် အောက်က ခလုပ်နဲ့ တောင်းပါ။')
            :(d.owner?'No payment method is switched on yet. Open <b>Settings</b> and add a KBZPay / Wave Pay / CB Pay number and QR.'
                     :'No payment method is live yet — use the button below to ask for minutes.'))+'</p>';
    } else {
      h+='<div class="paygrid">'+on.map(function(m){
        return '<div class="paym" data-m="'+m.id+'">'+
          '<div class="pmh"><b>'+eh(my?m.my:m.en)+'</b>'+
            (m.name?'<span class="mono">'+eh(m.name)+'</span>':'')+'</div>'+
          (m.qr?'<img class="pqr" alt="'+eh(m.my)+' QR" src="/api/pay/qr/'+m.id+
                '?t='+encodeURIComponent(TOKEN)+'&v='+Date.now()+'">'
               :'<div class="pqr none">'+(my?'QR မရှိ':'No QR')+'</div>')+
          (m.num?'<button class="pnum" data-copy="'+eh(m.num)+'">'+eh(m.num)+
                 ' <span>'+(my?'ကူးမယ်':'copy')+'</span></button>':'')+
          '</div>';
      }).join('')+'</div>';
      if(d.rate>0) h+='<p class="mono" style="font-size:12.5px;color:var(--tx2);margin-top:12px">'+
        (my?'၁ မိနစ် = ':'1 minute = ')+Number(d.rate).toLocaleString()+' MMK</p>';
      h+='<ol class="paysteps">'+
        (my?['ဖုန်းက app နဲ့ အပေါ်က QR ကို scan ဖတ်ပါ (ဒါမှမဟုတ် နံပါတ်ကို ကူးထည့်ပါ)',
             'ငွေလွှဲပြီးရင် <b>ငွေလွှဲနံပါတ် (transaction ID)</b> ကို မှတ်ထားပါ',
             'အောက်က ခလုပ်ကနှိပ်ပြီး ပမာဏနဲ့ ငွေလွှဲနံပါတ် ထည့်ပါ',
             'စစ်ဆေးပြီးတာနဲ့ မိနစ် တက်သွားပါမယ် — အခြေအနေကို အောက်မှာ ပြပါမယ်']
           :['Scan the QR above in your bank app (or copy the number)',
             'Note the <b>transaction ID</b> from the receipt',
             'Press the button below and enter the amount and that ID',
             'Minutes land once it is checked — the status shows below'])
        .map(function(s){return '<li>'+s+'</li>'}).join('')+'</ol>';
      h+='<div class="btns" style="margin-top:14px">'+
         '<button class="cta" id="paynew">'+(my?'ငွေလွှဲပြီးပြီ — တင်ပြမယ်':'I have paid — submit')+'</button></div>';
      h+='<p class="lede" style="font-size:12px;color:var(--tx3);margin-top:10px">'+
        (my?'ငွေလွှဲနံပါတ်ကို bank app ထဲ လိုက်စစ်ပြီးမှ အတည်ပြုပါတယ် — ချက်ချင်း မတက်ပါဘူး။'
           :'The transfer is checked against the bank app before it is approved — it is not instant.')+'</p>';
    }
    // ── ကိုယ့် တောင်းဆိုချက်များ ──
    var mine=d.mine||[];
    if(mine.length){
      h+='<div class="sech" style="margin:20px 0 8px;padding:0"><h3 style="font-size:13px">'+
        (my?'ကိုယ့် တင်ပြချက်များ':'Your submissions')+'</h3></div>';
      h+=mine.map(function(r){
        return '<div class="opt"><div class="txt"><span>'+
          eh(payName(r.method,my))+' · '+Number(r.amount||0).toLocaleString()+' MMK'+
          (r.minutes?' · '+r.minutes+(my?' မိနစ်':' min'):'')+'</span>'+
          '<span class="mono" style="font-size:11.5px">'+eh(r.ref)+
          (r.why?' · '+eh(r.why):'')+'</span></div>'+
          payStat(r.status,my)+
          (r.status==='pending'?' <button class="lnk paydel" data-id="'+r.id+'">'+
            (my?'ရုပ်သိမ်း':'cancel')+'</button>':'')+'</div>';
      }).join('');
    }
    el.innerHTML=h;
    if(d.owner) paintPayAdmin();
  }).catch(function(err){ console.error('pay',err); });
}
function payName(id,my){
  var m=(PAY&&PAY.methods||[]).filter(function(x){return x.id===id})[0];
  return m?(my?m.my:m.en):id;
}
function paintPayAdmin(){
  var sec=$('paysech'), el=$('payadmin'); if(!el) return;
  api('/pay/all').then(function(d){
    var rows=d.pays||[], my=(cur==='my');
    var pend=rows.filter(function(r){return r.status==='pending'});
    sec.hidden = rows.length===0; el.hidden = rows.length===0;
    if(!rows.length) return;
    el.innerHTML=(pend.length?'':'<p class="lede" style="font-size:13px;color:var(--tx2)">'+
        (my?'စစ်ဆေးရန် မရှိပါ။':'Nothing to review.')+'</p>')+
      rows.slice(0,40).map(function(r){
        var mins=r.minutes||'';
        return '<div class="opt"><div class="txt"><b>'+eh(r.acct_name||r.acct)+'</b>'+
          '<span>'+eh(payName(r.method,my))+' · '+Number(r.amount||0).toLocaleString()+' MMK · '+
          (my?'ငွေလွှဲနံပါတ် ':'ref ')+'<span class="mono">'+eh(r.ref)+'</span>'+
          (r.note?' · '+eh(r.note):'')+'</span></div>'+
          (r.status==='pending'
            ? '<span style="display:flex;gap:6px;align-items:center">'+
              '<input class="inp paymin" data-id="'+r.id+'" value="'+eh(mins)+
              '" style="width:74px" aria-label="minutes">'+
              '<button class="btn payok" data-id="'+r.id+'">'+(my?'အတည်ပြု':'Approve')+'</button>'+
              '<button class="lnk payno" data-id="'+r.id+'">'+(my?'လက်မခံ':'Decline')+'</button></span>'
            : payStat(r.status,my))+'</div>';
      }).join('');
  }).catch(function(err){ console.error('payall',err); });
}
document.addEventListener('click', function(e){
  var t=e.target.closest?e.target.closest('button,a'):e.target;
  if(!t) return;
  var my=(cur==='my');
  // ── နံပါတ် ကူးယူ ──
  if(t.classList.contains('pnum')){
    var v=t.getAttribute('data-copy')||'';
    var done=function(){ var o=t.innerHTML; t.innerHTML=eh(v)+' <span>'+(my?'ကူးပြီး ✓':'copied ✓')+'</span>';
      setTimeout(function(){ t.innerHTML=o; },1600); };
    if(navigator.clipboard&&navigator.clipboard.writeText){
      navigator.clipboard.writeText(v).then(done,function(){ window.prompt(my?'ကူးယူပါ':'Copy',v); });
    } else { window.prompt(my?'ကူးယူပါ':'Copy',v); }
  }
  // ── ငွေလွှဲ တင်ပြခြင်း ──
  if(t.id==='paynew'){
    var on=(PAY&&PAY.methods||[]).filter(function(m){return m.on&&(m.num||m.qr)});
    if(!on.length) return;
    var mid=on[0].id;
    if(on.length>1){
      var pick=window.prompt((my?'ဘယ်ကနေ လွှဲလဲ? ':'Which one? ')+
        on.map(function(m,i){return (i+1)+') '+(my?m.my:m.en)}).join('  '),'1');
      if(pick===null) return;
      var ix=parseInt(pick,10)-1; if(!(ix>=0&&ix<on.length)) return alert(my?'မမှန်ပါ':'Not valid');
      mid=on[ix].id;
    }
    var amt=window.prompt(my?'ဘယ်လောက် လွှဲလိုက်လဲ? (MMK)':'How much did you send? (MMK)','');
    if(amt===null) return;
    var ref=window.prompt(my?'ငွေလွှဲနံပါတ် (transaction ID) — bank app ထဲမှာ ရှိပါတယ်'
                            :'Transaction ID — it is in your bank app','');
    if(ref===null) return;
    t.disabled=true;
    api('/pay',{method:'POST',headers:{'Content-Type':'application/json'},
        body:JSON.stringify({method:mid,amount:amt,ref:ref})})
     .then(function(d){ t.disabled=false;
       alert(my?('တင်ပြပြီးပါပြီ။ ငွေလွှဲနံပါတ်ကို စစ်ဆေးပြီးမှ'+
                 (d.minutes?' '+d.minutes+' မိနစ် ':' မိနစ် ')+'တက်ပါမယ်။')
               :('Submitted. Minutes land once the transfer is checked'+
                 (d.minutes?' ('+d.minutes+' min)':'')+'.'));
       paintPay(); })
     .catch(function(err){ t.disabled=false; alert(String(err.message||err).slice(0,200)); });
  }
  if(t.classList.contains('paydel')){
    if(t.getAttribute('data-sure')!=='1'){
      t.setAttribute('data-sure','1'); t.textContent=(my?'သေချာလား?':'sure?');
      setTimeout(function(){ if(t.parentNode){t.removeAttribute('data-sure'); t.textContent=(my?'ရုပ်သိမ်း':'cancel');} },4000);
      return;
    }
    api('/pay/'+t.getAttribute('data-id'),{method:'DELETE'})
     .then(paintPay).catch(function(err){ alert(String(err.message||err).slice(0,200)); });
  }
  // ── ပိုင်ရှင် · အတည်ပြု / လက်မခံ ──
  if(t.classList.contains('payok')){
    var id=t.getAttribute('data-id');
    var box=document.querySelector('.paymin[data-id="'+id+'"]');
    var mn=box?box.value:'';
    if(!(parseFloat(mn)>0)) return alert(my?'ဘယ်နှစ်မိနစ် ပေါင်းထည့်မလဲ ထည့်ပါ':'Enter the minutes to add');
    if(t.getAttribute('data-sure')!=='1'){
      t.setAttribute('data-sure','1'); t.textContent=(my?'သေချာလား?':'sure?'); return;
    }
    t.disabled=true;
    api('/pay/'+id+'/approve',{method:'POST',headers:{'Content-Type':'application/json'},
        body:JSON.stringify({minutes:mn})})
     .then(function(){ paintPay(); paintPlan(); })
     .catch(function(err){ t.disabled=false; alert(String(err.message||err).slice(0,200)); });
  }
  if(t.classList.contains('payno')){
    var id2=t.getAttribute('data-id');
    var why=window.prompt(my?'ဘာကြောင့် လက်မခံလဲ? (သုံးစွဲသူ မြင်ရမယ်)':'Why declined? (the user sees this)','');
    if(why===null) return;
    api('/pay/'+id2+'/reject',{method:'POST',headers:{'Content-Type':'application/json'},
        body:JSON.stringify({why:why})})
     .then(function(){ paintPay(); })
     .catch(function(err){ alert(String(err.message||err).slice(0,200)); });
  }
  if(t.id==='payrefresh'){ paintPayAdmin(); }
  // ── ပိုင်ရှင် · ဆက်တင် ──
  if(t.id==='payedit'){
    var f=$('payform'); if(!f) return;
    if(!f.hidden){ f.hidden=true; return; }
    var d=PAY||{methods:[],rate:0};
    f.innerHTML='<div class="opt"><div class="txt"><b>'+(my?'၁ မိနစ် ဈေးနှုန်း':'Price per minute')+
        '</b><span>'+(my?'ပမာဏကနေ မိနစ်ကို အလိုအလျောက် တွက်ပါမယ်':'Turns the amount into minutes')+
        '</span></div><input class="inp" id="payrate" value="'+eh(d.rate||'')+
        '" style="width:120px" aria-label="rate"> <span class="mono" style="font-size:12px">MMK</span></div>'+
      (d.methods||[]).map(function(m){
        return '<div class="paycfg" data-m="'+m.id+'">'+
          '<div class="opt"><div class="txt"><b>'+eh(my?m.my:m.en)+'</b>'+
            '<span>'+(my?'ဖုန်းနံပါတ် / အကောင့်နာမည်':'Number / account name')+'</span></div>'+
            '<label class="chk"><input type="checkbox" class="payon" '+(m.on?'checked':'')+
            '> <span>'+(my?'ဖွင့်':'On')+'</span></label></div>'+
          '<div class="opt"><div class="txt"><span>'+(my?'နံပါတ်':'Number')+'</span></div>'+
            '<input class="inp paynum" value="'+eh(m.num)+'" style="width:190px" aria-label="number"></div>'+
          '<div class="opt"><div class="txt"><span>'+(my?'အကောင့် နာမည်':'Account name')+'</span></div>'+
            '<input class="inp payname" value="'+eh(m.name)+'" style="width:190px" aria-label="name"></div>'+
          '<div class="opt"><div class="txt"><span>QR</span>'+
            '<span>'+(m.qr?(my?'ထည့်ပြီးသား':'uploaded'):(my?'မထည့်ရသေး':'none'))+'</span></div>'+
            '<span style="display:flex;gap:6px"><label class="btn">'+(my?'QR တင်မယ်':'Upload QR')+
            '<input type="file" accept="image/*" class="payqr" data-m="'+m.id+'" hidden></label>'+
            (m.qr?'<button class="lnk payqrdel" data-m="'+m.id+'">'+(my?'ဖျက်':'remove')+'</button>':'')+
            '</span></div></div>';
      }).join('')+
      '<div class="btns" style="margin-top:14px"><button class="btn" id="paysave">'+
      (my?'သိမ်းမယ်':'Save')+'</button></div>';
    f.hidden=false;
  }
  if(t.id==='paysave'){
    var body={rate:$('payrate').value};
    [].forEach.call(document.querySelectorAll('.paycfg'),function(c){
      body[c.getAttribute('data-m')]={
        on: c.querySelector('.payon').checked,
        num: c.querySelector('.paynum').value.trim(),
        name: c.querySelector('.payname').value.trim()};
    });
    t.disabled=true;
    api('/pay/settings',{method:'POST',headers:{'Content-Type':'application/json'},
        body:JSON.stringify(body)})
     .then(function(){ t.disabled=false; $('payform').hidden=true; paintPay(); })
     .catch(function(err){ t.disabled=false; alert(String(err.message||err).slice(0,200)); });
  }
  if(t.classList.contains('payqrdel')){
    api('/pay/qr/'+t.getAttribute('data-m'),{method:'DELETE'})
     .then(function(){ paintPay(); $('payform').hidden=true; })
     .catch(function(err){ alert(String(err.message||err).slice(0,200)); });
  }
});
// ⚠️ file input က click event မဟုတ် — change ကို သီးသန့် နားထောင်ရသည်
document.addEventListener('change', function(e){
  if(!e.target.classList || !e.target.classList.contains('payqr')) return;
  var f=e.target.files && e.target.files[0]; if(!f) return;
  var mid=e.target.getAttribute('data-m'), my=(cur==='my');
  var fd=new FormData(); fd.append('file',f);
  fetch('/api/pay/qr/'+mid,{method:'POST',headers:{Authorization:'Bearer '+TOKEN},body:fd})
   .then(function(r){ if(!r.ok) return r.text().then(function(x){throw new Error(x)}); return r.json(); })
   .then(function(){ paintPay(); $('payform').hidden=true;
     alert(my?'QR တင်ပြီးပါပြီ။':'QR uploaded.'); })
   .catch(function(err){ alert(String(err.message||err).slice(0,200)); });
});

// ══ အမှိုက်ပုံး — ၂၄ နာရီအတွင်း ပြန်ရနိုင် ═══════════════════
// ⚠️ ဖျက်လိုက်တာ **ဘယ်ရောက်သွားလဲ မမြင်ရလျှင်** သုံးစွဲသူက ပျောက်သွားပြီ
//    ထင်သည်。 undo bar က ၁၅ စက္ကန့်ပဲ ရှိသည် — ဒီစာရင်းက ၂၄ နာရီ ရှိသည်。
function paintTrash(){
  var sec=$('trashsec'), el=$('trashlist'); if(!el) return;
  api('/trash').then(function(d){
    var it=d.jobs||[], my=(cur==='my');
    sec.hidden = it.length===0; el.innerHTML='';
    if(!it.length) return;
    var n=$('trashnote');
    if(n) n.textContent = my ? '၂၄ နာရီအတွင်း ပြန်ယူလို့ ရတယ်' : 'restorable for 24 hours';
    el.innerHTML=it.map(function(j){
      var left=Math.max(0, 86400-(Date.now()/1000-(j.deleted||0)));
      var hh=Math.floor(left/3600), mm=Math.floor((left%3600)/60);
      return '<div class="lrow"><div class="thumb im'+((j.id.charCodeAt(3)%5)+1)+'"></div>'+
        '<div class="lname"><b>'+(j.title||j.id)+'</b><span>'+(j.brand_id||'')+'</span></div>'+
        '<div class="lmeta hidesm">'+(j.recipe||'')+'</div>'+
        '<div class="ldur hidesm mono">'+hh+'h '+mm+'m</div><div class="wave hidesm"></div>'+
        '<div class="lacts"><button class="btn" data-restore="'+j.id+'">'+
        (my?'ပြန်ယူမယ်':'Restore')+'</button></div></div>';
    }).join('');
  }).catch(function(){});
}
document.addEventListener('click', function(e){
  var r=e.target.closest&&e.target.closest('[data-restore]');
  if(!r) return;
  r.disabled=true;
  api('/jobs/'+r.getAttribute('data-restore')+'/restore',{method:'POST'})
   .then(function(){ loadJobs(); paintTrash(); })
   .catch(function(err){ r.disabled=false; alert(String(err.message||err).slice(0,200)); });
});

// ══ ဖျက်ပြီးရင် ပြန်ယူခြင်း ═════════════════════════════════
var UNDO=null, UNDOT=null;
function showUndo(id, name){
  UNDO=id;
  var b=$('undobar'), t=$('undotxt'); if(!b) return;
  b.hidden=false;
  if(t) t.textContent = (cur==='my'
    ? '"'+(name||id)+'" ကို အမှိုက်ပုံးထဲ ထည့်လိုက်ပါပြီ — ၂၄ နာရီအတွင်း ပြန်ယူလို့ ရပါတယ်။'
    : '"'+(name||id)+'" moved to trash — you can undo within 24 hours.');
  clearTimeout(UNDOT);
  UNDOT=setTimeout(function(){ b.hidden=true; }, 15000);
}
var ug=$('undogo');
if(ug) ug.onclick=function(){
  if(!UNDO) return;
  ug.disabled=true;
  api('/jobs/'+UNDO+'/restore',{method:'POST'})
   .then(function(){ ug.disabled=false; $('undobar').hidden=true; UNDO=null; loadJobs(); })
   .catch(function(e){ ug.disabled=false; alert(String(e.message||e).slice(0,200)); });
};

// ══ ဖျက်ထားတာကို **ချက်ချင်း ကြည့်** (render မလုပ်ဘဲ) ════════
// ⚠️ ပြန်ထုတ်ရင် ၄–၈ မိနစ် ကြာသည် — ဖျက်လိုက်တာ ဘယ်လို ဖြစ်မလဲ
//    အဲဒီမတိုင်ခင် သိရမည်。 ⇒ player ကို ဖျက်ထားတဲ့ အပိုင်း ရောက်တိုင်း
//    **ခုန်ကျော်**ခိုင်းသည် (ရိုက်ထည့်တာ မဟုတ်、ကြည့်ရုံ)。
function gapList(){
  var g=[];
  [].forEach.call(document.querySelectorAll('#tx .row.gone'),function(r){
    var i=parseInt(r.getAttribute('data-i'),10), s=state.segs[i];
    if(s && s.o0!==undefined && s.o1!==undefined) g.push([s.o0, s.o1]);
  });
  return g.sort(function(a,b){return a[0]-b[0]});
}
function livePreview(){
  var v=$('prev'); if(!v) return;
  if(!v.__skip){
    v.__skip=true;
    v.addEventListener('timeupdate', function(){
      var g=(v.__gaps||[]);
      for(var i=0;i<g.length;i++){
        if(v.currentTime>=g[i][0]-0.05 && v.currentTime<g[i][1]-0.05){
          v.currentTime=g[i][1]; return;
        }
      }
    });
  }
  v.__gaps = gapList();
  var n=$('pvnote');
  if(n){
    var t=v.__gaps.reduce(function(a,x){return a+(x[1]-x[0])},0);
    n.hidden = v.__gaps.length===0;
    n.textContent = (cur==='my'
      ? 'ဖျက်ထားတာ '+v.__gaps.length+' ကြောင်း · '+t.toFixed(1)+'s — အပေါ်က ဗီဒီယိုက အဲဒီအပိုင်းတွေကို ခုန်ကျော်ပြီး ပြပါမယ် (ပြန်ထုတ်ရင် တကယ် ပါသွားပါမယ်)'
      : v.__gaps.length+' line(s) · '+t.toFixed(1)+'s — the player above skips them so you can hear the result before rendering');
  }
}

// ══ ပြင်ပြီး ပြန်ထုတ် — done စာမျက်နှာ ═════════════════════
// ⚠️ ဖောင့် · အရောင် · စာတန်း · ဂရပ်ဖစ် တွေက ဗီဒီယိုထဲ **ရိုက်ထည့်ပြီးသား** ⇒
//    ပြောင်းရင် ပြန်ထုတ်မှ ရသည်。 ပြန်ထုတ်တာက အရည်အသွေး မကျ — render တိုင်း
//    မူရင်း upload ကနေ ပြန်စသည်、ရှေ့ထုတ်ထားတာကနေ ဆက်မလုပ်ဘူး。
//    (တိုင်းထားသည် — encode တစ်ကြိမ် ထပ်လျှင်ပင် SSIM 0.9988 · PSNR 55dB)
var ADJ = {};                       // သုံးစွဲသူ ပြောင်းထားတာသာ
var CUTOPT = [];                    // ဖြတ်ပုံ ရွေးစရာ
var STYDEF = {};                    // ပုံစံရဲ့ ပုံသေ

function rrSum(){
  // ⚠️ "ဘာတွေ ပြောင်းမှာလဲ" ကို **ရေတွက်ပြပြီးမှ** ခလုပ် ပြရမည် —
  //    ဘာမှ မပြောင်းဘဲ ပြန်ထုတ်လျှင် မိနစ် အလကား ကုန်သည်。
  var bar=$('rrbar'), sm=$('rrsum'); if(!bar) return;
  var nset=Object.keys(ADJ||{}).length;
  var ncut=0, nfix=0;
  [].forEach.call(document.querySelectorAll('#tx .row'),function(r){
    var i=parseInt(r.getAttribute('data-i'),10);
    if(r.classList.contains('gone')){ ncut++; return; }
    var ed=r.querySelector('[data-ed]'); if(!ed) return;
    var o=((state.segs[i]||{}).text||'').trim(), t=(ed.textContent||'').trim();
    if(t!==o) nfix++;
  });
  var n=nset+ncut+nfix;
  bar.hidden = n===0;
  if(!sm) return;
  var my=(cur==='my'), p=[];
  if(nset) p.push(my? nset+' ခု ပြင်ထား' : nset+' setting changed');
  if(ncut) p.push(my? ncut+' ကြောင်း ဖြတ် (ရုပ်+အသံ ပါ)' : ncut+' line(s) cut from the video');
  if(nfix) p.push(my? nfix+' ကြောင်း စာတန်း ပြင်' : nfix+' caption fix(es)');
  sm.textContent = p.join(' · ') + (my
    ? ' — အားလုံးကို တစ်ခါတည်း ပြန်ထုတ်ပါမယ်။'
    : ' — all of it goes in one render.');
}

function adjPaint(){
  var el=$('adjrows'); if(!el) return;
  var d=STYDEF||{}, my=(cur==='my');
  function num(k,label,hint,min,max,step){
    var v=(ADJ[k]!==undefined)?ADJ[k]:(d[k]!==undefined?d[k]:'');
    return '<div class="row"><div class="lname"><b>'+label+'</b><span>'+hint+'</span></div>'+
      '<span class="rt"><input class="inp adjn" data-k="'+k+'" type="number" min="'+min+
      '" max="'+max+'" step="'+step+'" value="'+v+'" style="width:92px;text-align:right">'+
      (ADJ[k]!==undefined?'<span class="pill p-ac" style="margin-left:8px">'+(my?'ပြင်ထား':'changed')+'</span>':'')+
      '</span></div>';
  }
  function col(k,label,hint,dflt){
    var v=(ADJ[k]!==undefined)?ADJ[k]:(d[k]||dflt);
    return '<div class="row"><div class="lname"><b>'+label+'</b><span>'+hint+'</span></div>'+
      '<span class="rt"><input class="adjc" data-k="'+k+'" type="color" value="'+v+'" '+
      'style="width:44px;height:30px;border:1px solid var(--line);border-radius:8px;background:none">'+
      (ADJ[k]!==undefined?'<span class="pill p-ac" style="margin-left:8px">'+(my?'ပြင်ထား':'changed')+'</span>':'')+
      '</span></div>';
  }
  var copt=(CUTOPT||[]).map(function(c){
    var sel=((ADJ.cut||d.cut)===c.id)?' selected':'';
    return '<option value="'+c.id+'"'+sel+'>'+(my?c.my:c.en)+'</option>'; }).join('');
  var fopt=(FONTS||[]).map(function(f){
    var sel=((ADJ.mmf||d.mmf)===f.id)?' selected':'';
    return '<option value="'+f.id+'"'+sel+'>'+f.name+'</option>'; }).join('');
  el.innerHTML =
    // ⚠️ အလိုအလျောက် ဖြတ်တာ သဘောမကျလျှင် **ဒီမှာ ပြောင်းရသည်** —
    //    "မဖြတ်ပါ" ဆိုလျှင် တိတ်ဆိတ်မှု တစ်ခုမှ မဖြတ်တော့ဘူး。
    '<div class="row"><div class="lname"><b>'+(my?'အလိုအလျောက် ဖြတ်ပုံ':'Automatic cutting')+'</b>'+
      '<span>'+(my?'တိတ်ဆိတ်မှု ဘယ်လောက် ဖြတ်မလဲ':'how much silence to remove')+'</span></div>'+
      '<span class="rt"><select class="inp" id="adjcut" style="min-width:150px">'+copt+'</select>'+
      (ADJ.cut!==undefined?'<span class="pill p-ac" style="margin-left:8px">'+(my?'ပြင်ထား':'changed')+'</span>':'')+
      '</span></div>'+
    '<div class="row"><div class="lname"><b>'+(my?'စာတန်း ဖောင့်':'Subtitle font')+'</b>'+
      '<span>'+(my?'ရွေးလိုက်တဲ့ ဖောင့်အတိုင်း ထွက်မယ်':'the font you pick is the font you get')+'</span></div>'+
      '<span class="rt"><select class="inp" id="adjfont" style="min-width:170px">'+fopt+'</select></span></div>'+
    col('cap_fill', my?'စာတန်း အရောင်':'Subtitle colour',
        my?'အဖြူနံရံပေါ် အဖြူစာ မမြင်ရ — သတိထား':'white on a white wall disappears', '#FFFFFF')+
    col('cap_stroke', my?'အနားသတ် အရောင်':'Outline colour',
        my?'စာလုံးဘေးက အနား — ဖတ်ရလွယ်စေတယ်':'the edge around the letters', '#0B1B33')+
    num('cap_pct', my?'စာတန်း အရွယ်':'Subtitle size',
        my?'ဘောင်အမြင့်ရဲ့ အချိုး (၀.၀၃၅–၀.၁၁)':'share of frame height', 0.035, 0.110, 0.001)+
    num('cap_cover', my?'စာတန်း ဘယ်လောက်':'Subtitle coverage',
        my?'၀ = လုံးဝ မပါ · ၁ = အားလုံး':'0 = none · 1 = every line', 0, 1, 0.05)+
    num('gfx', my?'ဂရပ်ဖစ် အရေအတွက်':'Graphic cards',
        my?'၀ = မပါ':'0 = none', 0, 14, 1)+
    num('cap_typo', my?'Typography ဘယ်လောက်':'Typography share',
        my?'၀ = မပါ · စာတန်းရဲ့ အချိုး':'0 = none · share of captions', 0, 0.6, 0.05)+
    num('broll', my?'B-roll အရေအတွက်':'B-roll clips',
        my?'၀ = မပါ':'0 = none', 0, 20, 1);
  var c=$('adjcost');
  if(c) c.textContent = my
    ? 'ပြန်ထုတ်တိုင်း မိနစ် ကုန်ပါတယ် (ဗီဒီယို အရှည်အတိုင်း) · ၄–၈ မိနစ် စောင့်ရပါမယ်။'
    : 'Each re-render spends quota minutes (the video length) and takes 4–8 minutes.';
}

document.addEventListener('input', function(e){
  var n=e.target.closest&&e.target.closest('.adjn');
  if(n){ var k=n.getAttribute('data-k'); var v=parseFloat(n.value);
         if(isNaN(v)) delete ADJ[k]; else ADJ[k]=v; rrSum(); return; }
  var c=e.target.closest&&e.target.closest('.adjc');
  if(c){ ADJ[c.getAttribute('data-k')]=c.value; rrSum(); }
});
document.addEventListener('change', function(e){
  if(e.target && e.target.id==='adjfont'){ ADJ.mmf=e.target.value; rrSum(); }
  if(e.target && e.target.id==='adjcut'){ ADJ.cut=e.target.value; adjPaint(); rrSum(); }
});
document.addEventListener('click', function(e){
  if(e.target && e.target.id==='adjreset'){
    // ⚠️ "ပုံသေ ပြန်သုံး" = **ပြင်ချက် အားလုံး ဖျက်** (ပုံစံရဲ့ တိုင်းထားသော
    //    ကိန်းတွေ ပြန်သုံး)。 ဗီဒီယိုကို မထိ — ပြန်ထုတ်မှ သက်ရောက်သည်。
    ADJ={}; adjPaint(); rrSum();
  }
});

// ══ ရုပ်ကြမ်း · ပုံ စာကြည့်တိုက် ═══════════════════════════
function paintBroll(){
  var el=$('brolllist'); if(!el) return;
  api('/broll').then(function(d){
    var my=(cur==='my'), it=d.items||[];
    if(!it.length){
      el.innerHTML='<div class="row"><div class="lname"><b>'+
        (my?'ဘာမှ မထည့်ရသေးဘူး':'Nothing added yet')+'</b><span>'+
        (my?'ပုံ ဒါမှမဟုတ် ရုပ်ကြမ်း ထည့်ကြည့်ပါ':'add a photo or a clip')+'</span></div></div>';
      return;
    }
    var P={pending:['p-dim',my?'စောင့်နေ':'queued'],
           indexed:['p-ok',my?'ထည့်ပြီး':'added'],
           failed:['p-no',my?'မရ':'rejected']};
    el.innerHTML=it.map(function(x){
      var p=P[x.status]||P.pending;
      var tg=[]; try{ tg=JSON.parse(x.tags||'[]') }catch(e){}
      return '<div class="row"><div class="lname"><b>'+(x.name||x.id)+'</b>'+
        '<span class="my">'+(tg.join(' · ')||x.note||'')+'</span></div>'+
        '<div class="lmeta hidesm">'+(x.ext||'')+'</div><div class="wave hidesm"></div>'+
        '<div class="lacts"><span class="pill '+p[0]+'">'+p[1]+'</span>'+
        '<button class="iact idel" data-bdel="'+x.id+'" aria-label="Delete">🗑</button></div></div>';
    }).join('');
  }).catch(function(){});
}
document.addEventListener('change', function(e){
  var inp=e.target.closest&&e.target.closest('#brollup');
  if(!inp||!inp.files||!inp.files.length) return;
  var files=[].slice.call(inp.files), done=0;
  // ⚠️ တစ်ခုချင်း ပို့သည် — တစ်ခါတည်း ပို့လျှင် ကြီးလွန်းပြီး timeout ဖြစ်တတ်
  files.forEach(function(f){
    var fd=new FormData(); fd.append('file', f);
    fetch('/api/broll',{method:'POST',headers:{Authorization:'Bearer '+TOKEN},body:fd})
      .then(function(r){ return r.json(); })
      .then(function(){ if(++done===files.length){ inp.value=''; paintBroll(); } })
      .catch(function(){ if(++done===files.length){ inp.value=''; paintBroll(); } });
  });
});
document.addEventListener('click', function(e){
  var b=e.target.closest&&e.target.closest('[data-bdel]');
  if(!b) return;
  api('/broll/'+b.getAttribute('data-bdel'),{method:'DELETE'})
    .then(paintBroll).catch(function(){});
});

// ── ဘရန်း logo တင်ခြင်း ──
document.addEventListener('change', function(e){
  var inp = e.target.closest && e.target.closest('[data-logo]');
  if(!inp || !inp.files || !inp.files[0]) return;
  var bid = inp.getAttribute('data-logo'), f = inp.files[0];
  if(f.size > 4*1024*1024){ alert(cur==='my'?'၄ MB ထက် မကြီးရပါ':'Max 4 MB'); return; }
  var fd = new FormData(); fd.append('file', f);
  var prev = $('lp_'+bid);
  if(prev) prev.style.opacity='0.4';
  fetch('/api/brands/'+bid+'/logo?apply=1',
        {method:'POST', headers:{Authorization:'Bearer '+TOKEN}, body:fd})
   .then(function(r){ return r.json().then(function(d){ if(!r.ok) throw new Error(d.detail||'fail'); return d; }); })
   .then(function(d){
      if(prev){ prev.style.opacity='1';
        prev.style.backgroundImage='url(/api/brands/'+bid+'/logo?t='+
          encodeURIComponent(TOKEN)+'&v='+Date.now()+')'; }
      // ⚠️ ထုတ်လိုက်တဲ့ အရောင်ကို **ပြရမည်** — ဘာဖြစ်သွားလဲ မမြင်ရလျှင်
      //    သုံးစွဲသူက ဗီဒီယို ထွက်လာမှ သိရမည်、နောက်ကျသွားသည်。
      if(d.colors && d.colors.length){
        alert((cur==='my'?'အရောင် ထုတ်ပြီးပါပြီ:\n':'Palette applied:\n')+
              d.colors.join('  ')+'\n\n'+((d.info&&d.info.note)||''));
      }
      loadMeta();
   })
   .catch(function(err){ if(prev) prev.style.opacity='1';
                         alert(String(err.message||err).slice(0,200)); });
});
document.addEventListener('click', function(e){
  var dl = e.target.closest && e.target.closest('[data-logodel]');
  if(!dl) return;
  api('/brands/'+dl.getAttribute('data-logodel')+'/logo',{method:'DELETE'})
   .then(function(){ loadMeta(); }).catch(function(){});
});

// ── ဖောင့် — AI ကို ရွေးခိုင်းခြင်း ──
// ⚠️ AI ပြန်ပေးတဲ့ id ကို server က **စာရင်းနဲ့ တိုက်စစ်ပြီးသား**。 ဒီမှာ
//    ထပ်စစ်တာက UI က မရှိတဲ့ ဖောင့်ကို "ရွေးထား" ပြမိမှာ ကာကွယ်ဖို့。
var fa=$('fontai');
if(fa) fa.onclick=function(){
  var note=(($('fontnote')||{}).value||'').trim();
  fa.disabled=true; var old=fa.textContent;
  fa.textContent = cur==='my' ? 'ရွေးနေပါတယ်…' : 'Picking…';
  api('/fonts/suggest',{method:'POST',headers:{'Content-Type':'application/json'},
      body:JSON.stringify({note:note, style:state.style||'', brand:state.brand||''})})
   .then(function(d){
      fa.disabled=false; fa.textContent=old;
      if(!d.ok){ alert(d.err||'AI မရ'); return; }
      if(!FONTS.some(function(f){return f.id===d.id})){ alert('ဖောင့် မတွေ့: '+d.id); return; }
      state.font=d.id;
      // ⚠️ `loadMeta()` က စာရင်းကို ပြန်ဆွဲသဖြင့် ဒီမှာ ရေးထားတာ ပျောက်သည် —
      //    state ထဲ သိမ်းပြီး စာရင်း ပြန်ဆောက်တိုင်း ပြန်ပြရသည်。
      state.fontwhy = 'AI: ' + (d.why || d.id);
      loadMeta(); paintFontWhy();
   })
   .catch(function(e){ fa.disabled=false; fa.textContent=old;
                       alert(String(e.message||e).slice(0,200)); });
};

// ── ပြီးသွားတဲ့ ဗီဒီယို ဖျက်ခြင်း (done စာမျက်နှာ) ──
var jd=$('jdel');
if(jd) jd.onclick=function(){
  if(!state.jobid) return;
  // ⚠️ `confirm()` မမှီခို — အပေါ်က မှတ်ချက် ကြည့်ပါ。 နှစ်ဆင့် နှိပ်ခိုင်းသည်。
  if(jd.getAttribute('data-arm')!=='1'){
    jd.setAttribute('data-arm','1');
    jd.textContent = (cur==='my' ? 'တကယ် ဖျက်မှာလား? နောက်တစ်ခါ နှိပ်ပါ' : 'Really delete? Click again');
    jd.style.color='#E5484D'; jd.style.borderColor='#E5484D';
    jd.__t=setTimeout(function(){
      jd.removeAttribute('data-arm');
      jd.textContent=(cur==='my'?'ဖျက်မယ်':'Delete');
      jd.style.color=''; jd.style.borderColor='';
    }, 5000);
    return;
  }
  clearTimeout(jd.__t);
  jd.disabled=true; jd.textContent=(cur==='my'?'ဖျက်နေပါတယ်…':'Deleting…');
  api('/jobs/'+state.jobid,{method:'DELETE'})
   .then(function(){ jd.disabled=false; jd.removeAttribute('data-arm');
                     jd.textContent=(cur==='my'?'ဖျက်မယ်':'Delete');
                     jd.style.color=''; jd.style.borderColor='';
                     go('v-lib'); loadJobs(); })
   .catch(function(e){ jd.disabled=false; jd.removeAttribute('data-arm');
                       jd.textContent=(cur==='my'?'ဖျက်မယ်':'Delete');
                       jd.style.color=''; jd.style.borderColor='';
                       alert(String(e.message||e).slice(0,300)); });
};

// ── အောက်ခြေက "ပြင်ချက်နဲ့ ပြန်ထုတ်" — အပေါ်က ခလုပ်ကိုပဲ ခေါ်သည် ──
var rg=$('rrgo');
if(rg) rg.onclick=function(){ var t=$('txre'); if(t) t.click(); };

// ── Telegram ဆက်တင် ──
var ts=$('tgsave');
if(ts) ts.onclick=function(){
  api('/settings',{method:'POST',headers:{'Content-Type':'application/json'},
    body:JSON.stringify({tg_token:($('tgtok').value||'').trim(),
                         tg_chat:($('tgchat').value||'').trim()})})
   .then(function(){ ts.textContent = cur==='my' ? 'သိမ်းပြီး ✓' : 'Saved ✓';
     setTimeout(function(){lang(cur)},1800); }).catch(function(){});
};
$('retry').onclick=function(){scene('s-ready')};
$('q').addEventListener('input',paintJobs);
$('qclear').onclick=function(){$('q').value='';
  [].forEach.call(document.querySelectorAll('.stf'),function(b,i){b.setAttribute('aria-pressed',i===0?'true':'false')});
  paintJobs()};
['dragover','drop'].forEach(function(ev){
  document.addEventListener(ev,function(e){e.preventDefault();
    if(ev==='drop'&&e.dataTransfer.files[0]) start(e.dataTransfer.files[0])});
});

/* ── စတင် ── */
var t=localStorage.getItem('ikki_theme'); if(t) document.documentElement.setAttribute('data-theme',t);
orderProjectFlow(); lang(cur); paintStyles(); loadMeta(); loadJobs(); scene('s-ready');


/* ══ AI အစီအစဉ် — ဖတ်ရုံ ══════════════════════════════════
   ⚠️ Headtop ရဲ့ အခြေခံက 「AI က ဗီဒီယိုကို တိုက်ရိုက် မထုတ်ရ — ဖြစ်ရပ်
      တစ်ခုချင်းကို အကြံပြုပြီး renderer က အကောင်အထည်ဖော်ရမည်」。
      ဖြစ်ရပ်တွေကို **မပြနိုင်လျှင်** သုံးစွဲသူက ဘာဖြစ်သွားလဲ မသိဘဲ
      ကျန်နေမည် ⇒ ဒီအမြင်က အဲဒီကတိရဲ့ ပထမပိုင်းပါ (ပြင်တာက နောက်အဆင့်)。
   ⚠️ **headtop ပုံစံမှသာ** ရှိသည် — ကျန်ပုံစံတွေက worker က ဆုံးဖြတ်နေဆဲမို့
      plan မရှိပါ。 404 ဆိုလျှင် ဘောက်စ်ကို ဖျောက်ထားသည် (အမှား မဟုတ်)。 */
var PLAN_D=null, PLAN_TAB='all';
var PLAYER={caption:['စာတန်း','Captions'], template:['ဂရပ်ဖစ်','Graphics'],
            reframe:['punch-in','Punch-in'], asset:['B-roll','B-roll'],
            sfx:['SFX','SFX'], grade:['အရောင်','Grade']};
var PLKEY={captions:'caption', templateEvents:'template', cameraReframes:'reframe',
           assetEvents:'asset', sfxEvents:'sfx', colorGrades:'grade'};

function planEvents(p){
  var out=[];
  Object.keys(PLKEY).forEach(function(k){
    (p[k]||[]).forEach(function(e){ out.push(Object.assign({_k:PLKEY[k]}, e)) });
  });
  out.sort(function(a,b){ return (a.startTime||0)-(b.startTime||0) });
  return out;
}
function planTxt(e){
  var pr=e.props||{};
  if(Array.isArray(pr.lines)) return pr.lines.join(' / ');
  var t=[pr.before,pr.hot,pr.after].filter(Boolean).join(' ');
  if(t) return t;
  for(var i=0;i<['q','text','head','title','label','role'].length;i++){
    var k=['q','text','head','title','label','role'][i];
    if(typeof pr[k]==='string' && pr[k]) return pr[k];
  }
  if(typeof pr.zoom==='number') return (cur==='my'?'ချဲ့ ':'zoom ')+pr.zoom.toFixed(3)+'×';
  if(Array.isArray(pr.items)) return pr.items.join(' · ');
  return e.style && e.style.kind ? String(e.style.kind) : '';
}
function planPaint(){
  var box=$('planrows'), tb=$('plantabs'); if(!box||!PLAN_D) return;
  var ev=planEvents(PLAN_D), my=(cur==='my');
  var n={}; ev.forEach(function(e){ n[e._k]=(n[e._k]||0)+1 });
  tb.innerHTML='<button class="chip pltab" data-pl="all"'+
      (PLAN_TAB==='all'?' aria-pressed="true"':'')+'>'+(my?'အားလုံး':'All')+
      '<small>'+ev.length+'</small></button>'+
    Object.keys(PLAYER).filter(function(k){return n[k]}).map(function(k){
      return '<button class="chip pltab" data-pl="'+k+'"'+
        (PLAN_TAB===k?' aria-pressed="true"':'')+'>'+
        (my?PLAYER[k][0]:PLAYER[k][1])+'<small>'+n[k]+'</small></button>';
    }).join('');
  var rows=ev.filter(function(e){ return PLAN_TAB==='all'||e._k===PLAN_TAB });
  function mmss(x){ var m=Math.floor(x/60),q=('0'+Math.floor(x%60)).slice(-2);
                    return m+':'+q+'.'+String(Math.round((x%1)*10)); }
  box.innerHTML=rows.map(function(e){
    var c=+e.confidence||0;
    // ⚠️ ယုံကြည်မှု နိမ့်တာကို **မြင်သာစေရမည်** — ဖုံးထားလျှင် ဘယ်ဟာကို
    //    အရင် စစ်ရမလဲ မသိပါ。
    var pill = c>=0.8 ? 'p-ok' : (c>=0.6 ? 'p-ac' : 'p-dim');
    return '<div class="row"><span class="tc mono">'+mmss(+e.startTime||0)+
      '<br><i style="font-style:normal;color:var(--tx3)">'+
        ((+e.endTime||0)-(+e.startTime||0)).toFixed(1)+'s</i></span>'+
      '<div class="lname"><b class="my">'+esc(planTxt(e))+'</b>'+
        '<span class="my">'+esc(e.reason||'')+'</span></div>'+
      // ⚠️ template ID က **ဖြစ်ရပ်ကို ခွဲခြားပေးတဲ့ တစ်ခုတည်းသော အမှတ်** ⇒
      //    ဖြတ်ပစ်လို့ မရပါ (၉၂px ကော်လံမှာ `prem4.big_question` က ၁၁၉px
      //    လိုသည် — ၁၀ ခုထဲ ၆ ခု ပြတ်ခဲ့သည်)。 `.` မှာ ကြောင်းခွဲခွင့် ပေးသည်。
      '<div class="lmeta hidesm mono plid">'+
        esc(e.motionKitTemplateId||e._k).replace('.', '.<wbr>')+'</div>'+
      '<div class="lacts"><span class="pill '+pill+'">'+c.toFixed(2)+'</span></div></div>';
  }).join('') || '<div class="row"><div class="lname"><b>'+
      (my?'ဒီအမျိုးအစားမှာ ဘာမှ မရှိပါ':'Nothing of this kind')+'</b></div></div>';
  var w=(PLAN_D.qualityWarnings||[]);
  $('plann').textContent = (my? ev.length+' ဖြစ်ရပ်' : ev.length+' events')
    + (w.length ? ' · ' + (my? w.length+' သတိပေး' : w.length+' warnings') : '');
}
function planLoad(jid){
  var box=$('planbox'); if(!box) return;
  PLAN_D=null; box.hidden=true;
  api('/jobs/'+jid+'/editplan').then(function(p){
    PLAN_D=p; PLAN_TAB='all'; box.hidden=false; planPaint();
    var a=$('planjson');
    if(a){
      // ⚠️ blob နဲ့ ပေးသည် — endpoint က header token လိုသဖြင့် <a href>
      //    တိုက်ရိုက် ပေးလျှင် 401 ကျမည်。
      try{
        if(a.__u) URL.revokeObjectURL(a.__u);
        a.__u=URL.createObjectURL(new Blob([JSON.stringify(p,null,1)],
                                           {type:'application/json'}));
        a.href=a.__u; a.download=jid+'_plan.json';
      }catch(e){ a.hidden=true; }
    }
  }).catch(function(){ box.hidden=true; });   /* plan မရှိ = headtop မဟုတ် */
}
document.addEventListener('click',function(e){
  var t=e.target.closest&&e.target.closest('.pltab');
  if(!t) return;
  PLAN_TAB=t.getAttribute('data-pl'); planPaint();
});

// ══ render server အခြေအနေ ════════════════════════════════
function checkWorker(){
  api('/health').then(function(h){
    var b=$('wbanner'); if(!b) return;
    if(h.worker){ b.hidden=true; return }
    b.hidden=false;
    b.textContent = cur==='my'
      ? 'Render server ပိတ်နေသည် — အလုပ်ကို စောင့်ဆိုင်းထားပါသည်။ ပြန်တက်သည်နှင့် အလိုအလျောက် လုပ်ပါမည်။'
      : 'Render server is offline — your job is queued and will start automatically.';
  }).catch(function(){});
}


/* ══ ဘရန်း ပြင်ခြင်း ═══════════════════════════════════════
   ⚠️ Create စာမျက်နှာက **ရွေးရုံ**。 ပြင်တာ ဒီမှာ ခွဲထားသည် —
      ရောထားလျှင် ဗီဒီယိုတစ်ခု ထုတ်ရင်း ဘရန်း မှားပြင်မိနိုင်သည်。 */
var COLNAMES=[['နောက်ခံ','Background'],['အကွက်','Panel'],['အဓိက','Accent'],
              ['အရံ','Secondary'],['သတိပေး','Alert']];
var editing=null;
function bopen(b){
  editing = b || {id:'', name:'', aspect:'9:16', colors:['#0B1B33','#16304C','#F5C543','#4FA8DC','#E5484D'],
                  mmf:'Pyidaungsu-Bold', latin:'Figtree-Black', jp:'HiraginoSans-W7'};
  var neu = !editing.id;
  $('bettl').textContent = neu ? (cur==='my'?'ဘရန်း အသစ်':'New brand')
                               : (cur==='my'?'ဘရန်း ပြင်မယ်':'Edit brand');
  $('beid').textContent = editing.id || '';
  $('bename').value = editing.name || '';
  var cols = (editing.colors||[]).slice(0,5);
  while(cols.length<5) cols.push('#888888');
  $('becols').innerHTML = cols.map(function(c,i){
    return '<label><input type="color" value="'+c+'" data-ci="'+i+'" aria-label="'+COLNAMES[i][cur==='my'?0:1]+'">'+
      '<small>'+COLNAMES[i][cur==='my'?0:1]+'</small></label>';
  }).join('');
  var mm = FONTS.length ? FONTS : [{id:editing.mmf,name:editing.mmf}];
  $('bemmf').innerHTML = mm.map(function(f){
    return '<option value="'+f.id+'"'+(f.id===editing.mmf?' selected':'')+'>'+f.name+'</option>' }).join('');
  // Latin ဖောင့် — render မှာ တကယ် ရှိတာပဲ ပြရမည်
  $('belatin').innerHTML = ['Figtree-Black','Figtree-Bold','Outfit-Black','Outfit-Bold'].map(function(f){
    return '<option value="'+f+'"'+(f===editing.latin?' selected':'')+'>'+f+'</option>' }).join('');
  $('beaspect').innerHTML = (FMTS.length?FMTS:[{key:'9:16',w:1080,h:1920,label:''}]).map(function(f){
    return '<option value="'+f.key+'"'+(f.key===editing.aspect?' selected':'')+'>'+
      f.key+' · '+f.w+'×'+f.h+'</option>' }).join('');
  // ⚠️ house brand ၂ ခုကို မဖျက်ရ — recipe တွေက ရည်ညွှန်းသည်
  $('bedel').hidden = neu || editing.id==='zae' || editing.id==='zjl';
  $('bedit').hidden = false;
  $('bedit').scrollIntoView({behavior:'smooth', block:'center'});
}
function bclose(){ $('bedit').hidden=true; editing=null }
var bn=$('bnew'); if(bn) bn.onclick=function(){ bopen(null) };
var bc=$('becancel'); if(bc) bc.onclick=bclose;
var bs=$('besave'); if(bs) bs.onclick=function(){
  if(!editing) return;
  var name=$('bename').value.trim();
  if(!name){ $('bename').focus(); return }
  var cols=[].map.call(document.querySelectorAll('#becols input[type=color]'),function(i){return i.value});
  var body={name:name, colors:cols, mmf:$('bemmf').value, latin:$('belatin').value,
            jp:editing.jp||'HiraginoSans-W7', aspect:$('beaspect').value};
  if(editing.id) body.id=editing.id;
  bs.disabled=true;
  api('/brands',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)})
    .then(function(){ bs.disabled=false; bclose(); loadMeta() })
    .catch(function(){ bs.disabled=false });
};
var bd=$('bedel'); if(bd) bd.onclick=function(){
  if(!editing||!editing.id) return;
  // ⚠️ `confirm()` မမှီခို (တိတ်တဆိတ် false ပြန်သည်) — နှစ်ဆင့် နှိပ်ခိုင်းသည်
  if(!confirmTwo(bd, cur==='my'?'တကယ် ဖျက်မှာလား? နောက်တစ်ခါ နှိပ်ပါ':'Delete? Click again')) return;
  api('/brands/'+editing.id,{method:'DELETE'}).then(function(){
    if(state.brand===editing.id) state.brand='zae';
    bclose(); loadMeta();
  }).catch(function(){});
};
document.addEventListener('click',function(e){
  var ed=e.target.closest&&e.target.closest('[data-edit]');
  if(ed){ var id=ed.getAttribute('data-edit');
    var b=BRANDS.filter(function(x){return x.id===id})[0];
    if(b) bopen(b); }
});

/* ══ ပုံစံ ပြင်ခြင်း ══════════════════════════════════════
   ⚠️ ပုံစံတိုင်းရဲ့ ကိန်းတွေက reference ဗီဒီယိုမှ တိုင်းယူထားတာ。
      ⇒ field တိုင်းမှာ **ပုံသေကို ပြရမည်**၊ ပြင်ထားတာကို ခြယ်ရမည်。
   ⚠️ ဘောင်စစ်မှုက server မှာလည်း ရှိသည် (recipes.clean) — UI ကို မယုံရ。 */
var SMETA=null, sediting=null, sover={};
function loadStyles(){
  return api('/styles').then(function(d){
    SMETA=d; sover=d.over||{};
    var el=$('stylist'); if(!el) return;
    el.innerHTML=d.styles.map(function(st){
      var o=sover[st.id]||{}, n=Object.keys(o).length;
      return '<div class="lrow"><div class="thumb im'+((st.id.charCodeAt(0)%5)+1)+'"></div>'+
        '<div class="lname"><b>'+st.label+'</b><span class="my">'+
          (cur==='my'?'ဖြတ်မှု ':'cut ')+scutLabel(o.cut||st.cut)+
          ' · gfx '+(o.gfx!==undefined?o.gfx:st.gfx)+
          ' · B-roll '+(o.broll!==undefined?o.broll:st.broll)+'</span></div>'+
        '<div class="lmeta hidesm">'+st.theme+'</div>'+
        '<div class="ldur hidesm mono">'+(o.fps||st.fps)+'fps</div><div class="wave hidesm"></div>'+
        '<div class="lacts">'+
          (n?'<span class="pill p-chg">'+(cur==='my'?'ပြင်ထား '+n:n+' changed')+'</span>':'')+
          '<button class="btn" data-sedit="'+st.id+'">'+(cur==='my'?'ပြင်မယ်':'Edit')+'</button>'+
        '</div></div>';
    }).join('');
  }).catch(function(){});
}
function scutLabel(k){
  if(!SMETA) return k;
  var f=SMETA.cuts.filter(function(c){return c.id===k})[0];
  return f?(cur==='my'?f.my:f.en):k;
}
function sopen(id){
  if(!SMETA) return;
  var st=SMETA.styles.filter(function(x){return x.id===id})[0]; if(!st) return;
  sediting=st;
  var o=sover[id]||{};
  $('settl').textContent=st.label;
  $('seid').textContent=id;
  function row(key,label,hint,ctrl,dflt){
    var chg=(o[key]!==undefined);
    return '<div class="sef"><div class="k"><b'+(chg?' class="chg"':'')+'>'+label+'</b>'+
      (hint?'<span>'+hint+'</span>':'')+'</div><div class="v">'+ctrl+
      '<span class="dflt" title="'+(cur==='my'?'တိုင်းထားသော ပုံသေ':'measured default')+'">'+dflt+'</span></div></div>';
  }
  function sel(key,opts,val){
    return '<select class="sel" style="min-width:172px" data-sk="'+key+'">'+
      opts.map(function(o2){ return '<option value="'+o2[0]+'"'+(String(o2[0])===String(val)?' selected':'')+'>'+o2[1]+'</option>' }).join('')+'</select>';
  }
  function rng(key,min,max,step,val,fmt){
    return '<input type="range" data-sk="'+key+'" min="'+min+'" max="'+max+'" step="'+step+'" value="'+val+'">'+
      '<span class="num" data-num="'+key+'">'+fmt(val)+'</span>';
  }
  var pc=function(v){return (v*100).toFixed(1)+'%'};
  var cutOpts=SMETA.cuts.map(function(c){return [c.id, cur==='my'?c.my:c.en]});
  if(st.cut==='custom') cutOpts=[['custom',cur==='my'?'တိုင်းထားတာ':'As measured']].concat(cutOpts);
  var h='';
  // ⚠️ ဖောင့်ကို **အပေါ်ဆုံး** ထားသည် — ပုံစံတစ်ခုချင်းရဲ့ အထင်ရှားဆုံး
  //    ကွာဟမှုက ဖောင့် ဖြစ်သည်。 Zin က ပုံစံတိုင်း ဖောင့် သီးသန့် လိုသည်。
  h+=row('mmf', cur==='my'?'မြန်မာ ဖောင့်':'Burmese type',
      cur==='my'?'ဒီပုံစံအတွက်သာ — တခြားပုံစံကို မထိဘူး':'For this style only — others untouched',
      sel('mmf',(FONTS.length?FONTS:[{id:st.mmf,name:st.mmf}]).map(function(f){return [f.id,f.name]}),
          o.mmf||st.mmf), st.mmf);
  /* ⚠️ ပေါင်းထားသော ပုံစံ ၂ ခုရဲ့ ပြင်းအား — ဒါမရှိလျှင် ပေါင်းလိုက်တာက
        ပုံစံ ၂ ခု **ပျောက်သွား**ရုံပဲ ဖြစ်မည်。 */
  if(st.slide_amt)
    h+=row('slide_amt', cur==='my'?'ကတ် ပမာဏ':'Slide amount',
      cur==='my'?'ထူထူ = ဘောင်အပြည့် ကတ် အဓိက (အရင် Slide Heavy)':'Heavy = full-frame slide led',
      sel('slide_amt',[['light',cur==='my'?'ပါးပါး':'Light'],
                       ['heavy',cur==='my'?'ထူထူ':'Heavy']], o.slide_amt||st.slide_amt), st.slide_amt);
  if(st.pace)
    h+=row('pace', cur==='my'?'အရှိန်':'Pace',
      cur==='my'?'မြန် = ဖြတ်ချက် ပိုများ (အရင် Fast Cut) — စကားထဲ မဖြတ်ပါ':'Fast = more cuts (was Fast Cut) — never inside speech',
      sel('pace',[['normal',cur==='my'?'ပုံမှန်':'Normal'],
                  ['fast',cur==='my'?'မြန်':'Fast']], o.pace||st.pace), st.pace);
  h+=row('latin', cur==='my'?'Latin ဖောင့်':'Latin type','',
      sel('latin',(SMETA.latin||[st.latin]).map(function(f){return [f,f]}), o.latin||st.latin), st.latin);
  h+=row('cut', cur==='my'?'ဖြတ်မှု':'Cutting',
      cur==='my'?'တိတ်ဆိတ်မှုထဲမှာပဲ ဖြတ်တယ် — စကားထဲ ဘယ်တော့မှ မဖြတ်ဘူး':'Cuts only inside measured silence',
      sel('cut',cutOpts,o.cut||st.cut), scutLabel(st.cut));
  h+=row('fps','FPS', cur==='my'?'24 = ရုပ်ရှင်ဆန် · 30 = ချောမွေ့':'24 = filmic · 30 = smooth',
      sel('fps',[[24,'24'],[30,'30']],o.fps||st.fps), st.fps);
  h+=row('captions', cur==='my'?'စာတန်း ပုံစံ':'Caption style','',
      sel('captions',SMETA.captions.map(function(c){return [c,c]}),o.captions||st.captions), st.captions);
  if(st.cap_pct!==null&&st.cap_pct!==undefined)
    h+=row('cap_pct', cur==='my'?'စာတန်း အရွယ်':'Caption size',
      cur==='my'?'ဘောင် အမြင့်၏ %':'% of frame height',
      rng('cap_pct',0.035,0.110,0.005,(o.cap_pct!==undefined?o.cap_pct:st.cap_pct),pc), pc(st.cap_pct));
  if(st.cap_base!==null&&st.cap_base!==undefined)
    h+=row('cap_base', cur==='my'?'စာတန်း အနေရာ':'Caption position',
      cur==='my'?'အပေါ်မှ % — ကြီးလျှင် အောက်ဆုံးသို့':'% from top — higher sits lower',
      rng('cap_base',0.550,0.870,0.005,(o.cap_base!==undefined?o.cap_base:st.cap_base),pc), pc(st.cap_base));
  h+=row('stroke', cur==='my'?'စာတန်း အနားသတ်':'Caption stroke',
      cur==='my'?'အဖြူနံရံရော အမှောင် B-roll ရော ဖတ်လို့ရစေရန်':'Keeps text readable on light and dark',
      '<input type="checkbox" data-sk="stroke_on"'+(((o.stroke!==undefined?o.stroke:st.stroke))?' checked':'')+'>'+
      '<input type="color" data-sk="stroke" value="'+((o.stroke!==undefined?o.stroke:st.stroke)||'#1E3B5A')+'" style="width:40px;height:30px;border-radius:8px;border:1px solid var(--ln);background:none">',
      st.stroke||'—');
  h+=row('gfx', cur==='my'?'ဂရပ်ဖစ်':'Graphics',
      cur==='my'?'အများဆုံး — စကားနဲ့ ကိုက်တဲ့အခါပဲ တင်တယ်':'Max — only placed where the speech matches',
      rng('gfx',0,30,1,(o.gfx!==undefined?o.gfx:st.gfx),String), st.gfx);
  h+=row('broll','B-roll',
      cur==='my'?'အများဆုံး — စာကြည့်တိုက်နဲ့ ကိုက်တဲ့အခါပဲ':'Max — only where the library matches',
      rng('broll',0,10,1,(o.broll!==undefined?o.broll:st.broll),String), st.broll);
  h+=row('music', cur==='my'?'သီချင်း':'Music','',
      sel('music',SMETA.music.map(function(m){return [m===null?'none':m, m===null?(cur==='my'?'မပါ':'None'):m]}),
          (o.music!==undefined?(o.music===null?'none':o.music):(st.music===null?'none':st.music))),
      st.music||'—');
  h+=row('lufs', cur==='my'?'အသံအဆင့်':'Loudness','',
      sel('lufs',SMETA.lufs.map(function(l){return [l.v, cur==='my'?l.my:l.en]}),
          (o.lufs!==undefined?o.lufs:st.lufs)), st.lufs);
  /* ══ Headtop — plan လမ်းကြောင်းရဲ့ ထိန်းချုပ်ချက်များ ═══════════
     ⚠️ ဒါတွေက `recipes.BOUNDS` မှာ **စစ်ပြီးသား** ဖြစ်ပါလျက် UI မှာ
        မပါခဲ့သဖြင့် သုံးစွဲသူ ပြင်လို့ မရခဲ့ပါ (၂၀၂၆-၀၉-၂၁ စစ်၍ တွေ့)。
     ⚠️ ရွေးစရာ စာရင်းကို **server ကပေးတဲ့ `choices` ကနေသာ** ယူသည် —
        ဒီမှာ ပြန်ရေးလျှင် recipes နဲ့ ကွဲသွားမည်。
     ⚠️ `plan` ပုံစံမှသာ ပြသည် — ကျန်ပုံစံတွေမှာ worker က ဆုံးဖြတ်နေဆဲမို့
        ဒီခလုတ်တွေက ဘာမှ မလုပ်ပါ。 မသက်ရောက်တာကို ပြထားလျှင် လိမ်ရာ ကျသည်。 */
  var CH=(SMETA&&SMETA.choices)||{};
  function chrow(key,label,hint,names){
    var opts=(CH[key]||[]).map(function(v){
      return [v, (names&&names[v]) ? (cur==='my'?names[v][0]:names[v][1]) : String(v)] });
    if(!opts.length) return '';
    return row(key,label,hint,sel(key,opts,(o[key]!==undefined?o[key]:st[key])),
               st[key]==null?'—':String(st[key]));
  }
  function ckrow(key,label,hint){
    var v=(o[key]!==undefined?o[key]:st[key]);
    return row(key,label,hint,
      '<input type="checkbox" data-sk="'+key+'"'+(v?' checked':'')+'>',
      st[key]?'on':'off');
  }
  if(st.plan){
    h+='<div class="sef sef-h"><b>'+(cur==='my'?'Headtop · AI အစီအစဉ်':'Headtop · AI plan')+'</b></div>';
    h+=chrow('energy', cur==='my'?'စွမ်းအင်':'Energy',
        cur==='my'?'ဂရပ်ဖစ် ဘယ်လောက် မကြာခဏ ပြမလဲ':'How often a visual change lands',
        {minimal:['နည်းနည်း','Minimal'],standard:['ပုံမှန်','Standard'],dynamic:['များများ','Dynamic']});
    h+=chrow('motion', cur==='my'?'ရုပ် လှုပ်ရှားမှု':'Motion intensity',
        cur==='my'?'punch-in · ရွေ့လျားမှု ပြင်းအား':'punch-in and movement strength',
        {low:['နည်း','Low'],normal:['ပုံမှန်','Normal'],high:['ပြင်း','High']});
    h+=chrow('broll_freq', cur==='my'?'B-roll မကြာခဏ':'B-roll frequency',
        cur==='my'?'စာကြည့်တိုက်နဲ့ ကိုက်တဲ့အခါပဲ':'only where the library matches',
        {low:['နည်း','Low'],normal:['ပုံမှန်','Normal'],high:['များ','High']});
    h+=row('zoom_amt', cur==='my'?'punch-in ပမာဏ':'Punch-in amount',
        cur==='my'?'၁.၀၈ ဆ ထက် မကျော်ရ — မျက်နှာ မပျက်စေရန်':'never beyond 1.08× so the face holds',
        rng('zoom_amt',0,0.12,0.005,(o.zoom_amt!==undefined?o.zoom_amt:(st.zoom_amt||0)),
            function(v){return (1+parseFloat(v)).toFixed(3)+'×'}),
        (1+(st.zoom_amt||0)).toFixed(3)+'×');
    h+=ckrow('sfx_on', cur==='my'?'SFX အသံ':'Sound effects',
        cur==='my'?'ကိုယ်ပိုင် ကစ်ထဲကသာ — စကားအောက်မှာ':'from your own kit only, under the voice');
    h+=ckrow('autocut', cur==='my'?'အလိုအလျောက် ဖြတ်':'Auto jump-cut',
        cur==='my'?'တိတ်ဆိတ်မှု အထဲမှာပဲ — စကားထဲ ဘယ်တော့မှ မဖြတ်':'inside silence only, never in speech');
    h+=row('silence_ms', cur==='my'?'တိတ်ဆိတ်မှု ဖြတ်မှတ်':'Silence threshold',
        cur==='my'?'ဒီထက် ရှည်မှ ဖြတ်သည်':'cuts only gaps longer than this',
        rng('silence_ms',150,1200,10,(o.silence_ms!==undefined?o.silence_ms:(st.silence_ms||400)),
            function(v){return Math.round(v)+'ms'}),
        (st.silence_ms||400)+'ms');
    h+=ckrow('shot_grade', cur==='my'?'အပိုင်းလိုက် အရောင်':'Per-shot grade',
        cur==='my'?'အပြင်/အတွင်း ခွဲပြီး သီးသန့် ချိန်သည်':'treats outdoor and indoor separately');
    /* ⚠️ `review` ကို **ဒီမှာ မပြရ** — အဲဒါက job တစ်ခုချင်းရဲ့ `mode`
       (API က ဆုံးဖြတ်သည်) ဖြစ်ပြီး ပုံစံရဲ့ ပုံသေ မဟုတ်ပါ。 ဒီမှာ ထားလျှင်
       အမှန်တရား နှစ်နေရာ ဖြစ်ပြီး ဘယ်ဟာ အနိုင်ရလဲ မသိတော့ပါ (၂၀၂၆-၀၉-၂၁)。 */
    h+='<div class="sef sef-h"><b>'+(cur==='my'?'ကျန် ဆက်တင်':'Other settings')+'</b></div>';
  }
  h+=row('scrim', cur==='my'?'Scrim (အမှောင် အလွှာ)':'Scrim (dark layer)',
      cur==='my'?'စာတန်း/ဂရပ်ဖစ် ပေါ်ချိန်မှာသာ ဖတ်လို့ရစေတယ်':'Appears only behind captions and graphics',
      '<input type="checkbox" data-sk="scrim"'+(((o.scrim!==undefined?o.scrim:st.scrim))?' checked':'')+'>',
      st.scrim?'on':'off');
  $('sefields').innerHTML=h;
  $('sereset').hidden = !Object.keys(o).length;
  $('sedit').hidden=false;
  $('sedit').scrollIntoView({behavior:'smooth',block:'center'});
}
function sclose(){ $('sedit').hidden=true; sediting=null }
var sc2=$('secancel'); if(sc2) sc2.onclick=sclose;
var ss2=$('sesave'); if(ss2) ss2.onclick=function(){
  if(!sediting) return;
  var st=sediting, o={};
  [].forEach.call(document.querySelectorAll('#sefields [data-sk]'),function(i){
    var k=i.getAttribute('data-sk');
    if(k==='stroke_on'||k==='stroke') return;
    var v = i.type==='checkbox' ? i.checked
          : (i.type==='range' ? parseFloat(i.value) : i.value);
    if(k==='fps') v=parseInt(v,10);
    if(k==='lufs') v=parseFloat(v);
    if(k==='gfx'||k==='broll'||k==='silence_ms') v=parseInt(v,10);
    if(k==='music'&&v==='none') v=null;
    o[k]=v;
  });
  // ⚠️ stroke က checkbox + အရောင် နှစ်ခု တွဲ — ပိတ်ထားလျှင် null
  var on=document.querySelector('#sefields [data-sk="stroke_on"]');
  var cl=document.querySelector('#sefields [data-sk="stroke"]');
  if(on) o.stroke = on.checked ? (cl?cl.value:'#1E3B5A') : null;
  if(o.cut==='custom') delete o.cut;
  // ပုံသေနဲ့ တူတာကို မသိမ်းဘူး — ပုံသေ ပြောင်းလျှင် လိုက်ပြောင်းစေရန်
  var keep={};
  Object.keys(o).forEach(function(k){
    var dv = st[k];
    if(k==='cut') dv=st.cut;
    if(String(o[k])!==String(dv)) keep[k]=o[k];
  });
  ss2.disabled=true;
  api('/styles/'+st.id,{method:'POST',headers:{'Content-Type':'application/json'},
      body:JSON.stringify({over:keep})})
    .then(function(){ ss2.disabled=false; sclose(); loadStyles() })
    .catch(function(){ ss2.disabled=false });
};
var sr=$('sereset'); if(sr) sr.onclick=function(){
  if(!sediting) return;
  api('/styles/'+sediting.id,{method:'DELETE'}).then(function(){ sclose(); loadStyles() }).catch(function(){});
};
document.addEventListener('input',function(e){
  var i=e.target.closest&&e.target.closest('#sefields input[type=range]');
  if(!i) return;
  var k=i.getAttribute('data-sk'), n=document.querySelector('[data-num="'+k+'"]');
  // ⚠️ slider တိုင်းရဲ့ ပြပုံ **သီးသန့်** — ကိန်းအကြမ်း ပြလျှင် ၀.၀၄၅ ဆိုတာ
  //    ဘာကို ဆိုလိုမှန်း မသိပါ (punch က ၁.၀၄၅× · တိတ်ဆိတ်မှုက ၄၀၀ms)。
  if(!n) return;
  if(k==='cap_pct'||k==='cap_base') n.textContent=(parseFloat(i.value)*100).toFixed(1)+'%';
  else if(k==='zoom_amt')           n.textContent=(1+parseFloat(i.value)).toFixed(3)+'×';
  else if(k==='silence_ms')         n.textContent=Math.round(i.value)+'ms';
  else                              n.textContent=i.value;
});
document.addEventListener('click',function(e){
  var se=e.target.closest&&e.target.closest('[data-sedit]');
  if(se) sopen(se.getAttribute('data-sedit'));
});

})();

/* ── နောက် ဗီဒီယို — `#new` နဲ့ ရောက်လာလျှင် တန်း ဖိုင် ရွေးခိုင်းသည် ──
   ⚠️ browser က user နှိပ်မှသာ file picker ဖွင့်ခွင့်ပေး၍ **တန်း မဖွင့်နိုင်**、
      ⇒ upload ကွက်ကို ချုံ့ပြပြီး အလင်းပေးသည် (သတိထားမိစေရန်)。 */
(function(){
  function go(){
    if(location.hash!=='#new') return;
    var b=document.querySelector('[data-go="v-new"]'); if(b) b.click();
    var d=document.getElementById('drop');
    if(d){ d.scrollIntoView({behavior:'smooth',block:'center'});
      d.style.transition='box-shadow .3s'; d.style.boxShadow='0 0 0 4px var(--ac)';
      setTimeout(function(){ d.style.boxShadow='' },1800); }
    history.replaceState(null,'',location.pathname);
  }
  if(document.readyState==='loading') document.addEventListener('DOMContentLoaded',go);
  else go();
})();
