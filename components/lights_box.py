from __future__ import annotations

from dash import html


def lights_render():
    """Lightbulb tile — button opens the lights modal."""
    return [
        html.Button(
            html.Img(src="/assets/icons/lightbulb.svg", className="lights-icon"),
            id="open-lights-modal",
            n_clicks=0,
            className="lights-trigger-btn",
        )
    ]


def create_lights_modal_layout() -> html.Div:
    """Static modal structure — shown/hidden via callback."""
    return html.Div(
        id="lights-modal",
        className="modal",
        style={"display": "none"},
        children=[
            html.Div(
                className="modal-content lights-modal-content",
                children=[
                    html.Div(
                        className="modal-header",
                        children=[
                            html.Span("Lampor inomhus", className="modal-title"),
                            html.Button("×", id="close-lights-modal", className="modal-close-button"),
                        ],
                    ),
                    html.Div(
                        className="lights-modal-buttons",
                        children=[
                            html.Button("Av",  id="light-btn-off", n_clicks=0, className="light-btn off-btn"),
                            html.Button("50%", id="light-btn-50",  n_clicks=0, className="light-btn mid-btn"),
                            html.Button("På",  id="light-btn-on",  n_clicks=0, className="light-btn on-btn"),
                        ],
                    ),
                    html.Div(id="lights-status-msg", className="lights-status-msg"),
                ],
            ),
        ],
    )
