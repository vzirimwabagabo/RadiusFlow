from models import RadGroupCheck, RadGroupReply, RadUserGroup


class GroupRepository:
    def __init__(self, db):
        self.db = db

    def exists(self, groupname: str) -> bool:
        return self.db.query(RadGroupReply).filter(RadGroupReply.groupname == groupname).first() is not None

    def delete_group_records(self, groupname: str) -> None:
        self.db.query(RadGroupReply).filter(RadGroupReply.groupname == groupname).delete()
        self.db.query(RadGroupCheck).filter(RadGroupCheck.groupname == groupname).delete()
        self.db.query(RadUserGroup).filter(RadUserGroup.groupname == groupname).delete()
