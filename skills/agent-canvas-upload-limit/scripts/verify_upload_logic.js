/**
 * 直接拿磁盘上真正会被浏览器加载的那个 bundle，抽出上传校验函数跑用例。
 * 脚本自己从 bundle 里解析出上限常量，所以打补丁前后都能跑：
 *   node verify_upload_logic.js            # 验当前文件
 *   node verify_upload_logic.js --expect-patched   # 断言确实已解除 3MB 限制
 * 退出码 0 = 全部通过。
 */
const fs = require("fs");
const path = require("path");

const ASSETS = "/opt/agent-canvas/frontend/assets";
const expectPatched = process.argv.includes("--expect-patched");

function findBundle() {
  const hits = fs
    .readdirSync(ASSETS)
    .filter((f) => f.startsWith("llm-not-configured-banner-") && f.endsWith(".js"))
    .map((f) => path.join(ASSETS, f));
  for (const p of hits) {
    const t = fs.readFileSync(p, "utf8");
    if (/Mr=\d/.test(t)) return { file: p, text: t };
  }
  throw new Error(`在 ${ASSETS} 里找不到含上传上限常量的 bundle`);
}

/** 按大括号配对切出一个函数的源码，避免把整个 bundle eval 进来。 */
function cutFunction(text, start) {
  const head = text.indexOf("function ", start);
  if (head < 0) throw new Error("找不到函数定义");
  let depth = 0;
  for (let i = text.indexOf("{", head); i < text.length; i++) {
    if (text[i] === "{") depth++;
    else if (text[i] === "}") {
      if (--depth === 0) return { src: text.slice(head, i + 1), end: i + 1 };
    }
  }
  throw new Error("函数大括号没闭合");
}

function loadLimits() {
  const { file, text } = findBundle();
  const m = text.match(/Mr=([0-9.e+*\s]+),Nr=([0-9.e+*\s]+);/);
  if (!m) throw new Error("bundle 里的 Mr/Nr 常量格式不认识");
  const consts = `Mr=${m[1]},Nr=${m[2]};`;
  const pr = cutFunction(text, text.indexOf(m[0]));
  const fr = cutFunction(text, pr.end);
  // eslint-disable-next-line no-new-func
  const factory = new Function(
    `${consts}${pr.src}${fr.src}return {Pr, Fr, Mr, Nr};`
  );
  return { file, ...factory() };
}

const { file, Pr, Fr, Mr, Nr } = loadLimits();
const MB = 1024 * 1024;
const mb = (n) => n * MB;
const f = (name, size) => ({ name, size });

let failed = 0;
const results = [];
function check(label, got, wantValid) {
  const ok = got.isValid === wantValid;
  if (!ok) failed++;
  results.push(
    `${ok ? "PASS" : "FAIL"}  ${label} -> ${
      got.isValid ? "通过" : "拒绝：" + got.errorMessage
    }`
  );
}

console.log(`目标文件：${file}`);
console.log(`解析出的上限：单文件 Mr=${Mr}（${(Mr / MB).toFixed(1)}MB），合计 Nr=${Nr} 字节\n`);

check("3MB 单个文件", Pr([f("a.bin", mb(3))]), Mr >= 3 * MB);
check("9.4MB 单个文件", Pr([f("a.bin", 9.4 * mb(1))]), Mr >= 9.4 * MB);
check("300MB 单个文件", Pr([f("a.bin", mb(300))]), Mr >= 300 * MB);
check("刚好等于单文件上限", Pr([f("a.bin", Mr)]), true);
check("超出单文件上限 1 字节", Pr([f("big.bin", Mr + 1)]), false);
check(
  "合计 1.5GB",
  Fr([f("a", mb(800)), f("b", mb(700))], []),
  Nr >= mb(1500)
);
check("刚好等于合计上限", Fr([f("a", Nr)], []), true);
check("超出合计上限 1 字节", Fr([f("a", Nr + 1)], []), false);

// 已经上传的文件也要计入合计（第二个参数是既有文件）
check(
  "新文件 + 已存在文件超过合计上限",
  Fr([f("new", mb(600))], [f("old", Nr)], []),
  false
);

for (const r of results) console.log(r);

if (expectPatched) {
  const assert = (label, cond) => {
    if (!cond) {
      failed++;
      console.log(`FAIL  ${label}`);
    } else {
      console.log(`PASS  ${label}`);
    }
  };
  assert("单文件上限已大于 3MB", Mr > 3 * MB);
  assert("单文件上限为 500MB", Mr === 5e8);
  assert("提示文案已是 500MB", /Files over 500MB are not allowed/.test(fs.readFileSync(file, "utf8")));
  assert("旧文案 3MB 已消失", !/exceeding 3MB are not allowed/.test(fs.readFileSync(file, "utf8")));
}

if (failed) {
  console.log(`\n有 ${failed} 项未通过`);
  process.exit(1);
}
console.log("\n全部通过");
