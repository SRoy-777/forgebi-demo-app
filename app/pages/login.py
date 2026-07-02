from dash import html, dcc, Input, Output, State, callback
import dash_bootstrap_components as dbc
from backend.services.notifier import send_admin_email_alert


layout = dbc.Container(

    [

        dbc.Row(

            [

                dbc.Col(

                    dbc.Card(

                        dbc.CardBody(

                            [

                                html.H2(

                                    "ForgeBI Login",

                                    style={

                                        'textAlign': 'center',

                                        'marginBottom': '25px',

                                        'fontWeight': 'bold'

                                    }

                                ),

                                html.Div(
                                    [
                                        html.P("🔑 Demo Account Details:", style={'fontWeight': 'bold', 'marginBottom': '5px', 'fontSize': '13px', 'color': '#C8A04D'}),
                                        html.P("Email: demo@forgebi.com", style={'margin': '0', 'fontSize': '12px', 'fontFamily': 'monospace', 'color': '#4a4a4a'}),
                                        html.P("Password: demo123", style={'margin': '0', 'fontSize': '12px', 'fontFamily': 'monospace', 'color': '#4a4a4a'})
                                    ],
                                    style={
                                        'backgroundColor': '#FAF8F5',
                                        'border': '1px solid #E8E5DF',
                                        'borderRadius': '6px',
                                        'padding': '10px 15px',
                                        'marginBottom': '20px',
                                        'textAlign': 'left'
                                    }
                                ),

                                dbc.Input(

                                    id='login-email',

                                    type='email',

                                    placeholder='Enter Email',

                                    className='mb-3'

                                ),

                                dbc.Input(

                                    id='login-password',

                                    type='password',

                                    placeholder='Enter Password',

                                    className='mb-3'

                                ),

                                dbc.Button(

                                    "Login",

                                    id='login-btn',

                                    color='dark',

                                    style={

                                        'width': '100%'

                                    }

                                ),

                                html.Div(

                                    id='login-message',

                                    style={

                                        'color': 'red',

                                        'marginTop': '15px',

                                        'textAlign': 'center'

                                    }

                                ),

                                html.Div(
                                    html.A(
                                        "Forgot Password?",
                                        id="forgot-password-link",
                                        n_clicks=0,
                                        style={
                                            "textAlign": "center",
                                            "display": "block",
                                            "marginTop": "15px",
                                            "color": "#6c757d",
                                            "fontSize": "14px",
                                            "textDecoration": "underline",
                                            "cursor": "pointer"
                                        }
                                    )
                                )

                            ]

                        ),

                        style={

                            'padding': '20px',

                            'borderRadius': '12px'

                        }

                    ),

                    width=4

                )

            ],

            justify='center',

            style={

                'marginTop': '120px'

            }

        ),

        # Forgot Password Modal
        dbc.Modal(
            [
                dbc.ModalHeader(dbc.ModalTitle("Request Password Reset")),
                dbc.ModalBody(
                    [
                        html.P("Enter your registered email address below. We will send a request automatically to the Administrator."),
                        dbc.Input(
                            id="reset-email-input",
                            type="email",
                            placeholder="Enter email",
                            className="mb-3"
                        ),
                        html.Div(id="reset-request-status", style={"textAlign": "center"})
                    ]
                ),
                dbc.ModalFooter(
                    [
                        dbc.Button("Send Request", id="btn-submit-reset", color="danger", className="me-2"),
                        dbc.Button("Close", id="btn-close-reset", color="secondary")
                    ]
                )
            ],
            id="forgot-password-modal",
            is_open=False,
        )

    ],

    fluid=True

)


# ---------------------------------------------------
# Forgot Password Callbacks
# ---------------------------------------------------

@callback(
    Output("forgot-password-modal", "is_open"),
    [
        Input("forgot-password-link", "n_clicks"),
        Input("btn-close-reset", "n_clicks")
    ],
    [State("forgot-password-modal", "is_open")],
    prevent_initial_call=True
)
def toggle_forgot_password_modal(link_clicks, close_clicks, is_open):
    if link_clicks or close_clicks:
        return not is_open
    return is_open


@callback(
    [
        Output("reset-request-status", "children"),
        Output("reset-request-status", "style")
    ],
    Input("btn-submit-reset", "n_clicks"),
    State("reset-email-input", "value"),
    prevent_initial_call=True
)
def handle_reset_request(n_clicks, email_value):
    if not n_clicks or not email_value:
        return "Please enter your email address.", {"color": "red"}

    email_clean = email_value.strip()
    if "@" not in email_clean or "." not in email_clean:
        return "Invalid email address format.", {"color": "red"}

    subject = f"🚨 Password Reset Request: {email_clean}"
    html_content = f"""
    <div style="font-family: Arial, sans-serif; padding: 20px; border: 1px solid #ddd; border-radius: 8px;">
        <h2 style="color: #d9534f; border-bottom: 2px solid #d9534f; padding-bottom: 10px; margin-top: 0;">Password Reset Request</h2>
        <p>A user has requested a password reset because they forgot their login credentials.</p>
        <table style="width: 100%; border-collapse: collapse; margin-top: 15px; margin-bottom: 20px;">
            <tr style="background-color: #f9f9f9;">
                <td style="padding: 8px; font-weight: bold; width: 120px; border-bottom: 1px solid #eee;">User Email:</td>
                <td style="padding: 8px; border-bottom: 1px solid #eee;">{email_clean}</td>
            </tr>
        </table>
        <h3 style="color: #333; margin-bottom: 10px;">Next Steps for Administrator:</h3>
        <ol style="line-height: 1.6;">
            <li>Verify the user's identity.</li>
            <li>Generate a secure temporary password.</li>
            <li>Update their password in the PostgreSQL <code>user_access</code> database table.</li>
            <li>Run the snapshot export (<code>python snapshot/export_snapshots.py</code>) and upload script (<code>python upload_to_r2.py</code>) to sync changes to the app.</li>
            <li>Send the temporary password to the user.</li>
        </ol>
        <hr style="border: 0; border-top: 1px solid #eee; margin-top: 25px;">
        <p style="font-size: 11px; color: #777; margin-bottom: 0;">Sent automatically via Orient BI Reset Assistant.</p>
    </div>
    """

    success = send_admin_email_alert(subject, html_content)
    if success:
        return "Reset request sent to Administrator.", {"color": "green"}
    else:
        return "Failed to send request. Contact admin at mis@orientgroup.org.in directly.", {"color": "red"}