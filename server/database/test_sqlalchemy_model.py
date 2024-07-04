import uuid
from datetime import datetime
import pytest
import sqlalchemy
from pytest_postgresql import factories
from pytest_postgresql.janitor import DatabaseJanitor
from sqlalchemy import create_engine, select, text
from sqlalchemy.orm import sessionmaker

from database.crud import (create_user, get_user_by_token, add_model,
                           get_model_by_name, get_model_by_id, add_plugin_version, get_plugin_version_by_id,
                           get_plugin_versions_by_description_containing, get_plugin_versions_by_ide_type,
                           get_plugin_versions_by_name_containing, get_all_plugin_versions, add_telemetry,
                           get_telemetry_by_id, get_telemetries_with_typing_speed_in_range,
                           get_telemetries_with_relative_document_position_in_range,
                           get_telemetries_with_time_since_last_completion_in_range,
                           get_telemetries_with_document_char_length_in_range)

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


def test_adding_and_reading_users(db_transaction):
    # Arrange
    user_token = str(uuid.uuid4())
    user_joined_at = datetime.now(tz=datetime.now().astimezone().tzinfo)
    user = UserCreate(token=user_token, joined_at=str(user_joined_at))

    # Act
    returned_database_user = create_user(db_transaction, user)

    user_retrieved_by_token = get_user_by_token(db_transaction, user_token)

    # Assert
    assert str(returned_database_user.token) == user_token
    assert str(user_retrieved_by_token.token) == user_token
    assert user_retrieved_by_token.joined_at == user_joined_at
    assert user_retrieved_by_token.joined_at == user_joined_at


def test_adding_and_reading_models(db_transaction):
    # Arrange
    model_name_1 = "test_model_1"
    model_name_2 = "test_model_2"
    model1 = ModelNameCreate(model_name=model_name_1)
    model2 = ModelNameCreate(model_name=model_name_2)

    # Act
    model_returned_by_database_1 = add_model(db_transaction, model1)
    model_returned_by_database_2 = add_model(db_transaction, model2)

    model_returned_by_name = get_model_by_name(db_transaction, "test_model_1")
    model_returned_by_id = get_model_by_id(db_transaction, model_returned_by_database_2.model_id)

    # Assert
    assert model_returned_by_database_1.model_name == model_name_1
    assert model_returned_by_database_2.model_name == model_name_2
    assert model_returned_by_name.model_name == model_name_1
    assert model_returned_by_id.model_name == model_name_2


def test_adding_and_reading_plugin_versions(db_transaction):
    # Arrange
    version_name_1 = "test_version_1_goofy"
    version_name_2 = "test_version_2"

    version1 = PluginVersionCreate(version_name=version_name_1, ide_type="JetBrains", description="some description 1")
    version2 = PluginVersionCreate(version_name=version_name_2, ide_type="VSCode", description="some funny "
                                                                                               "description 2")

    # Act
    version_returned_by_database_1 = add_plugin_version(db_transaction, version1)
    version_returned_by_database_2 = add_plugin_version(db_transaction, version2)

    version_returned_by_id = get_plugin_version_by_id(db_transaction, version_returned_by_database_1.version_id)
    versions_returned_by_description = get_plugin_versions_by_description_containing(db_transaction, "funny")
    versions_returned_by_ide_type = get_plugin_versions_by_ide_type(db_transaction, "JetBrains")
    version_returned_by_name_containing = get_plugin_versions_by_name_containing(db_transaction, "goofy")

    def evaluate_equivalence_of_versions(v1, v2):
        return v1.version_name == v2.version_name and v1.ide_type == v2.ide_type and v1.description == v2.description

    # Assert
    assert evaluate_equivalence_of_versions(version_returned_by_database_1, version1)
    assert evaluate_equivalence_of_versions(version_returned_by_database_2, version2)
    assert evaluate_equivalence_of_versions(version_returned_by_id, version1)
    assert any([evaluate_equivalence_of_versions(v, version2) for v in versions_returned_by_description])
    assert all([v.ide_type == "JetBrains" for v in versions_returned_by_ide_type])
    assert any([evaluate_equivalence_of_versions(v, version1) for v in version_returned_by_name_containing])


def test_adding_and_reading_telemetry_data(db_transaction):
    # Arrange
    telemetry_1_id = str(uuid.uuid4())
    telemetry_2_id = str(uuid.uuid4())

    time_since_last_completion_1 = 100
    time_since_last_completion_2 = 200

    typing_speed_1 = 50
    typing_speed_2 = 100

    document_char_length_1 = 500
    document_char_length_2 = 1000

    relative_document_position_1 = 0.25
    relative_document_position_2 = 0.5

    telemetry1 = TelemetryCreate(telemetry_id=telemetry_1_id, time_since_last_completion=time_since_last_completion_1,
                                 typing_speed=typing_speed_1, document_char_length=document_char_length_1,
                                 relative_document_position=relative_document_position_1)
    telemetry2 = TelemetryCreate(telemetry_id=telemetry_2_id, time_since_last_completion=time_since_last_completion_2,
                                 typing_speed=typing_speed_2, document_char_length=document_char_length_2,
                                 relative_document_position=relative_document_position_2)

    # Act
    telemetry_returned_by_database_1 = add_telemetry(db_transaction, telemetry1)
    telemetry_returned_by_database_2 = add_telemetry(db_transaction, telemetry2)

    telemetry_returned_by_id = get_telemetry_by_id(db_transaction, telemetry_1_id)
    telemetries_with_typing_speed_in_range_of_one = get_telemetries_with_typing_speed_in_range(db_transaction, 0, 99)
    telemetries_with_typing_speed_in_range_of_both = get_telemetries_with_typing_speed_in_range(db_transaction, 49, 101)
    telemetries_with_relative_document_position_in_range_of_one = (
        get_telemetries_with_relative_document_position_in_range(db_transaction, 0, 0.49))
    telemetries_with_relative_document_position_in_range_of_both = (
        get_telemetries_with_relative_document_position_in_range(db_transaction, 0.24, 0.51))
    telemetries_with_time_since_last_completion_in_range_of_one = (
        get_telemetries_with_time_since_last_completion_in_range(db_transaction, 0, 101))
    telemetries_with_time_since_last_completion_in_range_of_both = (
        get_telemetries_with_time_since_last_completion_in_range(db_transaction, 99, 201))
    telemetries_with_document_char_length_in_range_of_one = (
        get_telemetries_with_document_char_length_in_range(db_transaction, 0, 501))
    telemetries_with_document_char_length_in_range_of_both = (
        get_telemetries_with_document_char_length_in_range(db_transaction, 499, 1001))

    containing_one = [telemetries_with_typing_speed_in_range_of_one,
                      telemetries_with_relative_document_position_in_range_of_one,
                      telemetries_with_document_char_length_in_range_of_one,
                      telemetries_with_time_since_last_completion_in_range_of_one]
    containing_both = [telemetries_with_typing_speed_in_range_of_both,
                       telemetries_with_relative_document_position_in_range_of_both,
                       telemetries_with_document_char_length_in_range_of_both,
                       telemetries_with_time_since_last_completion_in_range_of_both]

    def evaluate_equivalence_of_telemetries(t1, t2):
        return t1.time_since_last_completion == t2.time_since_last_completion \
            and t1.typing_speed == t2.typing_speed and t1.document_char_length == t2.document_char_length and \
            t1.relative_document_position == t2.relative_document_position

    # Assert
    assert evaluate_equivalence_of_telemetries(telemetry_returned_by_database_1, telemetry1)
    assert evaluate_equivalence_of_telemetries(telemetry_returned_by_database_2, telemetry2)
    assert evaluate_equivalence_of_telemetries(telemetry_returned_by_id, telemetry1)

    for case in zip(containing_one, containing_both):
        for t in case[0]:
            assert (evaluate_equivalence_of_telemetries(t, telemetry1)
                    or not evaluate_equivalence_of_telemetries(t, telemetry2))
        for t in case[1]:
            assert (evaluate_equivalence_of_telemetries(t, telemetry1)
                    or evaluate_equivalence_of_telemetries(t, telemetry2))
