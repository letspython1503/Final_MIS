import dash
from dash import dcc, html, Input, Output
import dash_mantine_components as dmc
import pandas as pd
from urllib.parse import parse_qs, urlparse
from datetime import datetime, date
from pages import structure_call_data_ELT  

dash.register_page(__name__, path="/details")

layout = dmc.MantineProvider(
    theme={"colorScheme": "light"},
    children=[
        dmc.Container([
        dcc.Location(id="details-url", refresh=False),
        dmc.Title("Period Summary", order=2, mb=10),
        html.Div(id="summary-table"),
        ],  
        style={
            "backgroundColor": "#d9d9d9",
            "padding": "32px",
            "borderRadius": "16px",
            "boxShadow": "0 2px 12px rgba(0,0,0,0.08)",
            "maxWidth": "1200px",
            "margin": "40px auto"}
        ),
        dmc.Container(
            [
                html.Hr(),
                dmc.Title("User-wise Summary (Top Performers - Target Hit)", order=2, mb=10),
                dmc.Text("Selected Period performance of each user for the selected period.",size='lg',mb=20),
                html.Div(id="overall-user-wise-table"),
                dmc.Space(h=20),
                dmc.Text("NSE: Top Performers - Target Hit", size='sm', mt=10, mb=20),
                html.Div(id="nse-top-performers"),
                dmc.Space(h=20),
                dmc.Text("MCX: Top Performers - Target Hit", size='sm', mt=10, mb=20),
                html.Div(id="mcx-top-performers"),
                dmc.Space(h=20),
                dmc.Text("CASH/EQUITY: Top Performers - Target Hit", size='sm', mt=10, mb=20),
                html.Div(id="cash-top-performers"),
                dmc.Space(h=20),
                dmc.Text("DERIVATIVES(Futures): Top Performers - Target Hit", size='sm', mt=10, mb=20),
                html.Div(id="derivaties-top-performers"),
                dmc.Space(h=20),
                dmc.Text("OPTIONS: Top Performers - Target Hit", size='sm', mt=10, mb=20),
                html.Div(id="options-top-performers"),
                dmc.Space(h=20),
            ],
            style={
                "backgroundColor": "#d9d9d9",
                "padding": "32px",
                "borderRadius": "16px",
                "boxShadow": "0 2px 12px rgba(0,0,0,0.08)",
                "maxWidth": "1200px",
                "margin": "40px auto"}
        ),
]
)

@dash.callback(
    Output("summary-table", "children"),
    Output("overall-user-wise-table", "children"),
    Output("nse-top-performers", "children"),
    Output("mcx-top-performers", "children"),
    Output("cash-top-performers", "children"),
    Output("derivaties-top-performers", "children"),
    Output("options-top-performers", "children"),
    Input("details-url", "href"),
)
def render_detail_tables(href):
    if not href:
        return html.Div("No URL provided"), html.Div()
    query = parse_qs(urlparse(href).query)
    period = query.get("period", [""])[0]
    scope = query.get("scope", ["monthly"])[0]
    sender = structure_call_data_ELT.backend_sender()
    df = sender.df.copy()
    df["InsertionTime"] = pd.to_datetime(df["InsertionTime"], errors="coerce")
    df["MonthPeriod"] = df["InsertionTime"].dt.strftime("%B-%Y" if scope == "monthly" else "%Y")
    df = df[df["MonthPeriod"] == period]
    if df.empty:
        return html.Div(f"No data for {period}"), html.Div()
    def generate_summary_rows(sub_df):
        total_calls = len(sub_df)
        target_hit = (sub_df["TargetHit"] == 1).sum()
        stoploss_hit = (sub_df["StopLossHit"] == 1).sum()
        closed = sub_df[sub_df["ExitPrice"].notna()]
        neither_df = closed[(closed["TargetHit"] != 1) & (closed["StopLossHit"] != 1)]
        n_pos = (((neither_df["BuySell"].str.upper() == "BUY") & (neither_df["ExitPrice"] > neither_df["Price"])) |
                 ((neither_df["BuySell"].str.upper() == "SELL") & (neither_df["ExitPrice"] < neither_df["Price"]))).sum()
        n_neg = (((neither_df["BuySell"].str.upper() == "BUY") & (neither_df["ExitPrice"] < neither_df["Price"])) |
                 ((neither_df["BuySell"].str.upper() == "SELL") & (neither_df["ExitPrice"] > neither_df["Price"]))).sum()
        n_red = (((neither_df["BuySell"].str.upper() == "BUY") & (neither_df["ExitPrice"] == neither_df["Price"])) |
                 ((neither_df["BuySell"].str.upper() == "SELL") & (neither_df["ExitPrice"] == neither_df["Price"]))).sum()
        open_df = sub_df[sub_df["ExitPrice"].isna()]
        o_pos = (((open_df["BuySell"].str.upper() == "BUY") & (open_df["LastTradedPrice"] > open_df["Price"])) |
                 ((open_df["BuySell"].str.upper() == "SELL") & (open_df["LastTradedPrice"] < open_df["Price"]))).sum()
        o_neg = (((open_df["BuySell"].str.upper() == "BUY") & (open_df["LastTradedPrice"] < open_df["Price"])) |
                 ((open_df["BuySell"].str.upper() == "SELL") & (open_df["LastTradedPrice"] > open_df["Price"]))).sum()
        o_red = (((open_df["BuySell"].str.upper() == "BUY") & (open_df["LastTradedPrice"] == open_df["Price"])) |
                 ((open_df["BuySell"].str.upper() == "SELL") & (open_df["LastTradedPrice"] == open_df["Price"]))).sum()

        def pct(val): return f"{(val / total_calls * 100):.1f}%" if total_calls else "0.0%"
        count_row = html.Tr([
            html.Td(period, style={"border": "1px solid #000000","textAlign":"center","fontWeight": "bold"}),
            html.Td(total_calls,style={"border": "1px solid #000000","textAlign": "right"}), html.Td(target_hit,style={"border": "1px solid #000000","textAlign": "right"}), html.Td(stoploss_hit,style={"border": "1px solid #000000","textAlign": "right"}),
            html.Td(n_pos,style={"border": "1px solid #000000","textAlign": "right"}), html.Td(n_neg,style={"border": "1px solid #000000","textAlign": "right"}), html.Td(n_red,style={"border": "1px solid #000000","textAlign": "right"}),
            html.Td(len(closed),style={"border": "1px solid #000000","textAlign": "right"}),
            html.Td(o_pos,style={"border": "1px solid #000000","textAlign": "right"}), html.Td(o_neg,style={"border": "1px solid #000000","textAlign": "right"}), html.Td(o_red,style={"border": "1px solid #000000","textAlign": "right"}),
            html.Td(len(open_df),style={"border": "1px solid #000000","textAlign": "right"})
        ])
        percent_row = html.Tr([
            html.Td("%",style={"border": "1px solid #000000","textAlign":"center","fontWeight": "bold"}),
            html.Td("100%" if total_calls else "0%",style={"border": "1px solid #000000","textAlign": "right"}),
            html.Td(pct(target_hit),style={"border": "1px solid #000000","textAlign": "right"}), html.Td(pct(stoploss_hit),style={"border": "1px solid #000000","textAlign": "right"}),
            html.Td(pct(n_pos),style={"border": "1px solid #000000","textAlign": "right"}), html.Td(pct(n_neg),style={"border": "1px solid #000000","textAlign": "right"}), html.Td(pct(n_red),style={"border": "1px solid #000000","textAlign": "right"}),
            html.Td(pct(len(closed)),style={"border": "1px solid #000000","textAlign":"right"}),
            html.Td(pct(o_pos),style={"border": "1px solid #000000","textAlign": "right"}), html.Td(pct(o_neg),style={"border": "1px solid #000000","textAlign": "right"}), html.Td(pct(o_red),style={"border": "1px solid #000000","textAlign": "right"}),
            html.Td(pct(len(open_df)),style={"border": "1px solid #000000","textAlign": "right"})
        ])
        return [count_row, percent_row]

    header = html.Thead([
        html.Tr([
            html.Th("UserId", style={"backgroundColor": "#fdd835", "textAlign": "center", "padding": "8px", "border": "1px solid #000000"}),
            html.Th("Total Calls", style={"backgroundColor": "#fdd835", "textAlign": "center", "padding": "8px", "border": "1px solid #000000"}),
            html.Th("Target Hit", style={"backgroundColor": "#fdd835", "textAlign": "center", "padding": "8px", "border": "1px solid #000000"}),
            html.Th("StopLoss Hit", style={"backgroundColor": "#fdd835", "textAlign": "center", "padding": "8px", "border": "1px solid #000000"}),
            html.Th("Closed: Positive", style={"backgroundColor": "#fdd835", "textAlign": "center", "padding": "6px", "border": "1px solid #000000"}),
            html.Th("Closed: Negative", style={"backgroundColor": "#fdd835", "textAlign": "center", "padding": "6px", "border": "1px solid #000000"}),
            html.Th("Closed: Redundant", style={"backgroundColor": "#fdd835", "textAlign": "center", "padding": "6px", "border": "1px solid #000000"}),
            html.Th("Total Closed Calls", style={"backgroundColor": "#fdd835", "textAlign": "center", "padding": "8px", "border": "1px solid #000000"}),
            html.Th("Open: Positive", style={"backgroundColor": "#fdd835", "textAlign": "center", "padding": "6px", "border": "1px solid #000000"}),
            html.Th("Open: Negative", style={"backgroundColor": "#fdd835", "textAlign": "center", "padding": "6px", "border": "1px solid #000000"}),
            html.Th("Open: Redundant", style={"backgroundColor": "#fdd835", "textAlign": "center", "padding": "6px", "border": "1px solid #000000"}),
            html.Th("Total Open Calls", style={"backgroundColor": "#fdd835", "textAlign": "center", "padding": "8px", "border": "1px solid #000000"}),
        ])
    ])

    def build_user_table(filtered_df):
        user_rows = []
        for uid, user_df in filtered_df.groupby("UserID"):
            rows = generate_summary_rows(user_df)
            count_row = rows[0]
            percent_row = rows[1]
            total_calls = int(count_row.children[1].children)
            target_hit_count = int(count_row.children[2].children)
            target_hit_pct = float(percent_row.children[2].children.strip('%'))
            user_rows.append({
                "uid": uid,
                "count_row": count_row,
                "percent_row": percent_row,
                "target_hit_pct": target_hit_pct
            })

        user_rows_sorted = sorted(user_rows, key=lambda x: x["target_hit_pct"], reverse=True)
        user_table_body = []
        for user in user_rows_sorted:
            user["count_row"].children[0] = html.Td(user["uid"], style={"border": "1px solid #000000","textAlign":"center","fontWeight": "bold"})
            user["percent_row"].children[0] = html.Td(" ", style={"border": "1px solid #000000","textAlign":"center","fontWeight": "bold"})
            user_table_body.extend([user["count_row"], user["percent_row"]])

        return dmc.Paper(
            dmc.Table(
                children=[
                    header,
                    html.Tbody(user_table_body)
                ],
                withTableBorder=True,
                withColumnBorders=True,
                striped=True,
                highlightOnHover=True,
                horizontalSpacing="md",
                verticalSpacing="sm"
            ),
            shadow="xs",
            radius="md",
            p="md",
            style={"marginBottom": "24px", "background": "#ffffff"}
        )

    summary_table = dmc.Paper(
        dmc.Table(
            children=[
                header,
                html.Tbody(generate_summary_rows(df))
            ],
            withTableBorder=True,
            withColumnBorders=True,
            striped=True,
            highlightOnHover=True,
            horizontalSpacing="md",
            verticalSpacing="sm"
        ),
        shadow="md",
        radius="lg",
        p="md",
        style={"marginBottom": "32px", "background": "#ffffff"}
    )

    user_table = build_user_table(df)

    # NSE
    nse_df = df[df["Exchange"].str.upper() == "NSE"]
    nse_top_performers = build_user_table(nse_df) if not nse_df.empty else html.Div("No NSE data for this period.")

    # MCX
    mcx_df = df[df["Exchange"].str.upper() == "MCX"]
    mcx_top_performers = build_user_table(mcx_df) if not mcx_df.empty else html.Div("No MCX data for this period.")

    # CASH/EQUITY
    cash_df = df[df["ExchSegment"].str.upper().isin(["EQUITY"])]
    cash_top_performers = build_user_table(cash_df) if not cash_df.empty else html.Div("No CASH/EQUITY data for this period.")

    # DERIVATIVES (FUT in ExchSegment)
    derivatives_df = df[df["ExchSegment"].str.upper().str.contains("FUT")]
    derivaties_top_performers = build_user_table(derivatives_df) if not derivatives_df.empty else html.Div("No DERIVATIVES data for this period.")

    # OPTIONS (OPT or OPTCOMM in ExchSegment)
    options_df = df[df["ExchSegment"].str.upper().isin(["OPT", "OPTCOMM"])]
    options_top_performers = build_user_table(options_df) if not options_df.empty else html.Div("No OPTIONS data for this period.")

    return (
        summary_table,
        user_table,
        nse_top_performers,
        mcx_top_performers,
        cash_top_performers,
        derivaties_top_performers,
        options_top_performers
    )