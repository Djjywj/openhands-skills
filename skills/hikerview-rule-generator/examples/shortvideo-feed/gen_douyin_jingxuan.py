# -*- coding: utf-8 -*-
"""生成抖音精选规则 v8
- 首页：单列表，默认 5 分钟以上、高赞、跳过带货/短剧/AI 生成（risk_infos 声明）
- 搜索：① 官方搜索接口（需海阔内登录抖音，自动读 cookie）② 精选池并发多页 + 搜索建议词匹配 ③ 提示卡
"""
import json, os, shutil

APP_UA = "com.ss.android.ugc.aweme/300000 (Linux; U; Android 13; zh_CN; Pixel; Build/TQ3A; )"

BASE = (
    "https://api-play-zjg.amemv.com/aweme/v1/feed/?device_platform=android&version_code=100000"
    "&channel=wandoujia&os_version=13&device_type=Pixel&device_id=7000000000000000000"
    "&iid=7000000000000000000&openudid=0000000000000000&aid=1128&count=20&feed_style=1"
    "&min_sec=300&_=1"
)

# 官方搜索接口：offset 用 fypage 占位（第1页 0、第2页 10…），keyword 由 ** 代入
SEARCH = (
    "https://api-play-zjg.amemv.com/aweme/v1/general/search/single/?device_platform=android"
    "&version_code=300000&version_name=30.0.0&os_version=13&os_api=33&device_type=Pixel"
    "&device_id=7000000000000000000&iid=7000000000000000000&openudid=0000000000000000"
    "&aid=1128&channel=wandoujia&count=10&offset=fypage@-1@*10@&keyword=**"
    "&search_channel=aweme_general&search_source=normal_search&query_correct_type=1"
    "&is_filter_search=0&hot_search=0&sort_type=0&publish_time=0&filter_duration=3&ts=1700000000"
)

TITLE = "抖音精选v8"

HEAD = r"""var APPUA='com.ss.android.ugc.aweme/300000 (Linux; U; Android 13; zh_CN; Pixel; Build/TQ3A; )';
var HDR={'User-Agent':APPUA,'Referer':'https://www.douyin.com/'};
var TITLE='__TITLE__';
var MIN_SEC=300;
var MIN_DIGG=3000;
var TARGET=12;
var MAX_PAGES=12;
var SPAGES=4;
var BLACK=['带货','橱窗','同款','秒杀','下单','购买','抢购','领券','优惠','包邮','小黄车','团购','旗舰店','直播预告','短剧','剧场','全集','逆袭','重生','穿越','赘婿','豪门','萌宝','隐忍','翻盘','复仇','娇妻','弃女','神医','战神','推文','爽文','剧情','演绎','摆拍','搬运','小说','总裁','婆媳','彩礼','营销号','#ai','ai生成','ai创作','ai制作','ai绘画','ai动画','ai视频','ai短片','ai电影','ai演员','ai写真','ai换脸','ai复活','ai配音','ai建模','ai数字人','aigc','即梦','可灵','sora','runway','ai浪潮','ai创作浪潮','用ai打开','ai新春','抖音ai','ai练习生','猫箱','oii'];
var BASE='__BASE__';
var SAPI='__SAPI__';
var SUGURL='https://aweme.snssdk.com/aweme/v1/search/sug/?keyword=__KW__&count=10&aid=1128&device_platform=android';

var _pv=0;
try{ _pv=parseInt(getParam('min_sec'),10); }catch(e0){}
if(!(_pv>0)){ try{ var _m=String(MY_URL).match(/[?&]min_sec=(\d+)/); if(_m){ _pv=parseInt(_m[1],10); } }catch(e1){} }
if(_pv>0){ MIN_SEC=_pv; }

function _feed(p){ return BASE+'&refresh_index='+p; }
function _surl(off){
  return SAPI.replace('fypage@-1@*10@', String(off));
}
function _hdrs(ck){
  var h={};
  for(var k in HDR){ if(HDR.hasOwnProperty(k)){ h[k]=HDR[k]; } }
  if(ck){ h['Cookie']=ck; }
  return h;
}
function _get(u,ck){
  var t='';
  if(!u){ return ''; }
  try{ t=fetch(u,{headers:_hdrs(ck)}); }catch(e){ t=''; }
  if(typeof t!=='string'){ t=(t&&t.body)?String(t.body):''; }
  return t||'';
}
function _many(list,ck){
  var res=[];
  if(typeof batchFetch==='function' && list && list.length){
    try{
      var reqs=[];
      for(var i=0;i<list.length;i++){ reqs.push({url:list[i], options:{headers:_hdrs(ck), timeout:15000}}); }
      var rs=batchFetch(reqs), arr=rs;
      if(typeof rs==='string'){
        arr=null;
        try{ var jj=JSON.parse(rs); if(jj && jj.length!==undefined){ arr=jj; } }catch(e){ arr=null; }
      }
      if(arr && arr.length!==undefined && arr.length>0){
        for(var k=0;k<arr.length;k++){
          var t=arr[k];
          if(typeof t!=='string'){ t=(t&&t.body)?String(t.body):''; }
          res.push(t||'');
        }
        return res;
      }
    }catch(e1){ res=[]; }
  }
  for(var q=0;q<list.length;q++){ res.push(_get(list[q],ck)); }
  return res;
}
function _ckStr(){
  var out='';
  try{ if(typeof getCookie==='function'){ out=String(getCookie('https://www.douyin.com')||''); } }catch(e){ out=''; }
  if(out.indexOf('sessionid')<0){
    try{
      if(typeof fetchCookie==='function'){ var t=String(fetchCookie('https://www.douyin.com')||''); if(t.indexOf('sessionid')>=0){ out=t; } }
    }catch(e2){}
  }
  if(out.indexOf('sessionid')<0){
    try{
      if(typeof getCookie==='function'){ var t2=String(getCookie('https://api-play-zjg.amemv.com')||''); if(t2.indexOf('sessionid')>=0){ out=t2; } }
    }catch(e3){}
  }
  if(out && out.charAt(0)==='['){
    var arr=null;
    try{ arr=JSON.parse(out); }catch(e4){ arr=null; }
    if(arr && arr.length!==undefined){
      var s=[];
      for(var i=0;i<arr.length;i++){ var o=arr[i]||{}; if(o.name){ s.push(o.name+'='+(o.value||'')); } }
      out=s.join('; ');
    }
  }
  return out;
}
function _sug(kw){
  var list=[];
  if(!kw){ return list; }
  var u=SUGURL.replace('__KW__', encodeURIComponent(kw));
  var t=_get(u,''), j=null;
  try{ j=JSON.parse(t); }catch(e){ j=null; }
  var L=(j&&j.sug_list)||[];
  for(var i=0;i<L.length;i++){
    var w=String((L[i]||{}).content||'').replace(/^\s+|\s+$/g,'');
    if(w){ list.push(w); }
    if(list.length>=8){ break; }
  }
  return list;
}
function _jpg(o){
  if(!o){ return ''; }
  var L=o.url_list||[];
  for(var i=0;i<L.length;i++){ if(/\.jpe?g/i.test(L[i])){ return L[i]; } }
  return L[0]||'';
}
function _num(n){ n=Number(n)||0; if(n>=10000){ return (n/10000).toFixed(1)+'万'; } return String(n); }
function _sec(n){ n=Math.round((Number(n)||0)/1000); return n; }
function _uri(v){
  var pa=(v||{}).play_addr||{};
  if(pa.uri){ return 'https://api-play.amemv.com/aweme/v1/play/?video_id='+pa.uri+'&ratio=1080p&line=0'; }
  var ul=pa.url_list||[];
  if(ul.length&&ul[0]){ return ul[0]; }
  var dl=((v||{}).download_addr||{}).url_list||[];
  if(dl.length&&dl[0]){ return dl[0]; }
  return '';
}
function _bad(s){
  s=String(s).toLowerCase();
  for(var i=0;i<BLACK.length;i++){ if(s.indexOf(BLACK[i])>=0){ return true; } }
  return false;
}
function _aiDecl(a){
  var ri=(a||{}).risk_infos, txt='';
  if(!ri){ return false; }
  if(typeof ri==='string'){ txt=ri; }
  else if(typeof ri.content==='string'){ txt=ri.content; }
  else if(ri.length!==undefined){ for(var i=0;i<ri.length;i++){ txt=txt+' '+String((ri[i]||{}).content||''); } }
  txt=String(txt).toLowerCase();
  if(txt.indexOf('ai 生成')>=0||txt.indexOf('ai生成')>=0||txt.indexOf('aigc')>=0
     || txt.indexOf('人工智能生成')>=0||txt.indexOf('ai创作')>=0||txt.indexOf('ai 创作')>=0){ return true; }
  var gi=(a||{}).aigc_info;
  if(gi && (gi.aigc_sticker_id||gi.aigc_type===-1)){ return true; }
  return false;
}
function _take(a,cands,seen,out,minDigg){
  if(!a || !a.aweme_id || seen[a.aweme_id]){ return 0; }
  seen[a.aweme_id]=1;
  var v=a.video||{};
  var sec=_sec(v.duration), digg=Number((a.statistics||{}).digg_count)||0;
  if(sec<MIN_SEC){ return 0; }
  if(digg<(minDigg>0?minDigg:MIN_DIGG)){ return 0; }
  var u=_uri(v);
  if(!u){ return 0; }
  var desc=String(a.desc||'').replace(/\s+/g,' ').replace(/^\s+|\s+$/g,''), nick=String((a.author||{}).nickname||'');
  if(_bad(desc+' '+nick)){ return 0; }
  if(_aiDecl(a)){ out.ai=(out.ai||0)+1; return 0; }
  cands.push({u:u,sec:sec,digg:digg,desc:desc,nick:nick,
              img:_jpg(v.cover)||_jpg(v.origin_cover)||_jpg(v.dynamic_cover),id:String(a.aweme_id)});
  return 1;
}
function _scanRaw(raw,cands,seen,out,minDigg){
  if(!raw){ return 0; }
  var j=null;
  try{ j=JSON.parse(raw); }catch(e){ return 0; }
  if(j && j.status_code!==undefined && out.code==='-'){ out.code=String(j.status_code); }
  if(j && j.status_code===2483){ out.login=1; out.err='抖音要求登录后才能搜索'; return 0; }
  if(j && !j.aweme_list && !j.data && (j.status_code===2154||j.status_code===8||j.status_code===10001)){
    out.err='被抖音风控拦截（status_code='+String(j.status_code)+'）'; return 0;
  }
  var stack=[j], n=0, guard=0;
  while(stack.length && guard<9000){
    guard++;
    var o=stack.pop();
    if(!o || typeof o!=='object'){ continue; }
    if(o.length!==undefined){
      for(var i=0;i<o.length;i++){ var it=o[i]; if(it && typeof it==='object'){ stack.push(it); } }
      continue;
    }
    if(o.aweme_id && o.video){ n+=_take(o,cands,seen,out,minDigg); continue; }
    for(var k in o){ if(!o.hasOwnProperty(k)){ continue; } var vv=o[k]; if(vv && typeof vv==='object'){ stack.push(vv); } }
  }
  return n;
}
function _item(c){
  var t=c.desc;
  if(t.length>34){ t=t.substring(0,34)+'…'; }
  if(!t){ t='抖音精选 '+c.id; }
  var d='';
  if(c.digg){ d='❤'+_num(c.digg); }
  if(c.sec>0){ var s=c.sec, dd=(s>=60)?(Math.floor(s/60)+'分'+(s%60)+'秒'):(s+'秒'); d=d+(d?' · ':'')+dd; }
  if(c.nick){ d=d+(d?' · ':'')+'@'+c.nick; }
  var img=c.img?c.img+'@Referer=https://www.douyin.com':'';
  return {title:t,desc:d,img:img,url:c.u+'#isVideo=true#',col_type:'movie_1_vertical_pic'};
}
function _href(kw){ return 'hiker://search?s='+encodeURIComponent(kw)+'&rule='+TITLE; }
function _webItem(kw){
  return {title:'🔎 在抖音网页里搜「'+kw+'」（官方结果，最全）',
          desc:'点开就是抖音搜索页，可直接看、也可长按嗅探播放',
          url:'web://https://www.douyin.com/search/'+encodeURIComponent(kw),col_type:'text_3'};
}
function _loginItem(){
  return {title:'🔑 登录抖音后就能用真·搜索（点这里打开登录页）',
          desc:'在网页里登录一次（手机号验证码），回来重新搜索即可',
          url:'web://https://www.douyin.com/',col_type:'text_3'};
}
function _loginTopItem(){
  return {title:'🔑 想用「真·搜索」？点这里登录抖音（登录一次，这张卡片会自动消失）',
          desc:'在打开的网页里用手机号验证码登录，回来后规则就能用抖音官方搜索',
          url:'web://https://www.douyin.com/',col_type:'text_3'};
}
function _againItem(kw){
  return {title:'🔄 登录好了？点这里重新搜「'+kw+'」',url:_href(kw),col_type:'text_3'};
}
function _sugItems(kw){
  var d=[], s=_sug(kw);
  for(var i=0;i<s.length && i<4;i++){
    if(s[i] && s[i]!==kw){ d.push({title:'🔍 建议搜索：'+s[i],url:_href(s[i]),col_type:'text_3'}); }
  }
  return d;
}
function _byLike(x,y){ return (y.digg||0)-(x.digg||0); }
function _char(msg,len){
  return [
    {title:'⚠️ 抖音没返回数据：'+msg,col_type:'text_3'},
    {title:'多半是被风控拦了，下拉刷新、或换个网络再试一次',col_type:'text_3'},
    {title:'（还不行就把这屏截图发给助手）返回长度 '+String(len),col_type:'text_3'}
  ];
}
function _diag(raw,code,extra){
  var head=String(raw||'').substring(0,90).replace(/[\r\n]+/g,' ');
  var d=[];
  d.push({title:'⚠️ 没取到视频（请把下面几行截图给助手）',col_type:'text_3'});
  d.push({title:'返回长度 '+String((raw||'').length)+'　状态码 '+code,col_type:'text_3'});
  if(extra){ d.push({title:'原因 '+extra,col_type:'text_3'}); }
  d.push({title:'返回开头 '+head,col_type:'text_3'});
  return d;
}
function _show(raw,out){
  if(out.err && out.err.indexOf('风控')>=0){ return _char(out.err,String((raw||'').length)); }
  return _diag(raw,out.code,out.err);
}
function _poolSearch(cands,seen,out){
  var plist=[];
  for(var q=1;q<=MAX_PAGES;q++){ plist.push(_feed(q)); }
  var raws=_many(plist,'');
  for(var a=0;a<raws.length;a++){ _scanRaw(raws[a],cands,seen,out,MIN_DIGG); }
  if(cands.length<10){ for(var b=0;b<raws.length;b++){ _scanRaw(raws[b],cands,seen,out,1000); } }
  if(!cands.length){ for(var c=0;c<raws.length;c++){ _scanRaw(raws[c],cands,seen,out,1); } }
  return raws;
}
function _match(cands,KW){
  if(!KW){ return cands; }
  var keys=[KW], s=_sug(KW);
  for(var i=0;i<s.length;i++){ keys.push(s[i]); }
  var hit=[];
  for(var j=0;j<cands.length;j++){
    var blob=(cands[j].desc+' '+cands[j].nick).toLowerCase();
    for(var k=0;k<keys.length;k++){
      var kk=String(keys[k]||'').toLowerCase();
      if(kk && blob.indexOf(kk)>=0){ hit.push(cands[j]); break; }
    }
  }
  return hit;
}
"""

FIND_MAIN = r"""
var cands=[], seen={}, out={code:'-',err:''}, raw='';
try{ raw=(typeof getResCode==='function')?getResCode():''; }catch(e){ raw=''; }
var ckf='';
try{ ckf=_ckStr(); }catch(e5){ ckf=''; }
var loggedf = ckf.indexOf('sessionid')>=0;
var plist=[];
for(var p=2;p<=MAX_PAGES;p++){ plist.push(_feed(p)); }
var raws=_many(plist,'');
raws.unshift(raw);
for(var a=0;a<raws.length;a++){ _scanRaw(raws[a],cands,seen,out,MIN_DIGG); }
if(cands.length<10 && MIN_DIGG>1000){
  var c2=[], s2={};
  for(var b=0;b<raws.length;b++){ _scanRaw(raws[b],c2,s2,out,1000); }
  if(c2.length>cands.length){ cands=c2; }
}
if(!cands.length){
  var c3=[], s3={};
  for(var b2=0;b2<raws.length;b2++){ _scanRaw(raws[b2],c3,s3,out,1); }
  if(c3.length){ cands=c3; }
}
if(!cands.length){
  if(out.err){ setResult(_show(raw,out)); }
  else{
    var m=[{title:'这次没筛到符合条件的视频（'+Math.round(MIN_SEC/60)+' 分钟以上 · 赞≥'+_num(MIN_DIGG)+'）',col_type:'text_3'},
           {title:'下拉刷新换一批就行（分类就一个“5 分钟以上”）',col_type:'text_3'}];
    if(out.ai){ m.push({title:'已自动跳过 '+out.ai+' 条「AI 生成」视频',col_type:'text_3'}); }
    if(!loggedf){ m.push(_loginTopItem()); }
    setResult(m);
  }
} else {
  cands.sort(_byLike);
  if(cands.length>TARGET){ cands=cands.slice(0,TARGET); }
  var res=[];
  for(var k=0;k<cands.length;k++){ res.push(_item(cands[k])); }
  if(!loggedf){ res.unshift(_loginTopItem()); }
  setResult(res);
}
"""

SEARCH_MAIN = r"""
var KW='';
try{ var mm=String(typeof MY_URL!=='undefined'?MY_URL:'').match(/[?&]keyword=([^&]*)/); if(mm){ KW=decodeURIComponent(mm[1]); } }catch(e0){ KW=''; }
if(!KW){ try{ KW=String(getParam('wd')||getParam('s')||''); }catch(e1){} }
var raw='';
try{ raw=(typeof getResCode==='function')?getResCode():''; }catch(e2){ raw=''; }
var ck='';
try{ ck=_ckStr(); }catch(e3){ ck=''; }
var logged = ck.indexOf('sessionid')>=0;
var cands=[], seen={}, out={code:'-',err:''};
var mode='pool';

if(logged){
  mode='search';
  var offs=[], base=0;
  try{ base=(Math.max(1,Number(MY_PAGE)||1)-1)*10; }catch(e4){ base=0; }
  for(var p=1;p<SPAGES;p++){ offs.push(_surl(base+p*10)); }
  var rs=_many(offs,ck);
  rs.unshift(raw);
  for(var a=0;a<rs.length;a++){ _scanRaw(rs[a],cands,seen,out,MIN_DIGG); }
  if(cands.length<8){ for(var b=0;b<rs.length;b++){ _scanRaw(rs[b],cands,seen,out,1000); } }
  if(!cands.length){ mode='pool'; }
}

if(mode==='pool'){ _poolSearch(cands,seen,out); }

var matched=cands;
if(mode==='pool' && KW){ matched=_match(cands,KW); }

if(!matched.length){
  var res0=[];
  res0.push({title:'🙁 没搜到「'+KW+'」里符合条件（'+Math.round(MIN_SEC/60)+' 分钟以上 · 赞≥'+_num(MIN_DIGG)+'）的视频',col_type:'text_3'});
  if(mode==='pool'){
    res0.push({title:'说明：抖音的搜索接口必须登录，不登录只能从精选池里找',col_type:'text_3'});
  }
  res0.push(_webItem(KW));
  if(mode==='pool'){
    res0.push(_loginItem());
    res0.push(_againItem(KW));
  }
  var sg=_sugItems(KW);
  for(var q1=0;q1<sg.length;q1++){ res0.push(sg[q1]); }
  setResult(res0);
} else {
  matched.sort(_byLike);
  if(matched.length>TARGET){ matched=matched.slice(0,TARGET); }
  var res=[];
  if(mode==='pool'){
    res.push({title:'ⓘ 没登录抖音，以下是精选池里的「'+KW+'」相关（往下有解锁真·搜索的入口）',col_type:'text_3'});
  } else {
    res.push({title:'🔎 抖音官方搜索结果：'+KW,col_type:'text_3'});
  }
  for(var k2=0;k2<matched.length;k2++){ res.push(_item(matched[k2])); }
  if(mode==='pool'){
    res.push(_webItem(KW));
    res.push(_loginItem());
    res.push(_againItem(KW));
  }
  setResult(res);
}
"""

head = (HEAD.replace("__BASE__", BASE).replace("__SAPI__", SEARCH).replace("__TITLE__", TITLE)).strip("\n")

rule = {
    "title": TITLE,
    "author": "OpenHands",
    "url": BASE + "&refresh_index=fypage;get;UTF-8;{User-Agent@" + APP_UA + "}",
    "version": 9,
    "col_type": "movie_1_vertical_pic",
    "class_name": "",
    "type": "video",
    "class_url": "",
    "area_name": "",
    "area_url": "",
    "sort_name": "",
    "sort_url": "",
    "year_name": "",
    "year_url": "",
    "find_rule": "js:" + (head + FIND_MAIN).strip("\n"),
    "search_url": SEARCH + ";get;UTF-8;{User-Agent@" + APP_UA + "}",
    "searchFind": "js:" + (head + SEARCH_MAIN).strip("\n"),
    "group": "②视频",
    "last_chapter_rule": ""
}

out = "/home/openhands/workspace/project/d451b3b3c0c2425db4db1c9f6f1520ed/海阔视界规则/抖音精选_rule.json"
bak = out + ".bak"
if os.path.exists(out):
    shutil.copyfile(out, bak)
    print("已覆盖备份旧规则 →", bak)
with open(out, "w", encoding="utf-8") as f:
    json.dump(rule, f, ensure_ascii=False, indent=2)
print("已写入:", out)
d = json.load(open(out, encoding="utf-8"))
print("版本:", d["version"], "标题:", d["title"], "分类:", repr(d["class_name"]))
print("正文长度: find_rule", len(d["find_rule"]), "searchFind", len(d["searchFind"]))
