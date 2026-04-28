"""
ISD String SDK — Professional GUI Workbench
============================================
Entry point.  Tab implementations live in:
  gui/_tab_cleaning.py
  gui/_tab_matching.py
  gui/_tab_tdd.py
Shared tokens, factories, dialogs → gui/_shared.py

Authors : 周暘恩, Anthony Chou

Run:
    .venv\\Scripts\\python.exe gui\\testing_app.py
or  (with venv activated):
    python gui\\testing_app.py
"""
from __future__ import annotations

import sys
import os

# DPI awareness on Windows
try:
    from ctypes import windll
    windll.shcore.SetProcessDpiAwareness(1)
except Exception:
    pass

import tkinter as tk
from tkinter import ttk

# Allow `from gui._shared import ...` etc.
_repo_root = os.path.normpath(os.path.join(os.path.dirname(__file__), ".."))
if _repo_root not in sys.path:
    sys.path.insert(0, _repo_root)

from gui._shared import (
    C, F_H1, F_SMALL,
    SDK_OK, SDK_ERROR,
    NOPARS_STRATEGY_TABLE, CLEANING_PARS_TABLE, MATCHING_TABLE,
    apply_style,
)
from gui._tab_cleaning import CleaningTab
from gui._tab_matching import MatchingTab
from gui._tab_tdd      import TDDTab


class App(tk.Tk):

    def __init__(self) -> None:
        super().__init__()
        self.title("ISD String SDK  —  Workbench")
        self.geometry("1300x780")
        self.minsize(920, 620)
        self.configure(bg=C["hdr_bg"])
        apply_style(self)
        self._build()

    def _build(self) -> None:
        # Banner
        banner = tk.Frame(self, bg=C["hdr_bg"])
        banner.pack(fill="x")
        tk.Label(banner, text="ISD String SDK Workbench",
                 font=F_H1, bg=C["hdr_bg"], fg="#ffffff",
                 padx=18, pady=10).pack(side="left")

        if not SDK_OK:
            tk.Label(banner, text=f"⚠  SDK import error: {SDK_ERROR}",
                     font=F_SMALL, bg=C["hdr_bg"], fg=C["warning"],
                     wraplength=600).pack(side="left", padx=12)
        else:
            n_clean = len(NOPARS_STRATEGY_TABLE) + len(CLEANING_PARS_TABLE)
            n_match = len(MATCHING_TABLE)
            tk.Label(banner,
                     text=f"{n_clean} cleaning functions  ·  {n_match} matching strategies",
                     font=F_SMALL, bg=C["hdr_bg"], fg="#a5b4fc").pack(side="left", padx=12)

        tk.Label(banner, text="Authors: 周暘恩, Anthony Chou",
                 font=F_SMALL, bg=C["hdr_bg"], fg="#6366f1").pack(side="right", padx=16)

        # Notebook
        nb = ttk.Notebook(self)
        nb.pack(fill="both", expand=True)
        nb.add(CleaningTab(nb), text="  🧹  Cleaning Lab  ")
        nb.add(MatchingTab(nb), text="  🔍  Matching Lab  ")
        nb.add(TDDTab(nb),      text="  🧪  TDD Workbench  ")


if __name__ == "__main__":
    App().mainloop()
