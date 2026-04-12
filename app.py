from __future__ import annotations

import sys

from src.cli_v35 import main as cli_main


def _is_gui_mode(argv: list[str]) -> bool:
    return "--gui" in argv


if __name__ == "__main__":
    args = sys.argv[1:]
    if _is_gui_mode(args):
        from src.gui.app import start_gui

        args = [arg for arg in args if arg != "--gui"]
        raise SystemExit(start_gui(args))
    raise SystemExit(cli_main(args))
