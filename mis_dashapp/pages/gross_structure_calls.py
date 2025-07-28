from pages import structure_call_data_ELT
import pandas as pd
import dash
import dash_mantine_components as dmc
from dash import html
from datetime import datetime, timedelta, date
from dash import callback, Output, Input, State
from dash import no_update

alldata = structure_call_data_ELT.backend_sender().get_data()

dash.register_page(__name__, path="/gross-structure-calls")

layout = dmc.MantineProvider(
    theme={"colorScheme": "light"},
    children=[
        dmc.Container(
            [
                dmc.Title("Gross Level Summary", order=2, mt=20),
                #Filters
                dmc.Group(
                    [
                        html.Div(
                            [
                                dmc.DatePickerInput(
                                    id="gross-date-input-range-picker",
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
                                    id="gross-exchange-multiselect",
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
                                    id="gross-segment-multiselect",
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
                dmc.Button("Select all dates",id="gross-all-date-button", size="sm", radius="sm", color="black", style={"marginTop": "5px"}),
                dmc.Paper(
                    [
                        dmc.Table(id="gross-summary-table-container", style={"marginTop": "20px", "width": "100%"})
                    ],
                    style={
                        "backgroundColor": "#ffffff",
                        "padding": "32px",
                        "borderRadius": "16px",
                        "boxShadow": "0 2px 12px rgba(0,0,0,0.08)",
                        "maxWidth": "1200px",
                        "margin": "40px auto"}
                ),
                dmc.Space(h=20),
                dmc.Paper(
                    [dmc.Table(id="gross-type-summary-table")],
                    style={
                        "backgroundColor": "#ffffff",
                        "padding": "32px",
                        "borderRadius": "16px",
                        "boxShadow": "0 2px 12px rgba(0,0,0,0.08)",
                        "maxWidth": "1200px",
                        "margin": "40px auto"}
                )
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
                dmc.Title("Summary - Yearly/Montly", order=3, mt=20),
                dmc.Space(h=20),
                dmc.Select(data=["Yearly","Monthly","Daily"],id="gross-time-range-select", placeholder="Select Time Range", label="Time Range", size="sm", radius="sm", withAsterisk=False, comboboxProps={"transitionProps": {"transition": "pop", "duration": 200}}),
                dmc.Paper(
                    [dmc.Table(id="gross-time-range-summary-table",)],
                    style={
                        "backgroundColor": "#ffffff",
                        "padding": "32px",
                        "borderRadius": "16px",
                        "boxShadow": "0 2px 12px rgba(0,0,0,0.08)",
                        "maxWidth": "1200px",
                        "margin": "40px auto"}
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
    Output("gross-summary-table-container", "children"),
    Output("gross-date-input-range-picker", "value"),
    Input("gross-all-date-button", "n_clicks"),
    Input("gross-date-input-range-picker", "value"),
    Input("gross-exchange-multiselect", "value"),
    Input("gross-segment-multiselect", "value"),
    prevent_initial_call=True
)
def update_gross_summary_table(n_clicks, date_range, exchanges, segments):
    ctx = dash.callback_context
    all_dates = [date(2024, 11, 1), datetime.now().date()]
    update_picker = no_update

    # Check if any filter is selected
    filters_selected = (
        (date_range and len(date_range) == 2) or
        (exchanges and len(exchanges) > 0) or
        (segments and len(segments) > 0)
    )

    if ctx.triggered and ctx.triggered[0]["prop_id"].startswith("gross-all-date-button"):
        start_date, end_date = all_dates
        update_picker = all_dates
    elif date_range and len(date_range) == 2:
        start_date = date_range[0]
        end_date = date_range[1]
    else:
        start_date, end_date = all_dates

    if not filters_selected:
        table = dmc.Table(
            [
                html.Tbody([
                    html.Tr([
                        html.Td("Select date range or any filter", colSpan=11, style={"textAlign": "center", "color": "red"})
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
        return table, update_picker

    alldata = structure_call_data_ELT.backend_sender().get_data(
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

    table = dmc.Table(
        [
            html.Thead([
                html.Tr([
                    html.Th("Total Calls", rowSpan=2, style={"backgroundColor": "#fdd835", "border": "1px solid #000000"}),
                    html.Th("Target Hit", rowSpan=2, style={"backgroundColor": "#fdd835", "border": "1px solid #000000"}),
                    html.Th("StopLoss Hit", rowSpan=2, style={"backgroundColor": "#fdd835", "border": "1px solid #000000"}),

                    html.Th("Neither target nor Stop loss hit", colSpan=3, style={"backgroundColor": "#fdd835", "border": "1px solid #000000"}),
                    html.Th("Total Closed Calls", rowSpan=2, style={"backgroundColor": "#fdd835", "border": "1px solid #000000"}),

                    html.Th("Open Calls", colSpan=3, style={"backgroundColor": "#fdd835", "border": "1px solid #000000"}),
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
                    html.Td(get_cell(0,0), style={"border": "1px solid #000000", "textAlign": "right"}),
                    html.Td(get_cell(1,0), style={"border": "1px solid #000000", "textAlign": "right"}),
                    html.Td(get_cell(2,0), style={"border": "1px solid #000000", "textAlign": "right"}),

                    html.Td(get_cell(3,0), style={"border": "1px solid #000000", "textAlign": "right"}),
                    html.Td(get_cell(4,0), style={"border": "1px solid #000000", "textAlign": "right"}),
                    html.Td(get_cell(5,0), style={"border": "1px solid #000000", "textAlign": "right"}),

                    html.Td(get_cell(6,0), style={"border": "1px solid #000000", "textAlign": "right"}),

                    html.Td(get_cell(7,0), style={"border": "1px solid #000000", "textAlign": "right"}),
                    html.Td(get_cell(8,0), style={"border": "1px solid #000000", "textAlign": "right"}),
                    html.Td(get_cell(9,0), style={"border": "1px solid #000000", "textAlign": "right"}),

                    html.Td(get_cell(10,0), style={"border": "1px solid #000000", "textAlign": "right"}),
                ]),
                html.Tr([
                    html.Td(get_cell(0,1), style={"border": "1px solid #000000", "textAlign": "right"}),
                    html.Td(get_cell(1,1), style={"border": "1px solid #000000", "textAlign": "right"}),
                    html.Td(get_cell(2,1), style={"border": "1px solid #000000", "textAlign": "right"}),

                    html.Td(get_cell(3,1), style={"border": "1px solid #000000", "textAlign": "right"}),
                    html.Td(get_cell(4,1), style={"border": "1px solid #000000", "textAlign": "right"}),
                    html.Td(get_cell(5,1), style={"border": "1px solid #000000", "textAlign": "right"}),

                    html.Td(get_cell(6,1), style={"border": "1px solid #000000", "textAlign": "right"}),

                    html.Td(get_cell(7,1), style={"border": "1px solid #000000", "textAlign": "right"}),
                    html.Td(get_cell(8,1), style={"border": "1px solid #000000", "textAlign": "right"}),
                    html.Td(get_cell(9,1), style={"border": "1px solid #000000", "textAlign": "right"}),

                    html.Td(get_cell(10,1), style={"border": "1px solid #000000", "textAlign": "right"}),
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
    return table, update_picker

@callback(
    Output("gross-time-range-summary-table", "children"),
    Input("gross-time-range-select", "value"),
    Input("gross-date-input-range-picker", "value"),
    Input("gross-exchange-multiselect", "value"),
    Input("gross-segment-multiselect", "value"),
    prevent_initial_call=True
)
def update_gross_time_range_summary_table(time_range, date_range, exchanges, segments):
    all_dates = [date(2024, 11, 1), datetime.now().date()]
    if date_range and len(date_range) == 2:
        start_date = date_range[0]
        end_date = date_range[1]
    else:
        start_date, end_date = all_dates

    if not time_range:
        summary_rows = [html.Tr([html.Td("Select time period", colSpan=11, style={"textAlign": "center", "color": "red"})])]
    elif time_range == "Yearly":
        summary_rows = structure_call_data_ELT.backend_sender().generate_timely_summary_rows(
            start_date=start_date,
            end_date=end_date,
            exchange=exchanges,
            exch_segment=segments,
            time="yearly",
        )
    elif time_range == "Monthly":
        summary_rows = structure_call_data_ELT.backend_sender().generate_timely_summary_rows(
            start_date=start_date,
            end_date=end_date,
            exchange=exchanges,
            exch_segment=segments,
            time="monthly",
        )
    elif time_range == "Daily":
        summary_rows = structure_call_data_ELT.backend_sender().generate_timely_summary_rows(
            start_date=start_date,
            end_date=end_date,
            exchange=exchanges,
            exch_segment=segments,
            time="daily",
        )

    filter_table = dmc.Table(
        [
            html.Thead([
                html.Tr([
                    html.Th("Month", rowSpan=2, style={"backgroundColor": "#fdd835", "textAlign": "center", "padding": "8px", "border": "1px solid #000000"}),
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
            html.Tbody(
                summary_rows,
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
    return filter_table

@callback(
    Output("gross-type-summary-table", "children"),
    Input("gross-time-range-select", "value"),
    Input("gross-all-date-button", "n_clicks"),
    Input("gross-date-input-range-picker", "value"),
    Input("gross-exchange-multiselect", "value"),
    Input("gross-segment-multiselect", "value"),
)
def update_gross_type_summary_table(time_range, n_clicks, date_range, exchanges, segments):
    ctx = dash.callback_context
    all_dates = [date(2024, 11, 1), datetime.now().date()]

    # Determine start and end date
    if ctx.triggered and ctx.triggered[0]["prop_id"].startswith("gross-all-date-button"):
        start_date, end_date = all_dates
    elif date_range and len(date_range) == 2:
        start_date = date_range[0]
        end_date = date_range[1]
    else:
        start_date, end_date = all_dates

    # Only show table if any filter is selected (same logic as summary table)
    filters_selected = (
        (date_range and len(date_range) == 2) or
        (exchanges and len(exchanges) > 0) or
        (segments and len(segments) > 0)
    )

    if not filters_selected:
        table = dmc.Table(
            [
                html.Tbody([
                    html.Tr([
                        html.Td("Select date range or any filter", colSpan=11, style={"textAlign": "center", "color": "red"})
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
        return table

    rows = structure_call_data_ELT.backend_sender().render_type_data_gross(
        start_date=start_date,
        end_date=end_date,
        exchange=exchanges,
        exch_segment=segments
    )

    table = dmc.Table(
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
    return table