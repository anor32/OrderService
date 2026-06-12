from app.core.interfaces import OrderRepository


class UnitOfWork:
    def __init__(self, session, db: OrderRepository):
        self.session = session
        self.db = db

    def __enter__(self):
        return self.db

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            self.session.commit()
        else:
            self.session.rollback()
        self.session.close()
