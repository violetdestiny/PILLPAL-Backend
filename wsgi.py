import sys
import logging

logging.basicConfig(stream=sys.stderr)
sys.stdout = sys.stderr

sys.path.insert(0, "/var/www/pillpal/PILLPAL-Backend")
sys.path.insert(0, "/var/www/pillpal/PILLPAL-Backend/src")

from src import create_app
application = create_app()
