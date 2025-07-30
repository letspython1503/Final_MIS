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
                                underline="hover",
                                style={
                                    "textDecoration": "none",
                                    "backgroundColor": "#ffffff",
                                    "fontSize": 20,
                                    "fontWeight": 500,
                                    "color": "#000000"
                                }
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
                                    gradient={"from": "indigo", "to": "cyan", "deg": 45},
                                    size="md",
                                    style={"fontWeight": 500, "boxShadow": "0 2px 8px rgba(83,103,252,0.15)"}
                                ),
                                href="/gross-structure-calls",
                                style={"textDecoration": "none"}
                            ),
                            dmc.Anchor(
                                dmc.Button(
                                    "Analyst Level",
                                    variant="gradient",
                                    gradient={"from": "teal", "to": "lime", "deg": 45},
                                    size="md",
                                    style={"fontWeight": 500, "boxShadow": "0 2px 8px rgba(83,103,252,0.10)"}
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
                    "borderRadius": 16,
                    "boxShadow": "0 8px 32px rgba(83,103,252,0.10)",
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
                        "borderRadius": 16,
                        "boxShadow": "0 2px 12px rgba(34, 34, 59, 0.04)",
                        "minHeight": "60vh"
                    }
                ),
            ], style={
                "background": "linear-gradient(135deg, #e0e7ff 0%, #f3f4f6 100%)",
                "minHeight": "100vh",
                "padding": 0,
            })
        ]
    )

dash.register_page(
    "home",
    path="/",
    layout=lambda: dmc.Container([
        dmc.Paper(
            [
                dmc.Title("Welcome to the MIS Dashboard", order=2, style={
                    "color": "#5367fc",
                    "fontFamily": "Montserrat, sans-serif",
                    "fontWeight": 700,
                    "marginBottom": 10,
                }),
                dmc.Text(
                    "Easily monitor and analyze your Management Information System data. "
                    "Use the navigation above to explore Gross Level and Analyst Level insights.",
                    ta="center",
                    size="lg",
                    style={"fontWeight": 600}
                ),
                dmc.Group(
                    [
                        dmc.Anchor(
                            dmc.Button(
                                "Get Started",
                                variant="gradient",
                                gradient={"from": "indigo", "to": "cyan", "deg": 45},
                                size="lg",
                                radius="xl",
                                style={"fontWeight": 600}
                            ),
                            href="/gross-structure-calls",
                            style={"textDecoration": "none"}
                        ),
                    ],
                    justify="center"
                ),
            ],
            shadow="xl",
            radius="lg",
            p=40,
            style={
                "maxWidth": 600,
                "margin": "60px auto",
                "background": "rgba(255,255,255,0.95)",
                "border": "1px solid #e0e7ff"
            }
        ),
    ], px=50, py=30, style={"backgroundColor": "transparent"})
)

app.layout = layout()
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port, debug=True)