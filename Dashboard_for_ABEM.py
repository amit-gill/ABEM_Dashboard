import os
import glob
import pandas as pd
import plotly.graph_objects as go
from dash import Dash, dcc, html
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output, State, MATCH, ALL
from dash_bootstrap_templates import load_figure_template
# =========================================================
# 1. LOAD DATA
# =========================================================

BASE_DIR = r"C:/Users/3059534/OneDrive - Queen's University Belfast/Documents/Research/ABEM/Exec/Output_SimResults/Simulation_data"
PATTERN = os.path.join(BASE_DIR, "Industrial_results_for_period_*.csv")

file_paths = sorted(glob.glob(PATTERN))
if not file_paths:
    raise FileNotFoundError(f"No CSVs found at {PATTERN}")

frames = []
for fp in file_paths:
    df_tmp = pd.read_csv(fp)
    df_tmp.columns = [c.strip() for c in df_tmp.columns]
    try:
        period = int(os.path.splitext(os.path.basename(fp))[0].split("_")[-1])
    except Exception:
        period = len(frames)
    df_tmp["Period"] = period
    frames.append(df_tmp)

df = pd.concat(frames, ignore_index=True)

numeric_cols = [
    "Industry ID", "Period",
    "Total domestic production", "Imports", "Actual Exports",
    "Total Sales", "Total Goods for Sale", "Employment"
]
for c in numeric_cols:
    if c in df.columns:
        df[c] = pd.to_numeric(df[c], errors="coerce")

# =========================================================
# 2. METRICS
# =========================================================

MACRO_METRICS = {
    "GDP (proxy: Σ Total domestic production)": "Total domestic production",
    "Imports": "Imports",
    "Exports (Actual)": "Actual Exports",
    "Total Sales": "Total Sales",
    "Total Goods for Sale": "Total Goods for Sale",
}
MACRO_SERIES_LABELS = {
    "Total domestic production": "GDP (proxy)",
    "Imports": "Imports",
    "Actual Exports": "Exports (Actual)",
    "Total Sales": "Total Sales",
    "Total Goods for Sale": "Total Goods for Sale",
}
macro_options = [{"label": k, "value": v} for k, v in MACRO_METRICS.items()]
macro_df = df.groupby("Period", as_index=False)[list(MACRO_METRICS.values())].sum()

MICRO_METRICS = {
    "Total domestic production": "Total domestic production",
    "Imports": "Imports",
    "Actual Exports": "Actual Exports",
    "Total Sales": "Total Sales",
    "Total Goods for Sale": "Total Goods for Sale",
}
micro_options = [{"label": k, "value": v} for k, v in MICRO_METRICS.items()]
default_micro_metrics = list(MICRO_METRICS.values())

industry_options = [
    {"label": str(int(i)), "value": int(i)}
    for i in sorted(df["Industry ID"].dropna().unique().astype(int))
]
default_industry = int(df["Industry ID"].dropna().astype(int).min())

compare_metric_options = [{"label": k, "value": v} for k, v in MICRO_METRICS.items()]

# =========================================================
# 3. APP SETUP
# =========================================================
dbc_css = "https://cdn.jsdelivr.net/gh/AnnMarieW/dash-bootstrap-templates/dbc.min.css"
app = Dash(external_stylesheets=[dbc.themes.MINTY, dbc.themes.BOOTSTRAP, dbc.icons.FONT_AWESOME, dbc_css], suppress_callback_exceptions=True, )
server = app.server

# =========================================================
# 4. FIGURE FORMATTER
# =========================================================
# adds  templates to plotly.io
load_figure_template(["minty", "minty_dark"])

def auto_place_legend(fig, theme, traces_threshold=3, is_bar_hint=False):
    """
    Heuristic-based legend placement:
    - If many traces OR hinted as bar chart → horizontal legend above plot (outside)
    - Else → boxed legend inside the plot (top-left)
    Keeps theme-adaptive background/border.
    """

    # Theme-adaptive colors
    if theme == "dark":
        legend_bg = "rgba(20,20,20,0.6)"
        legend_border = "rgba(255,255,255,0.3)"
    else:
        legend_bg = "rgba(255,255,255,0.6)"
        legend_border = "rgba(0,0,0,0.25)"

    # Determine chart type and trace count
    trace_count = len(fig.data)
    first_type = (fig.data[0].type if fig.data else "").lower()

    # Treat as bar if hinted or detected
    is_bar = is_bar_hint or first_type in ("bar",)

    # Heuristic:
    # - For bar charts OR many traces, place above the plot, horizontal, outside
    # - Otherwise, place inside (top-left), vertical
    if is_bar or trace_count > traces_threshold:
        # Outside above, horizontal row
        fig.update_layout(
            legend=dict(
                bgcolor=legend_bg,
                bordercolor=legend_border,
                borderwidth=1,
                orientation="h",
                yanchor="bottom",
                y=1.02,     # a bit above the plotting area
                xanchor="right",
                x=1.0,      # right-aligned
                font=dict(size=12),
                traceorder="normal",
            )
        )
        # Add a little extra top margin to make room for the legend outside the plot
        ml, mr = fig.layout.margin.l or 40, fig.layout.margin.r or 40
        fig.update_layout(margin=dict(l=ml, r=mr, t=max(70, (fig.layout.margin.t or 50)), b=fig.layout.margin.b or 40))
    else:
        # Inside top-left, vertical box
        fig.update_layout(
            legend=dict(
                bgcolor=legend_bg,
                bordercolor=legend_border,
                borderwidth=1,
                orientation="v",
                x=0.01,
                y=0.99,
                xanchor="left",
                yanchor="top",
                font=dict(size=12),
                traceorder="normal",
            )
        )


###

def format_currency_axis(fig, template, theme, height=350):
        
    # Adaptive legend background based on theme
    if theme == "dark":
        legend_bg = "rgba(20,20,20,0.6)"   # dark semi-transparent
        legend_border = "rgba(255,255,255,0.3)"
    else:
        legend_bg = "rgba(255,255,255,0.6)" # light semi-transparent
        legend_border = "rgba(0,0,0,0.25)"
    # 
    fig.update_layout(
        template=template,
        height=height,
        autosize=False,
        margin=dict(l=40, r=40, t=50, b=50),
        uirevision="static",
        title_x=0.5,
        #legend=dict(orientation="h", y=1.05, x=0),        
        legend=dict(
                bgcolor=legend_bg,
                bordercolor=legend_border,
                borderwidth=1,
                x=0.01,
                y=0.99,
                xanchor="left",
                yanchor="top",
                font=dict(size=12)
            ),
        showlegend=False,  # start hidden; JS will reveal on hover/interaction
    )

    # Integer periods
    fig.update_xaxes(
        tickmode="linear",
        dtick=1,
        tickformat=".0f",
        title="Period"
    )

    # Y axis in BILLIONS now
    fig.update_yaxes(
        title="£ billion",
        tickprefix="£",
        tickformat=","
    )

    # Scale the data + hover to BILLIONS
    for tr in fig.data:
        # Scale actual plotted values
        tr.y = tr.y / 1000

        # Scale hover too (customdata)
        tr.update(
            customdata=tr.y,
            hovertemplate="%{x}<br>£%{customdata:,.2f} bn<extra></extra>"
        )

    
    #---- Auto legend placement ----
    # Hint bar for comparison page: detect bar from first trace OR pass hint externally if you prefer.
    first_type = (fig.data[0].type if fig.data else "").lower()
    is_bar_hint = first_type == "bar"
    auto_place_legend(fig, theme, traces_threshold=3, is_bar_hint=is_bar_hint)

    return fig

# =========================================================
# 5. LAYOUT HELPERS
# =========================================================

def CenteredSection(children):
    return html.Div(
        html.Div(children, className="d-flex flex-column align-items-center text-center", style={"width": "100%"}),
        className="container-fluid"
    )

def sticky_header():
    return html.Div(
        [
            dbc.Row(
                [
                    dbc.Col(html.H1("ABEM Simulation Dashboard", className="text-white text-center"), width=12),
                ],
                justify="center",
                className="mt-2"
            ),
            #html.Hr(className="my-2")
        ],
        style={
            "position": "sticky",
            #"height" : "100px",
            #"top": "25px",
            #"zIndex": "2000",
            #"backgroundColor": "var(--bs-body-bg)",
            #"backdropFilter": "saturate(180%) blur(6px)",
        },
        className="bg-primary p-2",
    )

def nav_item(id_str, href, icon_class, label_text):
    """
    A single sidebar navigation item with icon + label.
    Tooltips show on collapsed (icon-only) mode via Bootstrap 'title' attribute.
    """
    return dcc.Link(
        html.Div(
            [
                html.I(className=f"{icon_class} nav-icon", **{"data-bs-toggle": "tooltip", "data-bs-placement": "right", "title": label_text}),
                html.Span(label_text, className="label ms-2"),
            ],
            id=id_str,
            className="nav-item"
        ),
        href=href,
        className="nav-link-wrapper"
    )

def sidebar():
    return html.Div(
        [
            # Sidebar header row (icon-only on collapsed; text hides via CSS)
            # html.Div(
            #     [
            #         html.I(className="bi bi-list me-2"),
            #         html.Span("Navigation", className="label")
            #     ],
            #     className="sidebar-header"
            # ),

            html.Div(
                [
                    nav_item("nav-macro", "/macro", "bi bi-graph-up", "MACRO"),
                    nav_item("nav-micro", "/micro", "bi bi-building", "MICRO"),
                    nav_item("nav-compare", "/compare", "bi bi-bar-chart-line", "COMPARISON"),
                ],
                className="sidebar-content"
            ),

            html.Div(className="flex-grow-1"),
            
            html.Span(
                [
                    #dbc.Label(className="fa fa-moon", html_for="theme-switch"),
                    dbc.Switch(
                        id="theme-switch",
                        label="Dark mode",
                        value=False,
                        className="d-inline-block ms-1",
                        style= {"fontSize": 14, },
                        label_style={"fontSize": 14, 
                                     "marginBottom": 0,
                                     "marginTop": 0,
                                     }
                    ),
                    #dbc.Label(className="fa fa-sun", html_for="theme-switch"),
                ],
                className="sidebar-footer mt-3"
            ),
        ],
        id="sidebar",
        className="sidebar expanded"  # default desktop: expanded
    )

# =========================================================
# 6. PAGE BODIES
# =========================================================

macro_body = html.Div([
    CenteredSection([
        html.H2("Macroeconomic Time Series"),
        dbc.Row([
            dbc.Col([
                html.Label("Indicators"),
                dcc.Dropdown(
                    id={"type": "metrics-dropdown", "page": "macro"},
                    options=macro_options,
                    value=["Total domestic production", "Imports"],
                    multi=True,
                )],
                width = 8,
                ),
            ],
            className="g-3",
            justify="center",
            style={"width": "80%", "margin": "0 auto", "marginBottom": "20px"},
        ),
        dcc.Graph(id={"type": "ts-graph", "page": "macro"}, style={"width": "100%", "height": "520px"}),
        html.Button("Download CSV", id={"type": "download-btn", "page": "macro"}, className="btn btn-outline-primary mt-2"),
        dcc.Download(id={"type": "download", "page": "macro"})
    ])
])


micro_body = html.Div([
    CenteredSection([
        html.H2("Microeconomic Time Series"),

        # ---- Row for Industry + Indicators ----
        dbc.Row(
            [
                dbc.Col(
                    [
                        html.Label("Industry"),
                        dcc.Dropdown(
                            id={"type": "industry-dropdown", "page": "micro"},
                            options=industry_options,
                            value=default_industry,
                            clearable=False,
                        ),
                    ],
                    width=1,
                ),

                dbc.Col(
                    [
                        html.Label("Indicators"),
                        dcc.Dropdown(
                            id={"type": "metrics-dropdown", "page": "micro"},
                            options=micro_options,
                            value=default_micro_metrics,
                            multi=True,
                        ),
                    ],
                    width=9,
                ),
            ],
            className="g-3",      # small gap between columns
            justify="center",
            style={"width": "80%", "margin": "0 auto", "marginBottom": "20px" },
        ),

        # ---- Graph ----
        dcc.Graph(
            id={"type": "ts-graph", "page": "micro"},
            style={"width": "100%", "height": "360px"}
        ),

        # ---- Download Button ----
        html.Button(
            "Download CSV",
            id={"type": "download-btn", "page": "micro"},
            className="btn btn-outline-primary mt-2"
        ),
        dcc.Download(id={"type": "download", "page": "micro"})
    ])
])


compare_body = html.Div([
    CenteredSection([
        html.H2("Industry Comparison — Multi‑Industry Time Series"),

        # --- Row: Indicator + Industries ---
        dbc.Row(
            [
                # Indicator column
                dbc.Col(
                    [
                        html.Label("Indicator"),
                        dcc.Dropdown(
                            id={"type": "metrics-dropdown", "page": "compare"},
                            options=compare_metric_options,
                            value="Total domestic production",
                            clearable=False,
                        ),
                    ],
                    width=4,
                ),

                # Industries column
                dbc.Col(
                    [
                        html.Label("Industries"),
                        dcc.Dropdown(
                            id={"type": "industry-multi", "page": "compare"},
                            options=industry_options,
                            value=[opt["value"] for opt in industry_options[:5]],
                            multi=True,
                        ),
                    ],
                    width=7,
                ),
            ],
            className="g-3",
            justify="center",
            style={"width": "85%", "margin": "0 auto", "marginBottom": "20px"},
        ),

        # --- Graph ---
        dcc.Graph(
            id={"type": "ts-graph", "page": "compare"},
            style={"width": "100%", "height": "100%"}
        ),

        # --- Download button ---
        html.Button(
            "Download CSV",
            id={"type": "download-btn", "page": "compare"},
            className="btn btn-outline-primary mt-2"
        ),
        dcc.Download(id={"type": "download", "page": "compare"}),
    ])
])

# =========================================================
# 7. LAYOUT + ROUTER
# =========================================================

app.layout = dbc.Container([
        html.Div([
            # Theme CSS link (switchable)
            html.Link(id="theme-link", rel="stylesheet", href=dbc.themes.MINTY),

            # App state + routing
            dcc.Store(id="theme-store", data="light"),
            dcc.Location(id="url"),
            #
            sticky_header(),
            #
            html.Div(
                [
                    # Collapsible Sidebar (left)
                    sidebar(),
                    # Content Area (right)
                    html.Div(id="page-content", className="content-area")
                ],
                className="layout"
            )
        ])
    ],
    fluid=True,
    className="dbc",
    )



@app.callback(Output("page-content", "children"), Input("url", "pathname"))
def router(path):
    if path and path.rstrip("/").endswith("/micro"):
        return micro_body
    if path and path.rstrip("/").endswith("/compare"):
        return compare_body
    return macro_body

# Highlight active nav item
@app.callback(
    Output("nav-macro", "className"),
    Output("nav-micro", "className"),
    Output("nav-compare", "className"),
    Input("url", "pathname"),
)
def highlight_nav(pathname):
    path = (pathname or "").rstrip("/")
    def cls(active):
        return "nav-item active" if active else "nav-item"
    return (
        cls(path.endswith("/macro") or path in ["", "/"]),
        cls(path.endswith("/micro")),
        cls(path.endswith("/compare")),
    )

# =========================================================
# 8. THEME TOGGLE
# =========================================================

@app.callback(
    [Output("theme-link", "href"), Output("theme-store", "data")],
    Input("theme-switch", "value")
)
def toggle_theme(is_dark):
    return (dbc.themes.MINTY, "dark") if is_dark else (dbc.themes.MINTY, "light")

# =========================================================
# 9. UNIFIED FIGURE CALLBACK
# =========================================================

@app.callback(
    Output({"type": "ts-graph", "page": MATCH}, "figure"),
    [
        Input({"type": "metrics-dropdown", "page": MATCH}, "value"),
        Input({"type": "industry-dropdown", "page": ALL}, "value"),
        Input({"type": "industry-multi", "page": ALL}, "value"),
        Input("url", "pathname"),
        Input("theme-store", "data"),
    ]
)
def draw_timeseries(metrics_selected, micro_ind, compare_ind, pathname, theme):

    template = "plotly_dark" if theme == "dark" else "plotly_white"
    template = "minty_dark" if theme == "dark" else "minty"
    path = (pathname or "").rstrip("/")

    # ----- Macro -----
    if path.endswith("/macro") or path in ["", "/"]:
        metrics = metrics_selected or []
        if isinstance(metrics, str):
            metrics = [metrics]

        fig = go.Figure()
        for col in metrics:
            if col in macro_df.columns:
                fig.add_trace(go.Scatter(
                    x=macro_df["Period"], y=macro_df[col],
                    mode="lines+markers", name=f"{MACRO_SERIES_LABELS.get(col, col)} (£bn)"
                ))
        fig.update_layout(title="Macroeconomic Indicators Over Time", xaxis_title="Period")
        return format_currency_axis(fig, template, theme)

    # ----- Micro -----
    if path.endswith("/micro"):
        metrics = metrics_selected or []
        if isinstance(metrics, str):
            metrics = [metrics]
        industry = micro_ind[0] if (micro_ind and micro_ind[0]) else default_industry

        dff = df[df["Industry ID"] == industry].sort_values("Period")
        fig = go.Figure()
        for col in metrics:
            if col in dff.columns:
                fig.add_trace(go.Scatter(
                    x=dff["Period"], y=dff[col],
                    mode="lines+markers", name=f"{col} (£bn)"
                ))
        fig.update_layout(title=f"Industry-{industry} Indicators Over Time", xaxis_title="Period")
        return format_currency_axis(fig, template, theme)

    # ----- Comparison -----
    if path.endswith("/compare"):
        metric = metrics_selected
        if isinstance(metric, list):
            metric = metric[0] if metric else "Total domestic production"

        inds = compare_ind[0] if (compare_ind and compare_ind[0]) else []
        if isinstance(inds, int):
            inds = [inds]

        fig = go.Figure()
        
        for ind in inds:
            dff = df[df["Industry ID"] == ind].sort_values("Period")
            if metric in dff.columns:
                fig.add_trace(go.Bar(
                    x=dff["Period"],
                    y=dff[metric],
                    name=f"Industry {ind}"
                ))

        fig.update_layout(
            barmode="group",
            title=f"Comparison — {metric} across Industries",
            xaxis_title="Period"
        )

        return format_currency_axis(fig, template, theme)

# =========================================================
# 10. DOWNLOAD CALLBACKS
# =========================================================

@app.callback(
    Output({"type": "download", "page": "macro"}, "data"),
    Input({"type": "download-btn", "page": "macro"}, "n_clicks"),
    State({"type": "metrics-dropdown", "page": "macro"}, "value"),
    prevent_initial_call=True
)
def download_macro(n, metrics):
    if isinstance(metrics, str):
        metrics = [metrics]
    cols = ["Period"] + metrics
    return dcc.send_data_frame(macro_df[cols].to_csv, "macro.csv", index=False)

@app.callback(
    Output({"type": "download", "page": "micro"}, "data"),
    Input({"type": "download-btn", "page": "micro"}, "n_clicks"),
    [
        State({"type": "industry-dropdown", "page": "micro"}, "value"),
        State({"type": "metrics-dropdown", "page": "micro"}, "value"),
    ],
    prevent_initial_call=True
)
def download_micro(n, ind, metrics):
    if isinstance(metrics, str):
        metrics = [metrics]
    dff = df[df["Industry ID"] == ind].sort_values("Period")
    cols = ["Period"] + metrics
    return dcc.send_data_frame(dff[cols].to_csv, f"micro_{ind}.csv", index=False)

@app.callback(
    Output({"type": "download", "page": "compare"}, "data"),
    Input({"type": "download-btn", "page": "compare"}, "n_clicks"),
    [
        State({"type": "metrics-dropdown", "page": "compare"}, "value"),
        State({"type": "industry-multi", "page": "compare"}, "value"),
    ],
    prevent_initial_call=True
)
def download_compare(n, metric, inds):
    if isinstance(inds, int):
        inds = [inds]
    rows = []
    for ind in inds:
        dff = df[df["Industry ID"] == ind].sort_values("Period")
        if metric in dff.columns:
            tmp = dff[["Period", metric]].copy()
            tmp.insert(1, "Industry ID", ind)
            rows.append(tmp)
    out = pd.concat(rows)
    return dcc.send_data_frame(out.to_csv, "comparison.csv", index=False)

# =========================================================
# 11. CUSTOM HTML, CSS & JS (COLLAPSIBLE SIDEBAR + TOOLTIP)
# =========================================================

app.index_string = """
<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <title>ABEM Dashboard</title>
        {%favicon%}
        {%css%}

        <!-- Bootstrap Icons -->
        <link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.css" rel="stylesheet"/>

        <style>
            :root {
                --sidebar-expanded: 250px;
                --sidebar-collapsed: 100px;
                --header-offset: 100px; /* approx sticky header height */
            }

            /* Sidebar base */
            .sidebar {
                position: fixed;
                top: var(--header-offset);
                left: 0;
                bottom: 0;
                display: flex;
                flex-direction: column;
                padding: 14px 12px;
                overflow-y: auto;
                /*overflow: visible !important;*/
                background-color: var(--bs-body-bg);
                border-right: 1px solid var(--bs-border-color);
                width: var(--sidebar-expanded);
                transition: width .25s ease;
                z-index: 2000;
            }
            .sidebar.collapsed {
                width: var(--sidebar-collapsed);
            }
            .sidebar-header {
                display: flex;
                align-items: center;
                font-weight: 600;
                font-size: 1.2rem;
                padding: 8px 10px;
                border-radius: .375rem;
                color: var(--bs-body-color);
            }
            .sidebar.collapsed .link-text {
                display: none; /* Removes text from layout */
            }
            .sidebar-content {
                margin-top: 25px;
                //top: 25x; ??
                display: flex;
                flex-direction: column;
                gap: 6px;
            }
            .tooltip {
                z-index: 5000 !important;
            }

            /*.nav-link-wrapper { text-decoration: none; color: inherit; }*/
            .nav-link-wrapper { text-decoration: none; color: var(--bs-info); }
            .nav-item {
                display: flex;
                align-items: center;
                gap: .25rem;
                padding: 10px 10px;
                border-radius: .375rem;
                color: var(--bs-primary);
                transition: background-color .15s ease, color .15s ease;
                text-align: center;
            }
            .nav-item:hover {
                background-color: rgba(var(--bs-primary-rgb), 0.18); /*  rgba(13, 110, 253, 0.18); /* primary tint */
                cursor: pointer;
            }
            .nav-item.active {
                background-color: rgba(var(--bs-primary-rgb), 0.25); /*rgba(13, 110, 253, 0.25);*/
                /*color: var(--bs-primary);*/
                font-weight: 550;
            }
            .nav-icon {
                font-size: 1.2rem;
                width: 24px;
                text-align: center;
            }

            /* Content area positioning (sibling of sidebar) */
            .content-area {
                margin-left: var(--sidebar-expanded);
                padding: 20px;
                width: calc(100% - var(--sidebar-expanded));
                transition: margin-left .25s ease, width .25s ease;
            }
            /* When sidebar collapses, shrink content left margin */
            .sidebar.collapsed + .content-area {
                margin-left: var(--sidebar-collapsed);
                width: calc(100% - var(--sidebar-collapsed));
            }

            /* Mobile behavior: sidebar slides over content */
            @media (max-width: 768px) {
                .sidebar {
                    transform: translateX(calc(-1 * var(--sidebar-expanded)));
                    width: var(--sidebar-expanded); /* show full width when open */
                    box-shadow: 0 0 0 rgba(0,0,0,0);
                    background-color: rgba(0,0,0,0.92);
                    color: #fff;
                }
                .sidebar .nav-item:hover { background-color: rgba(255,255,255,0.08); }
                .sidebar.sidebar-open {
                    transform: translateX(0);
                    box-shadow: 0 8px 24px rgba(0,0,0,0.35);
                }
                .content-area {
                    margin-left: 0 !important;
                    width: 100% !important;
                }
            }

            /* Outside toggle button (always visible, top-left) */
            #sidebar-toggle {
                position: fixed;
                top: calc(var(--header-offset) - 12px);
                left: 12px;
                z-index: 2100;
                background-color: var(--bs-body-bg); /* #0d6efd;*/
                color: var(--bs-primary); /* white;*/
                padding: 8px 12px;
                border: none;
                border-radius: 6px;
                cursor: pointer;
                display: inline-flex;
                align-items: center;
                gap: 8px;
                box-shadow: 0 4px 12px rgba(var(--bs-primary-rgb), 0.24); /*13,110,253,0.24);*/
            }
            #sidebar-toggle .bi { font-size: 1.2rem; }
            #sidebar-toggle:hover { filter: brightness(0.95); }
        </style>
    </head>

    <body>
        <!-- Outside toggle button (desktop collapses; mobile slides over) -->
        <button id="sidebar-toggle" title="Toggle menu">
            <i class="bi bi-list"></i> MENU
        </button>

        {%app_entry%}
        <footer>
            {%config%}
            {%scripts%}
            <!-- Bootstrap 5 JS bundle (for tooltips) -->
            <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js"></script>

            <script>
                // Initialize Bootstrap tooltips for all elements with data-bs-toggle="tooltip"
                function initTooltips(scope) {
                    var container = scope || document;
                    var tooltipTriggerList = [].slice.call(container.querySelectorAll('[data-bs-toggle="tooltip"]'))
                    tooltipTriggerList.map(function (el) {
                        // Avoid re-initialization
                        if (!el._tooltipInstance) {
                            //el._tooltipInstance = new bootstrap.Tooltip(el);                            
                            el._tooltipInstance = new bootstrap.Tooltip(el, {
                                container: 'body',
                                placement: 'right'
                            });

                        }
                        return el._tooltipInstance;
                    });
                }

                // Observe DOM changes to re-init tooltips when Dash updates content
                const observer = new MutationObserver(function(mutationsList) {
                    for (const mutation of mutationsList) {
                        if (mutation.type === 'childList') {
                            initTooltips(mutation.target);
                        }
                    }
                });
                observer.observe(document.body, { childList: true, subtree: true });

                // Run on page load
                document.addEventListener('DOMContentLoaded', function() {
                    initTooltips(document);
                });

                // Handle sidebar toggle button behavior:
                // - On mobile (<=768px): toggle slide-over (sidebar-open)
                // - On desktop: toggle collapsed class
                function isMobile() {
                    return window.matchMedia('(max-width: 768px)').matches;
                }

                function toggleSidebar() {
                    var sb = document.getElementById('sidebar');
                    var content = document.getElementById('page-content'); // keep id for compatibility
                    if (!sb) return;

                    if (isMobile()) {
                        // Slide over behavior
                        if (sb.classList.contains('sidebar-open')) {
                            sb.classList.remove('sidebar-open');
                        } else {
                            sb.classList.add('sidebar-open');
                        }
                    } else {
                        // Collapse/expand rail
                        if (sb.classList.contains('collapsed')) {
                            sb.classList.remove('collapsed');
                            sb.classList.add('expanded');
                        } else {
                            sb.classList.add('collapsed');
                            sb.classList.remove('expanded');
                        }
                    }
                }

                document.getElementById('sidebar-toggle').addEventListener('click', toggleSidebar);

                // Close slide-over when clicking outside on mobile
                document.addEventListener('click', function(e) {
                    var sb = document.getElementById('sidebar');
                    if (!sb) return;
                    if (!isMobile()) return;
                    const toggleBtn = document.getElementById('sidebar-toggle');
                    const sidebarClicked = sb.contains(e.target);
                    const toggleClicked = toggleBtn.contains(e.target);
                    if (!sidebarClicked && !toggleClicked && sb.classList.contains('sidebar-open')) {
                        sb.classList.remove('sidebar-open');
                    }
                });

                // Ensure correct state on resize (avoid stuck classes)
                window.addEventListener('resize', function() {
                    var sb = document.getElementById('sidebar');
                    if (!sb) return;
                    if (isMobile()) {
                        // mobile: ensure collapsed is removed; slide-over controls visibility
                        sb.classList.remove('collapsed');
                        sb.classList.add('expanded'); // full width when open
                    } else {
                        // desktop: ensure slide-over is closed
                        sb.classList.remove('sidebar-open');
                    }
                });
            </script>

            {%renderer%}
        </footer>
    </body>
</html>

<script>
(function() {
  const HIDE_DELAY_MS = 1200;  // hide after 1.2s of no interaction
  const SHOW_ON_EVENTS = ['plotly_hover', 'plotly_unhover', 'plotly_relayout', 'mousemove', 'touchstart'];

  function setShowLegend(gd, show) {
    // Avoid redundant relayouts
    const current = gd.layout && gd.layout.showlegend;
    if (current === show) return;
    Plotly.relayout(gd, { showlegend: show });
  }

  function wireLegendAutohide(gd) {
    if (!gd || gd._legendAutohideWired) return;
    gd._legendAutohideWired = true;

    let hideTimer = null;

    function showLegend() {
      clearTimeout(hideTimer);
      setShowLegend(gd, true);
      hideTimer = setTimeout(() => setShowLegend(gd, false), HIDE_DELAY_MS);
    }

    // Register events to bring the legend back while interacting
    SHOW_ON_EVENTS.forEach(evt => {
      gd.addEventListener(evt, showLegend, { passive: true });
    });

    // First render: ensure hidden
    setShowLegend(gd, false);
  }

  // Attach to existing and future graphs
  function initAll() {
    document.querySelectorAll('.js-plotly-plot').forEach(wireLegendAutohide);
  }

  // Run on load
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initAll);
  } else {
    initAll();
  }

  // Re-run when Dash updates DOM
  const mo = new MutationObserver(() => initAll());
  mo.observe(document.body, { childList: true, subtree: true });
})();
</script>
"""

# =========================================================
# 12. RUN APP
# =========================================================

if __name__ == "__main__":
    app.run(debug=True, port=8055)