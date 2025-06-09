from app import create_app, db
from flask_migrate import Migrate

app = create_app()
migrate = Migrate(app, db)

with app.app_context():
    # Run the app and create the database tables
    db.create_all()
    app.run(debug=True)
