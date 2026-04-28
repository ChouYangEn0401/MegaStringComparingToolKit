"""
ISD String SDK — Professional GUI Workbench
============================================
Tab 1 │ Cleaning Lab    — paste text or load CSV / Excel
                         → build a cleaning chain → process
Tab 2 │ Matching Lab    — compare two string lists with any strategy
Tab 3 │ TDD Workbench   — design & run tests for undone / in-progress strategies

Authors : 周暘恩, Anthony Chou
"""
from __future__ import annotations

import os
import sys
import threading
import traceback
from typing import Any, Dict, List, Optional, Tuple

import tkinter as tk
from tkinter import ttk, filedialog, messagebox

# ── DPI awareness on Windows ─────────────────────────────────────────────────
try:
    from ctypes import windll
    windll.shcore.SetProcessDpiAwareness(1)
except Exception:
    pass

# ── pandas ────────────────────────────────────────────────────────────────────
try:
    import pandas as pd
    PANDAS_OK = True
except ImportError:
    pd = None  # type: ignore
    PANDAS_OK = False

# ── SDK path ──────────────────────────────────────────────────────────────────
_sdk_root = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "src"))
if _sdk_root not in sys.path:
    sys.path.insert(0, _sdk_root)

try:
    from isd_str_sdk.str_cleaning import (
        CleaningStrategyAdapter,
        NOPARS_STRATEGY_TABLE,
        STRATEGY_TABLE as CLEANING_PARS_TABLE,
    )
    from isd_str_sdk.base.StrProcessorsChain import StrProcessorsChain  # noqa: F401
    from isd_str_sdk.str_matching import match as sdk_match
    from isd_str_sdk.str_matching.adapters import (
        MatchingStrategyAdapter,
        STRATEGY_TABLE as MATCHING_TABLE,
    )
    from isd_str_sdk.TDD.run_strategy_tests import run_strategy_test  # noqa: F401
    from isd_str_sdk.core.contexts import TwoSeriesComparisonContext
    SDK_OK = True
    SDK_ERROR = ""
except ImportError as _e:
    SDK_OK = False
    SDK_ERROR = str(_e)
    NOPARS_STRATEGY_TABLE = {}
    CLEANING_PARS_TABLE = {}
    MATCHING_TABLE = {}

# ─────────────────────────────────────────────────────────────────────────────
#  Design tokens
# ─────────────────────────────────────────────────────────────────────────────
C: Dict[str, str] = {
    "bg":         "#f0f4f8",
    "surface":    "#ffffff",
    "surface2":   "#f7f9fc",
    "border":     "#dde3ec",
    "accent":     "#4f46e5",
    "accent_lt":  "#ede9fe",
    "accent_dk":  "#3730a3",
    "text":       "#1e293b",
    "text_muted": "#64748b",
    "success":    "#10b981",
    "success_bg": "#d1fae5",
    "danger":     "#ef4444",
    "danger_bg":  "#fee2e2",
    "warning":    "#f59e0b",
    "warning_bg": "#fef3c7",
    "hdr_bg":     "#1e1b4b",
    "hdr_fg":     "#ffffff",
    "undone_bg":  "#fef3c7",
    "undone_fg":  "#92400e",
}

F_MONO  = ("Consolas", 10)
F_BODY  = ("Segoe UI", 10)
F_BOLD  = ("Segoe UI", 10, "bold")
F_H1    = ("Segoe UI", 15, "bold")
F_H2    = ("Segoe UI", 11, "bold")
F_SMALL = ("Segoe UI", 9)
F_CODE  = ("Consolas", 9)


# ─────────────────────────────────────────────────────────────────────────────
#  Style
# ─────────────────────────────────────────────────────────────────────────────

def _apply_style(root: tk.Tk) -> None:
    s = ttk.Style(root)
    s.theme_use("clam")

    s.configure(".", background=C["bg"], foreground=C["text"], font=F_BODY)
    s.configure("TFrame",         background=C["bg"])
    s.configure("TLabel",         background=C["bg"], foreground=C["text"])

    # Notebook
    s.configure("TNotebook",
                background=C["hdr_bg"], borderwidth=0, tabmargins=[0, 0, 0, 0])
    s.configure("TNotebook.Tab",
                background=C["hdr_bg"], foreground="#a5b4fc",
                padding=[20, 9], font=F_BOLD)
    s.map("TNotebook.Tab",
          background=[("selected", C["accent"]), ("active", "#312e81")],
          foreground=[("selected", "#ffffff"),  ("active", "#c7d2fe")])

    # LabelFrame
    s.configure("TLabelframe",
                background=C["surface"], bordercolor=C["border"],
                relief="solid", borderwidth=1)
    s.configure("TLabelframe.Label",
                background=C["surface"], foreground=C["accent"], font=F_BOLD)

    # Buttons
    s.configure("Accent.TButton",
                background=C["accent"], foreground="#ffffff",
                font=F_BOLD, padding=[12, 5], relief="flat", borderwidth=0)
    s.map("Accent.TButton",
          background=[("active", C["accent_dk"]), ("disabled", "#94a3b8")])

    s.configure("Danger.TButton",
                background=C["danger"], foreground="#ffffff",
                font=F_BOLD, padding=[8, 4], relief="flat", borderwidth=0)
    s.map("Danger.TButton",
          background=[("active", "#b91c1c")])

    s.configure("TButton",
                background=C["surface"], foreground=C["text"],
                font=F_BODY, padding=[8, 4], relief="flat",
                borderwidth=1, bordercolor=C["border"])
    s.map("TButton",
          background=[("active", C["accent_lt"])],
          bordercolor=[("active", C["accent"])])

    # Entry / Combobox
    for w in ("TCombobox", "TEntry"):
        s.configure(w, fieldbackground=C["surface"], background=C["surface"],
                    foreground=C["text"], bordercolor=C["border"],
                    selectbackground=C["accent_lt"], selectforeground=C["accent_dk"])

    # Treeview
    s.configure("Treeview",
                background=C["surface"], foreground=C["text"],
                fieldbackground=C["surface"], rowheight=26, font=F_BODY)
    s.configure("Treeview.Heading",
                background=C["surface2"], foreground=C["text"],
                font=F_BOLD, relief="flat")
    s.map("Treeview",
          background=[("selected", C["accent_lt"])],
          foreground=[("selected", C["accent_dk"])])

    # Scrollbar
    for orient in ("Vertical", "Horizontal"):
        s.configure(f"{orient}.TScrollbar",
                    background=C["border"], troughcolor=C["surface2"],
                    arrowcolor=C["text_muted"])

    s.configure("TScale", background=C["bg"], troughcolor=C["border"], sliderlength=14)


# ─────────────────────────────────────────────────────────────────────────────
#  Widget factories   (callers own placement — no auto pack/grid)
# ─────────────────────────────────────────────────────────────────────────────

def make_code_editor(parent: tk.Widget, height: int = 8) -> Tuple[tk.Frame, tk.Text]:
    """Return (wrapper_frame, text_widget). Caller must place wrapper_frame."""
    wrapper = tk.Frame(parent, bg=C["border"], bd=1)
    wrapper.rowconfigure(0, weight=1)
    wrapper.columnconfigure(0, weight=1)
    t = tk.Text(
        wrapper, wrap="none", font=F_MONO, height=height,
        bg=C["surface"], fg=C["text"], insertbackground=C["accent"],
        relief="flat", bd=0, padx=8, pady=6, undo=True,
        selectbackground=C["accent_lt"], selectforeground=C["accent_dk"],
    )
    vsb = ttk.Scrollbar(wrapper, orient="vertical",   command=t.yview)
    hsb = ttk.Scrollbar(wrapper, orient="horizontal", command=t.xview)
    t.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
    t.grid(row=0, column=0, sticky="nsew")
    vsb.grid(row=0, column=1, sticky="ns")
    hsb.grid(row=1, column=0, sticky="ew")
    return wrapper, t


def make_treeview(
    parent: tk.Widget,
    columns: Tuple[str, ...],
    col_widths: Optional[Dict[str, int]] = None,
    col_anchors: Optional[Dict[str, str]] = None,
    show: str = "headings",
) -> Tuple[tk.Frame, ttk.Treeview]:
    """Return (wrapper_frame, treeview). Caller must place wrapper_frame."""
    wrapper = tk.Frame(parent, bg=C["border"], bd=1)
    wrapper.rowconfigure(0, weight=1)
    wrapper.columnconfigure(0, weight=1)
    tv = ttk.Treeview(wrapper, columns=columns, show=show)
    vsb = ttk.Scrollbar(wrapper, orient="vertical",   command=tv.yview)
    hsb = ttk.Scrollbar(wrapper, orient="horizontal", command=tv.xview)
    tv.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
    tv.grid(row=0, column=0, sticky="nsew")
    vsb.grid(row=0, column=1, sticky="ns")
    hsb.grid(row=1, column=0, sticky="ew")
    for col in columns:
        w = (col_widths  or {}).get(col, 150)
        a = (col_anchors or {}).get(col, "w")
        tv.heading(col, text=col)
        tv.column(col, width=w, minwidth=50, anchor=a)
    return wrapper, tv


def make_listbox(parent: tk.Widget, height: int = 8) -> Tuple[tk.Frame, tk.Listbox]:
    """Return (wrapper_frame, listbox). Caller must place wrapper_frame."""
    wrapper = tk.Frame(parent, bg=C["border"], bd=1)
    wrapper.rowconfigure(0, weight=1)
    wrapper.columnconfigure(0, weight=1)
    lb = tk.Listbox(wrapper, font=F_BODY, relief="flat", bd=0, height=height,
                    bg=C["surface"], fg=C["text"], activestyle="none",
                    selectmode="single",
                    selectbackground=C["accent_lt"], selectforeground=C["accent_dk"])
    vsb = ttk.Scrollbar(wrapper, orient="vertical", command=lb.yview)
    lb.configure(yscrollcommand=vsb.set)
    lb.grid(row=0, column=0, sticky="nsew")
    vsb.grid(row=0, column=1, sticky="ns")
    return wrapper, lb


def hdr_label(parent: tk.Widget, text: str) -> None:
    tk.Label(parent, text=text, font=F_H2,
             bg=C["hdr_bg"], fg=C["hdr_fg"], anchor="w", padx=12, pady=8).pack(fill="x")


def section_sep(parent: tk.Widget, padx: int = 8) -> None:
    tk.Frame(parent, bg=C["border"], height=1).pack(fill="x", padx=padx, pady=4)


# ─────────────────────────────────────────────────────────────────────────────
#  Dialogs
# ─────────────────────────────────────────────────────────────────────────────

class ParamDialog(tk.Toplevel):
    """Collect comma-separated params for a parameterised cleaning strategy."""

    def __init__(self, parent: tk.Widget, strategy_name: str) -> None:
        super().__init__(parent)
        self.title(f"Configure — {strategy_name}")
        self.configure(bg=C["bg"])
        self.resizable(False, False)
        self.result: Optional[List[str]] = None

        tk.Label(self, text="Parameters  (comma-separated)", font=F_BOLD,
                 bg=C["bg"], fg=C["text"]).pack(padx=16, pady=(12, 2))
        tk.Label(self, text="Example:  @, #, !  or  hello, world",
                 font=F_SMALL, bg=C["bg"], fg=C["text_muted"]).pack(padx=16)
        self._entry = ttk.Entry(self, width=40, font=F_BODY)
        self._entry.pack(padx=16, pady=8)
        self._entry.focus_set()
        self._entry.bind("<Return>", lambda _: self._ok())

        row = tk.Frame(self, bg=C["bg"])
        row.pack(pady=(0, 12))
        ttk.Button(row, text="OK",     style="Accent.TButton", command=self._ok).pack(side="left", padx=4)
        ttk.Button(row, text="Cancel", command=self.destroy).pack(side="left", padx=4)
        self.grab_set()
        self.wait_window()

    def _ok(self) -> None:
        raw = self._entry.get().strip()
        self.result = [p.strip() for p in raw.split(",") if p.strip()] if raw else []
        self.destroy()


class ColumnPickerDialog(tk.Toplevel):
    """Pick one column name from a list."""

    def __init__(self, parent: tk.Widget, columns: List[str]) -> None:
        super().__init__(parent)
        self.title("Select Column")
        self.configure(bg=C["bg"])
        self.resizable(False, False)
        self.result: Optional[str] = None
        self._var = tk.StringVar(value=columns[0] if columns else "")

        tk.Label(self, text="Select column to import:", font=F_BOLD,
                 bg=C["bg"], fg=C["text"]).pack(padx=16, pady=(12, 4))
        ttk.Combobox(self, values=columns, textvariable=self._var,
                     state="readonly", font=F_BODY, width=24).pack(padx=16, pady=4)
        row = tk.Frame(self, bg=C["bg"])
        row.pack(pady=(4, 12))
        ttk.Button(row, text="OK",     style="Accent.TButton", command=self._ok).pack(side="left", padx=4)
        ttk.Button(row, text="Cancel", command=self.destroy).pack(side="left", padx=4)
        self.grab_set()
        self.wait_window()

    def _ok(self) -> None:
        self.result = self._var.get()
        self.destroy()


# ─────────────────────────────────────────────────────────────────────────────
#  Tab 1 — Cleaning Lab
# ─────────────────────────────────────────────────────────────────────────────

class CleaningTab(ttk.Frame):

    def __init__(self, notebook: ttk.Notebook) -> None:
        super().__init__(notebook)
        self._df: Optional[Any] = None
        self._file_path: str = ""
        self._mode = tk.StringVar(value="text")
        self._chain: List[Tuple[str, str, Optional[List[str]]]] = []
        self._result_data: List[Tuple[str, str]] = []
        self._build()

    # ─────────────────────────────────────────────────────────────────────────

    def _build(self) -> None:
        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=3, minsize=260)
        self.columnconfigure(1, weight=2, minsize=220)
        self.columnconfigure(2, weight=4, minsize=300)

        self._input_panel  = tk.Frame(self, bg=C["surface"])
        self._chain_panel  = tk.Frame(self, bg=C["bg"])
        self._output_panel = tk.Frame(self, bg=C["surface"])
        self._input_panel.grid( row=0, column=0, sticky="nsew", padx=(0, 1))
        self._chain_panel.grid( row=0, column=1, sticky="nsew", padx=1)
        self._output_panel.grid(row=0, column=2, sticky="nsew", padx=(1, 0))

        self._build_input()
        self._build_chain()
        self._build_output()

    # ── Input panel ───────────────────────────────────────────────────────────

    def _build_input(self) -> None:
        p = self._input_panel
        p.columnconfigure(0, weight=1)
        p.rowconfigure(2, weight=1)  # text frame
        p.rowconfigure(3, weight=1)  # file frame

        tk.Label(p, text="① Input", font=F_H2,
                 bg=C["hdr_bg"], fg=C["hdr_fg"], anchor="w", padx=12, pady=8
                 ).grid(row=0, column=0, sticky="ew")

        # Mode selector
        mode_bar = tk.Frame(p, bg=C["surface"])
        mode_bar.grid(row=1, column=0, sticky="ew", padx=8, pady=(6, 0))
        tk.Label(mode_bar, text="Mode:", font=F_BOLD,
                 bg=C["surface"], fg=C["text_muted"]).pack(side="left")
        for val, txt in (("text", "  ✏  Text  "), ("file", "  📂  File  ")):
            tk.Radiobutton(
                mode_bar, text=txt, variable=self._mode, value=val,
                command=self._on_mode_change,
                bg=C["surface"], fg=C["text"], activebackground=C["accent_lt"],
                selectcolor=C["accent_lt"], font=F_BODY, relief="flat", cursor="hand2",
            ).pack(side="left", padx=3)

        # ─ Text mode ─────────────────────────────────────────────────────────
        self._text_frame = tk.Frame(p, bg=C["surface"])
        self._text_frame.grid(row=2, column=0, sticky="nsew", padx=8, pady=6)
        self._text_frame.rowconfigure(1, weight=1)
        self._text_frame.columnconfigure(0, weight=1)

        tk.Label(self._text_frame, text="Paste your text below:", font=F_BOLD,
                 bg=C["surface"], fg=C["text_muted"], anchor="w").grid(
                     row=0, column=0, sticky="w")
        ed_wrap, self._input_text = make_code_editor(self._text_frame, height=16)
        ed_wrap.grid(row=1, column=0, sticky="nsew")

        # ─ File mode ─────────────────────────────────────────────────────────
        self._file_frame = tk.Frame(p, bg=C["surface"])
        self._file_frame.grid(row=3, column=0, sticky="nsew", padx=8, pady=6)
        self._file_frame.rowconfigure(5, weight=1)
        self._file_frame.columnconfigure(1, weight=1)

        tk.Button(
            self._file_frame, text="  📂  Load File (CSV / Excel)", font=F_BOLD,
            bg=C["accent"], fg="#fff", relief="flat", cursor="hand2",
            activebackground=C["accent_dk"], command=self._load_file,
        ).grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 6))

        tk.Label(self._file_frame, text="File:", font=F_SMALL,
                 bg=C["surface"], fg=C["text_muted"]).grid(row=1, column=0, sticky="w", pady=2)
        self._file_lbl = tk.Label(self._file_frame, text="(no file loaded)",
                                   font=F_CODE, bg=C["surface2"], fg=C["text_muted"],
                                   anchor="w", relief="flat", padx=4)
        self._file_lbl.grid(row=1, column=1, sticky="ew", pady=2)

        tk.Label(self._file_frame, text="Sheet:", font=F_BOLD,
                 bg=C["surface"], fg=C["text"]).grid(row=2, column=0, sticky="w", pady=3)
        self._sheet_combo = ttk.Combobox(self._file_frame, state="disabled", font=F_BODY)
        self._sheet_combo.grid(row=2, column=1, sticky="ew", pady=3)
        self._sheet_combo.bind("<<ComboboxSelected>>", self._on_sheet_change)

        tk.Label(self._file_frame, text="Column:", font=F_BOLD,
                 bg=C["surface"], fg=C["text"]).grid(row=3, column=0, sticky="w", pady=3)
        self._col_combo = ttk.Combobox(self._file_frame, state="disabled", font=F_BODY)
        self._col_combo.grid(row=3, column=1, sticky="ew", pady=3)
        self._col_combo.bind("<<ComboboxSelected>>", lambda _: self._update_preview())

        tk.Label(self._file_frame, text="Preview (first 5 rows):", font=F_BOLD,
                 bg=C["surface"], fg=C["text_muted"]).grid(row=4, column=0, columnspan=2,
                                                             sticky="w", pady=(6, 2))
        prev_wrap, self._preview_tv = make_treeview(
            self._file_frame, ("row", "value"),
            col_widths={"row": 46, "value": 260},
            col_anchors={"row": "center"},
        )
        prev_wrap.grid(row=5, column=0, columnspan=2, sticky="nsew")

        self._on_mode_change()

    # ── Chain panel ───────────────────────────────────────────────────────────

    def _build_chain(self) -> None:
        p = self._chain_panel
        p.columnconfigure(0, weight=1)
        p.rowconfigure(2, weight=2)
        p.rowconfigure(5, weight=3)

        tk.Label(p, text="② Chain Builder", font=F_H2,
                 bg=C["hdr_bg"], fg=C["hdr_fg"], anchor="w", padx=12, pady=8
                 ).grid(row=0, column=0, sticky="ew")

        # Search bar
        srow = tk.Frame(p, bg=C["bg"])
        srow.grid(row=1, column=0, sticky="ew", padx=8, pady=(8, 2))
        tk.Label(srow, text="Available:", font=F_SMALL,
                 bg=C["bg"], fg=C["text_muted"]).pack(side="left")
        tk.Label(srow, text="🔍", bg=C["bg"]).pack(side="right")
        self._search_var = tk.StringVar()
        self._search_var.trace_add("write", lambda *_: self._populate_available())
        ttk.Entry(srow, textvariable=self._search_var, width=14, font=F_BODY).pack(
            side="right", padx=2)

        av_wrap, self._avail_lb = make_listbox(p, height=9)
        av_wrap.grid(row=2, column=0, sticky="nsew", padx=8, pady=(0, 4))
        self._avail_lb.bind("<Double-Button-1>", lambda _: self._add_to_chain())

        tb = tk.Frame(p, bg=C["bg"])
        tb.grid(row=3, column=0, pady=2)
        ttk.Button(tb, text="Add ↓",  style="Accent.TButton", command=self._add_to_chain).pack(side="left", padx=2)
        ttk.Button(tb, text="Remove", style="Danger.TButton",  command=self._remove_from_chain).pack(side="left", padx=2)
        ttk.Button(tb, text="▲", command=self._move_up).pack(side="left", padx=1)
        ttk.Button(tb, text="▼", command=self._move_down).pack(side="left", padx=1)

        tk.Label(p, text="My Chain:", font=F_BOLD,
                 bg=C["bg"], fg=C["text_muted"]).grid(row=4, column=0, sticky="w",
                                                       padx=8, pady=(4, 0))
        ch_wrap, self._chain_lb = make_listbox(p, height=7)
        ch_wrap.grid(row=5, column=0, sticky="nsew", padx=8, pady=(2, 4))

        ttk.Button(p, text="Clear Chain", command=self._clear_chain).grid(
            row=6, column=0, sticky="ew", padx=8, pady=(0, 8))

        self._populate_available()

    # ── Output panel ──────────────────────────────────────────────────────────

    def _build_output(self) -> None:
        p = self._output_panel
        p.columnconfigure(0, weight=1)
        p.rowconfigure(2, weight=1)
        p.rowconfigure(4, weight=2)

        tk.Label(p, text="③ Output", font=F_H2,
                 bg=C["hdr_bg"], fg=C["hdr_fg"], anchor="w", padx=12, pady=8
                 ).grid(row=0, column=0, sticky="ew")

        abar = tk.Frame(p, bg=C["surface"])
        abar.grid(row=1, column=0, sticky="ew", padx=8, pady=6)
        tk.Button(abar, text="  ▶  Run Chain", font=F_BOLD,
                  bg=C["success"], fg="#fff", relief="flat", cursor="hand2",
                  activebackground="#059669", command=self._run_chain).pack(side="left", padx=(0, 6))
        tk.Button(abar, text="Export CSV", font=F_BODY,
                  bg=C["surface"], fg=C["text"], relief="flat", cursor="hand2", bd=1,
                  activebackground=C["accent_lt"], command=self._export_csv).pack(side="left")
        self._status_lbl = tk.Label(abar, text="", font=F_SMALL,
                                    bg=C["surface"], fg=C["text_muted"])
        self._status_lbl.pack(side="right")

        tk.Label(p, text="Text result:", font=F_BOLD,
                 bg=C["surface"], fg=C["text_muted"], anchor="w").grid(
                     row=2, column=0, sticky="w", padx=10)
        out_wrap, self._output_text = make_code_editor(p, height=6)
        out_wrap.grid(row=2, column=0, sticky="nsew", padx=8, pady=(18, 4))

        tk.Label(p, text="Column result:", font=F_BOLD,
                 bg=C["surface"], fg=C["text_muted"], anchor="w").grid(
                     row=3, column=0, sticky="w", padx=10, pady=(4, 0))
        res_wrap, self._result_tv = make_treeview(
            p, ("original", "result"),
            col_widths={"original": 210, "result": 210},
        )
        res_wrap.grid(row=4, column=0, sticky="nsew", padx=8, pady=(2, 8))
        self._result_tv.tag_configure("changed", background="#fffbeb")

    # ── Populate strategy list ────────────────────────────────────────────────

    def _populate_available(self) -> None:
        q = self._search_var.get().lower() if hasattr(self, "_search_var") else ""
        self._avail_lb.delete(0, "end")
        entries = (
            [(n, False) for n in sorted(NOPARS_STRATEGY_TABLE)]
            + [(n, True)  for n in sorted(CLEANING_PARS_TABLE)]
        )
        for name, has_pars in entries:
            if q and q not in name.lower():
                continue
            prefix = "[P] " if has_pars else "     "
            self._avail_lb.insert("end", f"{prefix}{name}")
            self._avail_lb.itemconfigure("end",
                fg=C["warning"] if has_pars else C["text"])

    # ── Chain management ──────────────────────────────────────────────────────

    def _add_to_chain(self) -> None:
        sel = self._avail_lb.curselection()
        if not sel:
            return
        raw = self._avail_lb.get(sel[0])
        has_pars = raw.startswith("[P]")
        strategy_name = raw[4:] if has_pars else raw.strip()

        pars: Optional[List[str]] = None
        if has_pars:
            dlg = ParamDialog(self, strategy_name)
            if dlg.result is None:
                return
            pars = dlg.result

        display = strategy_name if pars is None else f"{strategy_name}({', '.join(pars)})"
        self._chain.append((display, strategy_name, pars))
        self._chain_lb.insert("end", f"{len(self._chain):2}. {display}")

    def _remove_from_chain(self) -> None:
        sel = self._chain_lb.curselection()
        if not sel:
            return
        self._chain.pop(sel[0])
        self._refresh_chain_lb()

    def _move_up(self) -> None:
        sel = self._chain_lb.curselection()
        if not sel or sel[0] == 0:
            return
        i = sel[0]
        self._chain[i - 1], self._chain[i] = self._chain[i], self._chain[i - 1]
        self._refresh_chain_lb()
        self._chain_lb.selection_set(i - 1)

    def _move_down(self) -> None:
        sel = self._chain_lb.curselection()
        if not sel or sel[0] >= len(self._chain) - 1:
            return
        i = sel[0]
        self._chain[i], self._chain[i + 1] = self._chain[i + 1], self._chain[i]
        self._refresh_chain_lb()
        self._chain_lb.selection_set(i + 1)

    def _clear_chain(self) -> None:
        self._chain.clear()
        self._chain_lb.delete(0, "end")

    def _refresh_chain_lb(self) -> None:
        self._chain_lb.delete(0, "end")
        for i, (disp, *_) in enumerate(self._chain):
            self._chain_lb.insert("end", f"{i + 1:2}. {disp}")

    # ── Mode switching ────────────────────────────────────────────────────────

    def _on_mode_change(self) -> None:
        if self._mode.get() == "text":
            self._text_frame.grid()
            self._file_frame.grid_remove()
            self._input_panel.rowconfigure(2, weight=1)
            self._input_panel.rowconfigure(3, weight=0)
        else:
            self._text_frame.grid_remove()
            self._file_frame.grid()
            self._input_panel.rowconfigure(2, weight=0)
            self._input_panel.rowconfigure(3, weight=1)

    # ── File loading ──────────────────────────────────────────────────────────

    def _load_file(self) -> None:
        if not PANDAS_OK:
            messagebox.showerror("Missing dep", "pandas is required for file loading.")
            return
        path = filedialog.askopenfilename(
            title="Open file",
            filetypes=[("CSV", "*.csv"), ("Excel", "*.xlsx *.xls"), ("All", "*.*")],
        )
        if not path:
            return
        self._file_path = path
        self._file_lbl.configure(text=os.path.basename(path))
        ext = os.path.splitext(path)[1].lower()
        try:
            if ext == ".csv":
                self._df = pd.read_csv(path, dtype=str, keep_default_na=False)
                self._sheet_combo.configure(state="disabled")
                self._sheet_combo.set("(CSV — no sheet)")
                cols = list(self._df.columns)
                self._col_combo.configure(state="readonly", values=cols)
                if cols:
                    self._col_combo.current(0)
                self._update_preview()
            else:
                xl = pd.ExcelFile(path)
                self._sheet_combo.configure(state="readonly", values=xl.sheet_names)
                self._sheet_combo.current(0)
                self._on_sheet_change()
        except Exception as exc:
            messagebox.showerror("Load error", str(exc))

    def _on_sheet_change(self, _=None) -> None:
        sheet = self._sheet_combo.get()
        if not sheet or sheet.startswith("("):
            return
        try:
            self._df = pd.read_excel(self._file_path, sheet_name=sheet,
                                      dtype=str, keep_default_na=False)
            cols = list(self._df.columns)
            self._col_combo.configure(state="readonly", values=cols)
            if cols:
                self._col_combo.current(0)
            self._update_preview()
        except Exception as exc:
            messagebox.showerror("Sheet error", str(exc))

    def _update_preview(self) -> None:
        col = self._col_combo.get()
        for item in self._preview_tv.get_children():
            self._preview_tv.delete(item)
        if self._df is None or col not in self._df.columns:
            return
        for i, val in enumerate(self._df[col].head(5)):
            self._preview_tv.insert("", "end", values=(i + 1, val))

    # ── Run chain ─────────────────────────────────────────────────────────────

    def _apply_chain_to(self, text: str) -> str:
        result = text
        for _disp, name, pars in self._chain:
            adapter = CleaningStrategyAdapter(name)
            result = adapter.run(result, pars=pars) if pars is not None else adapter.run(result)
        return result

    def _run_chain(self) -> None:
        if not SDK_OK:
            messagebox.showerror("SDK not available", SDK_ERROR)
            return
        if not self._chain:
            messagebox.showwarning("Empty chain", "Add at least one function to the chain.")
            return
        self._status_lbl.configure(text="Running…", fg=C["warning"])
        self.update_idletasks()
        try:
            if self._mode.get() == "text":
                raw = self._input_text.get("1.0", "end").rstrip("\n")
                result = self._apply_chain_to(raw)
                self._output_text.delete("1.0", "end")
                self._output_text.insert("end", result)
                self._status_lbl.configure(text="Done ✓", fg=C["success"])
            else:
                col = self._col_combo.get()
                if not col or self._df is None:
                    messagebox.showwarning("No column", "Load a file and select a column.")
                    self._status_lbl.configure(text="", fg=C["text_muted"])
                    return
                from_vals = list(self._df[col])
                to_vals   = [self._apply_chain_to(str(v)) for v in from_vals]
                self._result_data = list(zip(from_vals, to_vals))
                for item in self._result_tv.get_children():
                    self._result_tv.delete(item)
                for orig, res in self._result_data:
                    self._result_tv.insert("", "end",
                        values=(orig, res),
                        tags=("changed",) if orig != res else ())
                self._status_lbl.configure(
                    text=f"Done ✓  {len(from_vals)} rows", fg=C["success"])
        except Exception:
            messagebox.showerror("Chain error", traceback.format_exc())
            self._status_lbl.configure(text="Error", fg=C["danger"])

    def _export_csv(self) -> None:
        if not self._result_data:
            messagebox.showinfo("Nothing to export", "Run the chain on a file first.")
            return
        path = filedialog.asksaveasfilename(defaultextension=".csv",
                                            filetypes=[("CSV", "*.csv")])
        if not path:
            return
        df_out = pd.DataFrame(self._result_data, columns=["original", "result"])
        df_out.to_csv(path, index=False, encoding="utf-8-sig")
        messagebox.showinfo("Exported", f"Saved to:\n{path}")


# ─────────────────────────────────────────────────────────────────────────────
#  Tab 2 — Matching Lab
# ─────────────────────────────────────────────────────────────────────────────

class MatchingTab(ttk.Frame):

    def __init__(self, notebook: ttk.Notebook) -> None:
        super().__init__(notebook)
        self._threshold    = tk.DoubleVar(value=0.5)
        self._strategy_var = tk.StringVar(value="FUZZY")
        self._result_data: List[Tuple[str, str, float]] = []
        self._build()

    def _build(self) -> None:
        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=3, minsize=200)
        self.columnconfigure(1, weight=3, minsize=200)
        self.columnconfigure(2, weight=1, minsize=165)
        self.columnconfigure(3, weight=5, minsize=300)

        self._p1 = tk.Frame(self, bg=C["surface"])
        self._p2 = tk.Frame(self, bg=C["surface"])
        self._pc = tk.Frame(self, bg=C["bg"])
        self._pr = tk.Frame(self, bg=C["surface"])
        self._p1.grid(row=0, column=0, sticky="nsew", padx=(0, 1))
        self._p2.grid(row=0, column=1, sticky="nsew", padx=1)
        self._pc.grid(row=0, column=2, sticky="nsew", padx=1)
        self._pr.grid(row=0, column=3, sticky="nsew", padx=(1, 0))

        self._build_list_panel(self._p1, "① Query List",     "_list1_text")
        self._build_list_panel(self._p2, "② Reference List", "_list2_text")
        self._build_config()
        self._build_results()

    def _build_list_panel(self, p: tk.Frame, title: str, attr: str) -> None:
        p.columnconfigure(0, weight=1)
        p.rowconfigure(1, weight=1)
        tk.Label(p, text=title, font=F_H2,
                 bg=C["hdr_bg"], fg=C["hdr_fg"], anchor="w", padx=12, pady=8
                 ).grid(row=0, column=0, sticky="ew")

        ed_wrap, text = make_code_editor(p, height=18)
        ed_wrap.grid(row=1, column=0, sticky="nsew", padx=8, pady=(6, 4))
        setattr(self, attr, text)

        tk.Label(p, text="One string per line  ·  or load from CSV / Excel",
                 font=F_SMALL, bg=C["surface"], fg=C["text_muted"]).grid(
                     row=2, column=0, sticky="ew", padx=10)

        btn_bar = tk.Frame(p, bg=C["surface"])
        btn_bar.grid(row=3, column=0, sticky="ew", padx=8, pady=(4, 8))
        ttk.Button(btn_bar, text="Load from file",
                   command=lambda t=text: self._load_list(t)).pack(side="left")

    def _build_config(self) -> None:
        p = self._pc
        p.columnconfigure(0, weight=1)
        hdr_label(p, "③ Config")

        inner = tk.Frame(p, bg=C["bg"])
        inner.pack(fill="both", expand=True, padx=8, pady=8)
        inner.columnconfigure(0, weight=1)

        tk.Label(inner, text="Strategy:", font=F_BOLD,
                 bg=C["bg"], fg=C["text"], anchor="w").pack(fill="x", pady=(0, 2))
        strats = sorted(MATCHING_TABLE.keys()) if SDK_OK else []
        self._strat_combo = ttk.Combobox(inner, values=strats,
                                          textvariable=self._strategy_var,
                                          state="readonly", font=F_BODY)
        self._strat_combo.pack(fill="x", pady=(0, 8))

        tk.Label(inner, text="Threshold:", font=F_BOLD,
                 bg=C["bg"], fg=C["text"], anchor="w").pack(fill="x")
        self._thresh_lbl = tk.Label(inner, text="0.50", font=F_H2,
                                    bg=C["bg"], fg=C["accent"])
        self._thresh_lbl.pack()
        ttk.Scale(
            inner, from_=0.0, to=1.0, variable=self._threshold, orient="horizontal",
            command=lambda _: self._thresh_lbl.configure(
                text=f"{self._threshold.get():.2f}"),
        ).pack(fill="x", pady=(0, 12))

        section_sep(inner, 0)

        tk.Button(inner, text="  ▶  Run Match", font=F_BOLD,
                  bg=C["success"], fg="#fff", relief="flat", cursor="hand2",
                  activebackground="#059669",
                  command=self._run_match).pack(fill="x", pady=(0, 4))
        ttk.Button(inner, text="Export Results",
                   command=self._export).pack(fill="x")

        self._match_status = tk.Label(inner, text="", font=F_SMALL,
                                      bg=C["bg"], fg=C["text_muted"], wraplength=160)
        self._match_status.pack(pady=6)

    def _build_results(self) -> None:
        p = self._pr
        p.columnconfigure(0, weight=1)
        p.rowconfigure(1, weight=1)

        hdr_row = tk.Frame(p, bg=C["hdr_bg"])
        hdr_row.pack(fill="x")
        tk.Label(hdr_row, text="④ Results", font=F_H2,
                 bg=C["hdr_bg"], fg=C["hdr_fg"], anchor="w", padx=12, pady=8).pack(side="left")
        self._count_lbl = tk.Label(hdr_row, text="",
                                   font=F_SMALL, bg=C["hdr_bg"], fg="#a5b4fc")
        self._count_lbl.pack(side="right", padx=12)

        tv_wrap, self._result_tv = make_treeview(
            p, ("query", "best_match", "score"),
            col_widths={"query": 170, "best_match": 195, "score": 70},
            col_anchors={"score": "center"},
        )
        tv_wrap.pack(fill="both", expand=True, padx=8, pady=8)
        self._result_tv.tag_configure("high",   background=C["success_bg"])
        self._result_tv.tag_configure("medium", background=C["warning_bg"])
        self._result_tv.tag_configure("low",    background=C["danger_bg"])

    # ── File loader ───────────────────────────────────────────────────────────

    def _load_list(self, target: tk.Text) -> None:
        if not PANDAS_OK:
            messagebox.showerror("Missing dep", "pandas required."); return
        path = filedialog.askopenfilename(
            filetypes=[("CSV", "*.csv"), ("Excel", "*.xlsx *.xls"), ("All", "*.*")])
        if not path:
            return
        try:
            ext = os.path.splitext(path)[1].lower()
            df = (pd.read_csv(path, dtype=str, keep_default_na=False) if ext == ".csv"
                  else pd.read_excel(path, dtype=str, keep_default_na=False))
        except Exception as e:
            messagebox.showerror("Load error", str(e)); return

        dlg = ColumnPickerDialog(self, list(df.columns))
        if dlg.result is None:
            return
        values = df[dlg.result].dropna().tolist()
        target.delete("1.0", "end")
        target.insert("end", "\n".join(str(v) for v in values))

    # ── Run ───────────────────────────────────────────────────────────────────

    def _run_match(self) -> None:
        if not SDK_OK:
            messagebox.showerror("SDK unavailable", SDK_ERROR); return
        raw1 = self._list1_text.get("1.0", "end").strip()
        raw2 = self._list2_text.get("1.0", "end").strip()
        if not raw1 or not raw2:
            messagebox.showwarning("Empty", "Provide both Query and Reference lists.")
            return

        list1 = [line.strip() for line in raw1.splitlines() if line.strip()]
        list2 = [line.strip() for line in raw2.splitlines() if line.strip()]
        strategy  = self._strategy_var.get()
        threshold = self._threshold.get()

        self._match_status.configure(text="Running…", fg=C["warning"])
        self.update_idletasks()

        def _worker() -> None:
            try:
                results = sdk_match(list1, list2, strategy=strategy, threshold=threshold)
                self.after(0, lambda: self._show_results(results))
            except Exception:
                err = traceback.format_exc()
                self.after(0, lambda: (
                    messagebox.showerror("Error", err),
                    self._match_status.configure(text="Error", fg=C["danger"]),
                ))

        threading.Thread(target=_worker, daemon=True).start()

    def _show_results(self, results: List[Tuple[str, str, float]]) -> None:
        for item in self._result_tv.get_children():
            self._result_tv.delete(item)
        self._result_data = results
        thresh = self._threshold.get()
        for q, ref, score in results:
            tag = "high" if score >= 0.8 else "medium" if score >= thresh else "low"
            self._result_tv.insert("", "end",
                values=(q, ref, f"{score:.4f}"), tags=(tag,))
        self._count_lbl.configure(text=f"{len(results)} match(es)")
        self._match_status.configure(
            text=f"Done ✓  {len(results)} pair(s)", fg=C["success"])

    def _export(self) -> None:
        if not self._result_data:
            messagebox.showinfo("Nothing", "Run a match first."); return
        path = filedialog.asksaveasfilename(defaultextension=".csv",
                                            filetypes=[("CSV", "*.csv")])
        if not path:
            return
        import csv as _csv
        with open(path, "w", newline="", encoding="utf-8-sig") as f:
            w = _csv.writer(f)
            w.writerow(["query", "best_match", "score"])
            w.writerows((q, r, f"{s:.4f}") for q, r, s in self._result_data)
        messagebox.showinfo("Exported", f"Saved to:\n{path}")


# ─────────────────────────────────────────────────────────────────────────────
#  Tab 3 — TDD Workbench
# ─────────────────────────────────────────────────────────────────────────────

class TDDTab(ttk.Frame):

    _UNDONE_NAMES = {
        "OnDevStrategy", "_on_dev_strategy_",
        "NewJACCARDStrategy", "AbbrevExactMatchStrategy",
    }

    def __init__(self, notebook: ttk.Notebook) -> None:
        super().__init__(notebook)
        self._test_rows: List[Dict[str, Any]] = []
        self._strategy_var = tk.StringVar(value="FUZZY")
        self._col1_var     = tk.StringVar(value="a")
        self._col2_var     = tk.StringVar(value="b")
        self._mode_var     = tk.StringVar(value="wrong_answer")
        self._thresh_var   = tk.DoubleVar(value=0.5)
        self._build()

    def _build(self) -> None:
        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=4, minsize=280)
        self.columnconfigure(1, weight=1, minsize=185)
        self.columnconfigure(2, weight=4, minsize=280)

        self._pe = tk.Frame(self, bg=C["surface"])
        self._pc = tk.Frame(self, bg=C["bg"])
        self._pr = tk.Frame(self, bg=C["surface"])
        self._pe.grid(row=0, column=0, sticky="nsew", padx=(0, 1))
        self._pc.grid(row=0, column=1, sticky="nsew", padx=1)
        self._pr.grid(row=0, column=2, sticky="nsew", padx=(1, 0))

        self._build_editor()
        self._build_config()
        self._build_results()

    # ── Test case editor (left) ───────────────────────────────────────────────

    def _build_editor(self) -> None:
        p = self._pe
        p.columnconfigure(0, weight=1)
        p.rowconfigure(2, weight=1)

        hdr_row = tk.Frame(p, bg=C["hdr_bg"])
        hdr_row.grid(row=0, column=0, sticky="ew")
        tk.Label(hdr_row, text="① Test Cases", font=F_H2,
                 bg=C["hdr_bg"], fg=C["hdr_fg"], anchor="w", padx=12, pady=8).pack(side="left")
        self._row_count_lbl = tk.Label(hdr_row, text="0 rows",
                                       font=F_SMALL, bg=C["hdr_bg"], fg="#a5b4fc")
        self._row_count_lbl.pack(side="right", padx=12)

        toolbar = tk.Frame(p, bg=C["surface"])
        toolbar.grid(row=1, column=0, sticky="ew", padx=6, pady=6)
        for text, cmd in (
            ("+ Add",      self._add_row),
            ("✕ Remove",   self._remove_row),
            ("▲",          self._move_row_up),
            ("▼",          self._move_row_down),
            ("Clear All",  self._clear_rows),
        ):
            ttk.Button(toolbar, text=text, command=cmd).pack(side="left", padx=2)
        ttk.Button(toolbar, text="Import CSV",
                   command=self._import_csv).pack(side="right", padx=2)

        tv_wrap, self._tv = make_treeview(
            p,
            ("#", "left", "right", "expected"),
            col_widths={"#": 32, "left": 170, "right": 170, "expected": 72},
            col_anchors={"#": "center", "expected": "center"},
        )
        tv_wrap.grid(row=2, column=0, sticky="nsew", padx=6, pady=(0, 4))
        self._tv.tag_configure("pass_row", background=C["success_bg"])
        self._tv.tag_configure("fail_row", background=C["danger_bg"])
        self._tv.bind("<Double-Button-1>", self._on_cell_dblclick)

        tk.Label(p, text="Double-click to edit  ·  click Expected to toggle True / False",
                 font=F_SMALL, bg=C["surface"], fg=C["text_muted"]).grid(
                     row=3, column=0, sticky="w", padx=6, pady=(0, 4))

    # ── Config (middle) ───────────────────────────────────────────────────────

    def _build_config(self) -> None:
        p = self._pc
        p.columnconfigure(0, weight=1)
        hdr_label(p, "② Config")

        inner = tk.Frame(p, bg=C["bg"])
        inner.pack(fill="both", expand=True, padx=8, pady=8)
        inner.columnconfigure(0, weight=1)

        tk.Label(inner, text="Strategy:", font=F_BOLD,
                 bg=C["bg"], fg=C["text"], anchor="w").pack(fill="x", pady=(0, 2))
        strats = sorted(MATCHING_TABLE.keys()) if SDK_OK else []
        self._strat_combo = ttk.Combobox(inner, values=strats,
                                          textvariable=self._strategy_var,
                                          state="readonly", font=F_BODY)
        self._strat_combo.pack(fill="x", pady=(0, 4))
        self._strat_combo.bind("<<ComboboxSelected>>", self._on_strat_change)

        self._strat_badge = tk.Label(inner, text="", font=F_SMALL,
                                     bg=C["success_bg"], fg="#065f46",
                                     relief="flat", padx=6, pady=2)
        self._strat_badge.pack(fill="x", pady=(0, 8))

        section_sep(inner, 0)

        tk.Label(inner, text="Score threshold:", font=F_BOLD,
                 bg=C["bg"], fg=C["text"], anchor="w").pack(fill="x", pady=(6, 0))
        self._thresh_disp = tk.Label(inner, text="0.50", font=F_H2,
                                     bg=C["bg"], fg=C["accent"])
        self._thresh_disp.pack()
        ttk.Scale(
            inner, from_=0.0, to=1.0, variable=self._thresh_var, orient="horizontal",
            command=lambda _: self._thresh_disp.configure(
                text=f"{self._thresh_var.get():.2f}"),
        ).pack(fill="x", pady=(0, 10))

        section_sep(inner, 0)

        for label, var in (("col1 name:", self._col1_var),
                            ("col2 name:", self._col2_var)):
            tk.Label(inner, text=label, font=F_BOLD,
                     bg=C["bg"], fg=C["text"], anchor="w").pack(fill="x", pady=(4, 0))
            ttk.Entry(inner, textvariable=var, font=F_BODY).pack(fill="x", pady=(0, 4))

        section_sep(inner, 0)

        tk.Label(inner, text="Display mode:", font=F_BOLD,
                 bg=C["bg"], fg=C["text"], anchor="w").pack(fill="x", pady=(4, 0))
        for val, txt in (("show_all", "Show all"), ("wrong_answer", "Wrong only")):
            tk.Radiobutton(
                inner, text=txt, variable=self._mode_var, value=val,
                bg=C["bg"], fg=C["text"], activebackground=C["accent_lt"],
                selectcolor=C["accent_lt"], font=F_BODY, relief="flat", cursor="hand2",
            ).pack(anchor="w")

        section_sep(inner, 0)

        tk.Button(inner, text="  ▶  Run Tests", font=F_BOLD,
                  bg=C["success"], fg="#fff", relief="flat", cursor="hand2",
                  activebackground="#059669",
                  command=self._run_tests).pack(fill="x", pady=(8, 4))

        self._run_status = tk.Label(inner, text="", font=F_BOLD,
                                    bg=C["bg"], fg=C["text_muted"])
        self._run_status.pack(pady=4)

        self._on_strat_change()

    # ── Results (right) ───────────────────────────────────────────────────────

    def _build_results(self) -> None:
        p = self._pr
        p.columnconfigure(0, weight=1)
        p.rowconfigure(1, weight=1)

        hdr_label(p, "③ Test Results")

        tv_wrap, self._res_tv = make_treeview(
            p,
            ("status", "left", "right", "got", "expected"),
            col_widths={"status": 46, "left": 150, "right": 150, "got": 60, "expected": 70},
            col_anchors={"status": "center", "got": "center", "expected": "center"},
        )
        tv_wrap.pack(fill="both", expand=True, padx=8, pady=(8, 4))
        self._res_tv.tag_configure("pass", background=C["success_bg"])
        self._res_tv.tag_configure("fail", background=C["danger_bg"])

        self._summary_lbl = tk.Label(p, text="No results yet.", font=F_BOLD,
                                     bg=C["surface2"], fg=C["text_muted"],
                                     anchor="w", padx=10, pady=6)
        self._summary_lbl.pack(fill="x", padx=8, pady=(0, 8))

    # ── Row editing ───────────────────────────────────────────────────────────

    def _refresh_tv(self) -> None:
        self._tv.delete(*self._tv.get_children())
        for i, row in enumerate(self._test_rows):
            exp = "True" if row["expected"] else "False"
            self._tv.insert("", "end", iid=str(i),
                            values=(i + 1, row["left"], row["right"], exp))
        self._row_count_lbl.configure(text=f"{len(self._test_rows)} rows")

    def _add_row(self) -> None:
        self._test_rows.append({"left": "input_A", "right": "input_B", "expected": True})
        self._refresh_tv()
        kids = self._tv.get_children()
        if kids:
            self._tv.selection_set(kids[-1])
            self._tv.see(kids[-1])

    def _remove_row(self) -> None:
        sel = self._tv.selection()
        if sel:
            self._test_rows.pop(int(sel[0]))
            self._refresh_tv()

    def _move_row_up(self) -> None:
        sel = self._tv.selection()
        if not sel:
            return
        i = int(sel[0])
        if i == 0:
            return
        self._test_rows[i - 1], self._test_rows[i] = self._test_rows[i], self._test_rows[i - 1]
        self._refresh_tv()
        self._tv.selection_set(str(i - 1))

    def _move_row_down(self) -> None:
        sel = self._tv.selection()
        if not sel:
            return
        i = int(sel[0])
        if i >= len(self._test_rows) - 1:
            return
        self._test_rows[i], self._test_rows[i + 1] = self._test_rows[i + 1], self._test_rows[i]
        self._refresh_tv()
        self._tv.selection_set(str(i + 1))

    def _clear_rows(self) -> None:
        if self._test_rows and messagebox.askyesno("Clear", "Remove all test cases?"):
            self._test_rows.clear()
            self._refresh_tv()

    def _import_csv(self) -> None:
        if not PANDAS_OK:
            messagebox.showerror("Missing dep", "pandas required."); return
        path = filedialog.askopenfilename(filetypes=[("CSV", "*.csv")])
        if not path:
            return
        try:
            df = pd.read_csv(path, dtype=str, keep_default_na=False)
            missing = {"left", "right", "expected"} - set(df.columns)
            if missing:
                messagebox.showerror("Format error",
                    f"CSV needs columns: left, right, expected\nMissing: {missing}")
                return
            for _, r in df.iterrows():
                exp = str(r["expected"]).strip().lower() in ("true", "1", "yes")
                self._test_rows.append({
                    "left": r["left"], "right": r["right"], "expected": exp})
            self._refresh_tv()
        except Exception as e:
            messagebox.showerror("Import error", str(e))

    def _on_cell_dblclick(self, event: tk.Event) -> None:
        if self._tv.identify_region(event.x, event.y) != "cell":
            return
        item = self._tv.identify_row(event.y)
        col  = self._tv.identify_column(event.x)
        if not item:
            return
        col_idx  = int(col.lstrip("#")) - 1
        col_name = ("#", "left", "right", "expected")[col_idx]
        if col_name == "#":
            return

        row_idx = int(item)
        if col_name == "expected":
            self._test_rows[row_idx]["expected"] = not self._test_rows[row_idx]["expected"]
            self._refresh_tv()
            return

        bbox = self._tv.bbox(item, col)
        if not bbox:
            return
        x, y, w, h = bbox
        var = tk.StringVar(value=str(self._test_rows[row_idx].get(col_name, "")))
        popup = tk.Entry(self._tv, textvariable=var, font=F_BODY,
                         bg=C["accent_lt"], fg=C["accent_dk"], relief="flat", bd=1,
                         insertbackground=C["accent"])
        popup.place(x=x, y=y, width=w, height=h)
        popup.focus_set()
        popup.select_range(0, "end")

        def _commit(_=None) -> None:
            self._test_rows[row_idx][col_name] = var.get()
            popup.destroy()
            self._refresh_tv()

        popup.bind("<Return>",   _commit)
        popup.bind("<FocusOut>", _commit)
        popup.bind("<Escape>",   lambda _: popup.destroy())

    # ── Strategy badge ────────────────────────────────────────────────────────

    def _on_strat_change(self, _=None) -> None:
        name = self._strategy_var.get()
        if name in self._UNDONE_NAMES:
            self._strat_badge.configure(
                text=f"⚠  {name}  — UNDONE / in-progress",
                bg=C["undone_bg"], fg=C["undone_fg"])
        else:
            self._strat_badge.configure(
                text=f"✓  {name}  — available",
                bg=C["success_bg"], fg="#065f46")

    # ── Run tests ─────────────────────────────────────────────────────────────

    def _run_tests(self) -> None:
        if not SDK_OK:
            messagebox.showerror("SDK unavailable", SDK_ERROR); return
        if not self._test_rows:
            messagebox.showwarning("No cases", "Add test cases first."); return

        strat_name = self._strategy_var.get()
        if strat_name not in MATCHING_TABLE:
            messagebox.showerror("Unknown", f"{strat_name!r} not in STRATEGY_TABLE"); return

        col1      = self._col1_var.get() or "a"
        col2      = self._col2_var.get() or "b"
        standard  = self._thresh_var.get()
        strat_cls = MATCHING_TABLE[strat_name]
        tests     = [(r["left"], r["right"], r["expected"]) for r in self._test_rows]

        self._run_status.configure(text="Running…", fg=C["warning"])
        self.update_idletasks()

        def _worker() -> None:
            detail: List[Dict[str, Any]] = []
            try:
                import pandas as _pd
                strat = strat_cls(col1, col2, standard=standard)
                for left, right, exp in tests:
                    ctx = TwoSeriesComparisonContext(
                        row1=_pd.Series({col1: left}),
                        row2=_pd.Series({col2: right}),
                    )
                    r = strat.evaluate(ctx)
                    detail.append({
                        "correct": r.success == exp,
                        "left": left, "right": right,
                        "got": r.success, "expected": exp,
                    })
            except Exception:
                err = traceback.format_exc()
                self.after(0, lambda: (
                    messagebox.showerror("Run error", err),
                    self._run_status.configure(text="Error", fg=C["danger"]),
                ))
                return
            self.after(0, lambda d=detail: self._show_results(d))

        threading.Thread(target=_worker, daemon=True).start()

    def _show_results(self, detail: List[Dict[str, Any]]) -> None:
        for item in self._res_tv.get_children():
            self._res_tv.delete(item)

        passed = sum(1 for d in detail if d["correct"])
        failed = len(detail) - passed
        mode   = self._mode_var.get()

        for d in detail:
            if mode == "wrong_answer" and d["correct"]:
                continue
            tag    = "pass" if d["correct"] else "fail"
            status = "✓" if d["correct"] else "✗"
            self._res_tv.insert("", "end", tags=(tag,),
                values=(status, d["left"], d["right"],
                        str(d["got"]), str(d["expected"])))

        # Colour source rows
        for i, d in enumerate(detail):
            self._tv.item(str(i), tags=("pass_row" if d["correct"] else "fail_row",))

        color = C["success"] if failed == 0 else C["danger"]
        self._summary_lbl.configure(
            text=f"  PASS {passed} / {len(detail)}   │   FAIL {failed} / {len(detail)}",
            fg=color)
        self._run_status.configure(
            text="ALL PASS ✓" if failed == 0 else f"{failed} FAIL(s) ✗",
            fg=color)


# ─────────────────────────────────────────────────────────────────────────────
#  Main App Window
# ─────────────────────────────────────────────────────────────────────────────

class App(tk.Tk):

    def __init__(self) -> None:
        super().__init__()
        self.title("ISD String SDK  —  Workbench")
        self.geometry("1300x780")
        self.minsize(920, 620)
        self.configure(bg=C["hdr_bg"])
        _apply_style(self)
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


# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    App().mainloop()
