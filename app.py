import dash
from dash import html, dcc, callback_context
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output, State
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
from anomaly_detector import AnomalyDetector
from virtualization_manager import VirtualizationManager

# Initialize the Dash app with a modern theme
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.FLATLY])
app.config.suppress_callback_exceptions = True

# Initialize the managers
detector = AnomalyDetector()
vm_manager = VirtualizationManager()

# Update interval (in milliseconds)
UPDATE_INTERVAL = 5000  # 5 seconds

# Simulated data for demonstration
def generate_sample_data():
    racks = [f"Rack-{i}" for i in range(1, 21)]
    data = {
        'rack_id': [],
        'temperature': [],
        'vibration': [],
        'power': [],
        'alert_count': [],
        'status': [],
        'timestamp': [],
        'cpu_usage': [],
        'memory_usage': [],
        'network_load': []
    }
    
    now = datetime.now()
    for rack in racks:
        for i in range(24):  # 24 hours of data
            data['rack_id'].append(rack)
            data['temperature'].append(np.random.normal(35, 5))
            data['vibration'].append(np.random.normal(0.5, 0.2))
            data['power'].append(np.random.normal(1000, 100))
            data['alert_count'].append(np.random.randint(0, 4))
            data['status'].append('normal' if np.random.random() > 0.2 else 'warning')
            data['timestamp'].append(now - timedelta(hours=i))
            data['cpu_usage'].append(np.random.uniform(20, 85))
            data['memory_usage'].append(np.random.uniform(30, 90))
            data['network_load'].append(np.random.uniform(10, 95))
    
    return pd.DataFrame(data)

# Layout components
def create_metric_card(title, value, color, icon, subtitle=None):
    return dbc.Card(
        dbc.CardBody([
            html.Div([
                html.I(className=f"fas {icon} fa-2x me-2", style={'color': color}),
                html.H4(title, className="card-title mb-0"),
            ], className="d-flex align-items-center"),
            html.H2(value, className="card-text text-center my-3", style={'color': color}),
            html.P(subtitle, className="text-muted mb-0") if subtitle else None,
        ]),
        className="mb-4 shadow-sm"
    )

def create_rack_map():
    """Create interactive rack map with status indicators."""
    server_status = vm_manager.get_server_status()
    
    fig = go.Figure()
    
    # Create a grid layout for racks
    rows, cols = 4, 5
    for idx, (rack_id, status) in enumerate(server_status.items()):
        row_idx = idx // cols
        col_idx = idx % cols
        
        # Get rack analysis
        analysis = detector.analyze_rack(
            rack_id,
            status['temperature'],
            np.random.normal(0.5, 0.2),  # Simulated vibration
            np.random.normal(1000, 100)   # Simulated power
        )
        
        # Determine color based on prediction and status
        if analysis['prediction']['status'] == 'critical':
            color = '#e74c3c'  # Red
        elif analysis['prediction']['status'] == 'warning':
            color = '#f1c40f'  # Yellow
        elif status['power_state'] == 'idle':
            color = '#95a5a6'  # Gray
        else:
            color = '#2ecc71'  # Green
        
        # Create hover text with prediction information
        hover_text = (
            f"<b>{rack_id}</b><br>" +
            f"Temperature: {status['temperature']:.1f}°C<br>" +
            f"CPU Usage: {status['cpu_usage']:.1f}%<br>" +
            f"Memory Usage: {status['memory_usage']:.1f}%<br>" +
            f"Power State: {status['power_state'].title()}<br>"
        )
        
        if analysis['prediction']['status'] != 'normal':
            hover_text += (
                f"<br><b>Prediction:</b><br>" +
                f"Status: {analysis['prediction']['status'].title()}<br>" +
                f"Confidence: {analysis['prediction']['confidence']*100:.1f}%<br>" +
                "Reasons:<br>" +
                "<br>".join(f"- {r}" for r in analysis['prediction']['reasons'])
            )
        
        fig.add_trace(go.Scatter(
            x=[col_idx],
            y=[row_idx],
            mode='markers+text',
            name=rack_id,
            text=[rack_id],
            marker=dict(size=40, color=color, symbol='square'),
            hovertemplate=hover_text + "<extra></extra>"
        ))
    
    fig.update_layout(
        showlegend=False,
        xaxis=dict(showgrid=False, zeroline=False, visible=False),
        yaxis=dict(showgrid=False, zeroline=False, visible=False),
        plot_bgcolor='white',
        height=500,
        margin=dict(l=20, r=20, t=20, b=20),
        paper_bgcolor='rgba(0,0,0,0)',
    )
    
    return fig

def create_server_load_visualization():
    """Create heatmap of server loads with VM allocation."""
    server_status = vm_manager.get_server_status()
    
    # Prepare data for heatmap
    racks = list(server_status.keys())
    metrics = ['CPU Usage', 'Memory Usage', 'Network Load']
    
    z_data = []
    hover_text = []
    
    for metric in metrics:
        metric_data = []
        hover_row = []
        for rack in racks:
            if metric == 'CPU Usage':
                value = server_status[rack]['cpu_usage']
            elif metric == 'Memory Usage':
                value = server_status[rack]['memory_usage']
            else:
                value = server_status[rack]['network_load']
            
            metric_data.append(value)
            
            # Create hover text with VM information
            vms = server_status[rack]['virtual_machines']
            vm_text = "<br>".join([
                f"VM: {vm['id']} (from {vm['source_server']})"
                for vm in vms
            ])
            
            hover_row.append(
                f"Rack: {rack}<br>" +
                f"{metric}: {value:.1f}%<br>" +
                f"Power State: {server_status[rack]['power_state']}<br>" +
                (f"Hosted VMs:<br>{vm_text}" if vm_text else "No VMs")
            )
        
        z_data.append(metric_data)
        hover_text.append(hover_row)
    
    fig = go.Figure(data=go.Heatmap(
        z=z_data,
        x=racks,
        y=metrics,
        colorscale='Viridis',
        hoverongaps=False,
        hovertemplate="%{customdata}<extra></extra>",
        customdata=hover_text
    ))
    
    fig.update_layout(
        title='Server Resource Utilization Heatmap',
        height=300,
        margin=dict(l=50, r=20, t=50, b=20),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)'
    )
    
    return fig

def create_load_distribution_chart():
    df = generate_sample_data()
    latest_data = df.groupby('rack_id').first().reset_index()
    
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        x=latest_data['rack_id'],
        y=latest_data['cpu_usage'],
        name='CPU Usage',
        marker_color='#3498db'
    ))
    
    fig.add_trace(go.Bar(
        x=latest_data['rack_id'],
        y=latest_data['memory_usage'],
        name='Memory Usage',
        marker_color='#2ecc71'
    ))
    
    fig.update_layout(
        barmode='group',
        title='Server Load Distribution',
        height=300,
        margin=dict(l=50, r=20, t=50, b=20),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )
    
    return fig

# Tabs content
def create_monitoring_tab():
    return dbc.Container([
        dbc.Row([
            dbc.Col(create_metric_card("Total Racks", "20", "#3498db", "fa-server", "Active Monitoring"), width=3),
            dbc.Col(create_metric_card("Active Alerts", "5", "#f1c40f", "fa-exclamation-triangle", "Require Attention"), width=3),
            dbc.Col(create_metric_card("Critical Issues", "2", "#e74c3c", "fa-times-circle", "Immediate Action Needed"), width=3),
            dbc.Col(create_metric_card("Healthy Racks", "15", "#2ecc71", "fa-check-circle", "Operating Normally"), width=3),
        ]),
        
        dbc.Row([
            dbc.Col([
                html.H3("Data Center Rack Status", className="my-4"),
                dcc.Graph(id='rack-map', figure=create_rack_map(), config={'displayModeBar': False}),
            ], width=12)
        ]),
        
        dbc.Row([
            dbc.Col([
                html.H3("Rack Details", className="my-4"),
                dbc.Card(
                    dbc.CardBody([
                        html.Div(id='rack-details'),
                        html.Div([
                            dbc.Button("Repair", color="primary", className="me-2", id="repair-btn"),
                            dbc.Button("Replace", color="danger", id="replace-btn"),
                        ], className="mt-3"),
                        html.Div(id='maintenance-alert', className="mt-3"),
                    ]),
                    className="shadow-sm"
                )
            ], width=12)
        ]),
    ], fluid=True)

def create_virtualization_tab():
    return dbc.Container([
        dbc.Row([
            dbc.Col([
                html.H3("Server Resource Utilization", className="my-4"),
                dcc.Graph(figure=create_server_load_visualization(), config={'displayModeBar': False}),
            ], width=12),
        ]),
        
        dbc.Row([
            dbc.Col([
                html.H3("Load Distribution", className="my-4"),
                dcc.Graph(figure=create_load_distribution_chart(), config={'displayModeBar': False}),
            ], width=12),
        ]),
        
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("Load Balancing Status"),
                    dbc.CardBody([
                        html.H5("Current Load Distribution Strategy", className="card-title"),
                        html.P("Dynamic resource allocation based on server utilization", className="card-text"),
                        dbc.ListGroup([
                            dbc.ListGroupItem([
                                html.Div("Active Load Balancing", className="fw-bold"),
                                html.Small("Distributing workload across available servers")
                            ]),
                            dbc.ListGroupItem([
                                html.Div("Power Optimization", className="fw-bold"),
                                html.Small("Consolidating loads to minimize power consumption")
                            ]),
                            dbc.ListGroupItem([
                                html.Div("Resource Scaling", className="fw-bold"),
                                html.Small("Automatic scaling based on demand")
                            ]),
                        ], flush=True),
                    ]),
                ], className="shadow-sm")
            ], width=12),
        ], className="mt-4"),
    ], fluid=True)

# Main app layout
app.layout = dbc.Container([
    dbc.Row([
        dbc.Col([
            html.H1("Data Center Monitoring System", className="text-primary my-4"),
            dbc.Tabs([
                dbc.Tab(create_monitoring_tab(), label="Monitoring", tab_id="monitoring"),
                dbc.Tab(create_virtualization_tab(), label="Virtualization", tab_id="virtualization"),
            ], id="tabs", active_tab="monitoring"),
        ])
    ]),
    
    dcc.Interval(
        id='interval-component',
        interval=UPDATE_INTERVAL,  # Update every 5 seconds
        n_intervals=0
    ),
    
    html.Div(id='maintenance-alert', className="mt-3")
], fluid=True, className="px-4")

# Callbacks
@app.callback(
    [Output('rack-map', 'figure'),
     Output('server-load-viz', 'figure')],
    [Input('interval-component', 'n_intervals')]
)
def update_graphs(n):
    """Update all graphs with latest data."""
    vm_manager.update_server_loads()
    vm_manager.optimize_workload()
    
    return create_rack_map(), create_server_load_visualization()

@app.callback(
    Output('rack-details', 'children'),
    [Input('rack-map', 'clickData'),
     Input('interval-component', 'n_intervals')]
)
def update_rack_details(clickData, n):
    if not clickData:
        return "Click on a rack to see details"
    
    rack_id = clickData['points'][0]['text']
    server_status = vm_manager.get_server_status()[rack_id]
    
    # Get analysis from anomaly detector
    analysis = detector.analyze_rack(
        rack_id,
        server_status['temperature'],
        np.random.normal(0.5, 0.2),  # Simulated vibration
        np.random.normal(1000, 100)   # Simulated power
    )
    
    # Create status color
    status_color = {
        'normal': 'success',
        'warning': 'warning',
        'critical': 'danger'
    }.get(analysis['prediction']['status'], 'secondary')
    
    return html.Div([
        html.H4(f"Rack ID: {rack_id}", className="mb-3"),
        
        # Current Status
        dbc.Alert(
            [
                html.H5("Current Status", className="alert-heading"),
                html.P(f"Power State: {server_status['power_state'].title()}", className="mb-0"),
                html.P(f"VM Hosting: {'Yes' if server_status['virtual_machines'] else 'No'}", className="mb-0")
            ],
            color=status_color,
            className="mb-3"
        ),
        
        # Metrics
        dbc.Row([
            dbc.Col([
                html.H5("Hardware Metrics", className="mb-3"),
                html.P([
                    html.I(className="fas fa-thermometer-half me-2"),
                    f"Temperature: {server_status['temperature']:.1f}°C"
                ]),
                html.P([
                    html.I(className="fas fa-microchip me-2"),
                    f"CPU Usage: {server_status['cpu_usage']:.1f}%"
                ]),
                html.P([
                    html.I(className="fas fa-memory me-2"),
                    f"Memory Usage: {server_status['memory_usage']:.1f}%"
                ]),
                html.P([
                    html.I(className="fas fa-network-wired me-2"),
                    f"Network Load: {server_status['network_load']:.1f}%"
                ]),
            ], width=6),
            
            dbc.Col([
                html.H5("Virtual Machines", className="mb-3"),
                html.Div([
                    dbc.ListGroup([
                        dbc.ListGroupItem(
                            [
                                html.Div(f"VM: {vm['id']}", className="fw-bold"),
                                html.Small(f"From: {vm['source_server']}"),
                                html.Div(f"Load: {vm['cpu_load']:.1f}%")
                            ]
                        ) for vm in server_status['virtual_machines']
                    ]) if server_status['virtual_machines'] else "No virtual machines"
                ])
            ], width=6),
        ]),
        
        # Prediction Information
        html.Div([
            html.H5("Failure Prediction", className="mt-4 mb-3"),
            dbc.Alert(
                [
                    html.P(f"Status: {analysis['prediction']['status'].title()}", className="mb-1"),
                    html.P(f"Confidence: {analysis['prediction']['confidence']*100:.1f}%", className="mb-1"),
                    html.P("Reasons:", className="mb-1"),
                    html.Ul([
                        html.Li(reason) for reason in analysis['prediction']['reasons']
                    ]) if analysis['prediction']['reasons'] else None,
                    html.P(
                        f"Predicted Failure: {analysis['prediction']['predicted_failure_time'].strftime('%Y-%m-%d %H:%M:%S')}"
                        if analysis['prediction']['predicted_failure_time']
                        else "No immediate failure predicted",
                        className="mt-2 mb-0"
                    )
                ],
                color=status_color
            )
        ]) if analysis['prediction']['status'] != 'normal' else None,
        
        # Action Buttons
        html.Div([
            dbc.Button("Repair", color="primary", className="me-2", id="repair-btn"),
            dbc.Button("Replace", color="danger", id="replace-btn"),
        ], className="mt-3"),
        
        html.Div(id='maintenance-alert', className="mt-3"),
    ])

@app.callback(
    Output('maintenance-alert', 'children'),
    [Input('repair-btn', 'n_clicks'),
     Input('replace-btn', 'n_clicks')],
    [State('rack-map', 'clickData')]
)
def handle_maintenance(repair_clicks, replace_clicks, clickData):
    """Handle repair and replace button clicks."""
    if not clickData or not callback_context.triggered:
        return None
        
    # Get the clicked rack
    rack_id = clickData['points'][0]['text']
    button_id = callback_context.triggered[0]['prop_id'].split('.')[0]
    
    if button_id == 'repair-btn' and repair_clicks:
        vm_manager.start_maintenance(rack_id, 'repair')
        return dbc.Alert(
            f"Repair started for {rack_id}. This will take 1 minute.",
            color="info",
            duration=60000  # Alert will disappear after 60 seconds
        )
    elif button_id == 'replace-btn' and replace_clicks:
        vm_manager.start_maintenance(rack_id, 'replace')
        return dbc.Alert(
            f"Replacement started for {rack_id}. This will take 1 minute.",
            color="warning",
            duration=60000  # Alert will disappear after 60 seconds
        )
    
    return None

if __name__ == '__main__':
    app.run_server(debug=True) 