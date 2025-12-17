# gunicorn.conf.py

import os

bind = f"0.0.0.0:{os.getenv('PORT', '8080')}"
workers = 1
threads = 4
timeout = 120

worker_class = "gthread"

loglevel = "info"
accesslog = "-"
errorlog = "-"

preload_app = True
