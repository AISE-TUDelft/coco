from logging import Logger
from typing import List

from fastapi import FastAPI

from database.crud import add_context, add_query, add_telemetry, add_generation, add_ground_truth
from database.db_schemas import ContextCreate, QueryCreate, TelemetryCreate, HadGenerationCreate, GroundTruthCreate

from models.Lifecycle import ActiveRequest, ModelCompletionDetails

from sqlalchemy.orm import Session as DBSession

from uuid import uuid4

def get_context_from_request(request: ActiveRequest, coco_version: str, app: FastAPI) -> ContextCreate:
    """
    Go from an ActiveRequest object (see models/Lifecycle.py) to a ContextCreate object (see database/db_schemas.py).
    """
    actual_generate_request = request.request
    prefix = actual_generate_request.prefix
    suffix = actual_generate_request.suffix
    language_id = app.languages[actual_generate_request.language]
    trigger_id = app.trigger_types[actual_generate_request.trigger]
    version_id = app.plugin_versions[coco_version]
    return ContextCreate(
        context_id=str(uuid4()),
        prefix=prefix,
        suffix=suffix,
        language_id=language_id,
        trigger_type_id=trigger_id,
        version_id=version_id
    )


def get_telemetry_from_request(request: ActiveRequest) -> TelemetryCreate:
    """
    Go from an ActiveRequest object (see models/Lifecycle.py) to a TelemetryCreate object (see database/db_schemas.py).
    """
    actual_telemetry = request.request.telemetry
    return TelemetryCreate(
        telemetry_id=str(uuid4()),
        time_since_last_completion=actual_telemetry.time_since_last_completion,
        typing_speed=actual_telemetry.typing_speed,
        document_char_length=actual_telemetry.document_length,
        relative_document_position=actual_telemetry.cursor_relative_position
    )


def get_query_from_request(request: ActiveRequest, context: ContextCreate,
                           telemetry: TelemetryCreate, user_id: str, app: FastAPI) -> QueryCreate:
    """
    Go from an ActiveRequest object (see models/Lifecycle.py) to a QueryCreate object (see database/db_schemas.py).
    """
    query_id = request.request.request_id
    user_id = user_id
    telemetry_id = telemetry.telemetry_id
    context_id = context.context_id
    total_serving_time= request.time_taken
    timestamp = request.request.timestamp
    server_version_id = app.config.server_version_id
    return QueryCreate(
        query_id=query_id,
        user_id=user_id,
        telemetry_id=telemetry_id,
        context_id=context_id,
        total_serving_time=total_serving_time,
        timestamp=str(timestamp),
        server_version_id=server_version_id
    )


def get_ground_truths_from_request(request: ActiveRequest, query: QueryCreate) -> List[GroundTruthCreate]:
    """
    Go from an ActiveRequest object (see models/Lifecycle.py) to a list of GroundTruthCreate objects (see database/db_schemas.py).
    """
    ground_truths = []
    if request.ground_truth is not None:
        for gt in request.ground_truth:
            ground_truths.append(GroundTruthCreate(
                query_id=query.query_id,
                truth_timestamp=str(gt[0]),
                ground_truth=gt[1]
            ))
    return ground_truths


def get_generation_from_request(request: ActiveRequest, query: QueryCreate, app: FastAPI) -> List[HadGenerationCreate]:
    """
    Go from an ActiveRequest object (see models/Lifecycle.py) to a HadGenerationCreate object (see database/db_schemas.py).
    """
    generations = []
    if request.completions is not None:
        for completion_model in request.completions.keys():
            generations.append(HadGenerationCreate(
                query_id=query.query_id,
                model_id=app.llms[completion_model],
                completion=request.completions[completion_model].completion,
                generation_time=0,
                shown_at=[str(x) for x in request.completions[completion_model].shown_at],
                was_accepted=request.completions[completion_model].accepted,
                confidence=1.0,
                logprobs=[0.2, 0.3, 0.4, 0.1]  # TODO: Fix this -> this is simply a placeholder for the time being
            ))

    return generations


def add_active_request_to_db(db_session: DBSession, request: ActiveRequest, user_id: str, server_version_id: str,
                             app: FastAPI, logger: Logger):
    """
    Go from an ActiveRequest object (see models/Lifecycle.py) to a database entry and add it to the database.
    """

    logger.log(f"Adding active request with id {request.request.request_id} to DB for user {user_id}")
    try:
        context = get_context_from_request(request, server_version_id, app)
        add_context(db_session, context)
        logger.log(f"Added context with id {context.context_id} to DB for active request with id {request.request.request_id}")

        telemetry = get_telemetry_from_request(request)
        add_telemetry(db_session, telemetry)
        logger.log(f"Added telemetry with id {telemetry.telemetry_id} to DB for active request with id {request.request.request_id}")


        query = get_query_from_request(request, context, telemetry, user_id, app)
        add_query(db_session, query)
        logger.log(f"Added query with id {query.query_id} to DB for active request with id {request.request.request_id}")

        generations = get_generation_from_request(request, query, app)
        for generation in generations:
            add_generation(db_session, generation)
        logger.log(f"Added {len(generations)} total generations to DB for active request with id {request.request.request_id}")

        ground_truths = get_ground_truths_from_request(request, query)
        for truth in ground_truths:
            add_ground_truth(db_session, truth)
        logger.log(f"Added {len(ground_truths)} total ground truths to DB for active request with id {request.request.request_id}")
    except Exception as e:
        print(f"Error adding active request to DB: {e}")
        db_session.rollback()
        raise e

    logger.log(f"Successfully added active request {request.request.request_id} to DB.")