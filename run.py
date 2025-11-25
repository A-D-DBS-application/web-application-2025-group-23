# Zodra alle pakketten geïnstalleerd zijn (requirements.txt), kun je de Flask-app starten met:
#   python run.py
#
# Je krijgt dan een melding zoals:
#   * Running on http://127.0.0.1:5000/
#
# Open dat adres in je browser om de webapp te bekijken.
from app import create_app

app = create_app()

if __name__ == '__main__':
    app.run(debug=True)
