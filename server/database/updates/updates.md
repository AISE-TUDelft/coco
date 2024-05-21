# Updating the schema of the database

## General Idea
In this project we decided to do a patch style update system, as is quite similarly defined in this [post](https://dev.to/hernanreyes/keeping-track-of-database-schema-changes-2g62).
What follows is a general overview of how the update system works, how to create a new update and how to apply it.

## How it works
The update system works by keeping track of the updates that have been applied to the database. This is done by storing the updates (patches) in the `database/updates` directory. The updates are stored in a file with the following format: 
`update_{number}_{name}.sql`. The number is the order in which the updates should be applied and the name is a short description of what the update does.

When the database is initialized, the system checks the `database/updates` directory for any updates that have not been applied yet. If there are any, they are applied in order.

## Creating a new update
Each update may rely upon the previous updates, so it is important to keep the updates in order. To create a new update, simply create a new file in the `database/updates` directory with the format `update_{number}_{name}.sql`. The number should be the next number in the sequence and the name should be a short description of what the update does.

Keep in mind that the updates should not break the system if applied (accidentally twice) and should be idempotent. To ensure this is the case, it is recommended to use the `CREATE TABLE IF NOT EXISTS` syntax for creating tables and the `ALTER TABLE IF EXISTS` syntax for altering tables.

### General guidelines for the update scripts
- The update scripts should be written in SQL.
  - The update scripts should be idempotent.
    - For Creating tables, use something like the following:
        ```postgresql
          DO $$
          BEGIN
              IF NOT EXISTS (
                  SELECT 1
                  FROM information_schema.tables 
                  WHERE table_name = 'TABLE_NAME'
              ) THEN
                  CREATE TABLE your_table_name (
                      column1 data_type1,
                      column2 data_type2,
                      ...
                  );
              END IF;
          END $$;
          ```
    - For deleting tables, use something analogous to the above.
    - For adding columns, you can use the following:
      ```postgresql
      DO $$
      BEGIN
          IF NOT EXISTS (
              SELECT 1
              FROM information_schema.columns
              WHERE table_name = 'TABLE_NAME' 
              AND column_name = 'COLUMN_NAME'
          ) THEN
              ALTER TABLE TABLE_NAME ADD COLUMN COLUMNS_NAME data_type;
          END IF;
      END $$;
      ```
    - For removing columns, something analogous to the above can be used.
    - For Inserting data, use the following
        ```postgresql
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1
                FROM information_schema.tables 
                WHERE table_name = 'TABLE_NAME'
            ) THEN
                INSERT INTO TABLE_NAME (column1, column2, ...)
                VALUES (value1, value2, ...);
            END IF;
        END $$;
        ```
    - For Updating data, use:
      ```postgresql
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1
                FROM information_schema.tables 
                WHERE table_name = 'TABLE_NAME'
            ) THEN
                UPDATE TABLE_NAME
                SET column1 = value1, column2 = value2, ...
                WHERE some_column = some_value;
            END IF;
        END $$;
      ```
- The update scripts should be tested before being added to the repository.
- The update scripts should be reviewed by a second person before being added to the repository.
- The update scripts should be added to the repository in the correct order (no duplicate or missing numbers).


## Applying updates
To apply an update, simply run the `update.py` script in the `database` directory. This script will check the `database/updates` directory for any updates that have not been applied yet and apply them in order.

If you want to apply upto a specific update, you can run the `update.py` script with the `--update` flag followed by the number of the update you want to apply. For example:
```bash
python update.py --update X
```
Where `X` is the number of the update you want to apply.

If you want to apply all updates, you can run the `update.py` script with the `--all` flag. For example:
```bash
python update.py --all
```

note that the `--all` flag is the default behavior of the script, so you can also run the script without any flags to apply all updates.
