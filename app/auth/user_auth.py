from flask import request, Blueprint, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from ..schema.models import db, Users
from flask_jwt_extended import jwt_required, create_refresh_token, get_jwt_identity, create_access_token
from ..utils.image_uploads import upload_image
from ..constants.http_status_codes import HTTP_400_BAD_REQUEST, HTTP_409_CONFLICT, HTTP_200_OK, HTTP_201_CREATED
import validators

# create a blueprint for this route
auth = Blueprint('auth', __name__, static_url_path='static/', url_prefix='/api/auth')

# register route
@auth.route('/register', methods=['POST', 'GET'])
def register():
    # get user details
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        bio = request.form.get('bio')
        password = request.form.get('password')
        # File upload
        file = request.files.get('file')

        # validating the name 
        if len(username) < 3:
            return jsonify({'error': "Name is too short"}), HTTP_400_BAD_REQUEST
        
        if not username.isalnum() or " " in username:
            return jsonify({"error": "Name should not contain numbers or symbols"}), HTTP_400_BAD_REQUEST
        
        if password == '' or not password or not username or not email or not bio or bio == '':
            return jsonify({'error': 'Required fields should not be empty.'})
        
        # validate the user email
        if not validators.email(email):
            return jsonify({"error": "Email is not valid"})
        
        # check if the user email is not already registered in the database
        if Users.query.filter_by(email=email).first():
            return jsonify({'error': "Email already exist"}), HTTP_409_CONFLICT
        
        # check if the username is not already registered in the database
        if Users.query.filter_by(username=username).first():
            return jsonify({"error": 'Username already exist'}), HTTP_409_CONFLICT

        # generate hashed password
        password_hashed = generate_password_hash(password)

        if not file:
            return jsonify({'error': 'No file provided.'}), HTTP_400_BAD_REQUEST
        
        file_url = upload_image(file)
        if not file_url:
            return jsonify({'error': 'Invalid file type.'}), HTTP_400_BAD_REQUEST

        user = Users(username=username, email=email, password_hash=password_hashed, bio=bio, profile_pic_url=file_url)
        db.session.add(user)
        db.session.commit()

        return jsonify({
            'message': 'User registered successfully!',
            'user':{
                'username': username,
                'email': email,
                'bio': bio,
                'profile_pic_url': file_url
            }
        }), HTTP_201_CREATED

# login route
@auth.route('/login', methods=['POST', 'GET'])
def login():
    if request.method == 'POST':
        email = request.json.get("email")
        password = request.json.get("password")

        # get the user by email
        user=Users.query.filter_by(email=email).first()

        if user:
            check_hashed_password=check_password_hash(user.password_hash, password)

            if check_hashed_password:
                # create jwt access tokens and refresh token to authenticate and authorise users
                refresh=create_refresh_token(identity=str(user.id))
                access=create_access_token(identity=str(user.id))

                return jsonify({
                    'user':{
                        'refresh': refresh,
                        'access': access,
                        'profile_picture': user.profile_pic_url,
                        'name': user.username,
                        'email': user.email,
                        'id': user.id
                    }
                }), HTTP_200_OK
        return jsonify({'error': 'wrong username or password'}), HTTP_400_BAD_REQUEST

# get current user profile route
@auth.route('/me', methods=['POST', 'GET'])
@jwt_required()
def current_user_profile():
    user_id = get_jwt_identity()

    user=Users.query.filter_by(id=user_id).first()

    if user:
        return jsonify({
        'user':{
            'name': user.username,
            'email': user.email,
            'profile': user.profile_pic_url,
            'bio': user.bio
        }
        }), HTTP_200_OK
    else:
        return jsonify({'error': HTTP_400_BAD_REQUEST}), HTTP_400_BAD_REQUEST

# create user refresh token
@auth.get("/token/refresh")
@jwt_required(refresh=True)
def refresh_token():
    user_id=get_jwt_identity()
    access=create_access_token(identity=str(user_id))

    return jsonify({
        'access': access
    }), HTTP_200_OK