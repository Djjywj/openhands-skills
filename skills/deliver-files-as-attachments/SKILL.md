---
name: deliver-files-as-attachments
description: This skill should be used whenever a task creates, generates, writes, modifies, converts, compiles, renders, or exports a file the user needs - including reports, documents, spreadsheets, PDFs, slide decks, images, charts, datasets, archives, certificates, and code bundles. Trigger phrases include "generate a report", "export as CSV/PDF/Excel", "save the output", "create a document", "download the file", "give me the file", "打包下载", "生成文件", "导出文件", "下载文件", "生成报告", "保存为文件", "把结果给我". It makes deliverables persist as real workspace files offered for download, instead of only being printed in chat.
triggers:
- attachment
- download
- export
- save to file
- generate file
- deliverable
- 附件
- 下载
- 导出
- 生成文件
- 保存文件
- 打包
---

# Deliver Files as Downloadable Attachments

## Purpose

When a task produces an artifact the user needs, persist it as a real file in the conversation
workspace and present it for download. Never satisfy a file request by printing the content in chat
only. A user who asks for a report, export, document, dataset, or archive expects a file they can
open, keep, and share - not a wall of text.

## When this applies

Activate this behavior whenever any of the following happen:

- The user asks to generate, create, export, convert, render, compile, build, or save a file.
- The task modifies an existing user file and the user needs the updated version.
- A command or tool writes output files (exports, build artifacts, screenshots, charts, logs, archives, backups).
- The result is large, binary, or meant to be opened in another application.

## Core rules

1. **Persist every deliverable to a file.** Write the artifact to disk with `file_editor` (preferred
   for text) or a command/tool that produces an output file. Printing the content in the reply is not
   a deliverable.
2. **Write inside the conversation workspace.** The workspace is the directory shown in the Files tab
   of the UI (the conversation's working directory, for example `/workspace/project`). Files written
   only to `/tmp`, `$HOME`, or another location outside the workspace are invisible to the user. Copy
   them into the workspace before reporting.
3. **Use a clear, stable path.** Default to the workspace root or an `output/` (or `dist/`) subfolder.
   Preserve any path or filename the user specified. Prefer ASCII, hyphenated names without spaces.
4. **Verify before reporting.** Confirm each file exists and is non-empty (`ls -la`, `stat`, `file`).
   For structured formats, sanity-check that the file parses or opens.
5. **Report downloads, not contents.** Present a short delivery block listing each file with its name,
   absolute path, size, and how to download it. Summarize what changed. Include only a short excerpt
   when the user asks for it or when it confirms correctness.
6. **List every file touched.** Report all created and modified files, not just the primary one. If
   there are many, group them or bundle them into one archive.

## Delivery block

End the task with a block like this:

```
Deliverables
- report.pdf  (1.2 MB)
  Path: /workspace/project/report.pdf
- data.csv  (84 KB)
  Path: /workspace/project/output/data.csv
Bundle: /workspace/project/output/bundle.zip  (1.3 MB)
To download: open the Files tab in Agent Canvas and select the file, then choose Download.
```

Include a clickable markdown link only when the environment provides a URL that works with the user's
existing session and does not require an embedded API key.

## Downloading in Agent Canvas

Deliverables written to the conversation workspace are listed in the Files tab, which provides
open/download controls. Markdown files additionally render as an inline preview with a "View" action.
The Files tab is the default and most reliable download path for every file type.

Verified backend routes (for reference):

| Route | Auth | Behavior |
| --- | --- | --- |
| `GET /api/file/download?path=<absolute-path>` | `X-Session-API-Key` | Returns the file with `Content-Disposition: attachment` (true download). |
| `GET /api/conversations/<conversation_id>/workspace/<relative-path>` | API key or cookie `oh_workspace_session_key` | Serves the workspace file inline. |
| `GET /api/v1/app-conversations/<app_conversation_id>/file?file_path=<absolute-path>` | session auth | Returns file content as JSON for previews. |

A relative link such as `/api/conversations/<conversation_id>/workspace/<relative-path>` may work in a
browser when the agent server shares the UI origin and accepts the session cookie. Verify it before
sharing. Never embed session keys, tokens, or credentials in a download link. When no key-free URL is
available, give the absolute path and tell the user to use the Files tab.

### Most reliable: serve the workspace over a host-mapped port

The Files tab is not always visible to the user, and the API routes above either need the session key
(401 without it) or return previews instead of downloads. When the user cannot find the Files tab or a
link "does nothing", serve the deliverable directory over a **container port that Agent Canvas maps to
a user-reachable host port**:

1. Find the port mapping. The repo context advertises it as `work_hosts`, e.g.
   `http://localhost:41757 (port 8011)` means container port 8011 is reachable at
   `http://localhost:41757`. If no mapping is advertised, list listening ports
   (`ss -ltnp`) and probe `http://host.docker.internal:<port>` to find a reachable one.
2. Put ASCII-named copies of each deliverable in a `download/` subfolder (avoid CJK/spaces in
   filenames, which break some download flows).
3. Start a static server on the container port (background it) and confirm it locally:

   ```bash
   python3 scripts/serve_deliverables.py --dir /workspace/project \
       --container-port 8011 --host-port 41757 \
       --files dmhyy_rule.json dmhyy_miniapp.zip dmhyy_kouling.txt \
       --background
   ```

   Or manually: `cd /workspace/project && nohup python3 -m http.server 8011 --bind 0.0.0.0 &`.
4. Verify from the agent side before reporting:
   `curl -sI http://host.docker.internal:41757/download/dmhyy_rule.json` (expect HTTP 200).
5. Give the user the landing-page URL (`http://localhost:41757/download/`) plus one direct link per
   file.

**Delivery preference (default): one direct link per file, never a combined page or bundle.**
Unless the user explicitly asks for an archive or a landing page:
- Do **not** generate a summary `index.html` listing several files.
- Do **not** zip the deliverables into a single bundle as the primary download.
- List each file with its own direct URL, most important first.

Notes and gotchas:

- The server runs inside the sandbox; it stops when the conversation/sandbox stops. Tell the user it is
  temporary, and that re-running the command restarts it.
- Do **not** use `python3 -m http.server` on port 3000 (the UI origin) — it is already in use. Use the
  mapped port instead.
- Prefer the mapped port the context calls a "web application" host; those are the ports the user can
  actually open.
- Always verify each link with `curl -I` first. A link you did not test is worse than no link.

## Bulk outputs and archives

> Note: prefer individual direct links by default (see "Delivery preference" above). Only build a
> single archive/bundle when the user explicitly asks for one.

When a task produces multiple related files or a directory tree, create one archive (`.zip` or
`.tar.gz`) and deliver it as the primary attachment, then list the individual paths. Use
`scripts/delivery_manifest.py` to verify files, optionally build an archive, and print a consistent
delivery block:

```bash
python3 scripts/delivery_manifest.py <path> [<path> ...] [--archive <archive-path>]
```

## Security

- Only deliver files the task actually produced for the user.
- Do not attach secrets, credentials, `.env` files, or private keys unless the user explicitly asked.
- Do not upload the file anywhere the user did not request.

## Examples

- "Generate a CSV of the last 30 days of orders." -> Write `orders.csv`, verify it, report its path and
  size; do not paste all rows.
- "Turn this Markdown into a PDF." -> Produce `document.pdf`, verify it with `file`, report the path.
- "Export the query results." -> Determine the requested format, write the file, report the path; if
  the format is unclear, pick a sensible default and say so.
- "Here is my script, make it work." -> Update the script file, run it, and report both the modified
  script and any output files it generated.

## Additional resources

- `scripts/delivery_manifest.py` - verify deliverables, optionally build an archive, and print a
  consistent delivery block.
- `scripts/serve_deliverables.py` - serve a directory over a host-mapped container port and print a
  key-free landing page plus direct download links (see "Most reliable" above).
