from db import db  # Import the initialized db
import json

class Policy(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.String(255))
    effect = db.Column(db.String(10))
    rules = db.Column(db.Text)  # Store JSON rules as text
    targets = db.Column(db.Text)  # Store JSON targets as text
    priority = db.Column(db.Integer)

    def to_dict(self):
        return {
            'id': self.id,
            'description': self.description,
            'effect': self.effect,
            'rules': json.loads(self.rules),  # Convert back to dictionary
            'targets': json.loads(self.targets),  # Convert back to dictionary
            'priority': self.priority
        }



