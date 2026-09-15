# see-images

让 Agent 真正"读"图片内容的技能 —— 截图、照片、图表、扫描件、界面截图，都能拿到里面写了什么。

## 解决什么问题

Agent 本身看不到图片像素，遇到"看看这张图"通常会回答"我看不到图片"就停住。这个技能把图片
交给一个能看图的模型，拿回文字描述再回答，于是"看不到"变成了"能回答"。

同时解决两个常见失败：

1. **"我看不到图片"** —— 对话模型是纯文本的，但视觉模型只差一次 HTTP 请求。`scripts/look.py`
   负责这一次请求。
2. **"我找不到你发的图片"** —— 在 Agent Canvas 里，聊天图片不是工作区文件，而是以 base64
   `data:` 形式存在对话事件日志里。只搜工作区当然找不到，`--latest` 直接从事件日志读。

## 长截图必须切片

整张长图会被缩放，损失往往是**静默**的：模型给出一个自信但错误的数字，而不是报错。
实测一张 1200×6000 的截图，整张读返回 `555.50`，而文件里写的是 `565.50`；把同一区域切片后
读，正确返回 `565.50`。所以凡是要精确文字，先判断再读。

判断分两步，别混为一谈：尺寸只是"要不要细看"的信号，是否真的读不清才是切片的依据。

```bash
python3 scripts/slice_image.py suspect.png --inspect-only
python3 scripts/slice_image.py suspect.png --readability unreadable --mode vertical --output-dir tiles
```

`--mode`：`vertical` 竖长截图、`horizontal` 全景图、`grid` 两向都要切。默认 12% 重叠是为了
不让任何一行卡在接缝上丢掉。读切片时按 `manifest.json` 的顺序逐张看，别因为相邻两块长得像就跳过。

## 安装

把本目录复制到 `~/.openhands/skills/see-images/`，新建对话即自动加载。

## 用法

```bash
python3 <this-skill-path>/scripts/look.py --latest "描述这张图，并逐字转录所有文字"
python3 <this-skill-path>/scripts/look.py a.png b.png "对比这两张图"
python3 <this-skill-path>/scripts/look.py --latest --save out.png "这是什么"
```

## 依赖

- `look.py`：`openai`、`Pillow`、`httpx`
- `slice_image.py`：`Pillow`
- API Key：环境变量 `DEEPSEEK_API_KEY`，或用 `OH_SECRET_KEY` 在内存里解密已有 profile
  （**从不**打印、记录或写盘）

## 文件

| 路径 | 用途 |
| --- | --- |
| `SKILL.md` | 工作流程、提问技巧、切片规则 |
| `scripts/look.py` | 调视觉模型读图 |
| `scripts/slice_image.py` | 检查尺寸信号并生成有序切片 + 阅读顺序清单 |
| `references/deepseek-vision-api.md` | 实测过的请求格式、限制与错误表 |
| `references/finding-chat-images.md` | 聊天图片存在哪、怎么取回 |
