from models import NAS


class NASRepository:
    def __init__(self, db):
        self.db = db

    def get_by_name(self, nasname: str):
        return self.db.query(NAS).filter(NAS.nasname == nasname).first()

    def list_all(self):
        return self.db.query(NAS).order_by(NAS.nasname).all()
