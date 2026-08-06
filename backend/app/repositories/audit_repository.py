class AuditRepository:
    def __init__(self, db):
        self.db = db

    def record(self, *_args, **_kwargs):
        return None
