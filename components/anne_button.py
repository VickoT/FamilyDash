from __future__ import annotations

from dash import html


def anne_button_render(is_active: bool = False, status_text: str | None = None):
    """Rendera Anne-knappen med valfri statusrad."""

    button_class = "anne-button active" if is_active else "anne-button"
    children = [
        html.Span("📱", className="anne-button-icon"),
        html.Span("ANNE", className="anne-button-text"),
    ]

    if status_text:
        children.append(html.Span(status_text, className="anne-button-status"))

    return html.Button(
        className=button_class,
        children=children,
        id="anne-button",
        n_clicks=0,
        title="Ring Anne"
    )
