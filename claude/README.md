# Claude Code integration

The files here wire clikernel's startup to the llmdojo regime. They live in this repo, rather than only in the config location they serve, because they must change in lockstep with the code: the startup text describes behavior that rules.py implements. See DEV.md for how the machinery works.

## The files

`startup.py` runs inside every new kernel (clikernel executes `~/.config/clikernel/startup.py` via `%run -i` at start). In a Python project it imports the standard tooling modules and prints `startup.txt`, which tells the session what to do next: read the module docs if they aren't already in context, list the pyskills, and complete the dojo.

The Claude Code and codex hooks (the SessionStart bootstrap gate, resumption-vs-compaction detection, and the post-compaction doc-state reset via `llmdojo.rules.forget_doced`) live in [aai-coding](https://github.com/AnswerDotAI/aai-coding) as the `aai-hook` CLI, alongside the `persistent-python` and `pyskills` skills.

## Setup

From the repo root:

    mkdir -p ~/.config/clikernel
    ln -sf "$PWD/claude/startup.py" "$PWD/claude/startup.txt" ~/.config/clikernel/

Everything else - hooks, skills, settings - is covered by aai-coding's SETUP.md.
