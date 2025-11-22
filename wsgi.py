import sys
import logging

logging.basicConfig(stream=sys.stderr)
sys.stdout = sys.stderr  

sys.path.insert(0, "/var/www/pillpal/PILLPAL-Backend")

try:
    from src import create_app
    application = create_app()
except Exception as e:
    print("WSGI ERROR:", e)
    raise
