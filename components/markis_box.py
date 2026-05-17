from __future__ import annotations

from dash import html


def markis_render():
    return [
        html.Button(
            html.Img(src="/assets/icons/markis.svg", className="markis-icon"),
            id="open-markis-modal",
            n_clicks=0,
            className="markis-trigger-btn",
        )
    ]


def create_markis_modal_layout() -> html.Div:
    return html.Div(
        id="markis-modal",
        className="modal",
        style={"display": "none"},
        children=[
            html.Div(
                className="modal-content markis-modal-content",
                children=[
                    html.Div(
                        className="modal-header",
                        children=[
                            html.Span("Markis", className="modal-title"),
                            html.Button("×", id="close-markis-modal", className="modal-close-button"),
                        ],
                    ),
                    html.Div(
                        className="markis-modal-buttons",
                        children=[
                            html.Button("Ut", id="markis-btn-open",  n_clicks=0, className="markis-btn open-btn"),
                            html.Button("⏸",  id="markis-btn-stop",  n_clicks=0, className="markis-btn stop-btn"),
                            html.Button("In", id="markis-btn-close", n_clicks=0, className="markis-btn close-btn"),
                        ],
                    ),
                    html.Div(id="markis-status-msg", className="markis-status-msg"),
                ],
            ),
        ],
    )
