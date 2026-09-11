# 详情页布局规范（视频 / 动漫类）

> 目标：详情页不能只有一串剧集，必须是「像样的一页」。
> 本文件给出**可直接复制的 ES5 实现**，按顺序拼装即可。
>
> 说明：本规范的思路与代码骨架来自开源技能库 wsh-feiyu/hikerskill 的真机调试经验（其标注为 App 实测通过），
> 本库已把其中的 ES6 写法**改写为 ES5** 以符合本库默认约定，并用官方文档核对了用到的 API/col_type。
> ⚠️ **UI 长相无法在本机验证**（`test_rule.js` 只测数据），最终仍需真机确认。

---

## 0. 标准返回顺序（硬性）

```
[海报卡] → [剧情简介] → [（可选）小菜单] → [（可选）线路切换] → [剧集列表]
```

- 顺序不要颠倒；**海报卡和剧集列表是必需项**。
- 不参与跳转的展示项（海报卡、简介）`url` 一律用 `javascript:;`。
- 别把长简介塞进海报卡的 `desc`（点一下会跳空白页）。

---

## 1. 海报卡

- `col_type`：`movie_1_vertical_pic_blur`（背景为该图的高斯模糊，可加 `extra:{gradient:true}` 渐变）。
- **`title` 只放单行标题**；**`desc` 放多行元信息**（用 `\n` 分隔）。
  ⚠️ 反过来写（信息堆进 title、desc 掏空）会导致**海报上方留白过高**。
- `url`：用 `封面 + '#.jpg#'` → 点击查看大图。

```js
// res = { title, pic, type, year, area, remark, actor, director, score }
function makePoster(res) {
    var meta = [];
    if (res.type)   { meta.push(res.type); }
    if (res.year)   { meta.push(res.year); }
    if (res.area)   { meta.push(res.area); }
    if (res.remark) { meta.push(res.remark); }
    var lines = [meta.join(' · ')];
    if (res.actor)    { lines.push('主演：' + res.actor); }
    if (res.director) { lines.push('导演：' + res.director); }
    if (res.score)    { lines.push('评分：' + res.score); }

    var pic = res.pic || '';
    if (pic) { pic = pic + '@Referer=' + HOST + '/'; }

    return {
        title: res.title || '',
        desc: lines.join('\n'),
        pic_url: pic,
        url: pic ? (pic + '#.jpg#') : 'javascript:;',
        col_type: 'movie_1_vertical_pic_blur',
        extra: { gradient: true }
    };
}
```

### 顶部留白还有另一半
**列表/搜索项跳详情时，url 必须带 `#immersiveTheme#`**：

```js
url: 详情地址 + '#immersiveTheme#' + '@rule=js:$.require("引擎名").detail()'
```

【官方】`help_js.md`：链接含 `#immersiveTheme#` 页面即沉浸，**只对二级页和子页面生效，首页无效**；请求时会自动清除该标记，不影响详情页里 `fetch(MY_URL)`。

---

## 2. 剧情简介（可展开 / 收起）

三种做法，**优先方式 1**：

| 方式 | 写法 | 适用 |
|------|------|------|
| 1（推荐） | `rich_text` + 内嵌 `<a href='#noLoading#@lazyRule=.js:...'>展开:</a>`，点击 `updateItem` 原地切换 | 需要折叠 |
| 2 | `col_type:'long_text'` 全量展示 | 不需要折叠 |
| 3 | `text_1` + `@rule` 跳到新页看全文 | 想换页 |

⚠️ **两个必踩的坑**：
1. `<a>` 的 `href` **必须用单引号**，因为 `@lazyRule=.js:` 代码内部全是双引号 —— 用双引号会在第一个内层 `"` 处截断属性，表现为"**展开两个字在，点了没反应**"。
2. 别用 `long_text` 假装折叠（它是整屏阅读样式），也别手写没有 `href` 的裸 `<a>展开:</a>`。

### 方式 1 的 ES5 可复制实现

```js
// 依赖：storage0（官方支持存 JSON 对象）、updateItem、findItem（官方动态刷新接口）
function setDesc(d, desc, num) {
    if (!desc || !String(desc).replace(/\s+/g, '')) { return; }
    num = num || 100;
    desc = String(desc).replace(/\s+/g, ' ').replace(/&nbsp;/g, ' ').replace(/^\s+|\s+$/g, '');
    if (!desc) { return; }

    var head = '<b><font color="#098AC1">∷剧情简介\t</font></b>';
    var m = 'desc';                      // extra.id / findItem / updateItem / storage0 的 key 必须一致
    var full = '　　' + desc;
    var isLong = desc.length > num;
    var sdc = isLong ? ('　　' + desc.substr(0, num)) : full;

    var title = head;
    if (isLong) {
        // 注意：这里用字符串拼接构造函数体（ES5 的 function，不是箭头函数）
        var fn = '(function(dc,sdc,m,cs){'
            + 'var show=storage0.getItem(m,"0");'
            + 'var title=findItem(m).title;'
            + 'var re=/(<\\/small><br>.*?>).+/g;'
            + 'var exp="展开:";var ret="收起:";'
            + 'if(show=="1"){'
            + 'updateItem(m,{title:title.replace(ret,exp).replace(re,"$1"+sdc+"</small>").replace(/(<\\/small><br>\\<font color=").*?(">)/,"$1"+cs.hide+"$2")});'
            + 'storage0.setItem(m,"0");'
            + '}else{'
            + 'updateItem(m,{title:title.replace(exp,ret).replace(re,"$1"+dc+"</small>").replace(/(<\\/small><br>\\<font color=").*?(">)/,"$1"+cs.show+"$2")});'
            + 'storage0.setItem(m,"1");'
            + '}'
            + 'return "hiker://empty";})';
        var args = '(' + JSON.stringify(full) + ',' + JSON.stringify(sdc)
            + ',"' + m + '",{"show":"black","hide":"grey"})';
        var lazy = '#noLoading#@lazyRule=.js:' + fn + args;
        // ⚠️ href 用单引号！
        title += "<small><a style='text-decoration:none;' href='" + lazy + "'>展开:</a></small>";
    }
    title += '<br><font color="grey">' + sdc + '</small>';

    d.push({
        title: title,
        col_type: 'rich_text',
        url: 'javascript:;',
        extra: { id: m, lineSpacing: 6, textSize: 15, lineVisible: false }
    });
}
```

要点：
- 正文与状态用 `storage0.setItem/getItem(m, ...)` 记住（`"0"` 收起 / `"1"` 展开），点击时 `updateItem(m,{title:...})` **原地替换**，不新开页面。
- 简介文本用 `JSON.stringify` 作为固定参数传进去（自动转义换行和引号）。
- 短文本（`<= num`）不生成"展开:"，直接显示全文。
- ⚠️ **`updateItem` 注意**：使用动态刷新时，页面里**尽量同时不要有 `input` 和 `flex_button`/`scroll_button`**（【官方】`help_js.md` 警告：刷新 flex/scroll 会全局刷新导致 input 失焦、数据混乱）。

---

## 3. 小菜单（可选）

跳子页面用 `hiker://page/<path>`（跨程序：`hiker://page/<path>?rule=<规则名>`），参数放 `extra` 对象里（子页面用 `MY_PARAMS.xxx` 取）：

```js
d.push({ title: '演职员', col_type: 'scroll_button', url: 'hiker://page/workers#noHistory#', extra: { id: res.id } });
d.push({ title: '剧照',   col_type: 'scroll_button', url: 'hiker://page/photos#noHistory#',  extra: { id: res.id } });
```

---

## 4. 线路切换（多线路时）

- 用 `scroll_button` 一排按钮，点一下写 myVar + `refreshPage(false)` 重渲染。
- **只有 1 条线路时可以不出这一行**。
- ⚠️ `tabs[]`（线路名）与 `lists[][]`（每线路的剧集）**必须索引一一对应**，错位就串剧。

```js
var tabs = res.tabs || [];          // ['线路A','线路B']
var cur = getMyVar('currentLine', '0');
for (var i = 0; i < tabs.length; i++) {
    var isActive = String(cur) === String(i);
    d.push({
        title: isActive
            ? '‘‘’’<b><font color="#FF5D50">' + tabs[i] + '</font></b>'   // 全角前缀包 HTML
            : tabs[i],
        col_type: 'scroll_button',
        url: $('#noLoading#').lazyRule(function(idx) {
            putMyVar('currentLine', String(idx));
            refreshPage(false);
            return 'hiker://empty';
        }, i),
        extra: { backgroundColor: isActive ? '#20FA7298' : '' }
    });
}
```

> 高亮前缀用全角引号 `‘‘’’`（`\u2018\u2018\u2019\u2019`）包 `<font>`；**别用反引号**，否则部分版本会把标签原样显示出来（见 `pitfalls.md` §三.10）。
> `$('#noLoading#').lazyRule(function(idx){...}, i)` 的第二参按序绑定到回调形参 —— 这是**获取闭包变量的正确姿势**（序列化回调拿不到外层变量，见 `pitfalls.md` §三.8）。

---

## 5. 剧集列表

按集数**动态**选列数（不要写死 `text_2`）：

```js
var eps = lists[parseInt(cur, 10) || 0] || [];
var colType = 'text_2';
if (eps.length > 30)      { colType = 'text_5'; }
else if (eps.length > 20) { colType = 'text_4'; }
else if (eps.length > 10) { colType = 'text_3'; }

for (var k = 0; k < eps.length; k++) {
    d.push({
        title: eps[k].name,
        url: eps[k].url + '#isVideo=true#',          // 直链才这么写；需二次解析的用 lazyRule
        col_type: colType,
        extra: { id: '规则名_' + res.id + '_' + k }   // 全局唯一，防进度串集
    });
}
```

- 需要点击时才解析真实地址 → 用 `$().lazyRule(function(u){...}, ep.url)`，**回调里内联完整解析逻辑、不要引用外层变量**，失败返回 `toast://解析失败`。
- 播放地址**默认不要加 `@headers=`**（部分 CDN 会因此播不了），确认防盗链再加。

---

## 6. 空态 / 错误态

任何一级解析失败，**不要返回空白**，给一行提示：

```js
if (!d.length) {
    d.push({ title: '没解析到内容，请稍后重试或换个线路', col_type: 'text_center_1', url: 'javascript:;' });
}
```

> ⚠️ 不要用 `col_type:'list_1'` —— **官方 45 个 col_type 里没有 `list_1`**（外部技能库有处误用，别抄）。
> 合法可用的：`text_center_1`、`text_1`、`blank_block`（详见 `col_type.md`）。

---

## 7. 组装骨架（把上面串起来）

```js
js:
var HOST = 'https://站点域名';
var raw = (typeof getResCode === 'function') ? getResCode() : '';
var d = [];
try {
    var res = parseDetail(raw);        // 自己实现的详情解析
    d.push(makePoster(res));           // 1 海报卡
    setDesc(d, res.intro, 100);        // 2 简介（可折叠）
    pushLines(d, res);                 // 3 线路切换
    pushEpisodes(d, res);              // 4 剧集
    if (!d.length) { d.push({ title: '没解析到内容', col_type: 'text_center_1', url: 'javascript:;' }); }
} catch (e) {
    setError('详情解析失败：' + e.message);   // 真机排障用
    d.push({ title: '解析失败：' + e.message, col_type: 'text_1', url: 'javascript:;' });
}
setResult(d);
```
