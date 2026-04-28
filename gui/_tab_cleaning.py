"""_tab_cleaning.py — Cleaning Lab tab."""
from __future__ import annotations

import os
import traceback
from typing import Any, Dict, List, Optional, Tuple

import tkinter as tk
from tkinter import ttk, filedialog, messagebox

from gui._shared import (
    C, F_BODY, F_BOLD, F_CODE, F_H2, F_MONO, F_SMALL,
    SDK_OK, SDK_ERROR, PANDAS_OK,
    NOPARS_STRATEGY_TABLE, CLEANING_PARS_TABLE, PARAM_META,
    CleaningStrategyAdapter,
    ColumnPickerDialog, SmartParamDialog,
    make_code_editor, make_treeview, make_listbox, section_sep,
)

try:
    import pandas as pd
except ImportError:
    pd = None  # type: ignore


class CleaningTab(ttk.Frame):

    def __init__(self, notebook: ttk.Notebook) -> None:
        super().__init__(notebook)
        self._df: Optional[Any] = None
        self._file_path: str = ""
        self._mode = tk.StringVar(value="text")
        self._chain: List[Tuple[str, str, Any]] = []   # (display, name, pars)
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
        p.rowconfigure(2, weight=1)
        p.rowconfigure(3, weight=1)

        tk.Label(p, text="① Input", font=F_H2,
                 bg=C["hdr_bg"], fg=C["hdr_fg"], anchor="w", padx=12, pady=8
                 ).grid(row=0, column=0, sticky="ew")

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

        # Text mode
        self._text_frame = tk.Frame(p, bg=C["surface"])
        self._text_frame.grid(row=2, column=0, sticky="nsew", padx=8, pady=6)
        self._text_frame.rowconfigure(1, weight=1)
        self._text_frame.columnconfigure(0, weight=1)
        tk.Label(self._text_frame, text="Paste your text below:", font=F_BOLD,
                 bg=C["surface"], fg=C["text_muted"], anchor="w").grid(row=0, column=0, sticky="w")
        ed_wrap, self._input_text = make_code_editor(self._text_frame, height=16)
        ed_wrap.grid(row=1, column=0, sticky="nsew")

        # File mode
        self._file_frame = tk.Frame(p, bg=C["surface"])
        self._file_frame.grid(row=3, column=0, sticky="nsew", padx=8, pady=6)
        self._file_frame.rowconfigure(5, weight=1)
        self._file_frame.columnconfigure(1, weight=1)

        tk.Button(self._file_frame, text="  📂  Load File (CSV / Excel)", font=F_BOLD,
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

    # ── Chain builder panel ───────────────────────────────────────────────────

    def _build_chain(self) -> None:
        p = self._chain_panel
        p.columnconfigure(0, weight=1)
        p.rowconfigure(2, weight=2)
        p.rowconfigure(5, weight=3)

        tk.Label(p, text="② Chain Builder", font=F_H2,
                 bg=C["hdr_bg"], fg=C["hdr_fg"], anchor="w", padx=12, pady=8
                 ).grid(row=0, column=0, sticky="ew")

        srow = tk.Frame(p, bg=C["bg"])
        srow.grid(row=1, column=0, sticky="ew", padx=8, pady=(8, 2))
        tk.Label(srow, text="Available:", font=F_SMALL,
                 bg=C["bg"], fg=C["text_muted"]).pack(side="left")
        tk.Label(srow, text="🔍", bg=C["bg"]).pack(side="right")
        self._search_var = tk.StringVar()
        self._search_var.trace_add("write", lambda *_: self._populate_available())
        ttk.Entry(srow, textvariable=self._search_var, width=14, font=F_BODY).pack(side="right", padx=2)

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
                 bg=C["bg"], fg=C["text_muted"]).grid(row=4, column=0, sticky="w", padx=8, pady=(4, 0))
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
                 bg=C["surface"], fg=C["text_muted"], anchor="w").grid(row=2, column=0, sticky="w", padx=10)
        out_wrap, self._output_text = make_code_editor(p, height=6)
        out_wrap.grid(row=2, column=0, sticky="nsew", padx=8, pady=(18, 4))

        tk.Label(p, text="Column result:", font=F_BOLD,
                 bg=C["surface"], fg=C["text_muted"], anchor="w").grid(row=3, column=0, sticky="w", padx=10, pady=(4, 0))
        res_wrap, self._result_tv = make_treeview(
            p, ("original", "result"),
            col_widths={"original": 210, "result": 210},
        )
        res_wrap.grid(row=4, column=0, sticky="nsew", padx=8, pady=(2, 8))
        self._result_tv.tag_configure("changed", background="#fffbeb")

    # ── Strategy list population ──────────────────────────────────────────────

    def _populate_available(self) -> None:
        q = self._search_var.get().lower() if hasattr(self, "_search_var") else ""
        self._avail_lb.delete(0, "end")
        for name in sorted(NOPARS_STRATEGY_TABLE):
            if not q or q in name.lower():
                self._avail_lb.insert("end", name)
        for name in sorted(CLEANING_PARS_TABLE):
            if not q or q in name.lower():
                self._avail_lb.insert("end", f"[P] {name}")

    # ── Chain operations ──────────────────────────────────────────────────────

    def _add_to_chain(self) -> None:
        sel = self._avail_lb.curselection()
        if not sel:
            return
        raw = self._avail_lb.get(sel[0])
        has_pars = raw.startswith("[P]")
        strategy_name = raw[4:] if has_pars else raw.strip()

        pars = None
        if has_pars:
            dlg = SmartParamDialog(self, strategy_name)
            if dlg.result is None:
                return
            pars = dlg.result

        if pars is None:
            display = strategy_name
        elif isinstance(pars, str):
            display = f"{strategy_name}({pars})"
        elif isinstance(pars, list) and pars and isinstance(pars[0], tuple):
            display = f"{strategy_name}({len(pars)} pairs)"
        else:
            display = f"{strategy_name}({', '.join(str(v) for v in pars)})"

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

    # ── Mode switching ─────────────────────────────────────────────────────────

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
