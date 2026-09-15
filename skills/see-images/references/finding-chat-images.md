# Finding an image the user sent in chat

An image a user sends in Agent Canvas is **not** written into the workspace. It is
embedded as a base64 `data:image/...` URL inside the conversation's event JSON at:

    ${OH_CONVERSATIONS_PATH:-$HOME/.openhands/agent-canvas/conversations}/<conv-id>/events/

An agent that only looks at the workspace will correctly report "I can't find the
image" — it never existed there. But the pixels do reach the model, and they can be
recovered.

## Easiest path: let the reader go get it

`look.py --latest` reads the newest image straight out of the event log and sends it
to the vision model. No extraction step, no guessing at paths:

```bash
python3 ~/.openhands/skills/see-images/scripts/look.py --latest "描述这张图"
python3 ~/.openhands/skills/see-images/scripts/look.py --latest --save img.png "图里写了什么"
```

`--save` drops a copy in the workspace, which is what you want when the user should be
able to open or download the file afterward.

## Path-based alternative: the attachments/ mirror

A background daemon also mirrors chat images into the workspace as:

    attachments/event<NNNNN>-<source>-<contenthash>.<ext>

List them with `ls -la attachments/` and pass the path to `look.py`. Files are named by
content hash, so re-sending the same image does not duplicate it. If the folder is
empty or stale, run a sync (idempotent — safe before answering):

```bash
python3 "$HOME/.openhands/agent-canvas/tools/sync_conversation_images.py"           # this conversation
python3 "$HOME/.openhands/agent-canvas/tools/sync_conversation_images.py" --all     # every conversation
python3 "$HOME/.openhands/agent-canvas/tools/sync_conversation_images.py" --wait 15 # tolerate a persistence race
```

`--wait N` polls for up to N seconds, covering the race where the user's message has not
been persisted yet when you first look. Tools live in `~/.openhands/agent-canvas/tools/`,
with a project-local `tools/` copy as fallback. Keep the daemon alive with:

```bash
bash "$HOME/.openhands/agent-canvas/tools/start_image_sync.sh"
```

It is a singleton via pidfile; log at `~/.openhands/agent-canvas/image_sync_watch.log`.

## Notes

- `attachments/` is self-ignoring (it contains its own `.gitignore`) so extracted
  images never get committed into the user's repository.
- Never ask the user to re-send an image before checking `attachments/` and running a
  sync first.
- Do not rely on the conversation's native image pass-through. It is unreliable in
  practice: image blocks are dropped whenever `force_string_serializer` resolves to
  `None` and the model name matches the SDK's `FORCE_STRING_SERIALIZER_MODELS` list
  (which includes `deepseek`). Always route the pixels through `look.py`.
