# components/energy_modal.py
"""
Energy devices modal.

Visar en horisontell stapelgraf över dagens (sedan midnatt) energiförbrukning
per enhet — samma data som HA:s energidashboard ("Individual devices total usage").
Datan hämtas via ha_client.get_energy_today() (HA-statistik över websocket).
"""

from dash import html, dcc
import plotly.graph_objects as go


# Enhet -> en eller flera HA statistic_ids (summeras) + färg.
# Ordningen spelar ingen roll; grafen sorteras efter förbrukning.
DEVICES = [
    {"name": "VVB",           "ids": ["sensor.vvb_total_energy_fixed"],                "color": "#8d6e63"},
    {"name": "Gräsklippare",  "ids": ["sensor.shellyoutdoorsg3_e4b063fd63f4_energy"],  "color": "#5c6bc0"},
    {"name": "Luftvärmepump", "ids": ["sensor.daikinap61890_energy_consumption"],      "color": "#ffb74d"},
    {"name": "Golvvärme",     "ids": ["sensor.office_energy_usage",
                                      "sensor.kitchen_energy_usage",
                                      "sensor.badrum_energy_usage",
                                      "sensor.barnrum_energy_usage"],                  "color": "#e57373"},
    {"name": "Laddbox",       "ids": ["sensor.zag029615_laddbox_energy_calculated"],   "color": "#9575cd"},
    {"name": "Tvättmaskin",   "ids": ["sensor.shellyplugsg3_indoorplug_energy"],       "color": "#f06292"},
    {"name": "Torktumlare",   "ids": ["sensor.torktumlare_energy"],                    "color": "#90a4ae"},
]

UNTRACKED_COLOR = "#607d8b"


def stat_ids() -> list[str]:
    """Alla statistic_ids för de spårade enheterna (utplattad)."""
    return [sid for d in DEVICES for sid in d["ids"]]


def _device_value(data: dict[str, float], device: dict) -> float:
    """Summan av en enhets sensorer (en enhet kan slå ihop flera)."""
    return sum(max(0.0, float(data.get(sid) or 0.0)) for sid in device["ids"])


def _device_sum(data: dict[str, float]) -> float:
    return sum(_device_value(data, d) for d in DEVICES)


def create_energy_modal_layout() -> html.Div:
    """Statisk modal-struktur. Grafen fylls via callback."""
    return html.Div(
        id="energy-modal",
        className="modal",
        style={"display": "none"},
        children=[
            html.Div(
                className="modal-content energy-modal-content",
                children=[
                    html.Div(
                        className="modal-header",
                        children=[
                            html.Span("Förbrukning idag", id="energy-modal-title", className="modal-title"),
                            html.Button("×", id="close-energy-modal", className="modal-close-button"),
                        ],
                    ),
                    dcc.Graph(
                        id="energy-devices-graph",
                        config={"displayModeBar": False},
                        style={"height": "min(70vh, 620px)", "width": "100%"},
                    ),
                ],
            ),
        ],
    )


def total_kwh(data: dict[str, float] | None, total_today: float | None) -> float:
    """Hela hushållets förbrukning idag (inkl. untracked).

    Använder live-värdet från MQTT (samma som power-tilen) så siffrorna matchar.
    Faller tillbaka på summan av enheterna om live-värdet saknas.
    """
    if total_today is not None:
        return max(0.0, float(total_today))
    return _device_sum(data or {})


def make_energy_title(data: dict[str, float] | None, total_today: float | None) -> str:
    """Rubrik med totalförbrukning, t.ex. 'Förbrukning idag · totalt 4.2 kWh'."""
    return f"Förbrukning idag · totalt {total_kwh(data, total_today):.1f} kWh"


def _empty_figure(msg: str = "Väntar på data...") -> go.Figure:
    fig = go.Figure()
    fig.update_layout(
        template="plotly_dark",
        title=msg,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(t=40, b=40, l=40, r=40),
    )
    return fig


def make_energy_figure(data: dict[str, float] | None, total_today: float | None) -> go.Figure:
    """Bygg horisontell stapelgraf från {statistic_id: kWh} + live-total."""
    if not data:
        return _empty_figure()

    rows = []
    for d in DEVICES:
        rows.append((d["name"], _device_value(data, d), d["color"]))

    # Untracked = hela hushållet (live) − summan av spårade enheter.
    untracked = max(0.0, total_kwh(data, total_today) - _device_sum(data))
    rows.append(("Övrigt", untracked, UNTRACKED_COLOR))

    # Sortera stigande: Plotly ritar första y-värdet nederst, så störst hamnar överst.
    rows.sort(key=lambda r: r[1])
    names = [r[0] for r in rows]
    vals = [r[1] for r in rows]
    colors = [r[2] for r in rows]

    fig = go.Figure(go.Bar(
        x=vals,
        y=[f"<b>{n}</b>" for n in names],
        orientation="h",
        marker_color=colors,
        text=[f"<b>{v:.1f}</b>" for v in vals],
        textposition="outside",
        textfont=dict(size=17, color="#ffffff"),
        cliponaxis=False,
        hovertemplate="%{y}: %{x:.1f} kWh<extra></extra>",
    ))
    fig.update_layout(
        template="plotly_dark",
        font=dict(size=15, color="#eceff1", weight="bold"),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(t=20, b=48, l=170, r=80),
        showlegend=False,
    )
    fig.update_xaxes(
        title=dict(text="kWh", font=dict(size=15, color="#cfd8dc")),
        tickfont=dict(size=13, color="#cfd8dc"),
        gridcolor="rgba(255,255,255,0.08)",
        zeroline=False,
    )
    fig.update_yaxes(showgrid=False, tickfont=dict(size=17, color="#ffffff"))
    return fig
