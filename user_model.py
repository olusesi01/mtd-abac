from flask_login import UserMixin
from db import db  # Import db from the new module

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    DistrictName = db.Column(db.String(100), nullable=False)
    SchoolName = db.Column(db.String(100), nullable=False)
    ClassID = db.Column(db.String(100), nullable=False)

    def __init__(self, username, password, DistrictName, SchoolName, ClassID):
        self.username = username
        self.password = password
        self.DistrictName = DistrictName
        self.SchoolName = SchoolName
        self.ClassID = ClassID
    

    @property
    def is_active(self):
        return True

    @property
    def is_authenticated(self):
        return True

    @property
    def is_anonymous(self):
        return False

    def get_id(self):
        return str(self.id)
