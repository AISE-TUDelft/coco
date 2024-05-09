BEGIN;


CREATE TABLE IF NOT EXISTS public."user"
(
    token uuid NOT NULL,
    PRIMARY KEY (token),
    CONSTRAINT uniqueness_on_user_token UNIQUE (token)
        INCLUDE(token)
);

CREATE TABLE IF NOT EXISTS public.generation
(
    request_id uuid NOT NULL,
    user_id uuid,
    prefix text NOT NULL,
    suffix text NOT NULL,
    trigger_type_id integer,
    language_id integer,
    ide_type_id integer,
    version_id integer,
    total_serving_time integer,
    CONSTRAINT primarykey_generate_request PRIMARY KEY (request_id),
    CONSTRAINT "UNIQUENESS_USER_ID_REQUEST_ID" UNIQUE (user_id, request_id)
);

CREATE TABLE IF NOT EXISTS public.model_name
(
    model_id integer NOT NULL,
    model_name text NOT NULL,
    PRIMARY KEY (model_id)
);

CREATE TABLE IF NOT EXISTS public.ide_type
(
    ide_type_id integer NOT NULL,
    ide_name text NOT NULL,
    PRIMARY KEY (ide_type_id)
);

CREATE TABLE IF NOT EXISTS public.version_id
(
    version_id integer NOT NULL,
    version_name text NOT NULL,
    description text,
    PRIMARY KEY (version_id)
);

CREATE TABLE IF NOT EXISTS public.trigger_type
(
    trigger_type_id integer NOT NULL,
    trigger_type_name text NOT NULL,
    PRIMARY KEY (trigger_type_id)
);

CREATE TABLE IF NOT EXISTS public.programming_language
(
    language_id integer NOT NULL,
    language_name text NOT NULL,
    PRIMARY KEY (language_id)
);

CREATE TABLE IF NOT EXISTS public.completion
(
    request_id uuid NOT NULL,
    model_id integer NOT NULL,
    completion text NOT NULL,
    generation_time integer,
    times_shown integer,
    was_accepted boolean NOT NULL,
    PRIMARY KEY (request_id, model_id)
);

ALTER TABLE IF EXISTS public.generation
    ADD CONSTRAINT user_fk FOREIGN KEY (user_id)
    REFERENCES public."user" (token) MATCH SIMPLE
    ON UPDATE NO ACTION
    ON DELETE NO ACTION
    NOT VALID;


ALTER TABLE IF EXISTS public.generation
    ADD CONSTRAINT langauge_fk FOREIGN KEY (language_id)
    REFERENCES public.programming_language (language_id) MATCH SIMPLE
    ON UPDATE NO ACTION
    ON DELETE NO ACTION
    NOT VALID;


ALTER TABLE IF EXISTS public.generation
    ADD CONSTRAINT trigger_type_fk FOREIGN KEY (trigger_type_id)
    REFERENCES public.trigger_type (trigger_type_id) MATCH SIMPLE
    ON UPDATE NO ACTION
    ON DELETE NO ACTION
    NOT VALID;


ALTER TABLE IF EXISTS public.generation
    ADD CONSTRAINT ide_type_fk FOREIGN KEY (ide_type_id)
    REFERENCES public.ide_type (ide_type_id) MATCH SIMPLE
    ON UPDATE NO ACTION
    ON DELETE NO ACTION
    NOT VALID;


ALTER TABLE IF EXISTS public.generation
    ADD CONSTRAINT version_id_fk FOREIGN KEY (version_id)
    REFERENCES public.version_id (version_id) MATCH SIMPLE
    ON UPDATE NO ACTION
    ON DELETE NO ACTION
    NOT VALID;


ALTER TABLE IF EXISTS public.completion
    ADD CONSTRAINT request_fk FOREIGN KEY (request_id)
    REFERENCES public.generation (request_id) MATCH SIMPLE
    ON UPDATE NO ACTION
    ON DELETE CASCADE
    NOT VALID;


ALTER TABLE IF EXISTS public.completion
    ADD CONSTRAINT model_id_fk FOREIGN KEY (model_id)
    REFERENCES public.model_name (model_id) MATCH SIMPLE
    ON UPDATE NO ACTION
    ON DELETE NO ACTION
    NOT VALID;

END;