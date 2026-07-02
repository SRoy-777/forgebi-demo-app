from dash import html
import dash_bootstrap_components as dbc

layout = dbc.Container(
    [
        # Header Row
        dbc.Row(
            [
                dbc.Col(
                    html.A(
                        dbc.Button(
                            "← Main Homepage",
                            color="warning",
                            size="sm",
                            className="px-3 py-1",
                            style={'fontWeight': 'bold'}
                        ),
                        href="/",
                        style={'textDecoration': 'none'}
                    ),
                    width=6
                ),
                dbc.Col(
                    html.Div(
                        "Orient BI Marketing Department",
                        className='text-end fw-bold text-muted small',
                        style={'letterSpacing': '1px', 'color': '#f8d7da'}
                    ),
                    width=6
                )
            ],
            className='mb-5 mt-2 align-items-center'
        ),

        # Center Banner Title
        html.Div(
            [
                html.H1(
                    "~ Marketing ~",
                    style={
                        'textAlign': 'center',
                        'fontSize': '56px',
                        'fontFamily': 'Outfit, sans-serif',
                        'fontWeight': '700',
                        'color': 'white',
                        'letterSpacing': '2px',
                        'marginTop': '100px',
                        'marginBottom': '20px'
                    }
                ),
                html.Div(
                    "Hold on! Developer is Developing",
                    style={
                        'textAlign': 'center',
                        'fontSize': '28px',
                        'color': '#ffc107',
                        'fontWeight': '500',
                        'fontStyle': 'italic',
                        'marginTop': '40px'
                    }
                ),
            ]
        ),

        # Footer
        html.Div(
            "Developed By Subhankar Roy",
            style={
                'position': 'fixed',
                'bottom': '10px',
                'left': '15px',
                'color': '#f8d7da',
                'fontSize': '12px',
                'opacity': '0.85'
            }
        )
    ],
    fluid=True,
    style={
        'backgroundColor': '#5a0b0b',
        'minHeight': '100vh',
        'padding': '20px'
    }
)
