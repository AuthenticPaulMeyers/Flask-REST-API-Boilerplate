from flask import Flask, jsonify, send_from_directory
import os
from .schema.models import db
from flask_jwt_extended import JWTManager
from dotenv import load_dotenv
from flask_migrate import Migrate
from .constants.http_status_codes import HTTP_429_TOO_MANY_REQUESTS, HTTP_404_NOT_FOUND, HTTP_500_INTERNAL_SERVER_ERROR, HTTP_503_SERVICE_UNAVAILABLE, HTTP_401_UNAUTHORIZED, HTTP_422_UNPROCESSABLE_ENTITY
from flask_cors import CORS
from flask_swagger_ui import get_swaggerui_blueprint 
from datetime import timedelta

load_dotenv(override=True)

# configure jwt
jwt = JWTManager()

# swagger ui setup for documentation
SWAGGER_URL = '/docs'
API_URL = '/static/swagger.yaml'

swaggerui_blueprint = get_swaggerui_blueprint(
    SWAGGER_URL,
    API_URL,
    config={'app_name': "AI Chat API with YAML"}
)

# config cors
cors = CORS()


# initiate app
def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)

    # initialise CORS
    cors.init_app(app, supports_credentials=True, resources={
    r"/*": {
        "origins": ["<Live API URL>", "<Localhost URL here>"],
        "methods": ["GET", "POST", "OPTIONS", "DELETE", "PUT"],
        "allow_headers": ["Content-Type", "Authorization"]
        }
    })

        # Configure token expiration time
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=24)    
    app.config['JWT_REFRESH_TOKEN_EXPIRES'] = timedelta(hours=48) 
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        "pool_size": 10,
        "max_overflow": 20,
        "pool_timeout": 30,
        "pool_recycle": 3600    # Recycle connections after 1 hour
    } 

    if test_config is None:
        app.config.from_mapping(
            SECRET_KEY=os.environ.get('SECRET_KEY'),
            SQLALCHEMY_DATABASE_URI=os.getenv('DATABASE_URL'),
            JWT_SECRET_KEY=os.getenv('JWT_SECRET_KEY'),
            SQLALCHEMY_TRACK_MODIFICATIONS=False
        )
    else:
        app.config.from_mapping(test_config)
    
    # initialise the database here
    db.app=app
    db.init_app(app)
    
    # initialise jwt here
    jwt.init_app(app)
    # initialise migrations
    Migrate(app, db)

    # initialise swagger ui blueprint
    app.register_blueprint(swaggerui_blueprint, url_prefix=SWAGGER_URL)

        # Serve the Swagger YAML file
    @app.route('/static/swagger.yaml')
    def send_swagger():
        return send_from_directory('static', 'swagger.yaml')

    # import more blueprints here
    from .auth.user_auth import auth

    # configure blueprints here
    app.register_blueprint(auth)
    
    # exception handling | catch runtime errors here
    @app.errorhandler(HTTP_404_NOT_FOUND)
    def handle_file_not_found(error):
        return jsonify({'error': f"{HTTP_404_NOT_FOUND} File not found!"}), HTTP_404_NOT_FOUND
    
    @app.errorhandler(HTTP_500_INTERNAL_SERVER_ERROR)
    def handle_internalServer_error(error):
        return jsonify({'error': "Something went wrong!"}), HTTP_500_INTERNAL_SERVER_ERROR
    
    @app.errorhandler(HTTP_503_SERVICE_UNAVAILABLE)
    def handle_connection_error(error):
        return jsonify({'error': "Service is currently unavailable. Our team is working on it!"}), HTTP_503_SERVICE_UNAVAILABLE
    
    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        return jsonify({
            "error": "token_expired",
            "msg": "Invalid token"
        }), HTTP_401_UNAUTHORIZED
    
    @jwt.unauthorized_loader
    def missing_token_callback(error):
        return jsonify({
            "error": "authorization_required",
            "msg": "Invalid token"
        }), HTTP_401_UNAUTHORIZED
    
    @jwt.invalid_token_loader
    def invalid_token_callback(error):
        return jsonify({
            "error": "invalid_token",
            "msg": "Invalid token"
        }), HTTP_422_UNPROCESSABLE_ENTITY
    
    # Kill inactive database sessions
    @app.teardown_appcontext
    def shutdown_session(exception=None):
        db.session.remove()

    return app