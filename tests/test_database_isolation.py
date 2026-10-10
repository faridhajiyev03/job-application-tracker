import pytest

pytestmark = pytest.mark.db


def test_default_application_engine_cannot_connect(app_modules):
    with pytest.raises(RuntimeError, match="default application engine is forbidden"):
        app_modules[1].engine.connect()


def test_commits_and_integrity_rollback_do_not_escape_database(database_factory):
    from sqlalchemy import func, select
    from sqlalchemy.exc import IntegrityError
    from sqlalchemy.orm import Session
    from models.user import User

    with database_factory() as first:
        with Session(first) as session:
            session.add(User(email="isolation@example.com", hashed_password="test-hash"))
            session.commit()
            session.add(User(email="isolation@example.com", hashed_password="duplicate"))
            with pytest.raises(IntegrityError):
                session.commit()
            session.rollback()
            assert session.scalar(select(func.count()).select_from(User)) == 1
        with database_factory() as second:
            assert first.url.database != second.url.database
            with Session(second) as session:
                assert session.scalar(select(func.count()).select_from(User)) == 0
                session.add(User(email="second@example.com", hashed_password="test-hash"))
                session.commit()
        with Session(first) as session:
            assert session.scalars(select(User.email)).all() == ["isolation@example.com"]
    with database_factory() as next_test:
        with Session(next_test) as session:
            assert session.scalar(select(func.count()).select_from(User)) == 0
