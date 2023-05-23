import os
import app

flask_app = app.app

if __name__ == "__main__":
    # App is run locally
    flask_app.run(debug=True, port=os.getenv("PORT", default=5000))

# Production command:
# gunicorn -w 4 --bind 0.0.0.0:${PORT} main:flask_app