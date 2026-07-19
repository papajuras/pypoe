from __future__ import annotations

from pathlib import Path

from nicegui import ui

from db.config import get_meta, set_meta

from .client import TradeClient
from .pricer import PriceFetcher
from .store import Flip, Store, _extract_query

store = Store()
_pricer: PriceFetcher = None  # type: ignore[assignment]


def _league():
    return get_meta("flipper_league", "Mirage")


def _init_pricer():
    global _pricer
    if _pricer is not None:
        return
    client = TradeClient("OAuth pypoe/0.1.0 (flipper)", league=_league())
    poesessid = Path("ignore/POESESSID").read_text().strip()
    client.session.cookies.set("POESESSID", poesessid, domain="www.pathofexile.com")
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
            ui.label("").classes("flex-1")
            ui.label("League:").classes("text-weight-medium")
            league_input = ui.input(value=_league(), on_change=self._set_league).classes("w-32")

        flips = store.list()
        if not flips:
            ui.label("No flips yet.").classes("text-grey-6 text-caption mt-2")
            return

        rows = []
        for f in flips:
            p = store.get_price(f.id)
            rows.append(self._row_data(f, p))

        liquid = [r for r in rows if r["liquid"]]
        illiquid = [r for r in rows if not r["liquid"]]

        if liquid:
            self._sort_rows(liquid)
            self._build_section("Liquid", liquid)
        if illiquid:
            self._build_section("Illiquid", illiquid)

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

        return {
            "flip": f,
            "has_data": p is not None,
            "cost": cost,
            "profit": profit,
            "pct": profit_pct,
            "liquid": liquid,
        }

    def _sort_rows(self, rows: list[dict]):
        key = self._sort_by
        rows.sort(key=lambda r: (r.get(key) is None, r.get(key) or 0), reverse=not self._sort_asc)

    def _build_section(self, title: str, rows: list[dict]):
        ui.label(title).classes("text-weight-bold text-caption mt-4")
        self._build_header()
        for r in rows:
            self._build_row(r)

    def _build_header(self):
        with ui.row().classes("items-center gap-2 w-full text-weight-bold text-caption"):
            ui.label("Name").classes("w-[200px]")
            for col in COLS[1:]:
                text = col["label"]
                if col["key"] == self._sort_by:
                    text += " ↑" if self._sort_asc else " ↓"
                ui.label(text).classes("w-[70px] cursor-pointer").on("click", lambda c=col: self._sort_click(c["key"]))
            ui.label("Actions").classes("w-[100px]")

    def _build_row(self, r: dict):
        f = r["flip"]
        with ui.row().classes("items-center gap-2 w-full"):
            ui.label(f.name or "[Unnamed]").classes("w-[200px] font-mono text-caption")
            ui.label(self._fmt_cost(r)).classes("w-[70px] font-mono text-caption")
            ui.label(self._fmt_profit(r)).classes(f"w-[70px] font-mono text-caption {self._profit_class(r)}")
            ui.label(self._fmt_pct(r)).classes(f"w-[70px] font-mono text-caption {self._profit_class(r)}")
            ui.button(icon="refresh", on_click=lambda f=f: _pricer.enqueue(f.id)).props("flat dense size=sm")
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

    def _set_league(self, e):
        set_meta("flipper_league", e.value.strip())
        _pricer.set_league(e.value.strip())

    def _create(self):
        self._editing = None
        self._show_form(Flip())

    def _edit(self, flip: Flip):
        self._editing = flip
        draft = Flip(
            name=flip.name,
            source_queries=list(flip.source_queries),
            target_queries=list(flip.target_queries),
            multiplier=flip.multiplier,
            cost=flip.cost,
        )
        self._show_form(draft)

    def _delete(self, flip: Flip):
        store.delete(flip.id)
        self._rebuild()

    def _show_form(self, draft: Flip):
        self._form_open = True
        src_inputs: list[ui.textarea] = []
        tgt_inputs: list[ui.textarea] = []

        def _close():
            self._form_open = False
            dialog.close()

        with ui.dialog() as dialog, ui.card().classes("p-6 min-w-[600px] max-w-[800px]"):
            ui.label("New flip" if self._editing is None else "Edit flip").classes("text-h6")

            name_input = ui.input("Flip name", value=draft.name).classes("w-full")

            with ui.row().classes("items-center gap-4 w-full"):
                with ui.column().classes("flex-1"):
                    ui.label("Multiplier").classes("text-weight-medium")
                    multiplier = ui.slider(min=0, max=10, step=0.01, value=draft.multiplier).classes("w-full")
                    mult_input = ui.number(label="", value=draft.multiplier, min=0, max=999, step=0.01, format="%.2f").classes("w-32")
                    multiplier.bind_value_to(mult_input, "value")
                    mult_input.bind_value_to(multiplier, "value")
                with ui.column():
                    ui.label("Cost (divines)").classes("text-weight-medium")
                    cost_input = ui.number(label="Cost", value=float(draft.cost), min=0, step=1).classes("w-32")

            ui.label("Source — items to acquire").classes("text-weight-medium mt-4")
            sc = ui.column().classes("w-full gap-1")
            for q in draft.source_queries:
                with sc:
                    inp = ui.textarea(value=q).classes("w-full font-mono")
                    inp.style("min-height: 3em")
                    src_inputs.append(inp)
            with ui.row().classes("gap-2"):
                ui.button(icon="add", text="Source query", on_click=lambda: _add_src()).props("flat dense")

            ui.label("Target — items to sell").classes("text-weight-medium mt-4")
            tc = ui.column().classes("w-full gap-1")
            for q in draft.target_queries:
                with tc:
                    inp = ui.textarea(value=q).classes("w-full font-mono")
                    inp.style("min-height: 3em")
                    tgt_inputs.append(inp)
            with ui.row().classes("gap-2"):
                ui.button(icon="add", text="Target query", on_click=lambda: _add_tgt()).props("flat dense")

            ui.separator().classes("mt-4")

            def _add_src():
                with sc:
                    inp = ui.textarea(value="").classes("w-full font-mono")
                    inp.style("min-height: 3em")
                    src_inputs.append(inp)

            def _add_tgt():
                with tc:
                    inp = ui.textarea(value="").classes("w-full font-mono")
                    inp.style("min-height: 3em")
                    tgt_inputs.append(inp)

            def save():
                draft.name = name_input.value.strip()
                if not draft.name:
                    name_input.classes("border-negative")
                    return
                draft.multiplier = multiplier.value
                draft.cost = int(cost_input.value or 0)
                src = [_extract_query(i.value) for i in src_inputs if i.value.strip()]
                tgt = [_extract_query(i.value) for i in tgt_inputs if i.value.strip()]
                draft.source_queries = [q for q, _ in src]
                draft.target_queries = [q for q, _ in tgt]
                if self._editing:
                    draft.id = self._editing.id
                    draft.created_at = self._editing.created_at
                store.put(draft)
                _close()
                self._rebuild()

            with ui.row().classes("gap-2 mt-2"):
                ui.button("Save", on_click=save).props("unelevated color=positive")
                ui.button("Cancel", on_click=_close).props("flat")

        dialog.open()
