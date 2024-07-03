import uuid
from datetime import datetime
import pytest
import sqlalchemy
from pytest_postgresql import factories
from pytest_postgresql.janitor import DatabaseJanitor
from sqlalchemy import create_engine, select, text
from sqlalchemy.orm import sessionmaker

from database.crud import create_user, get_user_by_token

from testcontainers.postgres import PostgresContainer

from database.db_schemas import *
from database.db_models import *

from database.database import config


def create_fresh_database(engine):
    # drop all tables
    Base.metadata.drop_all(engine)
    # create all tables from init.sql
    with engine.connect() as connection:
        connection.execute(text(open('./init.sql').read()))
    engine.dispose()


@pytest.fixture(scope='session')
def db_session():
    engine = create_engine(config.test_database_url)
    create_fresh_database(engine)
    yield sessionmaker(autocommit=False, autoflush=False, bind=engine)
    create_fresh_database(engine)
    engine.dispose()


@pytest.fixture(scope='function')
def db_transaction(db_session):
    session = db_session()
    connection = session.connection()
    transaction = connection.begin_nested()

    session.begin_nested()

    yield session

    transaction.rollback()
    connection.close()
    session.close()


def test_db_connection(db_transaction):
    # Arrange
    user_token = str(uuid.uuid4())
    user_joined_at = datetime.now(tz=datetime.now().astimezone().tzinfo)
    user = UserCreate(token=user_token, joined_at=str(user_joined_at))

    print(user_joined_at)

    # Act
    returned_database_user = create_user(db_transaction, user)

    user_retrieved_by_token = get_user_by_token(db_transaction, user_token)

    # Assert
    assert str(returned_database_user.token) == user_token
    assert str(user_retrieved_by_token.token) == user_token
    assert user_retrieved_by_token.joined_at == user_joined_at
    assert user_retrieved_by_token.joined_at == user_joined_at


