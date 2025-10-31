from flask import Blueprint, render_template

# Maak een blueprint (groep van routes)
main = Blueprint('main', __name__)

@main.route('/')
def index():
    return render_template('index.html', message="Den Flask werkt (via blueprint)!")
