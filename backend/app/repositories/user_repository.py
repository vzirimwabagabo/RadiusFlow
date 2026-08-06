from models import RadCheck, RadReply, RadUserGroup


class UserRepository:
    def __init__(self, db):
        self.db = db

    def exists(self, username: str) -> bool:
        return self.db.query(RadCheck).filter(RadCheck.username == username).first() is not None

    def list_usernames(self):
        return [row[0] for row in self.db.query(RadCheck.username).distinct().all()]

    def delete_user_records(self, username: str) -> None:
        self.db.query(RadCheck).filter(RadCheck.username == username).delete()
        self.db.query(RadReply).filter(RadReply.username == username).delete()
        self.db.query(RadUserGroup).filter(RadUserGroup.username == username).delete()
