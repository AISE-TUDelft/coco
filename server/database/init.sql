BEGIN TRANSACTION;

CREATE TABLE IF NOT EXISTS public."user"
(
    token uuid NOT NULL PRIMARY KEY,
    joined_at timestamp with time zone NOT NULL
);

CREATE TABLE IF NOT EXISTS public.query
(
    query_id uuid NOT NULL PRIMARY KEY,
    user_id uuid,
    telemetry_id uuid,
    context_id uuid,
    total_serving_time integer,
    "timestamp" timestamp with time zone,
    server_version_id integer,
    CONSTRAINT unique_user_query UNIQUE (user_id, query_id)
);

CREATE TABLE IF NOT EXISTS public.model_name
(
    model_id integer NOT NULL PRIMARY KEY,
    model_name text NOT NULL
);

CREATE TABLE IF NOT EXISTS public.plugin_version
(
    version_id integer NOT NULL PRIMARY KEY,
    version_name text NOT NULL,
    ide_type text NOT NULL,
    description text
);

CREATE TABLE IF NOT EXISTS public.trigger_type
(
    trigger_type_id integer NOT NULL PRIMARY KEY,
    trigger_type_name text NOT NULL
);

CREATE TABLE IF NOT EXISTS public.programming_language
(
    language_id integer NOT NULL PRIMARY KEY,
    language_name text NOT NULL
);

CREATE TABLE IF NOT EXISTS public.had_generation
(
    query_id uuid NOT NULL,
    model_id integer NOT NULL,
    completion text NOT NULL,
    generation_time integer NOT NULL,
    shown_at timestamp with time zone[] NOT NULL,
    was_accepted boolean NOT NULL,
    confidence double precision NOT NULL,
    PRIMARY KEY (query_id, model_id)
);

CREATE TABLE IF NOT EXISTS public.ground_truth
(
    query_id uuid NOT NULL,
    truth_timestamp timestamp with time zone NOT NULL,
    ground_truth text NOT NULL,
    PRIMARY KEY (query_id, truth_timestamp)
);

CREATE TABLE IF NOT EXISTS public.context
(
    context_id uuid NOT NULL PRIMARY KEY,
    prefix text,
    suffix text,
    language_id integer,
    trigger_type_id integer,
    version_id integer
);

CREATE TABLE IF NOT EXISTS public.telemetry
(
    telemetry_id uuid NOT NULL PRIMARY KEY,
    time_since_last_completion integer,
    typing_speed integer,
    document_char_length integer,
    relative_document_position double precision
);

-- Foreign Key Constraints
ALTER TABLE public.query
    ADD CONSTRAINT user_fk FOREIGN KEY (user_id)
    REFERENCES public."user" (token)
    ON UPDATE NO ACTION
    ON DELETE NO ACTION;

ALTER TABLE IF EXISTS public.query
    ADD CONSTRAINT fk_context FOREIGN KEY (context_id)
    REFERENCES public.context (context_id)
    ON UPDATE NO ACTION
    ON DELETE NO ACTION;

ALTER TABLE public.query
    ADD CONSTRAINT fk_telemetry FOREIGN KEY (telemetry_id)
    REFERENCES public.telemetry (telemetry_id)
    ON UPDATE NO ACTION
    ON DELETE NO ACTION;

ALTER TABLE public.had_generation
    ADD CONSTRAINT request_fk FOREIGN KEY (query_id)
    REFERENCES public.query (query_id)
    ON UPDATE NO ACTION
    ON DELETE CASCADE;

ALTER TABLE public.had_generation
    ADD CONSTRAINT model_id_fk FOREIGN KEY (model_id)
    REFERENCES public.model_name (model_id)
    ON UPDATE NO ACTION
    ON DELETE NO ACTION;

ALTER TABLE public.ground_truth
    ADD CONSTRAINT fk_to_query FOREIGN KEY (query_id)
    REFERENCES public.query (query_id)
    ON UPDATE NO ACTION
    ON DELETE CASCADE;

ALTER TABLE public.context
    ADD CONSTRAINT fk_language FOREIGN KEY (language_id)
    REFERENCES public.programming_language (language_id)
    ON UPDATE NO ACTION
    ON DELETE NO ACTION;

ALTER TABLE public.context
    ADD CONSTRAINT fk_trigger_type FOREIGN KEY (trigger_type_id)
    REFERENCES public.trigger_type (trigger_type_id)
    ON UPDATE NO ACTION
    ON DELETE NO ACTION;

ALTER TABLE public.context
    ADD CONSTRAINT fk_version FOREIGN KEY (version_id)
    REFERENCES public.plugin_version (version_id)
    ON UPDATE NO ACTION
    ON DELETE NO ACTION;

-- Indexes on Foreign Keys
CREATE INDEX idx_query_user_id ON public.query (user_id);
CREATE INDEX idx_query_language_id ON public.context (language_id);
CREATE INDEX idx_query_trigger_type_id ON public.context (trigger_type_id);
CREATE INDEX idx_query_version_id ON public.context (version_id);

-- Indexes on Primary Keys
CREATE INDEX telemetry_id_index ON public.telemetry (telemetry_id);

-- low cost index for foreign key lookups
CREATE INDEX idx_model_id ON public.model_name (model_id);
CREATE INDEX idx_version_id ON public.plugin_version (version_id);
CREATE INDEX idx_trigger_type_id ON public.trigger_type (trigger_type_id);
CREATE INDEX idx_language_id ON public.programming_language (language_id);

-- Indexes on FKs that will speed up the serving process
CREATE INDEX idx_query_query_id ON public.query (query_id);
CREATE INDEX idx_user_token ON public."user" (token);

-- Indexes that will speed up analysis
CREATE INDEX idx_query_id_model_id ON public.had_generation (query_id, model_id);
CREATE INDEX idx_query_id_truth_timestamp ON public.ground_truth (query_id, truth_timestamp);

COMMIT;
