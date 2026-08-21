# ipyai integration

The file here wires ipyai's kernels to the llmdojo regime, the way `claude/` does for clikernel. It lives in this repo because it must change in lockstep with the code: the imports and aliases it sets up are the ones the dojo round's cells use.

## The file

`startup.py` runs inside every kernel ipyai owns (ipyai executes `~/.config/ipyai/startup.py` at seeding, with `__file__` bound). It imports the standard tooling modules and defines the short aliases the round's `doc()` calls use (`pysk`, `edsk`, `dsk`, `exh`, `rgsk`, `acp`). ipyai's model-facing tool is `py`, not clikernel's `execute`, so there is no `clik` alias here and no printed banner: an ipyai session launched by `ipyaidojo` already has the worked round in its history.

It also installs the session rules (`llmdojo.rules.make_inspector`), applied to the model's cells only: ipyai runs the model's `py` cells with `store_history=False` and the user's typed cells with `True`, so IPython's `pre_run_cell` info tells them apart, and the user's own cells are never inspected. A rule's note prints ahead of the cell's output and so reaches the model inside the tool result; a blocking rule rejects the cell. Doc-state is keyed to the session file: ipyai names the session stem in the kernel's `LLMDOJO_HOST_ID`, and `ipyaidojo` seeds the baked round's doc-state under that key, so a warm session's docs count as read.

## Setup

From the repo root:

    mkdir -p ~/.config/ipyai
    ln -sf "$PWD/ipyai/startup.py" ~/.config/ipyai/

Then `ipyaidojo` starts ipyai with the round in history, and `dojobuild` rebuilds the ipyai store (`dojo_data/ipyai_store/`) beside the Claude and Codex ones.
