import jwt
from datetime import datetime, timedelta
from functools import wraps
from flask import jsonify, request
from . import api, db
from .models import User, Attendance

from .schema import user_schema, users_schema, attendance_schema, attendances_schema
from .constants import BASE_URI



def jwt_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = None
        if 'Authorization' in request.headers:
            token = request.headers['Authorization']

        if not token:
            return jsonify({"error": "Token is missing"}), 401

        try:
            data = jwt.decode(token, SECRET_KEY)
            user_id = data['user_id']
        except:
            return jsonify({"error": "Token is invalid"}), 401

        return f(*args, **kwargs)
    return decorated_function



# create new user
@api.route('/create/user', methods=['POST'])
def create_user():
    data = request.get_json()
    name = data.get('name')
    email = data.get('email')
    password = data.get('password')
    is_admin = data.get('is_admin', False)

    # Validate input
    if not name or not email or not password:
        return jsonify({'error': 'Name, email and password are required fields.'}), 400

    # Check if email already exists
    if User.query.filter_by(email=email).first():
        return jsonify({'error': 'Email already exists.'}), 400

    # Create new user
    new_user = User(name=name, email=email, is_admin=is_admin)
    new_user.set_password(password)
    db.session.add(new_user)
    db.session.commit()

    return jsonify({'message': 'User created successfully.'}), 201



# authenticate user



SECRET_KEY = 'mysecretkey'

@api.route('/authenticate/user', methods=['POST'])
def authenticate():
    try:
        email = request.json['email']
        password = request.json['password']
    except KeyError:
        return jsonify({"error": "Missing email or password"}), 400
    user = User.query.filter_by(email=email).first()
    if user is None or not user.check_password(password):
        return jsonify({"error": "Invalid email or password"}), 401
    # create a JSON Web Token
    token = jwt.encode({'user_id': user.id, 'exp':datetime.utcnow() + timedelta(minutes=30)}, SECRET_KEY)
    return jsonify({'token': token}), 200



# get all users
@api.route('/users', methods=['GET'])
# @jwt_required
def get_users():
    users = User.query.all()
    result = users_schema.dump(users)
    return jsonify(result), 200

    

# check in route 
@api.route('/attendance/checkin', methods=['POST'])
@jwt_required
def checkin():
    # Get the user_id from the request
    user_id = request.json['user_id']
    user = User.query.get(user_id)
    if user is None:
        return jsonify({"error": "User not found"}), 404
    
    # Get the last attendance of the user
    last_attendance = Attendance.query.filter_by(user_id=user_id).order_by(Attendance.check_in_time.desc()).first()
    
    # check if the last attendance is from today
    if last_attendance and last_attendance.check_in_time.date() == datetime.utcnow().date():
        return jsonify({"error": "You have already checked in today"}), 400
    
    # Create a new Attendance object
    attendance = Attendance(user_id=user_id, check_in_time=datetime.utcnow())




# check out route 
@api.route('/attendance/checkout', methods=['POST'])
@jwt_required
def checkout():
    # Get the user_id from the request
    user_id = request.json['user_id']
    user = User.query.get(user_id)
    if user is None:
        return jsonify({"error": "User not found"}), 404

    # Get the last attendance of the user
    last_attendance = Attendance.query.filter_by(user_id=user_id).order_by(Attendance.check_in_time.desc()).first()
    
    # check if the last attendance is from today
    if last_attendance is None or last_attendance.check_out_time is not None or last_attendance.check_in_time.date() != datetime.utcnow().date():
        return jsonify({"error": "You have not checked in today or you have already checked out"}), 400
    
    last_attendance.check_out_time = datetime.utcnow()
    db.session.commit()
    return jsonify(attendance_schema.dump(last_attendance)), 201
