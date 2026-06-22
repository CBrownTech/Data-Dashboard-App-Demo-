# Entry point for running the Flask development server.
# Run this file directly: python run.py
# The server starts at http://127.0.0.1:5000 with debug mode on,
# which means it auto-reloads whenever you save a file.
from __init__ import create_app

app = create_app()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
