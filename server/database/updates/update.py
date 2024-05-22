from models.CoCoConfig import CoCoConfig
from sqlalchemy import create_engine
from sqlalchemy.exc import OperationalError
import argparse
import os

config = CoCoConfig()


# TODO: get the connection like this for now but change it to use a central connection pool (maybe)
def __get_database_engine() -> create_engine:
    """
    Get the connection to the database
    :return: the connection to the database
    """
    try:
        engine = create_engine(config.database_url)
        return engine
    except OperationalError as e:
        print("Error connecting to the database")
        print(e)
        exit(1)


def __get_list_of_update_paths() -> list[str]:
    """
    Get the list of paths to the update files
    :return: the list of paths to the update files
    """
    files = [f for f in os.listdir("./updates") if os.path.isfile(os.path.join("./updates", f))]
    files = sorted([f for f in files if f.endswith(".sql")], key=lambda x: int(x.split("_")[1]))
    return files


def __update_to_desired_version(v: int = -1):
    """
    Update the database to the desired version
    :param v: the version to update to
    """
    engine = __get_database_engine()

    updated_to = -1

    list_of_updates = __get_list_of_update_paths()
    print(list_of_updates)
    try:
        with engine.connect() as connection:
            with connection.begin():
                for update in list_of_updates:
                    v_update = int(update.split("_")[1].split(".")[0])
                    if v_update > v:
                        break
                    with open(f"./updates/{update}", "r") as f:
                        sql = f.read()
                        connection.execute(sql)
                        updated_to = v_update
            connection.close()
        print("Database updated to version", updated_to)
    except Exception as e:
        print("Error updating the database")
        print("Updates were made up to version", updated_to)
        print(e)
        exit(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--update", type=int, help="Specify the version number to update to")
    parser.add_argument("--all", action="store_true", help="Update to the latest versions")
    args = parser.parse_args()

    if args.update is not None:
        version = args.update
        assert version >= 1, "Version must be greater than or equal to 1"
        print("Updating to version", version)
        __update_to_desired_version(version)
    elif args.all or (not args.update and not args.all):
        print("Updating to the latest versions")
        __update_to_desired_version()
    else:
        print("Please pass either the --update flag or the --all flag")
        exit(1)
