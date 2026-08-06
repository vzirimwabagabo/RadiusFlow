from models import RadAcct


class SessionRepository:
    def __init__(self, db):
        self.db = db

    def active(self):
        return self.db.query(RadAcct).filter(RadAcct.acctstoptime.is_(None)).all()
