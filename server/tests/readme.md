#### `tests`
Tests to be used with `pytest`. 

###### Usage
Ensure that you are on a Linux environment with the necessary hardware (2 Nvidia GPUs with ~12GB VRAM each). To run all tests:

First navigate to the tests directory:
```bash
$ cd coco/server/tests
```

For now it's not automated, so create DBs and populate them:
```
# Start the psql server
sudo service postgresql start

# Create the DBs
sudo -u postgres createdb coco_test  
sudo -u postgres createdb coco

# Navigate to the database folder
cd coco/server/database

# Populate the DBs with the init.sql file
sudo -u postgres psql -d coco -f init.sql
sudo -u postgres psql -d coco_test -f init.sql
```

Then run the following command:

```bash
$ pytest
```

Or, to run specific tests:

```bash
$ pytest test_main.py -k 'test_homepage'
```
