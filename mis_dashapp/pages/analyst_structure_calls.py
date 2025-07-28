from pages import structure_call_data_ELT
import dash
import dash_mantine_components as dmc
from dash import html
from datetime import datetime, date
from dash import callback, Output, Input
from dash import no_update
from dash import dcc
from pages import structure_call_data_ELT

backend = structure_call_data_ELT.backend_sender()
UserId = backend.user_id_sender()

dash.register_page(__name__, path="/analyst-structure-calls")

layout = dmc.MantineProvider(
    theme={"colorScheme": "light"},
    children=[
        dmc.Container(
            [
                dmc.Title("Analyst Level Summary", order=2, mt=20),
                dmc.Select(
                    id="analyst-user-select",
                    label="Select User",
                    placeholder="Select User",
                    data=[{"value": str(user), "label": str(user)} for user in UserId],
                    size="sm",
                    radius="sm",
                    withAsterisk=False,
                    style={"maxWidth": "300px", "marginBottom": "20px"},
                    clearable=True,
                ),
                #Filters
                dmc.Group(
                    [
                        html.Div(
                            [
                                dmc.DatePickerInput(
                                    id="analyst-date-input-range-picker",
                                    label="Date Range",
                                    minDate=date(2024, 11, 1),
                                    type="range",
                                    value=[date(2024, 11, 1), datetime.now().date()],
                                    maw=300,
                                ),
                                dmc.Space(h=10),
                            ]
                        ),
                        html.Div(
                            [
                                dmc.MultiSelect(
                                    id="analyst-exchange-multiselect",
                                    placeholder="Exchange",
                                    label="Select Exchange",
                                    data=[
                                        {"value": "NSE", "label": "NSE"},
                                        {"value": "MCX", "label": "MCX"},
                                    ],
                                    size="sm",
                                    radius="sm",
                                    withAsterisk=False,
                                    comboboxProps={"transitionProps": {"transition": "pop", "duration": 200}},
                                ),
                                dmc.Space(h=10),
                            ]
                        ),
                        html.Div(
                            [
                                dmc.MultiSelect(
                                    id="analyst-segment-multiselect",
                                    placeholder="Segments",
                                    label="Select Segment",
                                    data=[
                                        {
                                            "group": "Equity",
                                            "items": [
                                                {"value": "EQUITY", "label": "Equity"},
                                            ],
                                        },
                                        {
                                            "group": "Futures",
                                            "items": [
                                                {"value": "FUTCOMM", "label": "Commodity"},
                                                {"value": "FUTCUR", "label": "Currency"},
                                                {"value": "FUTIDX", "label": "FUTIDXs"},
                                                {"value": "FUTSTK", "label": "FUTSTKs"},
                                            ],
                                        },
                                        {
                                            "group": "Options",
                                            "items": [
                                                {"value": "OPT", "label": "Option"},
                                                {"value": "OPTCUR", "label": "Commodity"},
                                            ],
                                        },
                                    ],
                                    size="sm",
                                    radius="sm",
                                    withAsterisk=False,
                                    comboboxProps={"transitionProps": {"transition": "pop", "duration": 200}},
                                ),
                                dmc.Space(h=10),
                            ]
                        ),
                    ],
                    gap=10,
                ),
                dmc.Button("Select all dates",id="analyst-all-date-button", size="sm", radius="sm", color="black", style={"marginTop": "5px"}),
                html.Div(id="analyst-summary-table-container"),
                html.Div(id="analyst-type-range-summary-table"),
            ],
            style={
                "backgroundColor": "#d9d9d9",
                "padding": "32px",
                "borderRadius": "16px",
                "boxShadow": "0 2px 12px rgba(0,0,0,0.08)",
                "maxWidth": "1200px",
                "margin": "40px auto"
            }
        ),
        dmc.Container(
            [
                dmc.Title("Summary - Yearly/Montly/Daily", order=3, mt=20),
                dmc.Space(h=20),
                dmc.Select(data=["Yearly","Monthly","Daily"],id="analyst-time-range-select", placeholder="Select Time Range", label="Time Range", size="sm", radius="sm", withAsterisk=False, comboboxProps={"transitionProps": {"transition": "pop", "duration": 200}}),
                dmc.Space(h=20),
                dmc.Container(
                [
                    dmc.Text("Please click on the period to get additional details for that period", style={"fontSize": 15, "fontWeight": 500, "marginBottom": 10}),
                    dmc.Table(id="analyst-time-range-summary-table",)],
                style={
                    "backgroundColor": "#ffffff",
                    "padding": "32px",
                    "borderRadius": "16px",
                    "boxShadow": "0 2px 12px rgba(0,0,0,0.08)",
                    "maxWidth": "1200px",
                    "margin": "40px auto"
                    }
                ),
            ],
            style={
                "backgroundColor": "#d9d9d9",
                "padding": "32px",
                "borderRadius": "16px",
                "boxShadow": "0 2px 12px rgba(0,0,0,0.08)",
                "maxWidth": "1200px",
                "margin": "40px auto"
            }
        ) 
    ]
)

@callback(
    Output("analyst-summary-table-container", "children"),
    Output("analyst-date-input-range-picker", "value"),
    Input("analyst-user-select", "value"),
    Input("analyst-all-date-button", "n_clicks"),
    Input("analyst-date-input-range-picker", "value"),
    Input("analyst-exchange-multiselect", "value"),
    Input("analyst-segment-multiselect", "value"),
    prevent_initial_call=True
)
def update_analyst_summary_table(userid, n_clicks, date_range, exchanges, segments):
    ctx = dash.callback_context
    all_dates = [date(2024, 11, 1), datetime.now().date()]
    update_picker = no_update
    if not userid:
        return dmc.Text("Please select a user.", c="red", mt=30), update_picker if update_picker is not no_update else date_range
    if ctx.triggered and ctx.triggered[0]["prop_id"] == "analyst-all-date-button.n_clicks":
        start_date, end_date = all_dates
        update_picker = all_dates
    elif date_range and len(date_range) == 2:
        start_date = date_range[0]
        end_date = date_range[1]
    else:
        start_date, end_date = all_dates

    alldata = backend.get_data_filter_id(
        userid=userid,
        start_date=start_date,
        end_date=end_date,
        exchange=exchanges,
        exch_segment=segments
    )

    def get_cell(i, j):
        try:
            return alldata.iloc[i, j]
        except Exception:
            return "-"

    table = dmc.Container([
    dmc.Text("Analyst Level Summary", style={"fontSize": "24px", "fontWeight": 600, "marginBottom": "20px"}),
    dmc.Table(
        [
            html.Thead([
                html.Tr([
                    html.Th("Total Calls", rowSpan=2, style={"backgroundColor": "#fdd835", "border": "1px solid #000000"}),
                    html.Th("Target Hit", rowSpan=2, style={"backgroundColor": "#fdd835", "border": "1px solid #000000"}),
                    html.Th("StopLoss Hit", rowSpan=2, style={"backgroundColor": "#fdd835", "border": "1px solid #000000"}),

                    html.Th("Neither target nor Stop loss hit", colSpan=3, style={"backgroundColor": "#fdd835", "textAlign": "center", "border": "1px solid #000000"}),
                    html.Th("Total Closed Calls", rowSpan=2, style={"backgroundColor": "#fdd835", "border": "1px solid #000000"}),

                    html.Th("Open Calls", colSpan=3, style={"backgroundColor": "#fdd835", "textAlign": "center", "border": "1px solid #000000"}),
                    html.Th("Total Open Calls", rowSpan=2, style={"backgroundColor": "#fdd835", "border": "1px solid #000000"})
                ]),
                html.Tr([
                    html.Th("Positive", style={"backgroundColor": "#fdd835", "border": "1px solid #000000"}),
                    html.Th("Negative", style={"backgroundColor": "#fdd835", "border": "1px solid #000000"}),
                    html.Th("Redundant", style={"backgroundColor": "#fdd835", "border": "1px solid #000000"}),

                    html.Th("Positive", style={"backgroundColor": "#fdd835", "border": "1px solid #000000"}),
                    html.Th("Negative", style={"backgroundColor": "#fdd835", "border": "1px solid #000000"}),
                    html.Th("Redundant", style={"backgroundColor": "#fdd835", "border": "1px solid #000000"}),
                ])
            ]),
            html.Tbody([
                html.Tr([
                    html.Td(get_cell(0,0), style={"border": "1px solid #000000","textAlign": "right"}),
                    html.Td(get_cell(1,0), style={"border": "1px solid #000000","textAlign": "right"}),
                    html.Td(get_cell(2,0), style={"border": "1px solid #000000","textAlign": "right"}),

                    html.Td(get_cell(3,0), style={"border": "1px solid #000000","textAlign": "right"}),
                    html.Td(get_cell(4,0), style={"border": "1px solid #000000","textAlign": "right"}),
                    html.Td(get_cell(5,0), style={"border": "1px solid #000000","textAlign": "right"}),

                    html.Td(get_cell(6,0), style={"border": "1px solid #000000","textAlign": "right"}),

                    html.Td(get_cell(7,0), style={"border": "1px solid #000000","textAlign": "right"}),
                    html.Td(get_cell(8,0), style={"border": "1px solid #000000","textAlign": "right"}),
                    html.Td(get_cell(9,0), style={"border": "1px solid #000000","textAlign": "right"}),

                    html.Td(get_cell(10,0), style={"border": "1px solid #000000","textAlign": "right"}),
                ]),
                html.Tr([
                    html.Td(get_cell(0,1), style={"border": "1px solid #000000","textAlign": "right"}),
                    html.Td(get_cell(1,1), style={"border": "1px solid #000000","textAlign": "right"}),
                    html.Td(get_cell(2,1), style={"border": "1px solid #000000","textAlign": "right"}),

                    html.Td(get_cell(3,1), style={"border": "1px solid #000000","textAlign": "right"}),
                    html.Td(get_cell(4,1), style={"border": "1px solid #000000","textAlign": "right"}),
                    html.Td(get_cell(5,1), style={"border": "1px solid #000000","textAlign": "right"}),

                    html.Td(get_cell(6,1), style={"border": "1px solid #000000","textAlign": "right"}),

                    html.Td(get_cell(7,1), style={"border": "1px solid #000000","textAlign": "right"}),
                    html.Td(get_cell(8,1), style={"border": "1px solid #000000","textAlign": "right"}),
                    html.Td(get_cell(9,1), style={"border": "1px solid #000000","textAlign": "right"}),

                    html.Td(get_cell(10,1), style={"border": "1px solid #000000","textAlign": "right"}),
                ])
            ])
        ],
        withTableBorder=True,
        withColumnBorders=True,
        striped=True,
        highlightOnHover=True,
        mt=30,
        style={"borderCollapse": "collapse"}
    )
    ],style={
        "backgroundColor": "#ffffff",
        "padding": "32px",
        "borderRadius": "16px",
        "boxShadow": "0 2px 12px rgba(0,0,0,0.08)",
        "maxWidth": "1200px",
        "margin": "40px auto"
    })
    
    return table, update_picker if update_picker is not no_update else date_range

@callback(
    Output("analyst-time-range-summary-table", "children"),
    Input("analyst-time-range-select", "value"),
    Input("analyst-user-select", "value"),
    Input("analyst-all-date-button", "n_clicks"),
    Input("analyst-date-input-range-picker", "value"),
    Input("analyst-exchange-multiselect", "value"),
    Input("analyst-segment-multiselect", "value"),
    prevent_initial_call=True
)
def update_analyst_time_range_summary_table(time_range, user_id, n_clicks, date_range, exchanges, segments):
    if not user_id:
        return dmc.Text("Please select a user.", c="red", mt=30)
    all_dates = [date(2024, 11, 1), datetime.now().date()]
    if date_range and len(date_range) == 2:
        start_date = date_range[0]
        end_date = date_range[1]
    else:
        start_date, end_date = all_dates

    if time_range == "Yearly":
        t = "yearly"
    elif time_range == "Monthly":
        t = "monthly"
    elif time_range == "Daily":
        t = "daily"
    else:
        return dmc.Text("Please select a valid time range.", c="red", mt=30)
    summary_rows = backend.generate_timely_summary_rows_id(
        userid=user_id,
        start_date=start_date,
        end_date=end_date,
        exchange=exchanges,
        exch_segment=segments,
        time=t,
    )
    filtered_table = dmc.Table(
        [
            html.Thead([
                html.Tr([
                    html.Th("Period", rowSpan=2, style={"backgroundColor": "#fdd835", "textAlign": "center", "padding": "8px", "border": "1px solid #000000"}),
                    html.Th("Total Calls", rowSpan=2, style={"backgroundColor": "#fdd835", "textAlign": "center", "padding": "8px", "border": "1px solid #000000"}),
                    html.Th("Target Hit", rowSpan=2, style={"backgroundColor": "#fdd835", "textAlign": "center", "padding": "8px", "border": "1px solid #000000"}),
                    html.Th("StopLoss Hit", rowSpan=2, style={"backgroundColor": "#fdd835", "textAlign": "center", "padding": "8px", "border": "1px solid #000000"}),

                    html.Th("Neither target nor Stop loss hit", colSpan=3, style={"backgroundColor": "#fdd835", "textAlign": "center", "padding": "8px", "border": "1px solid #000000"}),
                    html.Th("Total Closed Calls", rowSpan=2, style={"backgroundColor": "#fdd835", "textAlign": "center", "padding": "8px", "border": "1px solid #000000"}),

                    html.Th("Open Calls", colSpan=3, style={"backgroundColor": "#fdd835", "textAlign": "center", "padding": "8px", "border": "1px solid #000000"}),
                    html.Th("Total Open Calls", rowSpan=2, style={"backgroundColor": "#fdd835", "textAlign": "center", "padding": "8px", "border": "1px solid #000000"})
                ]),
                html.Tr([
                    html.Th("Positive", style={"backgroundColor": "#fdd835", "textAlign": "center", "padding": "6px", "border": "1px solid #000000"}),
                    html.Th("Negative", style={"backgroundColor": "#fdd835", "textAlign": "center", "padding": "6px", "border": "1px solid #000000"}),
                    html.Th("Redundant", style={"backgroundColor": "#fdd835", "textAlign": "center", "padding": "6px", "border": "1px solid #000000"}),

                    html.Th("Positive", style={"backgroundColor": "#fdd835", "textAlign": "center", "padding": "6px", "border": "1px solid #000000"}),
                    html.Th("Negative", style={"backgroundColor": "#fdd835", "textAlign": "center", "padding": "6px", "border": "1px solid #000000"}),
                    html.Th("Redundant", style={"backgroundColor": "#fdd835", "textAlign": "center", "padding": "6px", "border": "1px solid #000000"}),
                ])
            ]),
            html.Tbody([
                row
                for period, values, percents in summary_rows
                for row in [
                    html.Tr([
                        html.Td(
                            dcc.Link(
                                period,
                                href=f"/details?scope={'monthly' if time_range != 'Yearly' else 'yearly'}&period={period}",
                                target="_blank",
                                style={"textDecoration": "none", "color": "black", "fontWeight": "bold"}
                            ),
                            style={"border": "1px solid #000000","textAlign": "center", "fontWeight": "bold"}
                        ),
                        *[html.Td(cell,style={"border": "1px solid #000000","textAlign": "right"}) for cell in values]
                    ]),
                    html.Tr([
                        html.Td("%",style={"border": "1px solid #000000","textAlign": "center", "fontWeight": "bold"}),
                        *[html.Td(p,style={"border": "1px solid #000000","textAlign": "right"}) for p in percents]
                    ])
                ]
            ])
        ],
        withTableBorder=True,
        withColumnBorders=True,
        striped=True,
        highlightOnHover=True,
        horizontalSpacing="sm",
        verticalSpacing="xs",
        style={"borderCollapse": "collapse", "width": "100%", "marginTop": "20px"}
    )

    return filtered_table

@callback(
    Output("analyst-type-range-summary-table", "children", allow_duplicate=True),
    Output("analyst-date-input-range-picker", "value", allow_duplicate=True),
    Input("analyst-user-select", "value"),
    Input("analyst-all-date-button", "n_clicks"),
    Input("analyst-date-input-range-picker", "value"),
    Input("analyst-exchange-multiselect", "value"),
    Input("analyst-segment-multiselect", "value"),
    prevent_initial_call=True
)
def update_analyst_type_range_summary_table(userid, _, date_range, exchanges, segments):
    ctx = dash.callback_context
    all_dates = [date(2024, 11, 1), datetime.now().date()]
    update_picker = no_update
    if not userid:
        return dmc.Text("Please select a user.", c="red", mt=30), update_picker if update_picker is not no_update else date_range
    if ctx.triggered and ctx.triggered[0]["prop_id"] == "analyst-all-date-button.n_clicks":
        start_date, end_date = all_dates
        update_picker = all_dates
    elif date_range and len(date_range) == 2:
        start_date = date_range[0]
        end_date = date_range[1]
    else:
        start_date, end_date = all_dates
    rows = backend.render_type_data_gross_id(
        userid=userid,
        start_date=start_date,
        end_date=end_date,
        exchange=exchanges,
        exch_segment=segments
    )

    table = dmc.Container(
        [
            dmc.Text("Calls Type Summary", style={"fontSize": "24px", "fontWeight": 600, "marginBottom": "20px"}),
            dmc.Table(
                [
                    html.Thead([
                        html.Tr([
                            html.Th("Call Type", rowSpan=2, style={"backgroundColor": "#fdd835", "textAlign": "center", "padding": "8px", "border": "1px solid #000000"}),
                            html.Th("Total Calls", rowSpan=2, style={"backgroundColor": "#fdd835", "textAlign": "center", "padding": "8px", "border": "1px solid #000000"}),
                            html.Th("Target Hit", rowSpan=2, style={"backgroundColor": "#fdd835", "textAlign": "center", "padding": "8px", "border": "1px solid #000000"}),
                            html.Th("StopLoss Hit", rowSpan=2, style={"backgroundColor": "#fdd835", "textAlign": "center", "padding": "8px", "border": "1px solid #000000"}),

                            html.Th("Neither target nor Stop loss hit", colSpan=3, style={"backgroundColor": "#fdd835", "textAlign": "center", "padding": "8px", "border": "1px solid #000000"}),
                            html.Th("Total Closed Calls", rowSpan=2, style={"backgroundColor": "#fdd835", "textAlign": "center", "padding": "8px", "border": "1px solid #000000"}),

                            html.Th("Open Calls", colSpan=3, style={"backgroundColor": "#fdd835", "textAlign": "center", "padding": "8px", "border": "1px solid #000000"}),
                            html.Th("Total Open Calls", rowSpan=2, style={"backgroundColor": "#fdd835", "textAlign": "center", "padding": "8px", "border": "1px solid #000000"})
                        ]),
                        html.Tr([
                            html.Th("Positive", style={"backgroundColor": "#fdd835", "textAlign": "center", "padding": "6px", "border": "1px solid #000000"}),
                            html.Th("Negative", style={"backgroundColor": "#fdd835", "textAlign": "center", "padding": "6px", "border": "1px solid #000000"}),
                            html.Th("Redundant", style={"backgroundColor": "#fdd835", "textAlign": "center", "padding": "6px", "border": "1px solid #000000"}),

                            html.Th("Positive", style={"backgroundColor": "#fdd835", "textAlign": "center", "padding": "6px", "border": "1px solid #000000"}),
                            html.Th("Negative", style={"backgroundColor": "#fdd835", "textAlign": "center", "padding": "6px", "border": "1px solid #000000"}),
                            html.Th("Redundant", style={"backgroundColor": "#fdd835", "textAlign": "center", "padding": "6px", "border": "1px solid #000000"}),
                        ]),
                    ]),
                    html.Tbody(
                        rows,
                        style={"textAlign": "center", "fontSize": "14px"}
                    )
                ],
                withTableBorder=True,
                withColumnBorders=True,
                striped=True,
                highlightOnHover=True,
                horizontalSpacing="sm",
                verticalSpacing="xs",
                style={"borderCollapse": "collapse", "width": "100%", "marginTop": "20px"}
            )
        ],
        style={
            "backgroundColor": "#ffffff",
            "padding": "32px",
            "borderRadius": "16px",
            "boxShadow": "0 2px 12px rgba(0,0,0,0.08)",
            "maxWidth": "1200px",
            "margin": "40px auto"
        }
    )
    return table, update_picker if update_picker is not no_update else date_range
