
# Zodra alle pakketten geïnstalleerd zijn (requirements.txt), kun je de Flask-app starten met:
#   python run.py
#
# Je krijgt dan een melding zoals:
#   * Running on http://127.0.0.1:5000/
#
# Open dat adres in je browser om de webapp te bekijken.
from flask import Flask
from app import create_app, db

app = create_app()

# Optioneel: bij eerste run tabellen aanmaken (voor demo/doeleinden)
# Je kan dit weghalen als je migrations gaat gebruiken.
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True)

