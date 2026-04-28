"""_tab_matching.py — Matching Lab tab."""
from __future__ import annotations

import csv as _csv
import os
import threading
import traceback
from typing import List, Optional, Tuple

import tkinter as tk
from tkinter import ttk, filedialog, messagebox

from gui._shared import (
    C, F_BODY, F_BOLD, F_H2, F_SMALL,
    SDK_OK, SDK_ERROR, PANDAS_OK,
    MATCHING_TABLE, sdk_match,
    ColumnPickerDialog,
    make_code_editor, make_treeview, hdr_label, section_sep,
)

try:
    import pandas as pd
except ImportError:
    pd = None  # type: ignore


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
        with open(path, "w", newline="", encoding="utf-8-sig") as f:
            w = _csv.writer(f)
            w.writerow(["query", "best_match", "score"])
            w.writerows((q, r, f"{s:.4f}") for q, r, s in self._result_data)
        messagebox.showinfo("Exported", f"Saved to:\n{path}")
