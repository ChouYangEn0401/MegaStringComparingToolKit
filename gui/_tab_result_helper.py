"""_tab_result_helper.py — Matching Result Helper tab.

After running a match in Matching Lab you often need to:
  • For matched rows   → pull extra columns from Table A and/or Table B
  • For unmatched rows → keep rows that had no partner, with chosen columns

This tab lets you load both full tables, load (or import) the match result,
define which columns you want per scenario, then build and export the joined
output as CSV or Excel.
"""
from __future__ import annotations

import csv as _csv
import os
import traceback
from typing import Any, Callable, Dict, List, Optional, Set, Tuple

import tkinter as tk
from tkinter import ttk, filedialog, messagebox

try:
    import pandas as pd
    PANDAS_OK = True
except ImportError:
    pd = None  # type: ignore
    PANDAS_OK = False

from gui._shared import (
    C, F_BODY, F_BOLD, F_H2, F_SMALL, F_CODE,
    PANDAS_OK as _PD_OK,
    ColumnPickerDialog, SheetPickerDialog, MultiColumnPickerDialog,
    make_treeview, hdr_label,
)


# ─────────────────────────────────────────────────────────────────────────────
#  Small helpers
# ─────────────────────────────────────────────────────────────────────────────

def _load_df(parent: tk.Widget) -> Optional[Tuple["pd.DataFrame", str]]:
    """Open file dialog → load CSV or Excel sheet → return (df, path)."""
    path = filedialog.askopenfilename(
        filetypes=[("CSV", "*.csv"), ("Excel", "*.xlsx *.xls"), ("All", "*.*")])
    if not path:
        return None
    try:
        ext = os.path.splitext(path)[1].lower()
        if ext == ".csv":
            df = pd.read_csv(path, dtype=str, keep_default_na=False)
        else:
            xl = pd.ExcelFile(path)
            sheets = xl.sheet_names
            if len(sheets) == 1:
                df = pd.read_excel(path, sheet_name=sheets[0],
                                   dtype=str, keep_default_na=False)
            else:
                dlg = SheetPickerDialog(parent, sheets)
                if dlg.result is None:
                    return None
                df = pd.read_excel(path, sheet_name=dlg.result,
                                   dtype=str, keep_default_na=False)
        return df, path
    except Exception as exc:
        messagebox.showerror("Load error", str(exc))
        return None


def _save_df(df: "pd.DataFrame") -> None:
    path = filedialog.asksaveasfilename(
        defaultextension=".csv",
        filetypes=[("CSV", "*.csv"), ("Excel", "*.xlsx"), ("All", "*.*")],
    )
    if not path:
        return
    try:
        ext = os.path.splitext(path)[1].lower()
        if ext in (".xlsx", ".xls"):
            df.to_excel(path, index=False)
        else:
            df.to_csv(path, index=False, encoding="utf-8-sig")
        messagebox.showinfo("Exported", f"Saved to:\n{path}")
    except Exception as exc:
        messagebox.showerror("Save error", str(exc))


# Ensure DataFrame column labels are unique to avoid pandas merge errors.
def _ensure_unique_columns(df: "pd.DataFrame", suffix: str = "_dup") -> "pd.DataFrame":
    cols = list(df.columns)
    seen = {}
    new_cols = []
    for c in cols:
        if c in seen:
            seen[c] += 1
            # first duplicate gets suffix, subsequent duplicates get numeric suffix
            new_name = f"{c}{suffix}" if seen[c] == 1 else f"{c}{suffix}{seen[c]}"
            new_cols.append(new_name)
        else:
            seen[c] = 0
            new_cols.append(c)
    df.columns = new_cols
    return df


# ─────────────────────────────────────────────────────────────────────────────
#  TablePanel — reusable left/right table loader pane
# ─────────────────────────────────────────────────────────────────────────────

class _TablePanel(tk.Frame):
    """Load a table, remember df, let user pick the key column."""

    def __init__(self, parent: tk.Widget, title: str) -> None:
        super().__init__(parent, bg=C["surface"])
        self.df: Optional["pd.DataFrame"] = None
        self._path = ""
        self._key_var = tk.StringVar()
        self._build(title)

    def _build(self, title: str) -> None:
        self.columnconfigure(0, weight=1)
        self.rowconfigure(3, weight=1)

        tk.Label(self, text=title, font=F_H2,
                 bg=C["hdr_bg"], fg=C["hdr_fg"],
                 anchor="w", padx=12, pady=8).grid(row=0, column=0, sticky="ew")

        tk.Button(self, text="  📂  Load File (CSV / Excel)", font=F_BOLD,
                  bg=C["accent"], fg="#fff", relief="flat", cursor="hand2",
                  activebackground=C["accent_dk"], command=self._load
                  ).grid(row=1, column=0, sticky="ew", padx=8, pady=(8, 4))

        info = tk.Frame(self, bg=C["surface"])
        info.grid(row=2, column=0, sticky="ew", padx=8, pady=(0, 6))
        info.columnconfigure(1, weight=1)

        tk.Label(info, text="File:", font=F_SMALL,
                 bg=C["surface"], fg=C["text_muted"]).grid(row=0, column=0, sticky="w")
        self._file_lbl = tk.Label(info, text="(none)", font=F_CODE,
                                   bg=C["surface2"], fg=C["text_muted"],
                                   anchor="w", padx=4, relief="flat")
        self._file_lbl.grid(row=0, column=1, sticky="ew")

        tk.Label(info, text="Key column:", font=F_BOLD,
                 bg=C["surface"], fg=C["text"]).grid(row=1, column=0, sticky="w", pady=(4, 0))
        self._key_combo = ttk.Combobox(info, textvariable=self._key_var,
                                        state="disabled", font=F_BODY)
        self._key_combo.grid(row=1, column=1, sticky="ew", pady=(4, 0))

        tk.Label(self, text="Preview (first 6 rows):", font=F_BOLD,
                 bg=C["surface"], fg=C["text_muted"], anchor="w").grid(
                     row=3, column=0, sticky="w", padx=10, pady=(2, 0))

        self._preview_frame = tk.Frame(self, bg=C["surface"])
        self._preview_frame.grid(row=4, column=0, sticky="nsew", padx=8, pady=(2, 8))
        self.rowconfigure(4, weight=1)
        self._preview_frame.rowconfigure(0, weight=1)
        self._preview_frame.columnconfigure(0, weight=1)
        self._tv: Optional[ttk.Treeview] = None

    def _load(self) -> None:
        if not PANDAS_OK:
            messagebox.showerror("Missing dep", "pandas is required."); return
        res = _load_df(self)
        if res is None:
            return
        df, path = res
        self.df = df
        self._path = path
        self._file_lbl.configure(text=os.path.basename(path), fg=C["text"])
        cols = list(df.columns)
        self._key_combo.configure(state="readonly", values=cols)
        self._key_combo.current(0)
        self._refresh_preview()

    def _refresh_preview(self) -> None:
        if self.df is None:
            return
        # Destroy old treeview and rebuild for new column set
        for w in self._preview_frame.winfo_children():
            w.destroy()
        cols = list(self.df.columns)
        col_widths = {c: max(60, min(160, len(c) * 9)) for c in cols}
        tv_wrap, tv = make_treeview(
            self._preview_frame, tuple(cols), col_widths=col_widths)
        tv_wrap.grid(row=0, column=0, sticky="nsew")
        self._tv = tv
        for _, row in self.df.head(6).iterrows():
            tv.insert("", "end", values=tuple(str(row[c]) for c in cols))

    @property
    def key_column(self) -> Optional[str]:
        val = self._key_var.get()
        return val if val else None

    @property
    def columns(self) -> List[str]:
        return list(self.df.columns) if self.df is not None else []


# ─────────────────────────────────────────────────────────────────────────────
#  ResultHelperTab
# ─────────────────────────────────────────────────────────────────────────────

class ResultHelperTab(ttk.Frame):
    """
    Matching Result Helper.

    Workflow:
      ① Load Table A  (full data, pick key column)
      ② Load Table B  (full data, pick key column)
      ③ Load match results CSV or import from current session
      ④ Define per-scenario output columns → Build → Preview → Export
    """

    # Called by MatchingTab when results are ready so this tab can grab them
    _session_results: List[Tuple[str, str, float]] = []

    def __init__(self, notebook: ttk.Notebook,
                 get_match_results: Optional[Callable[[], List[Tuple[str, str, float]]]] = None
                 ) -> None:
        super().__init__(notebook)
        self._get_match_results = get_match_results
        self._match_df: Optional["pd.DataFrame"] = None   # query / best_match / score
        self._output_df: Optional["pd.DataFrame"] = None  # stacked (all scenarios)
        self._scenario_frames: Dict[str, "pd.DataFrame"] = {}  # key → df per scenario
        self._split_var = tk.BooleanVar(value=False)
        self._build()

    # ── Layout ───────────────────────────────────────────────────────────────

    def _build(self) -> None:
        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=2, minsize=220)
        self.columnconfigure(1, weight=2, minsize=220)
        self.columnconfigure(2, weight=2, minsize=260)
        self.columnconfigure(3, weight=3, minsize=320)

        self._pa = _TablePanel(self, "① Table A")
        self._pb = _TablePanel(self, "② Table B")
        self._pa.grid(row=0, column=0, sticky="nsew", padx=(0, 1))
        self._pb.grid(row=0, column=1, sticky="nsew", padx=1)

        self._pm = tk.Frame(self, bg=C["surface"])
        self._pm.grid(row=0, column=2, sticky="nsew", padx=1)
        self._build_match_panel()

        self._po = tk.Frame(self, bg=C["bg"])
        self._po.grid(row=0, column=3, sticky="nsew", padx=(1, 0))
        self._build_output_panel()

    # ── ③ Match results panel ─────────────────────────────────────────────

    def _build_match_panel(self) -> None:
        p = self._pm
        p.columnconfigure(0, weight=1)
        p.rowconfigure(4, weight=1)

        tk.Label(p, text="③ Match Results", font=F_H2,
                 bg=C["hdr_bg"], fg=C["hdr_fg"],
                 anchor="w", padx=12, pady=8).grid(row=0, column=0, sticky="ew")

        btn_bar = tk.Frame(p, bg=C["surface"])
        btn_bar.grid(row=1, column=0, sticky="ew", padx=8, pady=(8, 4))
        tk.Button(btn_bar, text="📂 Load from file", font=F_BOLD,
                  bg=C["accent"], fg="#fff", relief="flat", cursor="hand2",
                  activebackground=C["accent_dk"],
                  command=self._load_match_file).pack(side="left", padx=(0, 4))
        self._import_btn = tk.Button(
            btn_bar, text="⇩ Import from session", font=F_BODY,
            bg=C["surface"], fg=C["text"], relief="flat", cursor="hand2", bd=1,
            activebackground=C["accent_lt"],
            command=self._import_from_session)
        self._import_btn.pack(side="left")

        info = tk.Frame(p, bg=C["surface"])
        info.grid(row=2, column=0, sticky="ew", padx=8)
        info.columnconfigure(1, weight=1)
        tk.Label(info, text="Source:", font=F_SMALL,
                 bg=C["surface"], fg=C["text_muted"]).grid(row=0, column=0, sticky="w")
        self._match_src_lbl = tk.Label(info, text="(none)", font=F_CODE,
                                        bg=C["surface2"], fg=C["text_muted"],
                                        anchor="w", padx=4, relief="flat")
        self._match_src_lbl.grid(row=0, column=1, sticky="ew")

        tk.Label(p, text="Preview:", font=F_BOLD,
                 bg=C["surface"], fg=C["text_muted"], anchor="w").grid(
                     row=3, column=0, sticky="w", padx=10, pady=(6, 2))

        prev_frame = tk.Frame(p, bg=C["surface"])
        prev_frame.grid(row=4, column=0, sticky="nsew", padx=8, pady=(0, 8))
        prev_frame.rowconfigure(0, weight=1)
        prev_frame.columnconfigure(0, weight=1)
        tv_wrap, self._match_tv = make_treeview(
            prev_frame, ("query", "best_match", "score"),
            col_widths={"query": 120, "best_match": 120, "score": 60},
            col_anchors={"score": "center"},
        )
        tv_wrap.grid(row=0, column=0, sticky="nsew")

    # ── ④ Output config + preview panel ──────────────────────────────────

    def _build_output_panel(self) -> None:
        p = self._po
        p.columnconfigure(0, weight=1)
        p.rowconfigure(6, weight=1)

        tk.Label(p, text="④ Output Builder", font=F_H2,
                 bg=C["hdr_bg"], fg=C["hdr_fg"],
                 anchor="w", padx=12, pady=8).pack(fill="x")

        inner = tk.Frame(p, bg=C["bg"])
        inner.pack(fill="both", expand=True, padx=6, pady=6)
        inner.columnconfigure(1, weight=1)

        # Scenario rows: matched / unmatched_a / unmatched_b
        scenarios = [
            ("matched",     "✅ Matched"),
            ("unmatched_a", "❌ Unmatched A"),
            ("unmatched_b", "❌ Unmatched B"),
        ]
        self._col_selections: Dict[str, Dict[str, List[str]]] = {
            s: {"a": [], "b": []} for s, _ in scenarios
        }
        self._col_lbl_widgets: Dict[str, Dict[str, tk.Label]] = {}

        for row_i, (key, label) in enumerate(scenarios):
            base = row_i * 3
            tk.Label(inner, text=label, font=F_BOLD,
                     bg=C["bg"], fg=C["text"], anchor="w"
                     ).grid(row=base, column=0, columnspan=3,
                            sticky="w", padx=4, pady=(10 if row_i else 4, 2))

            self._col_lbl_widgets[key] = {}

            for col_i, (tbl, tbl_lbl) in enumerate([("a", "Table A cols"), ("b", "Table B cols")]):
                tk.Label(inner, text=f"  {tbl_lbl}:", font=F_SMALL,
                         bg=C["bg"], fg=C["text_muted"]).grid(
                             row=base + 1 + col_i, column=0, sticky="e", padx=4)
                lbl = tk.Label(inner, text="(none)", font=F_SMALL,
                               bg=C["surface2"], fg=C["text_muted"],
                               anchor="w", padx=6, relief="flat")
                lbl.grid(row=base + 1 + col_i, column=1, sticky="ew", padx=2)
                self._col_lbl_widgets[key][tbl] = lbl

                # closure capture
                def _make_picker(k=key, tb=tbl, lb=lbl):
                    def _pick():
                        panel = self._pa if tb == "a" else self._pb
                        if panel.df is None:
                            messagebox.showwarning(
                                "No table", f"Load Table {'A' if tb=='a' else 'B'} first.")
                            return
                        dlg = MultiColumnPickerDialog(
                            self, panel.columns,
                            title=f"Columns from Table {'A' if tb=='a' else 'B'} — {k}",
                            prompt=f"Choose columns to include for \"{k}\" rows:",
                            preselect=self._col_selections[k][tb],
                        )
                        if dlg.result is not None:
                            self._col_selections[k][tb] = dlg.result
                            lb.configure(
                                text=", ".join(dlg.result) if dlg.result else "(none)",
                                fg=C["text"] if dlg.result else C["text_muted"])
                    return _pick

                ttk.Button(inner, text="Pick…", command=_make_picker()
                           ).grid(row=base + 1 + col_i, column=2, padx=2)

        tk.Frame(inner, bg=C["border"], height=1).grid(
            row=9, column=0, columnspan=3, sticky="ew", padx=4, pady=6)

        # Build button
        tk.Button(inner, text="  ▶  Build Output", font=F_BOLD,
                  bg=C["success"], fg="#fff", relief="flat", cursor="hand2",
                  activebackground="#059669",
                  command=self._build_output,
                  ).grid(row=10, column=0, columnspan=3, sticky="ew", padx=4, pady=(8, 4))
        ttk.Button(inner, text="Export (CSV / Excel)",
                   command=self._export).grid(
                       row=11, column=0, columnspan=3, sticky="ew", padx=4)

        ttk.Checkbutton(
            inner, text="Separate sheets per scenario (Excel only)",
            variable=self._split_var,
        ).grid(row=12, column=0, columnspan=3, sticky="w", padx=6, pady=(4, 0))

        self._build_status = tk.Label(inner, text="", font=F_SMALL,
                                       bg=C["bg"], fg=C["text_muted"])
        self._build_status.grid(row=13, column=0, columnspan=3)

        self._dup_warn_lbl = tk.Label(inner, text="", font=F_SMALL,
                                      bg=C["bg"], fg=C["warning"], wraplength=280, justify="left")
        self._dup_warn_lbl.grid(row=14, column=0, columnspan=3, pady=(0, 4))

        tk.Frame(inner, bg=C["border"], height=1).grid(
            row=15, column=0, columnspan=3, sticky="ew", padx=4, pady=6)

        tk.Label(inner, text="Preview:", font=F_BOLD,
                 bg=C["bg"], fg=C["text_muted"], anchor="w").grid(
                     row=16, column=0, columnspan=3, sticky="w", padx=4, pady=(4, 0))

        out_frame = tk.Frame(inner, bg=C["bg"])
        out_frame.grid(row=17, column=0, columnspan=3, sticky="nsew", padx=4, pady=(2, 4))
        inner.rowconfigure(17, weight=1)
        out_frame.rowconfigure(0, weight=1)
        out_frame.columnconfigure(0, weight=1)
        self._out_tv_wrap = out_frame   # rebuilt on each _build_output call

    # ── Load match results ────────────────────────────────────────────────

    def _load_match_file(self) -> None:
        if not PANDAS_OK:
            messagebox.showerror("Missing dep", "pandas is required."); return
        res = _load_df(self)
        if res is None:
            return
        df, path = res
        self._set_match_df(df, os.path.basename(path))

    def _import_from_session(self) -> None:
        if self._get_match_results is None:
            messagebox.showinfo("Not available",
                                "Open this tab from the main app to enable session import.")
            return
        rows = self._get_match_results()
        if not rows:
            messagebox.showwarning("Empty", "No match results in the current session.\n"
                                   "Run a match in Matching Lab first.")
            return
        df = pd.DataFrame(rows, columns=["query", "best_match", "score"])
        self._set_match_df(df, "session")

    def _set_match_df(self, df: "pd.DataFrame", source: str) -> None:
        # Normalise: ensure we have query / best_match / score columns
        cols_lower = {c.lower().replace(" ", "_"): c for c in df.columns}
        rename = {}
        for need, alts in [
            ("query",      ["query", "str1", "a", "input"]),
            ("best_match", ["best_match", "match", "str2", "b", "result"]),
            ("score",      ["score", "similarity", "ratio"]),
        ]:
            if need not in df.columns:
                for alt in alts:
                    if alt in cols_lower:
                        rename[cols_lower[alt]] = need
                        break
        if rename:
            df = df.rename(columns=rename)
        if "query" not in df.columns or "best_match" not in df.columns:
            messagebox.showerror("Bad format",
                                 "File must have columns: query, best_match (and optionally score).\n"
                                 f"Found: {list(df.columns)}")
            return
        if "score" not in df.columns:
            df["score"] = ""
        self._match_df = df
        self._match_src_lbl.configure(text=source, fg=C["text"])
        for item in self._match_tv.get_children():
            self._match_tv.delete(item)
        for _, row in df.head(10).iterrows():
            self._match_tv.insert("", "end",
                values=(str(row["query"]), str(row["best_match"]), str(row["score"])))

    # ── Build output ──────────────────────────────────────────────────────

    def _build_output(self) -> None:
        # Validate inputs
        if self._match_df is None:
            messagebox.showwarning("Missing", "Load match results (step ③)."); return
        ta_ok = self._pa.df is not None and self._pa.key_column
        tb_ok = self._pb.df is not None and self._pb.key_column

        match_df = self._match_df.copy()
        if "score" not in match_df.columns:
            match_df["score"] = None

        matched_queries: Set[str] = set(match_df["query"].dropna().astype(str))
        matched_refs:    Set[str] = set(match_df["best_match"].dropna().astype(str))

        frames: List["pd.DataFrame"] = []

        # ── scenario: matched ─────────────────────────────────────────────
        sel_a = self._col_selections["matched"]["a"]
        sel_b = self._col_selections["matched"]["b"]

        if sel_a or sel_b:
            base = match_df[["query", "best_match", "score"]].copy()
            if sel_a and ta_ok:
                a_sub = self._pa.df[[self._pa.key_column] + [
                    c for c in sel_a if c != self._pa.key_column]].copy()
                a_sub = a_sub.rename(columns={self._pa.key_column: "query"})
                # Make sure columns are unique (user may have selected another column named 'query')
                a_sub = _ensure_unique_columns(a_sub, suffix="_A")
                base = base.merge(a_sub, on="query", how="left", suffixes=("", "_A"))
            if sel_b and tb_ok:
                b_sub = self._pb.df[[self._pb.key_column] + [
                    c for c in sel_b if c != self._pb.key_column]].copy()
                b_sub = b_sub.rename(columns={self._pb.key_column: "best_match"})
                # Ensure unique column labels to avoid duplicate-name errors
                b_sub = _ensure_unique_columns(b_sub, suffix="_B")
                base = base.merge(b_sub, on="best_match", how="left", suffixes=("", "_B"))
            base.insert(0, "_scenario", "matched")
            frames.append(base)

        # ── scenario: unmatched A ─────────────────────────────────────────
        sel_ua = self._col_selections["unmatched_a"]["a"]
        sel_ub_ua = self._col_selections["unmatched_a"]["b"]

        if (sel_ua or sel_ub_ua) and ta_ok:
            ka = self._pa.key_column
            all_a_keys = self._pa.df[ka].dropna().astype(str)
            unmatched_a_keys = all_a_keys[~all_a_keys.isin(matched_queries)]
            unmatched_a = self._pa.df[self._pa.df[ka].astype(str).isin(unmatched_a_keys)]
            cols_needed = [c for c in sel_ua if c in unmatched_a.columns]
            if cols_needed:
                ua_out = unmatched_a[[ka] + [c for c in cols_needed if c != ka]].copy()
                ua_out = ua_out.rename(columns={ka: "query"})
                # Ensure unique columns to avoid collisions when concatenating
                ua_out = _ensure_unique_columns(ua_out, suffix="_A")
                ua_out["best_match"] = ""
                ua_out["score"] = ""
                ua_out.insert(0, "_scenario", "unmatched_A")
                frames.append(ua_out)

        # ── scenario: unmatched B ─────────────────────────────────────────
        sel_ub = self._col_selections["unmatched_b"]["b"]
        sel_ua_ub = self._col_selections["unmatched_b"]["a"]

        if (sel_ub or sel_ua_ub) and tb_ok:
            kb = self._pb.key_column
            all_b_keys = self._pb.df[kb].dropna().astype(str)
            unmatched_b_keys = all_b_keys[~all_b_keys.isin(matched_refs)]
            unmatched_b = self._pb.df[self._pb.df[kb].astype(str).isin(unmatched_b_keys)]
            cols_needed = [c for c in sel_ub if c in unmatched_b.columns]
            if cols_needed:
                ub_out = unmatched_b[[kb] + [c for c in cols_needed if c != kb]].copy()
                ub_out = ub_out.rename(columns={kb: "best_match"})
                # Ensure unique columns to avoid collisions when concatenating
                ub_out = _ensure_unique_columns(ub_out, suffix="_B")
                ub_out["query"] = ""
                ub_out["score"] = ""
                ub_out.insert(0, "_scenario", "unmatched_B")
                frames.append(ub_out)

        if not frames:
            messagebox.showwarning("Nothing selected",
                                   "Pick at least one output column for at least one scenario.")
            return

        # Store individual scenario frames for separate-sheet export
        self._scenario_frames = {
            f["_scenario"].iloc[0]: f for f in frames
        }
        self._output_df = pd.concat(frames, ignore_index=True).fillna("")

        # ── Duplicate key detection ────────────────────────────────────────
        dup_msgs: List[str] = []
        for sc_name, sc_df in self._scenario_frames.items():
            key_col = "query" if sc_name in ("matched", "unmatched_A") else "best_match"
            if key_col in sc_df.columns:
                dup_mask = sc_df[key_col].duplicated(keep=False) & (sc_df[key_col] != "")
                if dup_mask.any():
                    dup_vals = sc_df.loc[dup_mask, key_col].unique().tolist()[:5]
                    sample = ", ".join(f'"{v}"' for v in dup_vals)
                    more = f" … (+{len(sc_df.loc[dup_mask, key_col].unique()) - 5} more)" \
                           if len(sc_df.loc[dup_mask, key_col].unique()) > 5 else ""
                    dup_msgs.append(f"{sc_name}: duplicated keys [{sample}{more}]")

        if dup_msgs:
            self._dup_warn_lbl.configure(
                text="⚠ Duplicate keys detected (preserved from source):\n" + "\n".join(dup_msgs))
        else:
            self._dup_warn_lbl.configure(text="")

        self._refresh_output_preview()
        n = len(self._output_df)
        summary = ", ".join(
            f"{sc}: {len(df)}" for sc, df in self._scenario_frames.items()
        )
        self._build_status.configure(
            text=f"Built ✓  {n} total rows  ({summary})",
            fg=C["success"])

    def _refresh_output_preview(self) -> None:
        if self._output_df is None:
            return
        for w in self._out_tv_wrap.winfo_children():
            w.destroy()
        self._out_tv_wrap.rowconfigure(0, weight=1)
        self._out_tv_wrap.columnconfigure(0, weight=1)

        if len(self._scenario_frames) <= 1:
            # Single scenario → plain treeview
            df = self._output_df
            cols = list(df.columns)
            widths = {c: max(60, min(160, len(c) * 9)) for c in cols}
            tv_wrap, tv = make_treeview(self._out_tv_wrap, tuple(cols), col_widths=widths)
            tv_wrap.grid(row=0, column=0, sticky="nsew")
            for _, row in df.head(20).iterrows():
                tv.insert("", "end", values=tuple(str(row[c]) for c in cols))
        else:
            # Multiple scenarios → mini notebook for preview
            inner_nb = ttk.Notebook(self._out_tv_wrap)
            inner_nb.grid(row=0, column=0, sticky="nsew")
            for sc_name, sc_df in self._scenario_frames.items():
                tab = tk.Frame(inner_nb, bg=C["bg"])
                tab.rowconfigure(0, weight=1)
                tab.columnconfigure(0, weight=1)
                cols = list(sc_df.columns)
                widths = {c: max(60, min(160, len(c) * 9)) for c in cols}
                tv_wrap, tv = make_treeview(tab, tuple(cols), col_widths=widths)
                tv_wrap.grid(row=0, column=0, sticky="nsew")
                for _, row in sc_df.head(20).iterrows():
                    tv.insert("", "end", values=tuple(str(row[c]) for c in cols))
                inner_nb.add(tab, text=f"  {sc_name}  ")

    def _export(self) -> None:
        if self._output_df is None or self._output_df.empty:
            messagebox.showinfo("Nothing", "Build the output first."); return

        if self._split_var.get() and self._scenario_frames:
            # Separate sheets — must be Excel
            path = filedialog.asksaveasfilename(
                defaultextension=".xlsx",
                filetypes=[("Excel", "*.xlsx"), ("All", "*.*")],
                title="Export — separate sheets (Excel only)",
            )
            if not path:
                return
            try:
                with pd.ExcelWriter(path, engine="openpyxl") as writer:
                    for sc_name, sc_df in self._scenario_frames.items():
                        sheet_name = sc_name[:31]  # Excel sheet name limit
                        sc_df.to_excel(writer, sheet_name=sheet_name, index=False)
                messagebox.showinfo("Exported",
                    f"Saved to:\n{path}\n\nSheets: {', '.join(self._scenario_frames)}"
                )
            except Exception as exc:
                messagebox.showerror("Save error", str(exc))
        else:
            _save_df(self._output_df)
