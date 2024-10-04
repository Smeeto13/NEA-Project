import src.lib_file as lib_file
import csv
import os

users_data_file = "MOCK_USERS_DATA.csv"

db = lib_file.Project()

# Setup
db.set_dir("Tests")
if True is os.path.isfile("Tests/test.db"):
    print("Cleaning up old tests")
    assert db.delete_db("test.db") is True

    print("Creating DB to use for tests")
    assert db.create_db("test.db") is True

    print("Opening DB:")
    assert db.open_db("test.db") is True

# Add data
with open(data_file, "r") as data:
    for line in csv.DictReader(data):
        assert db.create_user(line["Uname"], line["Password"]) is True
        assert db.login(line["Uname"], line["Password"]) is True

