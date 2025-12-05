import sys
import os

# Add the project directory to the Python path
path = '/home/yourusername/UlendoInvoiceApp'
if path not in sys.path:
    sys.path.append(path)

# Import the Flask app
from main import app

# Create application object for WSGI
application = app

if __name__ == "__main__":
    app.run()
