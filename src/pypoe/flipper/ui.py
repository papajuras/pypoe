from __future__ import annotations

import threading
import time
from datetime import datetime, timezone
from pathlib import Path

from nicegui import ui

from pypoe.db.config import get_meta, set_meta
from pypoe.config import read_league

from .client import TradeClient
from .ninja import NinjaClient
from .pricer import PriceFetcher
from .store import Flip, Store, _extract_query

store = Store()
_pricer: PriceFetcher = None  # type: ignore[assignment]
_ninja: NinjaClient = None  # type: ignore[assignment]


def _init_pricer():
    global _pricer, _ninja
    if _pricer is not None:
        return
    poesessid = Path("ignore/POESESSID").read_text().strip()
    client = TradeClient("OAuth pypoe/0.1.0 (flipper)")
    client.session.cookies.set("POESESSID", poesessid, domain="www.pathofexile.com")
    _ninja = NinjaClient()
    _pricer = PriceFetcher(client, store)


COLS = [
    {"key": "name", "label": "Name"},
    {"key": "cost", "label": "Cost"},
    {"key": "profit", "label": "Profit"},
    {"key": "pct", "label": "Profit %"},
]


class FlipperPanel:
    def __init__(self):
        _init_pricer()
        self._sort_by = "profit"
        self._sort_asc = False
        self._form_open = False
        self._solver_status = ""
        self._container = ui.column().classes("w-full gap-3")
        with self._container:
            self._build()
        ui.timer(3, self._tick)

    def _tick(self):
        if not self._form_open:
            self._rebuild()

    def _rebuild(self):
        self._container.clear()
        with self._container:
            self._build()

    def _build(self):
        with ui.row().classes("items-center gap-4 w-full"):
            ui.label("Flipper").classes("text-h5 text-weight-bold")
            ui.button("New flip", icon="add", on_click=self._create).props("unelevated color=positive")
            self._queue_label = ui.label(f"queue: {_pricer.queue_size}").classes("text-caption text-grey-7")
            for q in (30, 29, 28, 27):
                enabled = get_meta(f"flipper_quality_{q}", True)
                ui.checkbox(text=f"Q{q}", value=enabled,
                            on_change=lambda e, q=q: set_meta(f"flipper_quality_{q}", e.value)
                ).props("dense")
            ui.label("").classes("flex-1")


        rate_limits = _pricer._client.rate_limits
        with ui.row().classes("items-center gap-2 text-caption"):
            if rate_limits:
                for entry in rate_limits:
                    color = "text-positive" if entry["pct"] < 50 else "text-warning" if entry["pct"] < 80 else "text-negative"
                    ui.label(entry["label"]).classes(f"cursor-help {color}").tooltip(entry["tooltip"])
            else:
                ui.label("Waiting for API data...").classes("text-caption text-grey-5")
            if _pricer._client._sync._backoff_until > time.time():
                remaining = int(_pricer._client._sync._backoff_until - time.time())
                ui.label(f"🔒 Backoff {remaining}s").classes("text-negative text-caption font-weight-bold")

        if _pricer._cloudflare_blocked:
            with ui.row().classes("items-center gap-2 w-full bg-yellow-2 p-3 rounded border border-yellow-6"):
                ui.label("🔒 Cloudflare challenge detected").classes("text-weight-bold text-yellow-9")
                if self._solver_status:
                    ui.label(self._solver_status).classes("text-caption text-grey-7")
                else:
                    ui.button("Solve with browser", icon="open_in_new", on_click=self._open_solver).props("unelevated dense")
                cf_input = ui.input(placeholder="cf_clearance cookie").classes("w-48 font-mono")
                ui.button("Apply & resume", icon="check", on_click=lambda: _pricer.resume_after_cloudflare(cf_input.value)).props("unelevated color=positive dense")

        flips = store.list()
        if not flips:
            ui.label("No flips yet.").classes("text-grey-6 text-caption mt-2")
            return

        rows = []
        for f in flips:
            p = store.get_price(f.id)
            rows.append(self._row_data(f, p))

        fresh_en = [r for r in rows if r["flip"].enabled and not r["stale"]]
        stale_en = [r for r in rows if r["flip"].enabled and r["stale"]]
        disabled = [r for r in rows if not r["flip"].enabled]

        liquid = [r for r in fresh_en if r["liquid"]]
        illiquid = [r for r in fresh_en if not r["liquid"]]

        if liquid:
            self._sort_rows(liquid)
            self._build_section("Liquid", liquid)
        if illiquid:
            self._sort_rows(illiquid)
            self._build_section("Illiquid", illiquid)
        if stale_en:
            self._sort_rows(stale_en)
            self._build_section("Stale", stale_en, muted=True)
        if disabled:
            self._sort_rows(disabled)
            self._build_section("Disabled", disabled, muted=True)

    def _toggle(self, flip, value):
        flip.enabled = value
        store.put(flip)
        self._rebuild()

    def _open_solver(self):
        self._solver_status = "Opening browser..."
        poesessid = Path("ignore/POESESSID").read_text().strip()
        threading.Thread(target=self._solver_thread, args=(poesessid,), daemon=True).start()

    def _solver_thread(self, poesessid):
        try:
            _pricer._client.solve_challenge()
            _pricer.resume_after_cloudflare("")
            self._solver_status = ""
        except Exception:
            self._solver_status = "Timed out — paste cookie manually"

    def _row_data(self, f: Flip, p: dict | None) -> dict:
        cost = None
        profit = None
        profit_pct = None
        liquid = False

        if p:
            src = p["source_avg"]
            tgt = p["target_avg"]
            if src > 0 and tgt > 0:
                cost = src + f.cost
                revenue = tgt * f.multiplier
                profit = revenue - cost
                profit_pct = (profit / cost * 100) if cost > 0 else None
                liquid = True

        stale = True
        age_h = None
        fa = p.get("fetched_at") if p else None
        if fa:
            try:
                dt = datetime.strptime(fa, "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
                age_h = (datetime.now(timezone.utc) - dt).total_seconds() / 3600
                stale = age_h > 4.0
            except ValueError:
                pass

        return {
            "flip": f,
            "has_data": p is not None,
            "cost": cost,
            "profit": profit,
            "pct": profit_pct,
            "liquid": liquid,
            "fetched_at": fa,
            "stale": stale,
            "age_h": age_h,
        }

    def _sort_rows(self, rows: list[dict]):
        key = self._sort_by
        rows.sort(key=lambda r: (r.get(key) is None, r.get(key) or 0), reverse=not self._sort_asc)

    def _build_section(self, title: str, rows: list[dict], muted: bool = False):
        cls = "text-grey-5" if muted else ""
        ui.label(title).classes(f"text-weight-bold text-caption mt-4 {cls}")
        self._build_header()
        for r in rows:
            self._build_row(r)

    def _build_header(self):
        with ui.row().classes("items-center gap-2 w-full text-weight-bold text-caption"):
            ui.label("").classes("w-[30px]")
            ui.label("Name").classes("w-[200px]")
            for col in COLS[1:]:
                text = col["label"]
                if col["key"] == self._sort_by:
                    text += " ↑" if self._sort_asc else " ↓"
                ui.label(text).classes("w-[70px] cursor-pointer").on("click", lambda c=col: self._sort_click(c["key"]))
            ui.label("Actions").classes("w-[80px] whitespace-nowrap")

    def _build_row(self, r: dict):
        f = r["flip"]
        name = f.name or "[Unnamed]"
        row_cls = "text-grey-5" if not f.enabled else ""
        freshness = None
        fa = r.get("fetched_at")
        if fa:
            try:
                dt = datetime.strptime(fa, "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
                age_h = (datetime.now(timezone.utc) - dt).total_seconds() / 3600
                t = min(age_h / 4.0, 1.0)
                hue = int(120 * (1 - t))
                freshness = (hue, age_h)
            except ValueError:
                pass
        with ui.row().classes(f"items-center gap-2 w-full {row_cls}"):
            if f.notes:
                ui.tooltip(f.notes)
            ui.checkbox(value=f.enabled, on_change=lambda e, f=f: self._toggle(f, e.value)).props("dense").classes("w-[30px]")
            with ui.row().classes("items-center gap-1 w-[200px]"):
                ui.label(name).classes("font-mono text-caption")
                if f.source_type == "ninja" or f.target_type == "ninja":
                    ui.label("[ninja]").style("background-color: #6b21a8; color: white; padding: 0 4px; border-radius: 3px; font-size: 0.7em").classes("font-mono")
            ui.label(self._fmt_cost(r)).classes("w-[70px] font-mono text-caption")
            ui.label(self._fmt_profit(r)).classes(f"w-[70px] font-mono text-caption {self._profit_class(r)}")
            ui.label(self._fmt_pct(r)).classes(f"w-[70px] font-mono text-caption {self._profit_class(r)}")
            if freshness:
                hue, age_h = freshness
                btn = ui.button(icon="refresh", on_click=lambda f=f: _pricer.enqueue(f.id, front=True)).props("dense size=sm")
                btn.style(f"background: hsl({hue}, 55%, 40%) !important; color: white !important;")
                with btn:
                    ui.tooltip(f"{age_h:.1f}h old")
            else:
                ui.button(icon="refresh", on_click=lambda f=f: _pricer.enqueue(f.id, front=True)).props("flat dense size=sm")
            ui.button(icon="edit", on_click=lambda f=f: self._edit(f)).props("flat dense size=sm")
            ui.button(icon="delete", on_click=lambda f=f: self._delete(f)).props("flat dense size=sm text-negative")

    def _sort_click(self, key: str):
        if self._sort_by == key:
            self._sort_asc = not self._sort_asc
        else:
            self._sort_by = key
            self._sort_asc = False
        self._rebuild()

    def _fmt_cost(self, r: dict) -> str:
        if not r["has_data"]:
            return "no data"
        if not r["liquid"]:
            return "illiquid"
        return f'{r["cost"]:.1f}d'

    def _fmt_profit(self, r: dict) -> str:
        if not r["has_data"]:
            return "no data"
        if not r["liquid"]:
            return "illiquid"
        v = r["profit"]
        return f'{v:+.1f}d' if v is not None else "—"

    def _fmt_pct(self, r: dict) -> str:
        if not r["has_data"]:
            return "no data"
        if not r["liquid"]:
            return "illiquid"
        v = r["pct"]
        return f'{v:+.0f}%' if v is not None else "—"

    def _profit_class(self, r: dict) -> str:
        if not r["liquid"] or r["profit"] is None:
            return "text-grey-6"
        return "text-positive" if r["profit"] >= 0 else "text-negative"

    def _create(self):
        self._editing = None
        self._show_form(Flip())

    def _edit(self, flip: Flip):
        self._editing = flip
        draft = Flip(
            name=flip.name,

            source_type=flip.source_type,
            source_queries=list(flip.source_queries),
            source_ninja_item=flip.source_ninja_item,
            source_ninja_type=flip.source_ninja_type,
            target_type=flip.target_type,
            target_queries=list(flip.target_queries),
            target_ninja_item=flip.target_ninja_item,
            target_ninja_type=flip.target_ninja_type,
            multiplier=flip.multiplier,
            cost=flip.cost,
            enabled=flip.enabled,
            notes=flip.notes,
        )
        self._show_form(draft)

    def _delete(self, flip: Flip):
        store.delete(flip.id)
        self._rebuild()

    def _show_form(self, draft: Flip):
        self._form_open = True
        all_items = _ninja.item_options(read_league())
        ninja_types = ["DivinationCard", "Currency"]

        def _ninja_opts(filter_type: str) -> dict[str, str]:
            return {
                i["name"]: f"{i['name']}  ({i['divine_value']:.2f}d)"
                for i in all_items if i["type"] == filter_type
            }

        def _close():
            self._form_open = False
            dialog.close()

        def _side_ninja(type_attr: str, item_attr: str, initial_type: str, initial_item: str):
            type_radio = ui.radio(
                ninja_types,
                value=initial_type,
            ).props("inline")
            sel = ui.select(
                label="Search item...",
                options=_ninja_opts(initial_type),
                with_input=True, clearable=True,
                value=initial_item or None,
            ).classes("w-full").props("use-input hide-selected")
            type_radio.on_value_change(lambda e: _set_opts(sel, e.value))
            return type_radio, sel

        def _set_opts(sel: ui.select, type_key: str):
            sel.options = _ninja_opts(type_key)
            sel.value = None
            sel.update()

        with ui.dialog() as dialog, ui.card().classes("p-6 min-w-[600px] max-w-[800px]"):
            ui.label("New flip" if self._editing is None else "Edit flip").classes("text-h6")
            name_input = ui.input("Flip name", value=draft.name).classes("w-full")
            name_error = ui.label("Name is required").classes("text-negative text-caption").set_visibility(False)
            notes_input = ui.textarea("Notes", value=draft.notes).classes("w-full").props("rows=2")

            with ui.row().classes("items-center gap-4 w-full"):
                with ui.column().classes("flex-1"):
                    ui.label("Multiplier").classes("text-weight-medium")
                    multiplier = ui.slider(min=0, max=10, step=0.0001, value=draft.multiplier).classes("w-full")
                    mult_input = ui.number(label="", value=draft.multiplier, min=0, max=999, step=0.0001, format="%.4f").classes("w-32")
                    multiplier.bind_value_to(mult_input, "value")
                    mult_input.bind_value_to(multiplier, "value")
                with ui.column():
                    ui.label("Cost (divines)").classes("text-weight-medium")
                    cost_input = ui.number(label="Cost", value=float(draft.cost), min=0, step=1).classes("w-32")

            # ── source ─────────────────────────────────────────
            ui.label("Source — items to acquire").classes("text-weight-medium mt-4")
            src_mode = ui.radio(
                ["Trade API", "poe.ninja"],
                value="Trade API" if draft.source_type == "query" else "poe.ninja",
            ).props("inline")

            src_query_box = ui.column().classes("w-full gap-1")
            src_ninja_box = ui.column().classes("w-full gap-1")
            src_inputs: list[ui.textarea] = []

            def _add_src():
                inp = ui.textarea(value="").classes("w-full font-mono")
                inp.style("min-height: 3em")
                src_inputs.append(inp)

            with src_query_box:
                for q in draft.source_queries:
                    inp = ui.textarea(value=q).classes("w-full font-mono")
                    inp.style("min-height: 3em")
                    src_inputs.append(inp)
                ui.button(icon="add", text="Query URL", on_click=_add_src).props("flat dense")

            with src_ninja_box:
                src_type_radio, src_select = _side_ninja(
                    "source_ninja_type", "source_ninja_item",
                    draft.source_ninja_type, draft.source_ninja_item,
                )

            src_query_box.set_visibility(draft.source_type == "query")
            src_ninja_box.set_visibility(draft.source_type == "ninja")
            src_mode.on_value_change(lambda e: _toggle_side(e.value, draft, "source_type", "source", src_query_box, src_ninja_box))

            # ── target ─────────────────────────────────────────
            ui.label("Target — items to sell").classes("text-weight-medium mt-4")
            tgt_mode = ui.radio(
                ["Trade API", "poe.ninja"],
                value="Trade API" if draft.target_type == "query" else "poe.ninja",
            ).props("inline")

            tgt_query_box = ui.column().classes("w-full gap-1")
            tgt_ninja_box = ui.column().classes("w-full gap-1")
            tgt_inputs: list[ui.textarea] = []

            def _add_tgt():
                inp = ui.textarea(value="").classes("w-full font-mono")
                inp.style("min-height: 3em")
                tgt_inputs.append(inp)

            with tgt_query_box:
                for q in draft.target_queries:
                    inp = ui.textarea(value=q).classes("w-full font-mono")
                    inp.style("min-height: 3em")
                    tgt_inputs.append(inp)
                ui.button(icon="add", text="Query URL", on_click=_add_tgt).props("flat dense")

            with tgt_ninja_box:
                tgt_type_radio, tgt_select = _side_ninja(
                    "target_ninja_type", "target_ninja_item",
                    draft.target_ninja_type, draft.target_ninja_item,
                )

            tgt_query_box.set_visibility(draft.target_type == "query")
            tgt_ninja_box.set_visibility(draft.target_type == "ninja")
            tgt_mode.on_value_change(lambda e: _toggle_side(e.value, draft, "target_type", "target", tgt_query_box, tgt_ninja_box))

            ui.separator().classes("mt-4")

            def _toggle_side(mode: str, d, ta: str, prefix: str, qbox, nbox):
                setattr(d, ta, "ninja" if mode == "poe.ninja" else "query")
                qbox.set_visibility(getattr(d, ta) == "query")
                nbox.set_visibility(getattr(d, ta) == "ninja")

            def save():
                draft.name = name_input.value.strip()
                if not draft.name:
                    name_input.classes(add="border-negative")
                    name_error.set_visibility(True)
                    return
                name_input.classes(remove="border-negative")
                name_error.set_visibility(False)
                draft.multiplier = multiplier.value
                draft.cost = int(cost_input.value or 0)
                draft.notes = notes_input.value.strip()
                if draft.source_type == "query":
                    src = [_extract_query(i.value) for i in src_inputs if i.value.strip()]
                    draft.source_queries = [q for q, _ in src]
                    draft.source_ninja_item = ""
                else:
                    draft.source_ninja_item = src_select.value or ""
                    draft.source_ninja_type = src_type_radio.value
                    draft.source_queries.clear()
                if draft.target_type == "query":
                    tgt = [_extract_query(i.value) for i in tgt_inputs if i.value.strip()]
                    draft.target_queries = [q for q, _ in tgt]
                    draft.target_ninja_item = ""
                else:
                    draft.target_ninja_item = tgt_select.value or ""
                    draft.target_ninja_type = tgt_type_radio.value
                    draft.target_queries.clear()
                if self._editing:
                    draft.id = self._editing.id
                    draft.created_at = self._editing.created_at
                store.put(draft)
                _pricer.enqueue(draft.id)
                _close()
                self._rebuild()

            with ui.row().classes("gap-2 mt-2"):
                ui.button("Save", on_click=save).props("unelevated color=positive")
                ui.button("Cancel", on_click=_close).props("flat")

        dialog.open()
