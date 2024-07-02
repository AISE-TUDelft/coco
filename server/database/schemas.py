from pydantic import BaseModel


# pydantic classes for the database models
# User
class UserBase(BaseModel):
    token: str
    joined_at: str


class User(UserBase):
    class Config:
        orm_mode = True


class UserCreate(UserBase):
    pass


# Query
class QueryBase(BaseModel):
    query_id: str
    user_id: str
    telemetry_id: str
    context_id: str
    total_serving_time: int
    timestamp: str
    server_version_id: int


class Query(QueryBase):
    class Config:
        orm_mode = True


class QueryCreate(QueryBase):
    pass


# Model Name
class ModelNameBase(BaseModel):
    model_id: int
    model_name: str


class ModelName(ModelNameBase):
    class Config:
        orm_mode = True


class ModelNameCreate(ModelNameBase):
    pass


# Plugin Version
class PluginVersionBase(BaseModel):
    version_id: int
    version_name: str
    ide_type: str
    description: str


class PluginVersion(PluginVersionBase):
    class Config:
        orm_mode = True


class PluginVersionCreate(PluginVersionBase):
    pass


# Trigger Type
class TriggerTypeBase(BaseModel):
    trigger_type_id: int
    trigger_type_name: str


class TriggerType(TriggerTypeBase):
    class Config:
        orm_mode = True


class TriggerTypeCreate(TriggerTypeBase):
    pass


# Programming Language
class ProgrammingLanguageBase(BaseModel):
    language_id: int
    language_name: str
    language_version: str


class ProgrammingLanguage(ProgrammingLanguageBase):
    class Config:
        orm_mode = True


class ProgrammingLanguageCreate(ProgrammingLanguageBase):
    pass


# Had Generation
class HadGenerationBase(BaseModel):
    query_id: str
    model_id: int
    completion: str
    generation_time: int
    shown_at: list[str]
    was_accepted: bool
    confidence: float


class HadGeneration(HadGenerationBase):
    class Config:
        orm_mode = True


class HadGenerationCreate(HadGenerationBase):
    pass


# Ground Truth
class GroundTruthBase(BaseModel):
    query_id: str
    model_id: int
    completion: str
    generation_time: int
    shown_at: list[str]
    was_accepted: bool
    confidence: float


class GroundTruth(GroundTruthBase):
    class Config:
        orm_mode = True


class GroundTruthCreate(GroundTruthBase):
    pass


# Context
class ContextBase(BaseModel):
    context_id: str
    prefix: str
    suffix: str
    language_id: int
    trigger_type_id: int
    version_id: int


class Context(ContextBase):
    class Config:
        orm_mode = True


class ContextCreate(ContextBase):
    pass


# Telemetry
class TelemetryBase(BaseModel):
    telemetry_id: str
    time_since_last_completion: int
    typing_speed: int
    document_char_length: int
    relative_document_position: float
