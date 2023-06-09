import os

from dotenv import load_dotenv

load_dotenv()

import app

flask_app = app.app

if __name__ == "__main__":
    # App is run without gunicorn
    flask_app.run(debug=True, port=os.getenv("PORT", default=5000))

# Production command:
# gunicorn -w 4 --bind 0.0.0.0:${PORT} main:flask_app

# Development command:
# gunicorn -w 2 --bind 0.0.0.0:5000 main:flask_app
