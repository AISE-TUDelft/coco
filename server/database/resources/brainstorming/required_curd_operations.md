# All required functions for DB CRUD operations of CoCo

## Read
### Single Table
#### User
- `get_all_users() -> List[User]`
- `get_user(token: str) -> User`

#### query
- `get_all_queries() -> List[Query]`
- `get_query(query_id: int) -> Query`
- `get_user_queries(token: str) -> List[Query]`
- `get_queries_in_range(start: datetime, end: datetime) -> List[Query]`
- `get_queries_bound_by_context(context_id: int) -> List[Query]`
- `get_query_by_telemetry_id(telemetry_id: int) -> Query`

#### programming_language
- `get_all_programming_languages() -> List[ProgrammingLanguage]`
- `get_programming_language(language_id: int) -> ProgrammingLanguage`
- `get_programming_language_by_name(language_name: str) -> ProgrammingLanguage`

#### had_generation
- `get_all_had_generations() -> List[HadGeneration]`
- `get_generations_by_query(query_id: int) -> List[HadGeneration]`
- `get_generations_by_query_and_model(query_id: int, model_id: int) -> HadGeneration`
- `get_generations_having_accuracy_in_range(start: float, end: float) -> List[HadGeneration]`
- `get_generations_having_acceptance_of(acceptance: bool) -> List[HadGeneration]`
- `get_generations_shown_times_in_range(start: int, end: int) -> List[HadGeneration]`

#### model_name
- `get_all_model_names() -> List[ModelName]`
- `get_model_name(model_id: int) -> ModelName`
- `get_model_name_by_name(model_name: str) -> ModelName`

#### ground_truth
- `get_all_ground_truths() -> List[GroundTruth]`
- `get_ground_truths_for(query_id: int) -> List[GroundTruth]`
- `get_ground_truths_within_time_range_for_query(start: datetime, end: datetime) -> List[GroundTruth]`


#### telemetry
- `get_all_telemetries() -> List[Telemetry]`
- `get_telemetries_with_time_since_last_completion_in_range(start: int, end: int) -> List[Telemetry]`
- `get_telemetries_with_typing_speed_in_range(start: int, end: int) -> List[Telemetry]`
- `get_telemetries_with_document_char_length_in_range(start: int, end: int) -> List[Telemetry]`
- `get_telemetries_with_relative_document_position_in_range(start: int, end: int) -> List[Telemetry]`

#### context
- `get_all_contexts() -> List[Context]`
- `get_context(context_id: int) -> Context`
- `get_contexts_for_language(language_id: int) -> List[Context]`
- `get_contexts_for_trigger_type(trigger_type_id: int) -> List[Context]`
- `get_contexts_for_version(version_id: int) -> List[Context]`

#### trigger_type
- `get_all_trigger_types() -> List[TriggerType]`
- `get_trigger_type(trigger_type_id: int) -> TriggerType`
- `get_trigger_type_by_name(trigger_type_name: str) -> TriggerType`
