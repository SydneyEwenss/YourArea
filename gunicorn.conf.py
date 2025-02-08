# taken from https://stackoverflow.com/a/75480960

# https://www.uvicorn.org/deployment/#gunicorn
# using custom one to disable Lifespan Protocol
# needs to be passed by string https://github.com/benoitc/gunicorn/issues/1539
worker_class = "uvicorn_worker.UvicornWorker"
