"""This module is the back-end file for 'TaskMaster'"""
# Use PEP 8
# Use logging module not print statements
# Use tick and cross symbols (✔/✖) in logging

import sqlite3 as sql
import os
import logging
import hashlib
import json

# Code relating to creating and managing Projects and Tasks


class Project:
    """This class provides functions for creating and managing a project with sqlite3"""

    def __init__(self) -> None:
        self.project_dir: str = ""
        self.user_id = 0
        self.user_name = ""
        self._user_auth = False
        self.project_id = 0
        self.project_name: str = ""
        self.project_db: sql.Connection

    def set_dir(self, project_dir) -> None:
        """Sets the working directory"""
        self.project_dir: str = project_dir

    def list_db(self) -> list:
        """Returns a list of DB files in project_dir"""

        files = os.listdir(self.project_dir)
        projects = []
        for file in files:
            if file.endswith(".db"):
                projects.append(file.removesuffix(".db"))

        return projects

    def create_db(self, file_name) -> bool:
        """Creates DB file, returns True if successful"""

        file_path = os.path.join(self.project_dir, file_name)
        logging.info("Creating DB: %s", file_path)
        # Checks if file already exists, Exits early if file already exists
        if True is os.path.isfile(file_path):
            logging.warning("File already exists")
            raise FileExistsError(f"File already exists: {file_path}")

        try:
            # Create DB File
            self.project_db = sql.connect(file_path)
            logging.info("DB connected ✔")

            self.project_db.execute("BEGIN TRANSACTION;")

            # User:
            self.project_db.execute("""CREATE TABLE "User" \
                    (ID INTEGER PRIMARY KEY NOT NULL UNIQUE, \
                    UserName      TEXT(20) UNIQUE,\
                    PassHash        CHAR(64));""")
            logging.info("User Table ✔")

            # Groups:
            self.project_db.execute("""CREATE TABLE "Group" \
                    (ID INTEGER PRIMARY KEY NOT NULL UNIQUE, \
                    groupName         TEXT(20) UNIQUE);""")
            logging.info("Group Table ✔")

            # Members:
            self.project_db.execute("""CREATE TABLE "Member" \
                    (ID INTEGER PRIMARY KEY NOT NULL UNIQUE, \
                    groupID         INT, \
                    memberID         INT, \
                    FOREIGN KEY(groupID) REFERENCES "Group"(ID) \
                    FOREIGN KEY(memberID) REFERENCES "User"(ID));""")
            logging.info("Member Table ✔")

            # Project:
            self.project_db.execute("""CREATE TABLE "Project" \
                    (ID INTEGER PRIMARY KEY NOT NULL UNIQUE, \
                    Name            TEXT(20), \
                    Description     TEXT(200), \
                    groupID         INT, \
                    FOREIGN KEY(groupID) REFERENCES "Group"(ID));""")
            logging.info("Project Table ✔")

            # Task:
            self.project_db.execute("""CREATE TABLE "Task" \
                    (ID INTEGER PRIMARY KEY NOT NULL UNIQUE, \
                    Name            TEXT(20),\
                    Description     TEXT(200), \
                    DateSet         DATE,\
                    DateDue         DATE,\
                    Complete        BINARY(1), \
                    projectID       INT,\
                    FOREIGN KEY(projectID) REFERENCES "Project"(ID));""")
            logging.info("Task Table ✔")

            self.project_db.commit()
        except sql.Error as e_thrown:
            self.project_db.close()
            logging.debug("exception while creating database: %s", e_thrown)
            logging.error("Error, Attempting to clean up:")
            try:
                os.remove(file_path)
            except os.error:
                logging.warning(
                    "Unable to remove \"%s\", Please remove manually.", file_path)

            logging.info("\"%s\" Removed", file_path)
            return False

        logging.info("DB Created ✔")
        self.project_db.close()
        return True

    def open_db(self, file_name) -> bool:
        """Open DB file, returns True if successful"""
        file_path = os.path.join(self.project_dir, file_name)

        if True is os.path.isfile(file_path):
            try:
                self.project_db = sql.connect(file_path)
            except sql.Error:
                logging.error("Unable to open DB")
                return False
        else:
            logging.error("File not found: %s", file_path)
            raise FileNotFoundError(f"No such file: {file_path}")

        logging.info("DB connected ✔")
        return True

    def delete_db(self, file_name) -> bool:
        """Deletes the DB {file_name}, return True if successful"""

        file_path = os.path.join(self.project_dir, file_name)
        if True is os.path.isfile(file_path):
            try:
                os.remove(file_path)
            except PermissionError:
                logging.warning(
                    "Unable to remove \"%s\", Please remove manually.", file_path)
                return False

            logging.info("\"%s\" Removed", file_path)
            return True
        else:
            logging.error("File not found: %s", file_path)
            raise FileNotFoundError(f"No such file: {file_path}")

    def join_group(self, user_name, group_name) -> bool:
        """Finds the user IDs corresponding to the username and group then creates a entry in the "Member" table to add user to group"""
        user_id: int = self.project_db.execute(
                f"""SELECT ID FROM "User" where UserName = "{user_name}";""").fetchone()[0]
        if user_id:
            try:
                group_id: int = self.project_db.execute(
                    f"""SELECT ID FROM "Group" where groupName = "{group_name}";""").fetchone()[0]
                self.project_db.execute("BEGIN TRANSACTION;")
                self.project_db.execute(
                    f"""INSERT INTO "Member" (groupID, memberID) VALUES({group_id},{user_id});""")
                self.project_db.commit()
            except sql.IntegrityError:
                logging.error("Unable to join group")
                self.project_db.rollback()
                return False
            return True
        else:
            return False

    def create_group(self, owner, group_name) -> bool:
        """creates a group with the name "group_name" and calls the "join_group function to add the group creator to the new group"""
        try:
            self.project_db.execute(
                f"""INSERT INTO "Group" (groupName) VALUES("{group_name}");""")
            self.project_db.commit()
            self.join_group(user_name=owner, group_name=group_name)
        except sql.IntegrityError as e_thrown:
            logging.error("Unable to create group: %s", e_thrown)
            self.project_db.rollback()
            return False
        return True

    def leave_group(self, group_id) -> bool:
        """Removes the logged in user from the group with the ID = group_id, Calls clean_up after running"""
        self.project_db.execute(f"""DELETE FROM "Member" where groupID = {
                                group_id} AND memberID = {self.user_id}""")
        self.clean_up()

    def create_user(self, user_name, user_password) -> bool:
        """Adds a new user to the DB and creates the users personal group"""
        password: str = user_password
        password_hasher = hashlib.sha256()
        password_hasher.update(password.encode())
        pass_hash = password_hasher.hexdigest()
        try:
            self.project_db.execute(
                f"""INSERT INTO "User" (UserName, PassHash) VALUES("{user_name}", "{pass_hash}");""")
        except sql.IntegrityError:
            logging.error(
                """Unable to add User: "%s" to database""", user_name)
            return False
        self.project_db.commit()
        self.create_group(owner=user_name, group_name=user_name)
        return True

    def login(self, user_name, user_password) -> bool:
        """Checks login credentials by hashing and comparing against DB values, sets the user authorisation flag to True if successful"""
        password: str = user_password
        password_hasher = hashlib.sha256()
        password_hasher.update(password.encode())
        pass_hash = password_hasher.hexdigest()
        user_id = self.project_db.execute(
            f"""SELECT ID FROM "User" where UserName = "{user_name}" and PassHash = "{pass_hash}";""").fetchone()
        if user_id is None:
            return False
        self.user_id: int = user_id[0]  # gets int from tuple
        self.user_name: str = user_name
        self._user_auth = True
        logging.info("Logged In")
        return True

    def logout(self):
        """De-authenticates the session"""
        self._user_auth = False
        logging.info("Logged Out")
        return True

    def remove_user(self) -> bool:
        """Removes the logged in user from the DB and calls the clean_up function"""
        if not self._user_auth:
            return False

        try:
            self.project_db.execute("BEGIN TRANSACTION;")
            self.project_db.execute(
                f"""DELETE FROM "Member" WHERE memberID = {self.user_id};""")
            self.project_db.execute(
                f"""DELETE FROM "User" WHERE ID = {self.user_id};""")
            self.project_db.commit()
            logging.info("User: %s Deleted from database")
        except sql.IntegrityError:
            logging.error(
                "Unable to delete user: %s from database", self.user_id)
            return False
        self.clean_up()
        return True

    def edit_user(self, new_name="", new_password="") -> bool:
        """Updates the users information in the database"""
        if not self._user_auth:
            return False

        new_pass_hash: str = ""
        to_edit: str = ""
        new_val: str = ""

        if new_password != "":
            password: str = new_password
            password_hasher = hashlib.sha256()
            password_hasher.update(password.encode())
            new_pass_hash = password_hasher.hexdigest()

        if new_name != "" and new_password != "":
            edit_both = True
            new_val = new_name
        elif new_name != "" and new_password == "":
            edit_both = False
            to_edit = "UserName"
            new_val = new_name
        elif new_name == "" and new_password != "":
            edit_both = False
            to_edit = "PassHash"
            new_val = new_pass_hash
        else:
            return True

        try:
            if edit_both:
                self.project_db.execute(
                    f"""UPDATE "User" set UserName = "{new_name}", PassHash = "{new_pass_hash}"  where ID = {self.user_id};""")
            else:
                self.project_db.execute(
                    f"""UPDATE "User" set {to_edit} = "{new_val}" where ID = {self.user_id};""")
            if edit_both or to_edit == "UserName":  # Update group name
                self.project_db.execute(f"""UPDATE "Group" SET groupName = "{
                                        new_val}" where groupName = "{self.user_name}";""")
        except sql.IntegrityError:
            logging.error("Unable to edit User: %s", self.user_id)
            return False
        self. project_db.commit()
        return True

    def list_groups(self) -> list:
        """Returns a list of groups that the logged in user is part of"""
        if not self._user_auth:
            return []
        groups = self.project_db.execute(
            f"""SELECT "Group".ID, groupName FROM "Group" \
                INNER JOIN "Member" on "Member".groupID = "Group".ID \
                where "Member".memberID = {self.user_id};""").fetchall()
        return groups

    def get_group_id(self, name):
        """Returns the ID corresponding to a group name"""
        if name == "Default":
            name = self.user_name
        group_id = self.project_db.execute(
            f"""SELECT ID, groupName FROM "Group" where groupName = "{name}";""").fetchone()
        return group_id[0]

    def de_tuple(self, list_of_tuples, extract_element=1) -> list:
        """Takes the lists of tuples outputted by sqlite3 fetch functions and extracts the tuple in the "extract_element" position"""
        output = []
        for i in list_of_tuples:
            output.append(i[extract_element])
        return output

    def list_project(self) -> list:
        """Returns a list of projects owned by the current user, or without owner

        Returns:
            list: a list of projects, items in the list are tuples with the structure [0]ID, [1]Name
        """

        project = self.project_db.execute(
            f"""SELECT Project.ID, Name FROM Project \
                INNER JOIN "Group" on Project.groupID = "Group".ID \
                INNER JOIN "Member" on "Member".groupID = "Group".ID \
                where memberID = {self.user_id};""").fetchall()
        return project

    def search_projects(self, search) -> list:
        """Returns list of tuples of projects in current DB meeting search criteria"""

        if self._user_auth is not True:
            return []

        project = self.project_db.execute(
            f"""SELECT Project.ID, Name FROM Project \
                INNER JOIN "Group" on Project.groupID = "Group".ID \
                INNER JOIN "Member" on "Member".groupID = "Group".ID \
                where Name like "%{search}%" AND memberID = {self.user_id};""").fetchall()
        return project

    def project_data(self, project_id, percentage_complete=True) -> list:
        """Returns all entries for a project"""
        project = self.project_db.execute(
            f"""SELECT Name,Description,groupName FROM Project \
                INNER JOIN "Group" on Project.groupID = "Group".ID \
                where Project.ID={project_id};""").fetchone()
        if percentage_complete:
            project = list(project)  # Convert to list to append later
            tasks_in_project = self.project_db.execute(
                f"""SELECT COUNT(ID) FROM Task where projectID = {project_id};""").fetchone()
            tasks_complete = self.project_db.execute(
                f"""SELECT COUNT(ID) FROM Task where projectID = {project_id} and Complete = True;""").fetchone()
            if tasks_complete[0] > 0 and tasks_in_project[0] > 0:
                completeness = round(
                    tasks_complete[0]/tasks_in_project[0] * 100, 2)
            else:
                completeness = 0
            logging.debug("%s complete", completeness)
            project.append(completeness)
        return project

    def create_project(self, project_name, description, group_id) -> bool:
        """Creates a mew project

        Args:
            project_name (string): name of the project, mas 20 char long
            description (string): description of the project, max 200 char long

        Returns:
            bool: Status of the operation (True=Successful)
        """

        try:
            self.project_db.execute(
                f"""INSERT INTO Project (Name, Description, groupID) \
                    VALUES("{project_name}", "{description}", {group_id});""")
        except sql.Error as e_thrown:
            logging.error(f"Unable to add  \
            {project_name} to database: {e_thrown}")
            return False
        self.project_db.commit()
        return True

    def current_project(self, project_id, project_name) -> None:
        """Sets Current Project"""
        self.project_id = project_id
        self.project_name = project_name

    def edit_project(self, project_name, description, group_id, project_id) -> bool:
        """Edits Project with id = project_id, all arguments should be set even if not being changed

        Returns:
            bool: Status of the operation (True=Successful)
        """
        try:
            self.project_db.execute(
                f"UPDATE Project set Name = '{project_name}', Description = '{description}', groupID = {group_id} \
                where ID = {project_id};")
        except sql.Error:
            logging.error("Unable to edit %s in database", project_name)
            return False
        self.project_db.commit()
        return True

    def delete_project(self, project_id) -> bool:
        """Deletes the project with id = project_id

        Args:
            project_id (int): Unique id of the project to be deleted

        Returns:
            bool: Status of the operation (True=Successful)
        """
        try:
            self.project_db.execute("BEGIN TRANSACTION;")
            self.project_db.execute(
                f"""DELETE FROM Task WHERE ProjectID = {project_id};""")
            self.project_db.execute(
                f"""DELETE FROM Project WHERE ID = {project_id};""")
            self.project_db.commit()
            logging.info("%s Deleted from database")
        except sql.Error:
            logging.error("Unable to delete %s from database", project_id)
            return False
        return True

    def list_tasks(self) -> list:
        """Returns a list of tasks in the project

        Returns:
            list: a list of tasks, items in the list are tuples with the structure [0]ID, [1]Name
        """

        tasks = self.project_db.execute(f"""SELECT ID, Name FROM Task \
                                        WHERE projectID = {self.project_id};""").fetchall()
        return tasks

    def task_data(self, task_id) -> tuple:
        """Returns a tuple containing the task data for the task with id = task_id

        Args:
            task_id (int): Unique id of the desired task

        Returns:
            tuple: [0]Name, [1]Description, [2]DateDue, [3]Complete
        """
        return self.project_db.execute(f"""SELECT Name, Description, DateDue, Complete from Task where ID = {task_id};""").fetchone()

    def search_tasks(self, search):
        """Returns a list of tasks matching the search criteria

        Args:
            search (string): Search string

        Returns:
            list: list of matching tasks
        """
        tasks = self.project_db.execute(f"""SELECT ID, Name FROM Task \
                                        WHERE projectID = {self.project_id} and Name like "%{search}%";""").fetchall()
        return tasks

    def create_task(self, task_name, task_description, date_set, date_due, complete) -> bool:
        """Creates Task within Current Project, returns True if successful

        Args:
            task_name (string)
            task_description (string)
            date_set (date)
            date_due (date)
            complete (bool)

        Returns:
            bool: Status of the operation (True=Successful)
        """

        try:
            self.project_db.execute(f"""INSERT INTO Task (Name, Description, DateSet, DateDue, Complete, projectID) \
                                    VALUES("{task_name}", "{task_description}", "{date_set}", "{date_due}", {complete}, {self.project_id});""")
        except sql.Error:
            logging.error("Unable to create task: %s in Project: %s",
                          task_name, self.project_name)
            return False

        self.project_db.commit()
        return True

    def edit_task(self, task_id, task_name, task_description, date_due, complete) -> None:
        """Edit the task with id = task_id, all arguments should be set even if not being changed
        Args:
            task_id (int): Unique id of the task to be edited
            task_name (string)
            task_description (string)
            date_due (datetime.date)
            complete (bool)
        """

        try:
            self.project_db.execute(
                f"""UPDATE Task set Name = "{task_name}", Description = "{task_description}", \
                DateDue = "{date_due}", Complete = {complete} where ID = {task_id};""")
        except sql.Error:
            logging.error("Unable to edit task: %s in Project: %s",
                          task_name, self.project_name)
            return False

        self.project_db.commit()
        return True

    def delete_task(self, task_id) -> bool:
        """Deletes the task with id = task_id
        Args:
            task_id (int): Unique id of the task to be deleted

        Returns:
            bool: Status of the operation (True=Successful)
        """
        try:
            self.project_db.execute(
                f"""DELETE FROM Task WHERE ID = {task_id};""")
        except sql.IntegrityError:
            logging.error("Unable to delete %s from database", task_id)
            return False

        self.project_db.commit()
        return True

    def clean_up(self) -> None:
        """Removes orphaned entities"""

        # Check for orphans:
        groups = self.de_tuple(self.list_groups(), extract_element=0)
        # Checks if a group has members, If a group has no members then the group will be deleted
        for group_id in groups:
            members = self.project_db.execute(
                f"""SELECT COUNT(ID) FROM "Member" where groupID = {group_id};""").fetchone()
            if members[0] == 0:
                # Get the projects owned by the group:
                projects = self.project_db.execute(
                    f"""SELECT Project.ID FROM Project where groupID = {group_id};""").fetchall()
                projects = self.de_tuple(projects, extract_element=0)
                for project_id in projects:
                    self.delete_project(project_id)

    def exit(self) -> bool:
        """Closes open database, Returns true if successful

        Returns:
            bool: Status of the operation (True=Successful)
        """
        try:
            self.project_db.close()
        except sql.Error:
            logging.error("Error closing database")
            return False

        return True


class Settings:
    """This class is responsible for reading from and updating the config.json file"""

    def __init__(self):
        """Initialises the Settings class with directory of config file"""
        self.file = "config.json"
        self._settings_json: str
        self.settings: dict = {
            "Note to user": "Please do not edit this file directly",
            "Theme": "System",
            "Debug": 20
        }
        self.read()

    def read(self) -> None:
        """Reads from the config.json file and stores the values in the self.settings dictionary"""
        if os.path.isfile(self.file):
            with open(self.file, "rt", encoding="utf-8") as settings_file:
                self._settings_json = settings_file.read()
            self.settings = json.loads(self._settings_json)
            self.check()
        else:
            # set defaults
            self.write()

    def write(self) -> None:
        """Writes the key:value pairs in self.settings to the config.json file"""
        self._settings_json = json.dumps(self.settings)
        with open(self.file, "wt", encoding="utf-8") as settings_file:
            settings_file.write(self._settings_json)

    def check(self) -> None:
        """Checks the values read from the config and corrects erroneous data"""
        error_flag = False
        if self.settings["Debug"] not in range(51):
            self.settings["Debug"] = 20
            error_flag = True
        if self.settings["Theme"] not in ("System", "Dark", "Light"):
            self.settings["Theme"] = "System"
            error_flag = True
        if error_flag is True:
            self.write()
