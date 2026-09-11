// ============================================================
// 聚阅子程序（接口源）模板 · parse 对象（完整实战版）
// 用法：聚阅宿主 → 新建接口 → 选「parseCode」模板 → 粘贴本文件 → 保存
// 依赖：仅依赖聚阅宿主（config.聚阅 运行时）。无需 rule.json / pages / libs.zip。
// 环境：聚阅运行时支持 ES6（let/const/=>/模板字符串/map 均可）。
// 可调海阔内置 API：request/fetch（同步返回字符串）、pdfa/pdfh/pd 四大金刚、
//                  getMyVar/putMyVar/getItem/setItem/getCookie/setCookie、
//                  base64Encode、MY_PAGE/MY_URL、refreshPage、$('').input/lazyRule。
// ============================================================
// ⚠️ 五大必坑（实战踩坑总结，务必遵守）：
//  1. 【#gameTheme# 二级标识】所有列表项（主页/分类/搜索）的 url 必须拼
//     `#gameTheme#` 后缀，否则点击不进二级菜单（选集渲染）→ 选集没法播放。
//     二级标识在 parse.二级标识 声明，与 url 后缀要一致。
//  2. 【验证码反爬】凡是有"系统安全验证/验证码"的站，所有 fetch 必须走
//     parse._fetchSafe 包装（撞盾页自动弹图片输入框），不能裸 request。
//  3. 【cookie 持久化】验证码通过后 getCookie(host) 存 getItem('fy_cookie')，
//     重启后 setCookie 恢复，避免每次重启都要重输。
//  4. 【云口令】云口令由用户在聚阅里生成（"分享→云剪贴板"），格式
//     云口令：聚阅接口￥<aesEnc(pasteurl)>￥<源名>(云N)@import=... ；
//     不要自己拼（aesEncode 是海阔内置，加密的是 pasteurl 短链不是源内容）。
//  5. 【二级返回结构】多线路 list 必须是 [线路1选集数组, 线路2选集数组, ...]，
//     单线路是一维选集数组；选集项 {title, url}。
// ============================================================
let parse = {
    作者: "",
    版本: "1",
    host: "https://站点/",   // 站点地址，拼 URL 用 parse.host
    Q: "〈〈〉〉",            // 标题前缀装饰符（可自定义）

    // 分页开关
    页码: {
        主页: false,
        分类: true,
        排行: true,
        更新: true
    },

    // 频道（宿主顶部导航项）
    频道: {
        包含项: ["分类", "排行", "周表"]
    },

    // 二级标识：列表项 url 末尾必须拼这个，点击才进二级菜单（选集）
    二级标识: "#gameTheme#",

    // UA（很多站对移动 UA 不触发验证码，优先用移动 UA）
    UA: "Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1",

    // ========== 验证码工具（有反爬的站必用，无验证码站可删） ==========
    _getCk: function() {
        try { return getVar('fy_cookie', '') || getItem('fy_cookie', ''); } catch (e) { return ''; }
    },
    _setCk: function(ck) {
        if (ck) try { setItem('fy_cookie', ck); putVar('fy_cookie', ck); } catch (e) {}
    },
    _isShield: function(html) {
        if (!html) return true;
        return /系统安全验证|mac_verify|访问此数据需要输入验证码|安全检测/.test(html);
    },
    _makeHead: function(referer, ck) {
        let h = { 'User-Agent': parse.UA, 'Referer': referer };
        if (ck) h['Cookie'] = ck;
        return h;
    },
    // 统一安全请求：返回 { html, verify }，撞盾页时 verify 是验证码输入卡片
    _fetchSafe: function(url) {
        let h = parse.host;
        let result = { html: '', verify: null };
        try {
            let autoCk = getCookie(h) || '';
            if (!autoCk) { let savedCk = getItem('fy_cookie', ''); if (savedCk) setCookie(h, savedCk); }
        } catch (e) {}
        try {
            result.html = request(url, {
                headers: { 'User-Agent': parse.UA, 'Referer': h + '/' },
                timeout: 15000
            }) || '';
        } catch (e) { log('请求异常: ' + e.message); }
        if (!result.html) { result.verify = parse._makeVerify(url, ''); return result; }
        if (!parse._isShield(result.html)) return result;
        result.verify = parse._makeVerify(url, result.html);
        result.html = '';
        return result;
    },
    // 验证码输入卡片：图片 + 用户输入 + POST 验证 + 持久化 cookie
    _makeVerify: function(url, shieldHtml) {
        let h = parse.host;
        let ua = parse.UA;
        let captchaUrl = h + '/captcha.php?type=code&r=' + Math.random();  // 视站点改
        let imgBase64 = '';
        try {
            let imgData = request(captchaUrl, { headers: { 'User-Agent': ua, 'Referer': url }, buffer: true });
            imgBase64 = base64Encode(imgData);
        } catch (e) { log('验证码图片失败: ' + e.message); }
        if (!imgBase64) {
            return {
                title: '🔒 获取验证码失败，点击重试',
                col_type: 'text_center_1',
                url: $('重试').lazyRule(() => { refreshPage(true); return 'hiker://empty'; })
            };
        }
        return {
            title: '🔒 点击图片输入验证码',
            pic_url: captchaUrl,
            col_type: 'movie_1_left_pic',
            url: $('').input((h, ua, ref) => {
                let code = input;
                let result = request(h + '/captcha.php?type=verify', {  // 视站点改
                    method: 'POST',
                    body: 'check=' + code,
                    headers: { 'User-Agent': ua, 'Referer': ref }
                });
                try {
                    let res = JSON.parse(result);
                    if (res.code == 1) {
                        try { let ck = getCookie(h); if (ck) setItem('fy_cookie', ck); } catch (e) {}
                        refreshPage(true);
                        return 'hiker://empty';
                    } else { return 'toast://' + (res.msg || '验证失败'); }
                } catch (e) { return 'toast://验证异常'; }
            }, h, ua, url)
        };
    },

    // ========== 主页 ==========
    主页: function() {
        let d = [];
        let host = parse.host;
        let _r = parse._fetchSafe(host);
        let html = _r.html || '';
        if (_r.verify) { d.push(_r.verify); return d; }
        let items = pdfa(html, 'body&&.列表容器class');
        items.forEach(item => {
            let url = pd(item, 'a&&href');
            let title = pdfh(item, 'a&&title') || pdfh(item, '.标题class&&Text');
            let img = pd(item, 'img&&data-src').replace(/&amp;/g, '&');
            let desc = pdfh(item, '.更新class&&Text') || '';
            if (url && !url.startsWith('http')) url = host + url;
            // ⚠️ 必须加 #gameTheme#（二级标识）
            if (title) d.push({ title, desc, img, url: url + '#gameTheme#', col_type: 'movie_3' });
        });
        return d;
    },

    // ========== 分类 ==========
    分类: function() {
        let d = [];
        let host = parse.host;
        let page = MY_PAGE;
        // 分类选项：{name, value}，value 是分类路径（如 cupfox-list/1 / label/qq）
        let cateOptions = [
            { name: '分类1', value: 'list/1' },
            { name: '分类2', value: 'list/2' }
        ];
        let raw_url = getMyVar('tturl', host + '/' + cateOptions[0].value + '.html');
        let true_url = raw_url;
        // 拼分页 URL（视站点格式调整）
        if (true_url.indexOf('/list/') > -1) {
            let base = true_url.replace(/\.html$/, '').replace(/-+$/, '');
            true_url = base + '--------' + page + '---.html';
        }
        let _r = parse._fetchSafe(true_url);
        let html = _r.html;
        if (_r.verify) { d.push(_r.verify); return d; }
        if (parseInt(page) === 1) {
            let Color = () => '#' + ('00000' + (Math.random() * 0x1000000 << 0).toString(16)).substr(-6);
            cateOptions.forEach(opt => {
                let isActive = raw_url.indexOf('/' + opt.value) > -1;
                d.push({
                    title: isActive ? parse.Q + ('<b><span style="color:' + Color() + '">' + opt.name + '</span></b>') : opt.name,
                    url: $('hiker://empty').lazyRule(params => {
                        putMyVar('tturl', params.host + '/' + params.value + '.html');
                        refreshPage(true);
                        return 'hiker://empty';
                    }, { value: opt.value, host }),
                    col_type: 'scroll_button'
                });
            });
            d.push({ col_type: 'blank_block' });
        }
        let items = pdfa(html, '.列表容器class');
        items.forEach(item => {
            let url = pd(item, 'a&&href');
            let title = pdfh(item, 'a&&title') || pdfh(item, '.标题class&&Text');
            let img = pd(item, 'img&&data-src').replace(/&amp;/g, '&');
            let desc = pdfh(item, '.更新class&&Text') || '';
            if (url && !url.startsWith('http')) url = host + url;
            if (title) d.push({ title, desc, img, url: url + '#gameTheme#', col_type: 'movie_3' });
        });
        return d;
    },

    // ========== 二级（详情页）：返回结构化对象，宿主自动渲染选集 ==========
    二级: function(url) {
        let _r = parse._fetchSafe(url);
        let html = _r.html || '';
        if (_r.verify) {
            return { title: '需要验证', desc: '', img: '', line: [], list: [], extenditems: [_r.verify] };
        }
        let host = parse.host;
        let 标题 = (pdfh(html, '.标题class&&Text') || pdfh(html, 'h3&&Text') || '').trim();
        let 图片 = pdfh(html, '.海报class&&img&&data-src');
        if (图片 && !图片.includes('http')) 图片 = host + 图片;
        let 简介 = (pdfh(html, '.简介class&&Text') || '').replace(/^简介[:：]\s*/, '');
        // 线路名（与选集容器一一对应）
        let tabs = pdfa(html, 'body&&.线路tab容器&&a');
        let lines = tabs.map(a => (pdfh(a, 'Text') || '').replace(/\(\d+\)/g, '').trim());
        // 选集：多线路 → [线路1选集, 线路2选集, ...]
        let conts = pdfa(html, 'body&&.选集容器class');
        let list = conts.map(cont => {
            return pdfa(cont, 'ul&&a').map(a => {
                let ep = (pdfh(a, 'a&&Text') || '').trim();
                let href = pd(a, 'a&&href') || '';
                if (href && !href.startsWith('http')) href = host + href;
                return { title: ep, url: href };
            });
        });
        return {
            detail1: parse.Q + '<b>' + 标题 + '</b>',
            detail2: '站点名',
            desc: '<small>' + 简介 + '</small>',
            img: 图片 ? 图片 + '@Referer=' + host : '',
            line: lines.length > 1 ? lines : '',
            list: list.length > 1 ? list : (list[0] || [])
        };
    },

    // ========== 搜索 ==========
    搜索: function(name) {
        let d = [];
        let page = MY_PAGE;
        let host = parse.host;
        let _r = parse._fetchSafe(host + '/搜索路径/' + name + '----------' + page + '---.html');
        let html = _r.html;
        if (_r.verify) { d.push(_r.verify); return d; }
        let list = pdfa(html, 'body&&.列表容器class');
        list.forEach(li => {
            d.push({
                title: pdfh(li, 'img&&alt') || pdfh(li, '.标题class&&Text'),
                desc: pdfh(li, '.更新class&&Text'),
                img: pdfh(li, 'img&&data-src'),
                url: host + pdfh(li, 'a&&href') + '#gameTheme#'  // ⚠️ 必加
            });
        });
        return d;
    },

    // ========== 解析：把选集地址（播放页）变成可播直链（m3u8） ==========
    解析: function(url) {
        let _r = parse._fetchSafe(url);
        let html = _r.html || '';
        if (_r.verify) return url;
        // 从播放页提取播放地址（正则/解析，视站点而定）
        let m = html.match(/var\s+player_aaaa\s*=\s*(\{[\s\S]*?\})\s*<\/script>/);
        if (!m) return 'toast://未找到播放地址';
        let playerData;
        try { playerData = JSON.parse(m[1]); } catch (e) { return 'toast://解析失败'; }
        let playUrl = playerData.url || '';
        let encrypt = parseInt(playerData.encrypt) || 0;
        if (encrypt === 1) playUrl = unescape(playUrl);
        else if (encrypt === 2) try { playUrl = unescape(base64Decode(playUrl)); } catch (e) {}
        // 已是 http 链接直接返回（自营直链 m3u8）
        if (playUrl && /^https?:\/\//i.test(playUrl)) return playUrl;
        // 否则走解析接口（视站点而定，如 playerconfig.js 的 player_list + parse 接口）
        return playUrl;
    },

    // ========== 最新章节 ==========
    最新: function(url) {
        return '';
    }
};
