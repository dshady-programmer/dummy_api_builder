from models import db
from api.v1.app import app, migrate
from extensions import cache

db.init_app(app)
migrate.init_app(app, db)
cache.init_app(app)
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5900, debug=True)
