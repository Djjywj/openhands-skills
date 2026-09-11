#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""校验海阔视界 rule.json 的字段完整性与常见陷阱。

用法:
    python validate_rule.py <path/to/rule.json 或 目录>
    python validate_rule.py <path> --json      # 额外输出机器可读 JSON 报告

退出码: 0=通过(仅警告), 1=存在错误(字段缺失/不匹配), 2=用法错误

输出分三段：[错误]（退出码 1）/ [警告]（真问题，建议改）/ [提示]（兼容性建议，不算错）。
"""
import json
import sys
import os
import re
import io
import contextlib

REQUIRED = ["title", "url", "type", "find_rule", "class_name", "class_url"]
VALID_TYPES = {"video", "audio", "image", "other", "tool", "all"}

# 官方 help_col_type 收录的样式
VALID_COL_TYPES = {
    "movie_1", "movie_2", "movie_3", "movie_3_marquee",
    "movie_1_left_pic", "movie_1_vertical_pic", "movie_1_vertical_pic_blur",
    "text_1", "text_2", "text_3", "text_4", "text_5", "text_center_1",
    "long_text", "rich_text",
    "pic_1", "pic_1_full", "pic_1_center", "pic_2", "pic_2_card", "pic_3", "pic_3_square",
    "icon_1_search", "icon_2", "icon_2_round", "icon_4", "icon_4_card",
    "icon_round_4", "icon_round_small_4", "icon_small_3", "icon_small_4",
    "text_icon", "avatar",
    "line", "line_blank", "blank_block",
    "flex_button", "scroll_button", "input",
    "card_pic_1", "card_pic_2", "card_pic_2_2", "card_pic_2_2_left", "card_pic_3",
    "x5_webview_single",
}

# ES6+ 语法探测（旧版 JSEngine 仅 ES5，仅作兼容性提示，不判错）
ES6_PATTERNS = [
    (re.compile(r"\b(?:const|let)\s+"), "const / let（请用 var）"),
    (re.compile(r"=>"), "箭头函数 =>（请用 function(){}）"),
    (re.compile(r"`"), "反引号模板字符串（请用字符串拼接 +）"),
    (re.compile(r"\bclass\s+\w"), "class 类"),
    (re.compile(r"\b(?:async|await|yield)\b"), "async / await / yield"),
    (re.compile(r"\bfor\s*\([^)]*\bof\b"), "for...of（请用普通 for）"),
]

JS_FIELDS = ("find_rule", "searchFind", "detail_find_rule", "preRule",
             "sdetail_find_rule", "last_chapter_rule")

# JS 里出现的 col_type 字面量（如 col_type:'movie_3'），用于校验 JS 内动态样式
COL_TYPE_LITERAL = re.compile(r"""col_type\s*[:=]\s*['"]([a-zA-Z_0-9]+)['"]""")

# 常见反模式：(正则, 类别, 说明)  类别 warn=警告 / hint=提示
ANTI_PATTERNS = [
    (re.compile(r"hiker://search\?s="), "warn",
     "出现 hiker://search?s= —— 这是系统级搜索协议，会丢弃本源；自绘搜索框应改用 @rule 接回本源 search()"),
    (re.compile(r"""href\s*=\s*"[^"]*@lazyRule"""), "warn",
     'rich_text 里的 <a href="...@lazyRule..."> 用了双引号，会被内层双引号截断（表现为"展开:字在、点了没反应"）；href 必须用单引号'),
    (re.compile(r"JSON\.parse\s*\(\s*fetch\s*\("), "warn",
     "直接 JSON.parse(fetch(...))：fetch 失败会返回字符串 'error'，解析会整页崩；先判空串/'error' 再 parse"),
]


def _js_fields(rule):
    out = []
    for k, v in rule.items():
        if isinstance(v, str) and (k in JS_FIELDS or v.lstrip().startswith("js:")):
            out.append((k, v))
    return out


def _strip_js(code):
    s = code.lstrip()
    return s[3:].lstrip() if s.startswith("js:") else code


def detect_dependencies(path, rule):
    """识别规则依赖类型，返回 (deps 列表, notes 列表)。"""
    d = os.path.dirname(os.path.abspath(path))
    text = json.dumps(rule, ensure_ascii=False)
    deps, notes = [], []

    # 1. 库打包依赖：同目录存在 require.json / libs.zip
    has_req = os.path.exists(os.path.join(d, "require.json"))
    has_libs = os.path.exists(os.path.join(d, "libs.zip"))
    if has_req or has_libs:
        deps.append("库打包依赖（require.json + libs.zip）")
        notes.append("必须连包整体导入，不能只丢 rule.json；libs.zip 内的库会自动安装到设备")

    # 2. 跨规则程序依赖：hiker://page/...?rule=<固定程序名>（排除自引用）
    my_title = str(rule.get("title", "")).strip()
    progs = set(re.findall(r'hiker://page/[^"\']*?\?rule=([^"\'&?\\]+)', text))
    progs.discard(my_title)
    if progs:
        deps.append("跨规则程序依赖：" + "、".join(sorted(progs)))
        notes.append("需按原标题安装这些程序（如保留『%s』），否则对应功能（解析/渲染等）失效"
                     % "』『".join(sorted(progs)))

    # 2b. 自身是基础程序（被依赖方）
    if str(rule.get("type", "")).strip() == "tool" and "$.exports" in text and (
        f"?rule={my_title}" in text or my_title == ""
    ):
        notes.append("⚠ 该规则是供其他规则调用的『基础程序/模板』（如 Q模板、解析引擎），"
                     "依赖方需按标题『%s』安装后通过 $.require('hiker://page/...?rule=%s') 调用；"
                     "它本身通常自包含" % (my_title, my_title))

    # 3. 框架型：type:all + hiker://empty
    is_framework = (str(rule.get("type", "")).strip() == "all") and ("hiker://empty" in str(rule.get("url", "")))
    if is_framework:
        if "config.聚阅" in text or "聚阅" in text:
            deps.append("框架型（聚阅宿主，含子程序加载器）")
            notes.append("提供云口令导入入口；子程序经云口令/远程源装入其 juItem.json")
        else:
            deps.append("框架型（自包含聚阅子程序，自带运行时）")
            notes.append("type:all 普通『本地导入』可能拒绝；应先装聚阅框架宿主再作为子程序导入（云口令/远程源），少数版本可独立导入")

    # 4. 其它 $.require 调用（非 hiker://）且未命中库打包：提示可能缺库
    if "$.require(" in text and not progs and not (has_req or has_libs):
        deps.append("含 $.require(...) 调用（可能依赖外部库/框架）")
        notes.append("确认这些库已通过 require.json+libs.zip 或框架宿主提供，否则运行报找不到模块")

    if not deps:
        deps.append("无依赖（普通规则，可直接导入）")
    return deps, notes


def validate(path):
    errors, warnings, notices = [], [], []

    if os.path.isdir(path):
        cand = os.path.join(path, "rule.json")
        if not os.path.exists(cand):
            cands = [f for f in os.listdir(path) if f.endswith(".json")]
            if len(cands) == 1:
                cand = os.path.join(path, cands[0])
            else:
                print(f"[错误] 目录中没有 rule.json: {path}")
                return 1, [], [], []
        path = cand

    try:
        with open(path, encoding="utf-8") as f:
            raw = f.read()
    except Exception as e:
        print(f"[错误] 读取失败: {e}")
        return 1, [], [], []

    try:
        rule = json.loads(raw.lstrip("\ufeff"))
    except Exception as e:
        print(f"[错误] JSON 解析失败: {e}")
        return 1, [], [], []

    is_tool = str(rule.get("type", "")).strip() in ("tool", "all")
    required = [k for k in REQUIRED if not (is_tool and k in ("class_name", "class_url"))]
    no_class = not str(rule.get("class_name", "") or "").strip() and not str(rule.get("class_url", "") or "").strip()
    for k in required:
        v = rule.get(k, "")
        if v is None or (isinstance(v, str) and v.strip() == ""):
            # 合法：单列表规则（class_name/class_url 均为空，首页直接用 url）
            if k in ("class_name", "class_url") and no_class:
                continue
            errors.append(f"字段 '{k}' 缺失或为空")
    if no_class:
        warnings.append("无分类（单列表）规则：class_name/class_url 均为空，首页直接请求 url")

    t = str(rule.get("type", "")).strip()

    # ---- class_name / class_url ----
    cn = [x for x in str(rule.get("class_name", "")).split("&") if x != ""]
    cu = [x for x in str(rule.get("class_url", "")).split("&") if x != ""]
    if cn and cu and len(cn) != len(cu):
        errors.append(f"class_name({len(cn)}) 与 class_url({len(cu)}) 数量不一致")

    # ---- type ----
    if t and t not in VALID_TYPES:
        warnings.append(f"type='{t}' 非标准值，建议用 {sorted(VALID_TYPES)}")

    # ---- col_type（顶层 + JS 内字面量） ----
    for cf in ("col_type", "detail_col_type", "sdetail_col_type"):
        v = str(rule.get(cf, "")).strip()
        if v and v not in VALID_COL_TYPES:
            warnings.append(f"{cf}='{v}' 不在官方常用样式表内，请确认拼写（见 references/col_type.md）")
    js_bodies = _js_fields(rule)
    bad_literals = set()
    for _fname, _code in js_bodies:
        for mt in COL_TYPE_LITERAL.finditer(_strip_js(_code)):
            lit = mt.group(1)
            if lit not in VALID_COL_TYPES:
                bad_literals.add(lit)
    if bad_literals:
        warnings.append(
            "JS 里用了不存在的 col_type: "
            + ", ".join(sorted(bad_literals))
            + "（官方 45 个样式里没有它，真机会渲染异常；见 references/col_type.md，常见误用是 list_1 → 改用 text_center_1/blank_block）"
        )

    # ---- 搜索 ----
    su = str(rule.get("search_url", ""))
    if su and "**" not in su and "%%" not in su:
        warnings.append("search_url 未包含 **（或 %%）搜索占位符")
    if su and not str(rule.get("searchFind", "")).strip() and t in ("video", "image", "audio", "other"):
        warnings.append("有 search_url 但缺 searchFind，搜索可能无结果")

    # ---- 筛选占位符 ----
    url = str(rule.get("url", ""))
    for pref in ("area", "sort", "year"):
        name_f, url_f = pref + "_name", pref + "_url"
        if str(rule.get(name_f, "")).strip() or str(rule.get(url_f, "")).strip():
            ph = "fy" + pref
            if ph not in url:
                warnings.append(f"定义了 {name_f}/{url_f} 但 url 中无 {ph} 占位符，筛选可能不生效")

    if t in ("video", "image", "audio") and "fypage" not in url and "hiker://" not in url:
        warnings.append("url 中未发现 fypage 占位符，可能无法翻页")

    # ---- API 修饰符 ----
    fr = str(rule.get("find_rule", ""))
    if "JSON.parse" in fr and "getResCode" in fr:
        if ";get;UTF-8;" not in url and "hiker://" not in url:
            warnings.append("find_rule 用 JSON.parse 解析 API，但 url 未加 ;get;UTF-8;{referer@...} 修饰符")

    # ---- 视频 #isVideo ----
    if t == "video":
        dfr = str(rule.get("detail_find_rule", ""))
        sdr = str(rule.get("sdetail_find_rule", "")).strip()
        if dfr and "#isVideo=true#" not in dfr and sdr not in ('"*"', "*"):
            warnings.append("视频规则的 detail_find_rule 未出现 #isVideo=true#，可能无法直接播放")
        if not str(rule.get("searchFind", "")).strip():
            warnings.append("视频规则建议填写 searchFind 以支持搜索")

    # ---- 图片防盗链 ----
    if t == "image":
        text_all = json.dumps(rule, ensure_ascii=False)
        if "@Referer=" not in text_all and "@headers=" not in text_all:
            warnings.append("图片规则未发现 @Referer= / @headers= 防盗链设置，图可能裂")

    # ---- 反模式扫描（原始 JSON 文本 + 反转义后的 JS 字段） ----
    all_js = "\n".join(_strip_js(c) for _f, c in js_bodies)
    for pat, kind, msg in ANTI_PATTERNS:
        if pat.search(raw) or pat.search(all_js):
            (warnings if kind == "warn" else notices).append(msg)

    # ---- ES 语法检查（兼容性提示，不算错误） ----
    for fname, code in js_bodies:
        body = _strip_js(code)
        hits = [msg for pat, msg in ES6_PATTERNS if pat.search(body)]
        if hits:
            notices.append(
                f"{fname} 含 ES6+ 语法：{'; '.join(hits)} —— "
                "新版海阔引擎支持 ES6+（官方文档示例即用 let/const/箭头函数），但旧版仅支持 ES5；"
                "本库默认写 ES5 以兼容所有版本。真机实测 ES6 可用时此提示可忽略。"
            )

    # ---- 结构性提示（不阻塞） ----
    if all_js:
        if "MY_URL" not in all_js and "getParam(" in all_js:
            notices.append("JS 里用了 getParam(...) 但没见 MY_URL —— 占位 URL 的 query 不一定保留，详情参数建议从 MY_URL 解析（见 references/pitfalls.md §二.6）")
        if "MY_KEYWORD" not in all_js and "getParam(" in all_js and str(rule.get("searchFind", "")).strip():
            notices.append("搜索解析里未见 MY_KEYWORD —— 搜索词建议用内置变量 MY_KEYWORD 而非 getParam('kw')")
        if "#immersiveTheme#" not in raw and t == "video" and ("@rule=" in raw or "lazyRule" in raw):
            notices.append("视频规则跳详情未发现 #immersiveTheme# —— 详情页顶部可能留白（见 references/detail_layout.md §1）")
        if not re.search(r"""url\s*:\s*['"]javascript:""", all_js) and "col_type" in all_js and t == "video":
            notices.append("未见 url:'javascript:;' —— 海报卡/简介等纯展示项应设它以免误跳转（见 references/pitfalls.md §一.5）")
        if "#isVideo=true#" not in raw and t == "video" and "m3u8" in all_js:
            notices.append("JS 里出现 m3u8 但没有 #isVideo=true# —— 确认播放直链已加媒体标识")

    deps, notes = detect_dependencies(path, rule)

    # ---- 输出 ----
    print(f"规则: {rule.get('title','?')}  | type={t}  | group={rule.get('group','?')}")
    print(f"文件: {path}")
    print(f"字段数: {len(rule)}")

    print("\n[依赖识别]")
    for dep in deps:
        print(f"  - {dep}")
    for n in notes:
        print(f"      ↳ {n}")
    if deps and "无依赖" in deps[0]:
        print("      （生成后可直接导入；仍建议用 test_rule.js 在 PC 验证解析）")

    if warnings:
        print("\n[警告]")
        for w in warnings:
            print(f"  - {w}")
    if notices:
        print("\n[提示]（兼容性/优化建议，不影响通过）")
        for n in notices:
            print(f"  - {n}")
    if errors:
        print("\n[错误]")
        for e in errors:
            print(f"  - {e}")
        return 1, errors, warnings, notices
    print("\n校验通过 ✓")
    return 0, errors, warnings, notices


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    as_json = "--json" in sys.argv
    if not args:
        print("用法: python validate_rule.py <rule.json 或 目录> [--json]")
        sys.exit(2)
    path = args[0]

    # --json 时人类可读报告走 stderr，stdout 只留纯 JSON，方便管道解析
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        code, errors, warnings, notices = validate(path)
    human = buf.getvalue()

    if as_json:
        sys.stderr.write(human)
        try:
            with open(path, encoding="utf-8") as f:
                rule = json.loads(f.read().lstrip("\ufeff"))
        except Exception:
            rule = {}
        deps, notes = detect_dependencies(path, rule)
        print(json.dumps({
            "path": path, "ok": code == 0,
            "errors": errors, "warnings": warnings, "notices": notices,
            "dependencies": deps, "notes": notes,
        }, ensure_ascii=False, indent=2))
    else:
        sys.stdout.write(human)
    sys.exit(code)


if __name__ == "__main__":
    main()
