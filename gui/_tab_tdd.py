"""_tab_tdd.py — TDD Workbench tab."""
from __future__ import annotations

import threading
import traceback
from typing import Any, Dict, List, Optional, Tuple

import tkinter as tk
from tkinter import ttk, filedialog, messagebox

from gui._shared import (
    C, F_BODY, F_BOLD, F_H2, F_SMALL,
    SDK_OK, SDK_ERROR,
    MATCHING_TABLE, TwoSeriesComparisonContext,
    make_treeview, hdr_label, section_sep,
)


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

    # ── Editor (left) ─────────────────────────────────────────────────────────

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

    # ── Row operations ────────────────────────────────────────────────────────

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
        self._test_rows.clear()
        self._refresh_tv()

    def _import_csv(self) -> None:
        path = filedialog.askopenfilename(
            filetypes=[("CSV", "*.csv"), ("All", "*.*")])
        if not path:
            return
        import csv
        try:
            with open(path, newline="", encoding="utf-8-sig") as f:
                reader = csv.DictReader(f)
                for r in reader:
                    exp = str(r.get("expected", "true")).strip().lower() in ("true", "1", "yes")
                    self._test_rows.append({
                        "left": r.get("left", ""), "right": r.get("right", ""), "expected": exp})
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
            detail: list = []
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
            self.after(0, lambda d=detail: self._show_test_results(d))

        threading.Thread(target=_worker, daemon=True).start()

    def _show_test_results(self, detail: list) -> None:
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

        for i, d in enumerate(detail):
            self._tv.item(str(i), tags=("pass_row" if d["correct"] else "fail_row",))

        color = C["success"] if failed == 0 else C["danger"]
        self._summary_lbl.configure(
            text=f"  PASS {passed} / {len(detail)}   │   FAIL {failed} / {len(detail)}",
            fg=color)
        self._run_status.configure(
            text="ALL PASS ✓" if failed == 0 else f"{failed} FAIL(s) ✗",
            fg=color)
