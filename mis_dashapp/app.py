import dash
from dash import dcc, html, Output, Input
import dash_mantine_components as dmc
import os

app = dash.Dash(__name__, use_pages=True, suppress_callback_exceptions=True)

app.title = "MIS Dashboard"

dash.register_page(
    "home",
    path="/",
    layout=lambda: dmc.Container([
        dmc.Text(" ", style={"marginTop": 20}),
    ], px=50, py=30, style={"backgroundColor": "#ffffff"})
)

def layout():
    return dmc.MantineProvider(
        theme={"colorScheme": "light"},
        withGlobalClasses=True,
        deduplicateCssVariables=True,
        children=[
            html.Div([
                dmc.Container([
                    dmc.Group(
                        [
                            dmc.Anchor(
                                "Home",
                                href="/",
                                fw=500,
                                gradient={"from": "black", "to": "black"},
                                underline = "hover",
                                style={"textDecoration": "none","backgroundColor": "#ffffff","fontSize": 20, "fontWeight": 500, "color": "#000000"}
                            ),
                            dmc.Title(                            
                                "MIS DASHBOARD",
                                order=1,
                                ta='center',
                                style={
                                    "color": "#5367fc",
                                    "fontSize": 48,
                                    "fontWeight": 700,
                                    "letterSpacing": 2,
                                    "marginBottom": 10,
                                    "fontFamily": "Montserrat, sans-serif"
                                }
                            ),
                        ],
                        gap=300,
                    ),
                    dmc.Group(
                        [
                            dmc.Anchor(
                                dmc.Button(
                                    "Gross Level",
                                    variant="gradient",
                                    style={"fontWeight": 500}
                                ),
                                href="/gross-structure-calls",
                                style={"textDecoration": "none"}
                            ),
                            dmc.Anchor(
                                dmc.Button(
                                    "Analyst Level",
                                    variant="gradient",
                                    style={"fontWeight": 500}
                                ),
                                href="/analyst-structure-calls",
                                style={"textDecoration": "none"}
                            ),
                        ],
                        justify="flex-end",
                        gap="xl",
                        mt=20,
                        mb=20
                    ),
                ], px=100, py=40, style={  
                    "backgroundColor": "#ffffff",
                    "borderRadius": 0,
                    "boxShadow": "0 4px 24px rgba(34, 34, 59, 0.08)",
                    "marginTop": 10,
                    "marginBottom": 40,
                    "maxWidth": "1600px",
                    "width": "100%",
                }),
                html.Div(
                    dash.page_container,
                    style={
                        "padding": "30px",
                        "backgroundColor": "#ffffff",
                        "borderRadius": 0,
                        "boxShadow": "0 2px 12px rgba(34, 34, 59, 0.04)",
                        "minHeight": "60vh"
                    }
                ),
            ], style={
                "backgroundColor": "#f3f4f6",
                "minHeight": "100vh",
                "padding": 0,
            })
        ]
    )

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run_server(host="0.0.0.0", port=port, debug=True)