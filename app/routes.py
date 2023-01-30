import jwt
import os
from random import choice
from datetime import datetime, timedelta
from functools import wraps
from flask import jsonify, request, send_file, url_for, render_template, redirect
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
@api.route(f'/{BASE_URI}/create/user', methods=['POST'])
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

@api.route(f'/{BASE_URI}/authenticate/user', methods=['POST'])
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
@api.route(f'/{BASE_URI}/users', methods=['GET'])
# @jwt_required
def get_users():
    users = User.query.all()
    result = users_schema.dump(users)
    return jsonify(result), 200

    

# check in route 
@api.route(f'/{BASE_URI}/attendance/checkin', methods=['POST'])
def checkin():
    # Get the user_id from the request
    user_id = request.json['user_id']
    user = User.query.get(user_id)
    if user is None:
        return jsonify({"error": "User not found"}), 404

    # Get the last attendance of the user
    last_attendance = Attendance.query.filter_by(user_id=user_id).order_by(Attendance.check_in_time.desc()).first()
    
    # check if the last attendance is from today
    if last_attendance is not None and last_attendance.check_out_time is None and last_attendance.check_in_time.date() == datetime.utcnow().date():
        return jsonify({"error": "You have not checked out today or you have already checked in"}), 400
    
    # Create a new Attendance object
    attendance = Attendance(user_id=user_id, check_in_time=datetime.utcnow())
    db.session.add(attendance)
    db.session.commit()
    return jsonify(attendance_schema.dump(attendance)),





# check out route 
@api.route(f'/{BASE_URI}/attendance/checkout', methods=['POST'])
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


# ACTIVE USERS
@api.route(f'/{BASE_URI}/users/checkedin')
def users_checked_in():
    today = datetime.utcnow().date()
    checked_in_users = User.query.join(Attendance).filter(
        Attendance.check_in_time.between(datetime.combine(today, datetime.min.time()), datetime.utcnow()),
        Attendance.check_out_time == None
    ).all()

    return jsonify([user.to_dict() for user in checked_in_users])

# OFFLINE USERS
@api.route(f'/{BASE_URI}/users/checkedout')
def users_checked_out():
    today = datetime.utcnow().date()
    checked_out_users = User.query.join(Attendance).filter(
        Attendance.check_out_time.between(datetime.combine(today, datetime.min.time()), datetime.combine(today, datetime.max.time()))
    ).all()

    return jsonify([user.to_dict() for user in checked_out_users])



@api.route(f'/{BASE_URI}/attendance', methods=['GET'])
def get_attendance():
    attendance_list = []
    attendance = Attendance.query.all()
    for a in attendance:
        check_in_day = a.check_in_time.strftime("%d")
        check_in_month = a.check_in_time.strftime("%m")
        check_in_year = a.check_in_time.strftime("%Y")
        check_in_time = a.check_in_time.strftime("%H:%M:%S")
        check_out_day = a.check_out_time.strftime("%d") if a.check_out_time else ''
        check_out_month = a.check_out_time.strftime("%m") if a.check_out_time else ''
        check_out_year = a.check_out_time.strftime("%Y") if a.check_out_time else ''
        check_out_time = a.check_out_time.strftime("%H:%M:%S") if a.check_out_time else ''
        attendance_list.append({
            'user_id': a.user_id,
            'check_in_day': check_in_day,
            'check_in_month': check_in_month,
            'check_in_year': check_in_year,
            'check_in_time': check_in_time,
            'check_out_day': check_out_day,
            'check_out_month': check_out_month,
            'check_out_year': check_out_year,
            'check_out_time': check_out_time
        })
    return jsonify(attendance_list)






# ADMIN LOGIN
@api.route('/', methods=["POST", "GET"])
def _index():
    email = request.form.get("email")
    password = request.form.get("password")

    if email == 'johndoe@fake.com' and password == '123@':
        return redirect('/dashboard')
    return render_template('signin.html')


#ADMIN DASHBOARD
@api.route('/dashboard')
def dashboard():
     # all users 
    all_users = User.query.count()
    # all attendance
    all_attendance = Attendance.query.count()
    # check in users for today
    today = datetime.utcnow().date()
    attendances = Attendance.query.filter(db.func.date(Attendance.check_in_time) == today).all()
    user_ids = [attendance.user_id for attendance in attendances]
    checkin_users = len(set(user_ids))
    return render_template('dashboard.html', all_users=all_users, all_attendance=all_attendance, checkin_users=checkin_users)
   



#ADMIN USERATTENDANCE
@api.route('/users')
def users():
    return render_template('attendance.html')


#ADMIN USERATTENDANCE
@api.route('/attendance')
def attendance():
    attendances = Attendance.query.join(User).add_columns(
        User.name.label('user_name'),
        Attendance.check_in_time,
        Attendance.check_out_time
    ).all()

    attendance_list = []
    for attendance in attendances:
        check_in_day = attendance.check_in_time.strftime('%d')
        check_in_month = attendance.check_in_time.strftime('%m')
        check_in_year = attendance.check_in_time.strftime('%Y')
        check_in_time = attendance.check_in_time.strftime('%H:%M:%S')

        check_out_day = attendance.check_out_time.strftime('%d') if attendance.check_out_time else "not found"
        check_out_month = attendance.check_out_time.strftime('%m') if attendance.check_out_time else "not found"
        check_out_year = attendance.check_out_time.strftime('%Y') if attendance.check_out_time else "not found"
        check_out_time = attendance.check_out_time.strftime('%H:%M:%S') if attendance.check_out_time else "not found"

        attendance_list.append({
            'user_name': attendance.user_name,
            'check_in_day': check_in_day,
            'check_in_month': check_in_month,
            'check_in_year': check_in_year,
            'check_in_time': check_in_time,
            'check_out_day': check_out_day,
            'check_out_month': check_out_month,
            'check_out_year': check_out_year,
            'check_out_time': check_out_time
        })

    return render_template('attendance.html', attendances=attendance_list)