from py_abac import Policy as AbacPolicy
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine

class DatabaseStorage:
    def __init__(self):
        # Setup your database engine and session
        self.engine = create_engine('sqlite:///your_database.db')  # Example database URL
        self.Session = sessionmaker(bind=self.engine)
        self.session = self.Session()

    def add(self, policy):
        self.session.add(policy)
        self.session.commit()

    def get(self, policy_id):
        return self.session.query(AbacPolicy).filter_by(id=policy_id).first()

    def update(self, policy):
        self.session.merge(policy)
        self.session.commit()

    def get_all(self, limit=10, offset=0):
        return self.session.query(AbacPolicy).limit(limit).offset(offset).all()
