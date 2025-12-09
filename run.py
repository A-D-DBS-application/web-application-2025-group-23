# Zodra alle pakketten geïnstalleerd zijn (requirements.txt), kun je de Flask-app starten met:
#   python run.py
#
# Je krijgt dan een melding zoals:
#   * Running on http://127.0.0.1:5000/
#
# Open dat adres in je browser om de webapp te bekijken.
from app import create_app
import os

app = create_app()

if __name__ == "__main__":
    # Use threaded mode for better performance
    # debug=True: Herladen bij code wijzigingen (traag)
    # debug=False: Sneller, maar geen auto-reload
    # Kies een van beide met de omgevingsvariabele DEBUG
    
    debug_mode = os.getenv('FLASK_DEBUG', 'True').lower() == 'true'
    
    # Use threaded=True voor beter multi-tasking
    app.run(
        host="0.0.0.0",
        port=5001,
        debug=debug_mode,
        threaded=True,           # Enables multiple threads for concurrent requests
        use_reloader=debug_mode  # Only reload on code changes if debug is on
    )

