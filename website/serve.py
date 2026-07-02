import http.server
import socketserver
import os

PORT = 8000
DIRECTORY = os.path.dirname(os.path.abspath(__file__))

class CustomHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)

    def do_GET(self):
        # Translate /website-assets/ pathing to local workspace pathing
        if self.path.startswith('/website-assets/'):
            # Strip the prefix /website-assets
            self.path = self.path.replace('/website-assets', '', 1)
        
        # Mock behavior for /login redirect to simulate dashboard login click
        if self.path == '/login':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(b"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>ForgeBI Login Simulator</title>
                <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;600;700&display=swap" rel="stylesheet">
                <style>
                    body { 
                        font-family: 'Plus Jakarta Sans', sans-serif; 
                        background: #FAF8F5; 
                        text-align: center; 
                        padding: 100px 20px; 
                        color: #1A1612; 
                        margin: 0;
                    }
                    .card { 
                        max-width: 440px; 
                        margin: 0 auto; 
                        padding: 40px; 
                        background: white; 
                        border: 1px solid rgba(200, 160, 77, 0.2); 
                        border-radius: 12px; 
                        box-shadow: 0 20px 40px -20px rgba(26, 22, 18, 0.08); 
                    }
                    h2 { 
                        color: #1A1612; 
                        margin-bottom: 15px; 
                        font-weight: 700;
                    }
                    p {
                        color: #6E655B;
                        font-size: 0.95rem;
                        line-height: 1.6;
                        margin-bottom: 25px;
                    }
                    .btn-gold {
                        display: inline-block;
                        background-color: #C8A04D;
                        color: #110F0C;
                        padding: 0.8rem 2rem;
                        font-weight: 600;
                        border-radius: 6px;
                        text-decoration: none;
                        box-shadow: 0 4px 14px rgba(200, 160, 77, 0.25);
                        transition: all 0.3s ease;
                    }
                    .btn-gold:hover {
                        background-color: #B58E3B;
                        transform: translateY(-2px);
                        box-shadow: 0 6px 20px rgba(200, 160, 77, 0.35);
                    }
                    .badge-gold {
                        display: inline-block;
                        font-size: 0.7rem;
                        font-weight: 700;
                        background-color: rgba(200, 160, 77, 0.1);
                        color: #C8A04D;
                        padding: 4px 12px;
                        border-radius: 12px;
                        text-transform: uppercase;
                        margin-bottom: 20px;
                    }
                </style>
            </head>
            <body>
                <div class="card">
                    <span class="badge-gold">Portal Simulation</span>
                    <h2>ForgeBI Demo Gateway</h2>
                    <p>
                        This simulates routing to the <strong>/login</strong> path. 
                        In the production setup, this endpoint displays the secure Orient BI / ForgeBI Dash Dashboard login screen.
                    </p>
                    <a href="/" class="btn-gold">Return to Homepage</a>
                </div>
            </body>
            </html>
            """)
            return
            
        return super().do_GET()

if __name__ == '__main__':
    # Change directory to script folder to be completely certain relative paths resolve
    os.chdir(DIRECTORY)
    
    # Allow address re-use to prevent 'Port already in use' errors on quick restarts
    socketserver.TCPServer.allow_reuse_address = True
    
    with socketserver.TCPServer(("", PORT), CustomHandler) as httpd:
        print(f"==================================================")
        print(f" ForgeBI Homepage isolated preview server active")
        print(f" URL: http://localhost:{PORT}")
        print(f" Press Ctrl+C to terminate.")
        print(f"==================================================")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nShutting down server.")
