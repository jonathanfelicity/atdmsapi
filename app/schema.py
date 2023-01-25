from marshmallow_sqlalchemy import SQLAlchemyAutoSchema
from .models import User, Attendance



class UserSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = User
        load_instance = True
        include_relationships = True
        exclude = ['password']

class AttendanceSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = Attendance
        load_instance = True
        include_relationships = True



# Initialize the User schema
user_schema = UserSchema()
users_schema = UserSchema(many=True)


# Initialize the Attendance schema
attendance_schema = AttendanceSchema()
attendances_schema = AttendanceSchema(many=True)


