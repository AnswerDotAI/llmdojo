# Claude Code integration

The files here wire Claude Code up to a clikernel workbench running the llmdojo regime. They live in this repo, rather than only in the config locations they serve, because they must change in lockstep with the code: the hook imports `llmdojo.rules`, and both the hook messages and the startup text describe behavior that rules.py implements. See DEV.md for how the machinery works.

## The files

`startup.py` runs inside every new kernel (clikernel executes `~/.config/clikernel/startup.py` via `%run -i` at start). In a Python project it imports the standard tooling modules and prints `startup.txt`, which tells the session what to do next: read the module docs if they aren't already in context, list the pyskills, and complete the dojo.

`python-project-bootstrap.sh` is a Claude Code SessionStart hook. In a Python project it prints the bootstrap gate (no file access before the skills and the dojo). It also reads the transcript to tell resumption apart from compaction, prints a message saying exactly which state survived, and after a compaction resets the persisted doc-state record via `llmdojo.rules.forget_doced` so doc notes re-fire.

## Setup

You need clikernel and its tooling ecosystem installed (pyskills, exhash, rgapi, and friends), and the `coding-patterns` and `persistent-python` skills from [skill-plugins](https://github.com/AnswerDotAI/skill-plugins) in `~/.claude/skills`.

From the repo root:

    mkdir -p ~/.config/clikernel ~/.claude/hooks
    ln -sf "$PWD/claude/startup.py" "$PWD/claude/startup.txt" ~/.config/clikernel/
    ln -sf "$PWD/claude/python-project-bootstrap.sh" ~/.claude/hooks/

Then register the hook in `~/.claude/settings.json` (that file stays personal and unversioned), merging into any existing `hooks` key:

    "hooks": {
      "SessionStart": [
        {"hooks": [{"type": "command", "command": "/absolute/path/to/home/.claude/hooks/python-project-bootstrap.sh"}]}
      ]
    }

Settings load at startup, so the hook takes effect from the next session.
