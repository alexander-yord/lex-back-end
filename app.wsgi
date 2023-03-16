import sys 

sys.path.insert(0, "/var/www/back-end/")

from api.main import app as application
application.secret_key = "Sofia2022"
