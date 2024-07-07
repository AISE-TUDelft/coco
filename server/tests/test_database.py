# NOTE: commented out because the imports aren't in the requirements file
# adding pytest-postgresql uses a different version of psychopg (1 or 2?)

import uuid
from datetime import datetime, timedelta
import pytest
import sqlalchemy
from pytest_postgresql import factories
from pytest_postgresql.janitor import DatabaseJanitor
from sqlalchemy import create_engine, select, text
from sqlalchemy.orm import sessionmaker, Session

from ..database.crud import (create_user, get_user_by_token, add_model,
                           get_model_by_name, get_model_by_id, add_plugin_version, get_plugin_version_by_id,
                           get_plugin_versions_by_description_containing, get_plugin_versions_by_ide_type,
                           get_plugin_versions_by_name_containing, get_all_plugin_versions, add_telemetry,
                           get_telemetry_by_id, get_telemetries_with_typing_speed_in_range,
                           get_telemetries_with_relative_document_position_in_range,
                           get_telemetries_with_time_since_last_completion_in_range,
                           get_telemetries_with_document_char_length_in_range, add_context, get_context_by_id,
                           get_contexts_where_version_is, get_contexts_where_language_is,
                           get_contexts_where_trigger_type_is, get_contexts_where_prefix_contains,
                           get_contexts_where_suffix_contains, get_contexts_where_prefix_or_suffix_contains,
                           add_trigger_type, get_trigger_type_by_id, get_trigger_type_by_name, add_programming_language,
                           get_programming_language_by_id, get_programming_language_by_name,
                           add_ground_truth, get_ground_truths_for, get_ground_truths_for_query_in_time_range,
                           add_query, get_query_by_id, get_query_by_telemetry_id, get_queries_in_time_range,
                           get_queries_bound_by_context, get_user_queries, get_generations_by_query_id,
                           add_generation, get_generations_by_query_and_model_id,
                           get_generations_having_acceptance_of, get_generations_having_confidence_in_range,
                           get_generations_with_shown_times_in_range, update_status_of_generation)

from testcontainers.postgres import PostgresContainer

from ..database.db_schemas import *
from ..database.db_models import *

from ..models import CoCoConfig
config = CoCoConfig()


def bring_database_in_state_with_two_queries(transaction):
    user_id = str(uuid.uuid4())
    user_joined_at = datetime.now(tz=datetime.now().astimezone().tzinfo) - timedelta(days=1)

    user = UserCreate(token=user_id, joined_at=str(user_joined_at))

    context_id_1 = str(uuid.uuid4())
    context_id_2 = str(uuid.uuid4())

    prefix_1 = "print(\"Hello"
    prefix_2 = "print(\"John"

    suffix_1 = "\")"
    suffix_2 = "\"is fake)"

    language_id_1 = 1
    language_id_2 = 2

    trigger_type_id_1 = 1
    trigger_type_id_2 = 2

    version_id_1 = 1
    version_id_2 = 2

    context1 = ContextCreate(context_id=context_id_1, prefix=prefix_1, suffix=suffix_1,
                             language_id=language_id_1, trigger_type_id=trigger_type_id_1, version_id=version_id_1)
    context2 = ContextCreate(context_id=context_id_2, prefix=prefix_2, suffix=suffix_2,
                             language_id=language_id_2, trigger_type_id=trigger_type_id_2, version_id=version_id_2)

    telemetry_id_1 = str(uuid.uuid4())
    telemetry_id_2 = str(uuid.uuid4())

    time_since_last_completion_1 = 100
    time_since_last_completion_2 = 200

    typing_speed_1 = 50
    typing_speed_2 = 100

    document_char_length_1 = 500
    document_char_length_2 = 1000

    relative_document_position_1 = 0.25
    relative_document_position_2 = 0.5

    telemetry1 = TelemetryCreate(telemetry_id=telemetry_id_1,
                                 time_since_last_completion=time_since_last_completion_1,
                                 typing_speed=typing_speed_1, document_char_length=document_char_length_1,
                                 relative_document_position=relative_document_position_1)
    telemetry2 = TelemetryCreate(telemetry_id=telemetry_id_2,
                                 time_since_last_completion=time_since_last_completion_2,
                                 typing_speed=typing_speed_2, document_char_length=document_char_length_2,
                                 relative_document_position=relative_document_position_2)

    user_returned_by_database = create_user(transaction, user)

    context_1_from_database = add_context(transaction, context1)
    context_2_from_database = add_context(transaction, context2)

    telemetry_1_from_database = add_telemetry(transaction, telemetry1)
    telemetry_2_from_database = add_telemetry(transaction, telemetry2)

    query_id_1 = str(uuid.uuid4())
    query_id_2 = str(uuid.uuid4())

    query_1 = QueryCreate(query_id=query_id_1, user_id=user_id, context_id=context_id_1,
                          telemetry_id=telemetry_id_1,
                          total_serving_time=500,
                          timestamp=str(
                              datetime.now(tz=datetime.now().astimezone().tzinfo) - timedelta(seconds=200)),
                          server_version_id=1)
    query_2 = QueryCreate(query_id=query_id_2, user_id=user_id, context_id=context_id_2,
                          telemetry_id=telemetry_id_2,
                          total_serving_time=1000,
                          timestamp=str(
                              datetime.now(tz=datetime.now().astimezone().tzinfo) - timedelta(seconds=100)),
                          server_version_id=2)

    query_1_from_database = add_query(transaction, query_1)
    query_2_from_database = add_query(transaction, query_2)

    return user, context1, context2, telemetry1, telemetry2, query_1, query_2


def create_fresh_database(engine):
    # drop all tables
    Base.metadata.drop_all(engine)
    # create all tables from init.sql
    with engine.connect() as connection:
        connection.execute(text(open('./init.sql').read()))
    engine.dispose()


class TestCrudOperations:

    @pytest.fixture(scope='session')
    def db_session(self):
        engine = create_engine(config.test_database_url)
        create_fresh_database(engine)
        yield sessionmaker(autocommit=False, autoflush=False, bind=engine)
        create_fresh_database(engine)
        engine.dispose()

    @pytest.fixture(scope='function')
    def db_transaction(self, db_session: sessionmaker[Session]):
        session = db_session()
        connection = session.connection()
        transaction = connection.begin_nested()

        session.begin_nested()

        yield session

        transaction.rollback()
        connection.close()
        session.close()

    def test_adding_and_reading_users(self, db_transaction):
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

    def test_adding_and_reading_models(self, db_transaction):
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

    def test_adding_and_reading_plugin_versions(self, db_transaction):
        # Arrange
        version_name_1 = "test_version_1_goofy"
        version_name_2 = "test_version_2"

        version1 = PluginVersionCreate(version_name=version_name_1, ide_type="JetBrains",
                                       description="some description 1")
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

    def test_adding_and_reading_telemetry_data(self, db_transaction):
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

        telemetry1 = TelemetryCreate(telemetry_id=telemetry_1_id,
                                     time_since_last_completion=time_since_last_completion_1,
                                     typing_speed=typing_speed_1, document_char_length=document_char_length_1,
                                     relative_document_position=relative_document_position_1)
        telemetry2 = TelemetryCreate(telemetry_id=telemetry_2_id,
                                     time_since_last_completion=time_since_last_completion_2,
                                     typing_speed=typing_speed_2, document_char_length=document_char_length_2,
                                     relative_document_position=relative_document_position_2)

        # Act
        telemetry_returned_by_database_1 = add_telemetry(db_transaction, telemetry1)
        telemetry_returned_by_database_2 = add_telemetry(db_transaction, telemetry2)

        telemetry_returned_by_id = get_telemetry_by_id(db_transaction, telemetry_1_id)
        telemetries_with_typing_speed_in_range_of_one = get_telemetries_with_typing_speed_in_range(db_transaction, 0,
                                                                                                   99)
        telemetries_with_typing_speed_in_range_of_both = get_telemetries_with_typing_speed_in_range(db_transaction, 49,
                                                                                                    101)
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

    def test_adding_and_reading_context(self, db_transaction):
        # Arrange
        uuid_1 = str(uuid.uuid4())
        uuid_2 = str(uuid.uuid4())

        prefix_1 = "print(\"Hello"
        prefix_2 = "print(\"John"

        suffix_1 = "\")"
        suffix_2 = "\"is fake)"

        language_id_1 = 1
        language_id_2 = 2

        trigger_type_id_1 = 1
        trigger_type_id_2 = 2

        version_id_1 = 1
        version_id_2 = 2

        context1 = ContextCreate(context_id=uuid_1, prefix=prefix_1, suffix=suffix_1,
                                 language_id=language_id_1, trigger_type_id=trigger_type_id_1, version_id=version_id_1)
        context2 = ContextCreate(context_id=uuid_2, prefix=prefix_2, suffix=suffix_2,
                                 language_id=language_id_2, trigger_type_id=trigger_type_id_2, version_id=version_id_2)

        # Act
        context_returned_by_database_1 = add_context(db_transaction, context1)
        context_returned_by_database_2 = add_context(db_transaction, context2)

        context_returned_by_id = get_context_by_id(db_transaction, uuid_1)
        context_fetched_with_version_id = get_contexts_where_version_is(db_transaction, version_id_2)
        context_fetched_with_language = get_contexts_where_language_is(db_transaction, version_id_1)
        context_fetched_with_trigger_type = get_contexts_where_trigger_type_is(db_transaction, trigger_type_id_2)
        context_fetched_with_prefix = get_contexts_where_prefix_contains(db_transaction, "Hello")
        context_fetched_with_suffix = get_contexts_where_suffix_contains(db_transaction, "fake")
        context_fetched_with_prefix_or_suffix = get_contexts_where_prefix_or_suffix_contains(db_transaction, "print(")

        def evaluate_equivalence_of_contexts(c1, c2):
            return c1.prefix == c2.prefix and c1.suffix == c2.suffix and c1.language_id == c2.language_id and \
                c1.trigger_type_id == c2.trigger_type_id and c1.version_id == c2.version_id

        # Assert
        assert str(context_returned_by_database_1.context_id) == uuid_1
        assert str(context_returned_by_database_2.context_id) == uuid_2
        assert evaluate_equivalence_of_contexts(context_returned_by_id, context1)
        assert any([evaluate_equivalence_of_contexts(c, context2) for c in context_fetched_with_version_id])
        assert all([evaluate_equivalence_of_contexts(c, context1) or not evaluate_equivalence_of_contexts(c, context2)
                    for c in context_fetched_with_language])
        assert all([evaluate_equivalence_of_contexts(c, context2) or not evaluate_equivalence_of_contexts(c, context1)
                    for c in context_fetched_with_trigger_type])
        assert all([evaluate_equivalence_of_contexts(c, context1) or not evaluate_equivalence_of_contexts(c, context2)
                    for c in context_fetched_with_prefix])
        assert all([evaluate_equivalence_of_contexts(c, context2) or not evaluate_equivalence_of_contexts(c, context1)
                    for c in context_fetched_with_suffix])
        assert all([evaluate_equivalence_of_contexts(c, context1) or evaluate_equivalence_of_contexts(c, context2)
                    for c in context_fetched_with_prefix_or_suffix])

    def test_adding_and_reading_trigger_types(self, db_transaction):
        # Arrange
        t_type_name_1 = "semi_automatic"
        t_type_name_2 = "just_felt_like_it"
        t_type_1 = TriggerTypeCreate(trigger_type_name=t_type_name_1)
        t_type_2 = TriggerTypeCreate(trigger_type_name=t_type_name_2)

        # Act
        t_type_returned_by_database_1 = add_trigger_type(db_transaction, t_type_1)
        t_type_returned_by_database_2 = add_trigger_type(db_transaction, t_type_2)

        t_type_returned_by_id = get_trigger_type_by_id(db_transaction, t_type_returned_by_database_1.trigger_type_id)
        t_type_returned_by_name = get_trigger_type_by_name(db_transaction, t_type_name_2)

        # Assert
        assert t_type_returned_by_database_1.trigger_type_name == t_type_name_1
        assert t_type_returned_by_database_2.trigger_type_name == t_type_name_2
        assert t_type_returned_by_id.trigger_type_name == t_type_name_1
        assert t_type_returned_by_name.trigger_type_name == t_type_name_2

    def test_adding_and_reading_programming_languages(self, db_transaction):
        # Arrange
        language_name_1 = "nohtyp"
        language_name_2 = "avaj"
        language_1 = ProgrammingLanguageCreate(language_name=language_name_1)
        language_2 = ProgrammingLanguageCreate(language_name=language_name_2)

        # Act
        language_returned_by_database_1 = add_programming_language(db_transaction, language_1)
        language_returned_by_database_2 = add_programming_language(db_transaction, language_2)

        language_returned_by_id = get_programming_language_by_id(db_transaction,
                                                                 language_returned_by_database_1.language_id)
        language_returned_by_name = get_programming_language_by_name(db_transaction, language_name_2)

        # Assert
        assert language_returned_by_database_1.language_name == language_name_1
        assert language_returned_by_database_2.language_name == language_name_2
        assert language_returned_by_id.language_name == language_name_1
        assert language_returned_by_name.language_name == language_name_2

    def test_writing_and_reading_queries(self, db_transaction):
        # Arrange
        user, context1, context2, telemetry1, telemetry2, query_1, query_2 = (
            bring_database_in_state_with_two_queries(db_transaction))

        # Act
        query_returned_by_id_1 = get_query_by_id(db_transaction, query_1.query_id)
        query_returned_by_telemetry_id = get_query_by_telemetry_id(db_transaction, telemetry2.telemetry_id)
        queries_in_time_range = get_queries_in_time_range(db_transaction,
                                                          str(datetime.now(
                                                              tz=datetime.now().astimezone().tzinfo) - timedelta(
                                                              seconds=300)),
                                                          str(datetime.now(tz=datetime.now().astimezone().tzinfo)))
        queries_returned_by_context = get_queries_bound_by_context(db_transaction, context1.context_id)
        user_queries = get_user_queries(db_transaction, user.token)

        def evaluate_equivalence_of_queries(q1, q2):
            return (str(q1.query_id) == str(q2.query_id) and str(q1.user_id) == str(q2.user_id) and
                    str(q1.context_id) == str(q2.context_id) and str(q1.telemetry_id) == str(q2.telemetry_id) and
                    q1.total_serving_time == q2.total_serving_time and str(q1.timestamp) == str(q2.timestamp) and
                    q1.server_version_id == q2.server_version_id)

        # Assert
        assert evaluate_equivalence_of_queries(query_returned_by_id_1, query_1)
        assert evaluate_equivalence_of_queries(query_returned_by_telemetry_id, query_2)
        assert all([evaluate_equivalence_of_queries(q, query_1) or evaluate_equivalence_of_queries(q, query_2)
                    for q in queries_in_time_range])
        assert all([evaluate_equivalence_of_queries(q, query_1) for q in queries_returned_by_context])
        assert all([evaluate_equivalence_of_queries(q, query_1) or evaluate_equivalence_of_queries(q, query_2)
                    for q in user_queries])

    def test_adding_and_reading_ground_truth(self, db_transaction):
        # Arrange
        user, context1, context2, telemetry1, telemetry2, query_1, query_2 = (
            bring_database_in_state_with_two_queries(db_transaction))
        truth_timestamp_now = datetime.now(tz=datetime.now().astimezone().tzinfo)
        truth_timestamp_yesterday = truth_timestamp_now - timedelta(days=1)

        query_id_1 = query_1.query_id
        query_id_2 = query_2.query_id

        ground_truth_1 = GroundTruthCreate(query_id=query_id_1, truth_timestamp=str(truth_timestamp_now),
                                           ground_truth="some ground truth")
        ground_truth_2 = GroundTruthCreate(query_id=query_id_1, truth_timestamp=str(truth_timestamp_yesterday),
                                           ground_truth="some other ground truth")
        ground_truth_3 = GroundTruthCreate(query_id=query_id_2, truth_timestamp=str(truth_timestamp_now),
                                           ground_truth="some ground truth for another query")

        # Act
        ground_truth_returned_by_database_1 = add_ground_truth(db_transaction, ground_truth_1)
        ground_truth_returned_by_database_2 = add_ground_truth(db_transaction, ground_truth_2)
        ground_truth_returned_by_database_3 = add_ground_truth(db_transaction, ground_truth_3)

        ground_truths_for_query_1 = get_ground_truths_for(db_transaction, query_id_1)
        ground_truths_for_query_2 = get_ground_truths_for(db_transaction, query_id_2)
        ground_truths_for_query_1_in_time_range_only_one = (
            get_ground_truths_for_query_in_time_range(db_transaction,
                                                      query_id_1,
                                                      str(truth_timestamp_now - timedelta(hours=1)),
                                                      str(truth_timestamp_now + timedelta(hours=1))))
        ground_truths_for_query_1_in_time_range_both = (
            get_ground_truths_for_query_in_time_range(db_transaction,
                                                      query_id_1,
                                                      str(truth_timestamp_now - timedelta(days=1)),
                                                      str(truth_timestamp_now + timedelta(days=1))))

        ground_truths_for_query_2_in_time_range_all = (
            get_ground_truths_for_query_in_time_range(db_transaction, query_id_2, None, None))

        def evaluate_equivalence_of_ground_truths(gt1, gt2):
            return str(gt1.query_id) == str(gt2.query_id) and str(gt1.truth_timestamp) == str(gt2.truth_timestamp) and \
                gt1.ground_truth == gt2.ground_truth

        # Assert
        assert evaluate_equivalence_of_ground_truths(ground_truth_returned_by_database_1, ground_truth_1)
        assert evaluate_equivalence_of_ground_truths(ground_truth_returned_by_database_2, ground_truth_2)
        assert evaluate_equivalence_of_ground_truths(ground_truth_returned_by_database_3, ground_truth_3)
        assert all([evaluate_equivalence_of_ground_truths(gt, ground_truth_1) or
                    evaluate_equivalence_of_ground_truths(gt, ground_truth_2) for gt in ground_truths_for_query_1])
        assert all([evaluate_equivalence_of_ground_truths(gt, ground_truth_3) for gt in ground_truths_for_query_2])
        assert len(ground_truths_for_query_1_in_time_range_only_one) == 1
        assert len(ground_truths_for_query_1_in_time_range_both) == 2
        assert all([evaluate_equivalence_of_ground_truths(gt, ground_truth_1)
                    for gt in ground_truths_for_query_1_in_time_range_only_one])
        assert all([evaluate_equivalence_of_ground_truths(gt, ground_truth_1) or
                    evaluate_equivalence_of_ground_truths(gt, ground_truth_2)
                    for gt in ground_truths_for_query_1_in_time_range_both])
        assert all([evaluate_equivalence_of_ground_truths(gt, ground_truth_3)
                    for gt in ground_truths_for_query_2_in_time_range_all])

    def test_adding_and_reading_had_generations(self, db_transaction):
        # Arrange
        user, context1, context2, telemetry1, telemetry2, query_1, query_2 = (
            bring_database_in_state_with_two_queries(db_transaction))

        model_id_1 = 1
        model_id_2 = 2

        completion_1 = "World!"
        completion_2 = "Doe"

        generation_time_1 = 100
        generation_time_2 = 200

        shown_at_1 = [str(datetime.now(tz=datetime.now().astimezone().tzinfo) + timedelta(seconds=100))]
        shown_at_2 = shown_at_1 + [str(datetime.now(tz=datetime.now().astimezone().tzinfo) + timedelta(seconds=200))]

        was_accepted_1 = True
        was_accepted_2 = False

        confidence_1 = 0.5
        confidence_2 = 0.75

        log_probs_1 = [0.1, 0.2, 0.3]
        log_probs_2 = [0.4, 0.5, 0.6]

        had_generation_1 = HadGenerationCreate(query_id=query_1.query_id, model_id=model_id_1, completion=completion_1,
                                               generation_time=generation_time_1, shown_at=shown_at_1,
                                               was_accepted=was_accepted_1, confidence=confidence_1,
                                               logprobs=log_probs_1)
        had_generation_2 = HadGenerationCreate(query_id=query_2.query_id, model_id=model_id_2, completion=completion_2,
                                               generation_time=generation_time_2, shown_at=shown_at_2,
                                               was_accepted=was_accepted_2, confidence=confidence_2,
                                               logprobs=log_probs_2)
        had_generation_3 = HadGenerationCreate(query_id=query_1.query_id, model_id=model_id_2, completion=completion_2,
                                               generation_time=generation_time_2, shown_at=shown_at_2,
                                               was_accepted=was_accepted_2, confidence=confidence_2,
                                               logprobs=log_probs_2)

        # Act
        had_generation_returned_by_database_1 = add_generation(db_transaction, had_generation_1)
        had_generation_returned_by_database_2 = add_generation(db_transaction, had_generation_2)
        had_generation_returned_by_database_3 = add_generation(db_transaction, had_generation_3)

        generations_by_query_id_1 = get_generations_by_query_id(db_transaction, query_1.query_id)
        generations_by_query_id_2 = get_generations_by_query_id(db_transaction, query_2.query_id)
        generations_for_query_1_and_model_2 = get_generations_by_query_and_model_id(db_transaction,
                                                                                    query_1.query_id, model_id_2)
        generations_with_acceptance = get_generations_having_acceptance_of(db_transaction, True)
        generations_with_confidence_in_range_high = (
            get_generations_having_confidence_in_range(db_transaction, 0.6, 1.0))
        generations_with_confidence_in_range_all = (
            get_generations_having_confidence_in_range(db_transaction, 0.4, 0.8))
        generations_with_shown_times_in_range_low = get_generations_with_shown_times_in_range(db_transaction,
                                                                                              0,
                                                                                              1)
        generations_with_shown_times_in_range_all = get_generations_with_shown_times_in_range(db_transaction,
                                                                                              1,
                                                                                              3)

        def evaluate_equivalence_of_generations(g1, g2):
            return str(g1.query_id) == str(
                g2.query_id) and g1.model_id == g2.model_id and g1.completion == g2.completion \
                and g1.generation_time == g2.generation_time and len(g1.shown_at) == len(g2.shown_at) and \
                g1.was_accepted == g2.was_accepted and g1.confidence == g2.confidence

        # Assert
        assert evaluate_equivalence_of_generations(had_generation_returned_by_database_1, had_generation_1)
        assert evaluate_equivalence_of_generations(had_generation_returned_by_database_2, had_generation_2)
        assert all([evaluate_equivalence_of_generations(g, had_generation_1) or
                    evaluate_equivalence_of_generations(g, had_generation_3)
                    for g in generations_by_query_id_1])
        assert all([evaluate_equivalence_of_generations(g, had_generation_2) for g in generations_by_query_id_2])
        assert evaluate_equivalence_of_generations(generations_for_query_1_and_model_2, had_generation_3)
        assert all([evaluate_equivalence_of_generations(g, had_generation_1) for g in generations_with_acceptance])
        assert all([evaluate_equivalence_of_generations(g, had_generation_2) or
                    evaluate_equivalence_of_generations(g, had_generation_3)
                    for g in generations_with_confidence_in_range_high])
        assert all([evaluate_equivalence_of_generations(g, had_generation_1) or
                    evaluate_equivalence_of_generations(g, had_generation_2) or
                    evaluate_equivalence_of_generations(g, had_generation_3)
                    for g in generations_with_confidence_in_range_all])
        assert len(generations_with_confidence_in_range_high) == 2
        assert len(generations_with_confidence_in_range_all) == 3
        assert len(generations_with_shown_times_in_range_low) == 1
        assert len(generations_with_shown_times_in_range_all) == 3
        assert all([evaluate_equivalence_of_generations(g, had_generation_1)
                    for g in generations_with_shown_times_in_range_low])
        assert all([evaluate_equivalence_of_generations(g, had_generation_1) or
                    evaluate_equivalence_of_generations(g, had_generation_2) or
                    evaluate_equivalence_of_generations(g, had_generation_3)
                    for g in generations_with_shown_times_in_range_all])

    def test_updating_generation_status(self, db_transaction):
        # Arrange
        user, context1, context2, telemetry1, telemetry2, query_1, query_2 = (
            bring_database_in_state_with_two_queries(db_transaction))

        model_id = 1
        completion = "World!"
        generation_time = 100
        shown_at_1 = [str(datetime.now(tz=datetime.now().astimezone().tzinfo) + timedelta(seconds=100))]
        shown_at_2 = shown_at_1 + [str(datetime.now(tz=datetime.now().astimezone().tzinfo) + timedelta(seconds=200))]
        was_accepted = False
        confidence = 0.5
        log_probs = [0.1, 0.2, 0.3]
        generation = HadGenerationCreate(query_id=query_1.query_id, model_id=model_id, completion=completion,
                                         generation_time=generation_time, shown_at=shown_at_1,
                                         was_accepted=was_accepted, confidence=confidence,
                                         logprobs=log_probs)

        generation_returned_by_db = add_generation(db_transaction, generation)

        # Act
        new_status = HadGenerationUpdate(was_accepted=True, shown_at=shown_at_2)
        update_status_of_generation(db_transaction, generation_returned_by_db.query_id,
                                    generation_returned_by_db.model_id, new_status)
        updated_generation = get_generations_by_query_id(db_transaction, query_1.query_id)[0]

        # Assert
        assert updated_generation.was_accepted
        assert len(updated_generation.shown_at) == 2
        assert all([str(s) in shown_at_2 for s in updated_generation.shown_at])
