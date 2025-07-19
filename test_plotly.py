import plotly.graph_objects as go
from datetime import datetime, timedelta

# Skapa 24 timmars dummy-tidpunkter
start_time = datetime.now().replace(minute=0, second=0, microsecond=0)
timestamps = [start_time + timedelta(hours=i) for i in range(24)]

# Dummypriser i kr/kWh
prices = [
    0.45, 0.42, 0.38, 0.35, 0.33, 0.30, 0.28, 0.34,
    0.50, 0.65, 0.72, 0.75, 0.78, 0.80, 0.76, 0.70,
    0.66, 0.99, 0.58, 0.54, 0.50, 0.48, 0.47, 0.46
]

# Skapa plot
fig = go.Figure(
    data=[go.Scatter(x=timestamps, y=prices, mode='lines+markers')],
    layout=go.Layout(
        title="Dummy elpris per timme",
        xaxis_title="Tid",
        yaxis_title="kr/kWh",
        hovermode="x unified"
    )
)

# Visa
fig.show()
