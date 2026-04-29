"""
_shared.py — Design tokens, widget factories, dialogs.
Imported by the tab modules and testing_app.py.
"""
from __future__ import annotations

import os
import sys
import traceback
from typing import Any, Dict, List, Optional, Tuple

import tkinter as tk
from tkinter import ttk, filedialog, messagebox

# ── SDK path ──────────────────────────────────────────────────────────────────
_sdk_root = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "src"))
if _sdk_root not in sys.path:
    sys.path.insert(0, _sdk_root)

try:
    from isd_str_sdk.str_cleaning import (
        CleaningStrategyAdapter,
        NOPARS_STRATEGY_TABLE,
        STRATEGY_TABLE as CLEANING_PARS_TABLE,
        PARAM_META,
    )
    from isd_str_sdk.base.StrProcessorsChain import StrProcessorsChain  # noqa: F401
    from isd_str_sdk.str_matching import match as sdk_match
    from isd_str_sdk.str_matching.adapters import (
        MatchingStrategyAdapter,
        STRATEGY_TABLE as MATCHING_TABLE,
        STRATEGY_PARAM_META as MATCHING_PARAM_META,
        get_strategy_param_meta,
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
    MATCHING_PARAM_META = {}
    PARAM_META = {}

    def get_strategy_param_meta(name: str) -> dict:  # type: ignore[misc]
        return {}

try:
    import pandas as pd
    PANDAS_OK = True
except ImportError:
    pd = None  # type: ignore
    PANDAS_OK = False

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

def apply_style(root: tk.Tk) -> None:
    s = ttk.Style(root)
    s.theme_use("clam")

    s.configure(".", background=C["bg"], foreground=C["text"], font=F_BODY)
    s.configure("TFrame",  background=C["bg"])
    s.configure("TLabel",  background=C["bg"], foreground=C["text"])

    s.configure("TNotebook",
                background=C["hdr_bg"], borderwidth=0, tabmargins=[0, 0, 0, 0])
    s.configure("TNotebook.Tab",
                background=C["hdr_bg"], foreground="#a5b4fc",
                padding=[20, 9], font=F_BOLD)
    s.map("TNotebook.Tab",
          background=[("selected", C["accent"]), ("active", "#312e81")],
          foreground=[("selected", "#ffffff"),  ("active", "#c7d2fe")])

    s.configure("TLabelframe",
                background=C["surface"], bordercolor=C["border"],
                relief="solid", borderwidth=1)
    s.configure("TLabelframe.Label",
                background=C["surface"], foreground=C["accent"], font=F_BOLD)

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

    for w in ("TCombobox", "TEntry"):
        s.configure(w, fieldbackground=C["surface"], background=C["surface"],
                    foreground=C["text"], bordercolor=C["border"],
                    selectbackground=C["accent_lt"], selectforeground=C["accent_dk"])

    s.configure("Treeview",
                background=C["surface"], foreground=C["text"],
                fieldbackground=C["surface"], rowheight=26, font=F_BODY)
    s.configure("Treeview.Heading",
                background=C["surface2"], foreground=C["text"],
                font=F_BOLD, relief="flat")
    s.map("Treeview",
          background=[("selected", C["accent_lt"])],
          foreground=[("selected", C["accent_dk"])])

    for orient in ("Vertical", "Horizontal"):
        s.configure(f"{orient}.TScrollbar",
                    background=C["border"], troughcolor=C["surface2"],
                    arrowcolor=C["text_muted"])

    s.configure("TScale", background=C["bg"], troughcolor=C["border"], sliderlength=14)

# ─────────────────────────────────────────────────────────────────────────────
#  Widget factories  (callers own placement)
# ─────────────────────────────────────────────────────────────────────────────

def make_code_editor(parent: tk.Widget, height: int = 8) -> Tuple[tk.Frame, tk.Text]:
    wrapper = tk.Frame(parent, bg=C["border"], bd=1)
    wrapper.rowconfigure(0, weight=1)
    wrapper.columnconfigure(0, weight=1)
    t = tk.Text(wrapper, wrap="none", font=F_MONO, height=height,
                bg=C["surface"], fg=C["text"], insertbackground=C["accent"],
                relief="flat", bd=0, padx=8, pady=6, undo=True,
                selectbackground=C["accent_lt"], selectforeground=C["accent_dk"])
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

class ColumnPickerDialog(tk.Toplevel):
    """Pick one column name from a list."""

    def __init__(self, parent: tk.Widget, columns: List[str],
                 prompt: str = "Select column to import:") -> None:
        super().__init__(parent)
        self.title("Select Column")
        self.configure(bg=C["bg"])
        self.resizable(False, False)
        self.result: Optional[str] = None
        self._var = tk.StringVar(value=columns[0] if columns else "")

        tk.Label(self, text=prompt, font=F_BOLD,
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


class SheetPickerDialog(tk.Toplevel):
    """Pick one sheet name from an Excel workbook."""

    def __init__(self, parent: tk.Widget, sheets: List[str]) -> None:
        super().__init__(parent)
        self.title("Select Sheet")
        self.configure(bg=C["bg"])
        self.resizable(False, False)
        self.result: Optional[str] = None
        self._var = tk.StringVar(value=sheets[0] if sheets else "")

        tk.Label(self, text="Select sheet to import:", font=F_BOLD,
                 bg=C["bg"], fg=C["text"]).pack(padx=16, pady=(12, 4))
        ttk.Combobox(self, values=sheets, textvariable=self._var,
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


class MultiColumnPickerDialog(tk.Toplevel):
    """Pick multiple column names from a list via checkboxes."""

    def __init__(self, parent: tk.Widget, columns: List[str],
                 title: str = "Select Columns",
                 prompt: str = "Check the columns to include:",
                 preselect: Optional[List[str]] = None) -> None:
        super().__init__(parent)
        self.title(title)
        self.configure(bg=C["bg"])
        self.resizable(True, True)
        self.result: Optional[List[str]] = None
        self._vars: Dict[str, tk.BooleanVar] = {}

        tk.Label(self, text=prompt, font=F_BOLD,
                 bg=C["bg"], fg=C["text"]).pack(padx=16, pady=(12, 4))

        # Scrollable checkbox area
        outer = tk.Frame(self, bg=C["border"], bd=1)
        outer.pack(padx=16, pady=4, fill="both", expand=True)
        outer.rowconfigure(0, weight=1)
        outer.columnconfigure(0, weight=1)
        canvas = tk.Canvas(outer, bg=C["surface"], highlightthickness=0, width=240)
        vsb = ttk.Scrollbar(outer, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=vsb.set)
        canvas.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        inner = tk.Frame(canvas, bg=C["surface"])
        canvas.create_window((0, 0), window=inner, anchor="nw")
        inner.bind("<Configure>", lambda _: canvas.configure(
            scrollregion=canvas.bbox("all"),
            height=min(300, len(columns) * 28 + 8),
        ))

        ps = set(preselect or [])
        for col in columns:
            v = tk.BooleanVar(value=(col in ps))
            self._vars[col] = v
            tk.Checkbutton(inner, text=col, variable=v, font=F_BODY,
                           bg=C["surface"], fg=C["text"], anchor="w",
                           activebackground=C["accent_lt"],
                           selectcolor=C["accent_lt"]).pack(fill="x", padx=8, pady=1)

        # Select / deselect all
        ctrl = tk.Frame(self, bg=C["bg"])
        ctrl.pack(padx=16, pady=(4, 0), fill="x")
        ttk.Button(ctrl, text="All",  command=lambda: [v.set(True)  for v in self._vars.values()]).pack(side="left", padx=2)
        ttk.Button(ctrl, text="None", command=lambda: [v.set(False) for v in self._vars.values()]).pack(side="left", padx=2)

        row = tk.Frame(self, bg=C["bg"])
        row.pack(pady=(6, 12))
        ttk.Button(row, text="OK",     style="Accent.TButton", command=self._ok).pack(side="left", padx=4)
        ttk.Button(row, text="Cancel", command=self.destroy).pack(side="left", padx=4)
        self.grab_set()
        self.wait_window()

    def _ok(self) -> None:
        self.result = [col for col, v in self._vars.items() if v.get()]
        self.destroy()


class SmartParamDialog(tk.Toplevel):
    """
    Adaptive parameter dialog for parameterised cleaning strategies.

    Reads PARAM_META[strategy_name] and renders the appropriate UI:
      "choice"     → combobox  → returns str
      "multi_list" → checkboxes → returns List[str]
      "list_str"   → multi-entry → returns List[str]
      "list_pairs" → text (old=new per line) → returns List[Tuple[str,str]]
    """

    def __init__(self, parent: tk.Widget, strategy_name: str) -> None:
        super().__init__(parent)
        self.title(f"Configure  —  {strategy_name}")
        self.configure(bg=C["bg"])
        self.resizable(False, False)
        self.result = None   # set to the correctly-typed value on OK

        meta = PARAM_META.get(strategy_name)
        if meta is None:
            # Fallback: comma-list for anything unknown
            kind, opts = "list_str", "Comma-separated parameters"
        else:
            kind, opts = meta

        tk.Label(self, text=strategy_name, font=F_BOLD,
                 bg=C["bg"], fg=C["accent"]).pack(padx=16, pady=(12, 0))
        tk.Frame(self, bg=C["border"], height=1).pack(fill="x", padx=12, pady=6)

        if kind == "choice":
            self._build_choice(opts)
        elif kind == "multi_list":
            self._build_multi_list(opts)
        elif kind == "list_pairs":
            self._build_pairs(opts)
        else:
            self._build_list_str(opts)

        row = tk.Frame(self, bg=C["bg"])
        row.pack(pady=(6, 12))
        ttk.Button(row, text="OK",     style="Accent.TButton", command=self._ok).pack(side="left", padx=4)
        ttk.Button(row, text="Cancel", command=self.destroy).pack(side="left", padx=4)
        self.grab_set()
        self.wait_window()

    # ── Choice (combobox) ───────────────────────────────────────────────────

    def _build_choice(self, options: List[str]) -> None:
        self._kind = "choice"
        tk.Label(self, text="Select:", font=F_BOLD,
                 bg=C["bg"], fg=C["text"]).pack(padx=16, pady=(0, 2))
        self._var = tk.StringVar(value=options[0] if options else "")
        cb = ttk.Combobox(self, textvariable=self._var,
                          values=options, state="readonly", font=F_BODY, width=22)
        cb.pack(padx=16, pady=(0, 6))

    def _ok_choice(self) -> Any:
        return self._var.get()

    # ── Multi-checkbox list ─────────────────────────────────────────────────

    def _build_multi_list(self, options: List[str]) -> None:
        self._kind = "multi_list"
        tk.Label(self, text="Select one or more:", font=F_BOLD,
                 bg=C["bg"], fg=C["text"]).pack(padx=16, pady=(0, 4))
        frm = tk.Frame(self, bg=C["bg"])
        frm.pack(padx=16, pady=(0, 6))
        self._chk_vars: Dict[str, tk.BooleanVar] = {}
        for opt in options:
            v = tk.BooleanVar(value=opt in ("英文", "數字", "字間空白"))
            self._chk_vars[opt] = v
            tk.Checkbutton(frm, text=opt, variable=v, font=F_BODY,
                           bg=C["bg"], fg=C["text"],
                           activebackground=C["accent_lt"],
                           selectcolor=C["accent_lt"]).pack(anchor="w")

    def _ok_multi_list(self) -> List[str]:
        return [k for k, v in self._chk_vars.items() if v.get()]

    # ── List-of-strings entry ────────────────────────────────────────────────

    def _build_list_str(self, hint: str) -> None:
        self._kind = "list_str"
        tk.Label(self, text=hint, font=F_SMALL,
                 bg=C["bg"], fg=C["text_muted"], wraplength=260).pack(padx=16, pady=(0, 4))
        # 5 entry rows so user can type one item per row
        self._entries: List[ttk.Entry] = []
        frm = tk.Frame(self, bg=C["bg"])
        frm.pack(padx=16, pady=(0, 4))
        for i in range(5):
            e = ttk.Entry(frm, font=F_BODY, width=26)
            e.grid(row=i, column=0, pady=2)
            self._entries.append(e)
        self._entries[0].focus_set()

    def _ok_list_str(self) -> List[str]:
        return [e.get().strip() for e in self._entries if e.get().strip()]

    # ── List-of-pairs entry ──────────────────────────────────────────────────

    def _build_pairs(self, hint: str) -> None:
        self._kind = "list_pairs"
        tk.Label(self, text=hint, font=F_SMALL,
                 bg=C["bg"], fg=C["text_muted"], wraplength=280).pack(padx=16, pady=(0, 4))
        tk.Label(self, text="One pair per line:  old = new",
                 font=F_SMALL, bg=C["bg"], fg=C["text_muted"]).pack(padx=16)
        frm = tk.Frame(self, bg=C["border"], bd=1)
        frm.pack(padx=16, pady=4)
        frm.rowconfigure(0, weight=1)
        frm.columnconfigure(0, weight=1)
        self._pairs_text = tk.Text(frm, font=F_MONO, width=30, height=7,
                                   bg=C["surface"], fg=C["text"], relief="flat",
                                   bd=0, padx=6, pady=4)
        vsb = ttk.Scrollbar(frm, orient="vertical", command=self._pairs_text.yview)
        self._pairs_text.configure(yscrollcommand=vsb.set)
        self._pairs_text.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        self._pairs_text.focus_set()

    def _ok_pairs(self) -> List[Tuple[str, str]]:
        result = []
        for line in self._pairs_text.get("1.0", "end").splitlines():
            line = line.strip()
            if not line or "=" not in line:
                continue
            idx = line.index("=")
            old = line[:idx].strip()
            new = line[idx + 1:].strip()
            if old:
                result.append((old, new))
        return result

    # ── Dispatch ────────────────────────────────────────────────────────────

    def _ok(self) -> None:
        dispatch = {
            "choice":     self._ok_choice,
            "multi_list": self._ok_multi_list,
            "list_str":   self._ok_list_str,
            "list_pairs": self._ok_pairs,
        }
        fn = dispatch.get(self._kind, self._ok_list_str)
        self.result = fn()
        self.destroy()
