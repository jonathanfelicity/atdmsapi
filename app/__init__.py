from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow

api = Flask(__name__)

api.app_context().push()
api.config['SECRET_KEY']= 'f0fc14b08995b4cbd607ed82031ed0839214f47d6750c73ebd4d0b0422093a8ef3f724'
api.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'
api.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
# Initialize the database and ORM
db = SQLAlchemy(api)
ma = Marshmallow(api)




from . import routes