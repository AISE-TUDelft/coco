-- import the vector extension from pgvector -> https://github.com/pgvector/pgvector
CREATE EXTENSION IF NOT EXISTS vector;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM information_schema.tables
        WHERE table_name = 'embedding'
    ) THEN
        CREATE TABLE embedding (
          embedding_id BIGSERIAL PRIMARY KEY,
          embedding_vector vector NOT NULL  --This is the actual embedding vector -> TODO: change this to a fixed size vector so we can index it
        );

        -- add a index on the embedding_id column
        CREATE INDEX embedding_id_index ON embedding (embedding_id);
        -- we could also think about adding an index on the embedding_vector column
        -- as the developers mention it would reduce the time-wise complexity of the queries
        -- but it would be a trade of for some recall and precision as the results become approximate
        -- TODO: talk about this
        -- CREATE INDEX ON embedding USING hnsw (embedding_vector vector);
    END IF;

    IF NOT EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_name = 'context'
        AND column_name = 'embedding_ids'
    ) THEN
        -- add a column to store the embedding ids
        ALTER TABLE context ADD COLUMN embedding_ids BIGINT[];
        -- also add the foreign key constraint
        ALTER TABLE context
            ADD CONSTRAINT fk_to_embedding FOREIGN KEY (embedding_ids)
            REFERENCES embedding (embedding_id)
            ON UPDATE NO ACTION
            ON DELETE NO ACTION;
    END IF;
END
$$;