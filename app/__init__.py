from flask import Flask

app = Flask(__name__)

# Add built-in functions to Jinja2 environment
app.jinja_env.globals.update(max=max, min=min)

from app import routes