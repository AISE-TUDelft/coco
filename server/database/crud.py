from typing import List, Type, Any
from uuid import uuid4
from sqlalchemy.orm import Session
from sqlalchemy import func

from . import models, schemas
from .models import User, Query


# helper functions
def is_valid_uuid(uuid: str) -> bool:
    return len(uuid) == 36


# READ operations
# User Table
def get_all_users(db: Session) -> list[Type[User]]:
    return db.query(models.User).all()


def get_user_by_token(db: Session, token: str) -> models.User:
    assert is_valid_uuid(token)
    return db.query(models.User).filter(models.User.token == token).first()


# Query Table
def get_all_queries(db: Session) -> list[models.Query]:
    return db.query(models.Query).all()


def get_query_by_id(db: Session, query_id: str) -> models.Query:
    assert is_valid_uuid(query_id)
    return db.query(models.Query).filter(models.Query.query_id == query_id).first()


def get_user_queries(db: Session, user_id: str) -> list[models.Query]:
    assert is_valid_uuid(user_id)
    return db.query(models.Query).filter(models.Query.user_id == user_id).all()


def get_queries_in_time_range(db: Session, start_time: str = None, end_time: str = None) -> list[Type[Query]]:
    if start_time and end_time:
        return db.query(models.Query).filter(models.Query.timestamp >= start_time,
                                             models.Query.timestamp <= end_time).all()
    elif start_time:
        return db.query(models.Query).filter(models.Query.timestamp >= start_time).all()
    elif end_time:
        return db.query(models.Query).filter(models.Query.timestamp <= end_time).all()
    return db.query(models.Query).all()


def get_queries_bound_by_context(db: Session, context_id: str) -> list[Type[Query]]:
    assert is_valid_uuid(context_id)
    return db.query(models.Query).filter(models.Query.context_id == context_id).all()


def get_query_by_telemetry_id(db: Session, telemetry_id: str) -> models.Query:
    assert is_valid_uuid(telemetry_id)
    return db.query(models.Query).filter(models.Query.telemetry_id == telemetry_id).first()


# programming_language Table
def get_all_programming_languages(db: Session) -> list[Type[models.ProgrammingLanguage]]:
    return db.query(models.ProgrammingLanguage).all()


def get_programming_language_by_id(db: Session, language_id: int) -> models.ProgrammingLanguage:
    return db.query(models.ProgrammingLanguage).filter(models.ProgrammingLanguage.language_id == language_id).first()


def get_programming_language_by_name(db: Session, language_name: str) -> models.ProgrammingLanguage:
    return db.query(models.ProgrammingLanguage).filter(
        models.ProgrammingLanguage.language_name == language_name).first()


# had_generation Table
def get_all_generations(db: Session) -> list[Type[models.HadGeneration]]:
    return db.query(models.HadGeneration).all()


def get_generations_by_query_id(db: Session, query_id: str) -> list[Type[models.HadGeneration]]:
    assert is_valid_uuid(query_id)
    return db.query(models.HadGeneration).filter(models.HadGeneration.query_id == query_id).all()


def get_generations_by_query_and_model_id(db: Session, query_id: str,
                                          model_id: int) -> list[Type[models.HadGeneration]]:
    assert is_valid_uuid(query_id)
    return db.query(models.HadGeneration).filter(models.HadGeneration.query_id == query_id,
                                                 models.HadGeneration.model_id == model_id).all()


def get_generations_having_confidence_in_range(db: Session, lower_bound: float = None,
                                               upper_bound: float = None) -> list[Type[models.HadGeneration]]:
    if lower_bound and upper_bound:
        return db.query(models.HadGeneration).filter(models.HadGeneration.confidence >= lower_bound,
                                                     models.HadGeneration.confidence <= upper_bound).all()
    elif lower_bound:
        return db.query(models.HadGeneration).filter(models.HadGeneration.confidence >= lower_bound).all()
    elif upper_bound:
        return db.query(models.HadGeneration).filter(models.HadGeneration.confidence <= upper_bound).all()

    return get_all_generations(db)


def get_generations_having_acceptance_of(db: Session, acceptance: bool) -> list[Type[models.HadGeneration]]:
    return db.query(models.HadGeneration).filter(models.HadGeneration.was_accepted == acceptance).all()


def get_generations_with_shown_times_in_range(db: Session, lower_bound: int = None,
                                              upper_bound: int = None) -> list[Type[models.HadGeneration]]:
    if lower_bound and upper_bound:
        return (db.query(models.HadGeneration)
                .filter(func.cardinality(models.HadGeneration.shown_at) >= lower_bound,
                        func.cardinality(models.HadGeneration.shown_at) <= upper_bound).all())

    elif lower_bound:
        return (db.query(models.HadGeneration)
                .filter(func.cardinality(models.HadGeneration.shown_at) >= lower_bound).all())

    elif upper_bound:
        return (db.query(models.HadGeneration)
                .filter(func.cardinality(models.HadGeneration.shown_at) <= upper_bound).all())

    return get_all_generations(db)


# model_name Table
def get_all_models(db: Session) -> list[Type[models.ModelName]]:
    return db.query(models.ModelName).all()


def get_model_by_id(db: Session, model_id: int) -> models.ModelName:
    return db.query(models.ModelName).filter(models.ModelName.model_id == model_id).first()


def get_model_by_name(db: Session, model_name: str) -> models.ModelName:
    return db.query(models.ModelName).filter(models.ModelName.model_name == model_name).first()


# ground_truth Table
def get_all_ground_truths(db: Session) -> list[Type[models.GroundTruth]]:
    return db.query(models.GroundTruth).all()


def get_ground_truths_for(db: Session, query_id: str) -> list[Type[models.GroundTruth]]:
    assert is_valid_uuid(query_id)
    return db.query(models.GroundTruth).filter(models.GroundTruth.query_id == query_id).all()


def get_ground_truths_for_query_in_time_range(db: Session, query_id: str, start_time: str = None,
                                              end_time: str = None) -> list[Type[models.GroundTruth]]:
    assert is_valid_uuid(query_id)
    if start_time and end_time:
        return db.query(models.GroundTruth).filter(models.GroundTruth.query_id == query_id,
                                                   models.GroundTruth.truth_timestamp >= start_time,
                                                   models.GroundTruth.truth_timestamp <= end_time).all()
    elif start_time:
        return db.query(models.GroundTruth).filter(models.GroundTruth.query_id == query_id,
                                                   models.GroundTruth.truth_timestamp >= start_time).all()
    elif end_time:
        return db.query(models.GroundTruth).filter(models.GroundTruth.query_id == query_id,
                                                   models.GroundTruth.truth_timestamp <= end_time).all()

    return get_ground_truths_for(db, query_id)


# telemetry table
def get_all_telemetries(db: Session) -> list[Type[models.Telemetry]]:
    return db.query(models.Telemetry).all()


def get_telemetries_with_time_since_last_completion_in_range(db: Session, lower_bound: int = None,
                                                             upper_bound: int = None) -> list[Type[models.Telemetry]]:
    if lower_bound and upper_bound:
        return db.query(models.Telemetry).filter(models.Telemetry.time_since_last_completion >= lower_bound,
                                                 models.Telemetry.time_since_last_completion <= upper_bound).all()
    elif lower_bound:
        return db.query(models.Telemetry).filter(models.Telemetry.time_since_last_completion >= lower_bound).all()
    elif upper_bound:
        return db.query(models.Telemetry).filter(models.Telemetry.time_since_last_completion <= upper_bound).all()

    return get_all_telemetries(db)


def get_telemetry_by_id(db: Session, telemetry_id: str) -> models.Telemetry:
    assert is_valid_uuid(telemetry_id)
    return db.query(models.Telemetry).filter(models.Telemetry.telemetry_id == telemetry_id).first()


def get_telemetries_with_typing_speed_in_range(db: Session, lower_bound: int = None,
                                               upper_bound: int = None) -> list[Type[models.Telemetry]]:
    if lower_bound and upper_bound:
        return db.query(models.Telemetry).filter(models.Telemetry.typing_speed >= lower_bound,
                                                 models.Telemetry.typing_speed <= upper_bound).all()
    elif lower_bound:
        return db.query(models.Telemetry).filter(models.Telemetry.typing_speed >= lower_bound).all()
    elif upper_bound:
        return db.query(models.Telemetry).filter(models.Telemetry.typing_speed <= upper_bound).all()

    return get_all_telemetries(db)


def get_telemetries_with_document_char_length_in_range(db: Session, lower_bound: int = None,
                                                       upper_bound: int = None) -> list[Type[models.Telemetry]]:
    if lower_bound and upper_bound:
        return db.query(models.Telemetry).filter(models.Telemetry.document_char_length >= lower_bound,
                                                 models.Telemetry.document_char_length <= upper_bound).all()
    elif lower_bound:
        return db.query(models.Telemetry).filter(models.Telemetry.document_char_length >= lower_bound).all()
    elif upper_bound:
        return db.query(models.Telemetry).filter(models.Telemetry.document_char_length <= upper_bound).all()

    return get_all_telemetries(db)


def get_telemetries_with_relative_document_position_in_range(db: Session, lower_bound: float = None,
                                                             upper_bound: float = None) -> list[Type[models.Telemetry]]:
    if lower_bound and upper_bound:
        return db.query(models.Telemetry).filter(models.Telemetry.relative_document_position >= lower_bound,
                                                 models.Telemetry.relative_document_position <= upper_bound).all()
    elif lower_bound:
        return db.query(models.Telemetry).filter(models.Telemetry.relative_document_position >= lower_bound).all()
    elif upper_bound:
        return db.query(models.Telemetry).filter(models.Telemetry.relative_document_position <= upper_bound).all()

    return get_all_telemetries(db)


# context Table
def get_all_contexts(db: Session) -> list[Type[models.Context]]:
    return db.query(models.Context).all()


def get_context_by_id(db: Session, context_id: str) -> models.Context:
    assert is_valid_uuid(context_id)
    return db.query(models.Context).filter(models.Context.context_id == context_id).first()


def get_contexts_where_language_is(db: Session, language_id: int) -> list[Type[models.Context]]:
    return db.query(models.Context).filter(models.Context.language_id == language_id).all()


def get_contexts_where_trigger_type_is(db: Session, trigger_type_id: int) -> list[Type[models.Context]]:
    return db.query(models.Context).filter(models.Context.trigger_type_id == trigger_type_id).all()


def get_contexts_where_version_is(db: Session, version_id: int) -> list[Type[models.Context]]:
    return db.query(models.Context).filter(models.Context.version_id == version_id).all()


# trigger_type Table
def get_all_trigger_types(db: Session) -> list[Type[models.TriggerType]]:
    return db.query(models.TriggerType).all()


def get_trigger_type_by_id(db: Session, trigger_type_id: int) -> models.TriggerType:
    return db.query(models.TriggerType).filter(models.TriggerType.trigger_type_id == trigger_type_id).first()


def get_trigger_type_by_name(db: Session, trigger_type_name: str) -> models.TriggerType:
    return db.query(models.TriggerType).filter(models.TriggerType.trigger_type_name == trigger_type_name).first()

