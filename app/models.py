from app import db
from datetime import datetime, timezone
from app.utils import hash_password


class Admin(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime)

    def __init__(self, username, email, password_hash, created_at=None):
        self.username = username
        self.email = email
        self.password_hash = password_hash
        # Evaluates the current time exactly when the object is instantiated
        self.created_at = created_at or datetime.now(timezone.utc)

    @staticmethod
    def get_by_email(email: str):
        return Admin.query.filter_by(email=email).first()

    @staticmethod
    def add(username: str, email: str, password: str):
        try:
            hashed_pw = hash_password(password)
            new_admin = Admin(username=username, email=email, password_hash=hashed_pw)
            db.session.add(new_admin)
            db.session.commit()
            return new_admin
        except Exception as ex:
            db.session.rollback()
            print(f"Could not add admin with email {email}, ex: {ex}")
            return False

    @staticmethod
    def get_by_id(admin_id: int):
        return Admin.query.filter_by(id=admin_id).first()


class Election(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    status = db.Column(db.String(20), default='Upcoming')
    created_at = db.Column(db.DateTime)

    candidates = db.relationship('Candidate', backref='election', lazy=True)
    votes = db.relationship('Vote', backref='election', lazy=True)

    def __init__(self, title, status='Upcoming', created_at=None):
        self.title = title
        self.status = status
        self.created_at = created_at or datetime.now(timezone.utc)


class Candidate(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    party = db.Column(db.String(50), nullable=False)
    election_id = db.Column(db.Integer, db.ForeignKey('election.id'), nullable=False)

    votes = db.relationship('Vote', backref='candidate', lazy=True)

    def __init__(self, name, party, election_id):
        self.name = name
        self.party = party
        self.election_id = election_id


class Voter(db.Model):
    __tablename__ = 'voter'
    id = db.Column(db.Integer, primary_key=True)
    prn = db.Column(db.String(20), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    image_path = db.Column(db.String(255), nullable=False)

    def __init__(self, prn, name, email, password_hash, image_path):
        self.prn = prn
        self.name = name
        self.email = email
        self.password_hash = password_hash
        self.image_path = image_path

    @staticmethod
    def get_by_prn(prn):
        return Voter.query.filter_by(prn=prn).first()

    @staticmethod
    def add(prn, name, email, password_hash, image_path):
        voter = Voter(prn, name, email, password_hash, image_path)
        db.session.add(voter)
        db.session.commit()
        return voter

    @staticmethod
    def get_all_voters():
        voters: list[Voter] = Voter.query.all()
        voter_data = []
        for voter in voters:
            voter_data.append({"id": voter.id, "prn": voter.prn, "name": voter.name, "email": voter.email})
        return voter_data


class Vote(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    voter_id = db.Column(db.Integer, db.ForeignKey('voter.id'), unique=True, nullable=False)
    candidate_id = db.Column(db.Integer, db.ForeignKey('candidate.id'), nullable=False)
    election_id = db.Column(db.Integer, db.ForeignKey('election.id'), nullable=False)
    timestamp = db.Column(db.DateTime)

    def __init__(self, voter_id, candidate_id, election_id, timestamp=None):
        self.voter_id = voter_id
        self.candidate_id = candidate_id
        self.election_id = election_id
        self.timestamp = timestamp or datetime.now(timezone.utc)
