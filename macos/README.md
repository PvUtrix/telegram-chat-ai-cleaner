# macOS Finder service: Clean Telegram Chat

`Clean Telegram Chat.workflow` adds **Clean Telegram Chat** to Finder's
right-click menu (Services) for `.json` files. It runs
`tg-analyzer clean --approach privacy --level 2 --format text` on a Telegram
Desktop export and writes `<name>_cleaned.txt` next to it.

## What it does

1. Cleans the chat into one text file.
2. If the result is over 1 MB, asks in a dialog whether to split it into
   1 MB parts (`<name>_cleaned_part001.txt`, ...) or keep one file.
3. Shows a result dialog (**Show in Finder**) or an error dialog with the last
   log lines (**Open Log**). The full log is `/tmp/tg_clean_log.txt`.

The tool renames the export JSON after the chat name and date range while it
parses it; that is expected.

Dialogs are used instead of notifications because macOS silently drops
`display notification` banners posted from a Finder service.

## Install

The service expects this repository at
`/Users/PvUtrix_1/Apps/_Tools/telegram_chat_analyzer` with a virtual
environment in `venv/`. Change the `TOOL=` line in the workflow's shell
script if the repository lives elsewhere.

```bash
cd /Users/PvUtrix_1/Apps/_Tools/telegram_chat_analyzer
/opt/homebrew/opt/python@3.12/bin/python3.12 -m venv venv
venv/bin/pip install -e .
venv/bin/pip install -r requirements.txt
ln -s "$PWD/macos/Clean Telegram Chat.workflow" ~/Library/Services/
/System/Library/CoreServices/pbs -update
```

The service is a symlink to this repository, so the committed copy is the
one that runs: edit it here and commit; there is nothing to copy back.

`requirements.txt` is required: `setup.py` does not list every runtime
dependency (for example `aiohttp`), and without it the CLI fails on import.

## Troubleshooting

- **"virtual environment is missing"**: `venv/` was deleted; rerun the
  install steps above.
- **"bad interpreter"** from a global `tg-analyzer`: Homebrew removed the
  Python it was installed with. The service only uses `venv/bin/tg-analyzer`.
- **Edit the script**: open the workflow in Automator, or replace
  `actions.0.action.ActionParameters.COMMAND_STRING` in
  `Contents/document.wflow` with `plutil -replace`. Automator saves through
  the symlink into this repository; commit the change.
