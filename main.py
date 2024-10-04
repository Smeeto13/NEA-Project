"""Main python file for "TaskMaster" project management """

# Backend imports:
from datetime import date
from datetime import datetime
import logging

# GUI:
from tkinter import messagebox
from customtkinter import *
from tkcalendar import DateEntry

# Third-party modules
from PIL import Image
import src.lib_file as lib_file

# Global Variables (Constants):
PROGRAM_NAME = "TaskMaster"
VERSION_NUMBER = "V2"


class ScrollList(CTkScrollableFrame):
    """Creates a GUI list with scroll bar from passed list, when a item is selected "master.select" is called with the value of the selected button"""

    def __init__(self, master, to_list: list):
        super().__init__(master)

        # configure grid system
        self.grid_columnconfigure(0, weight=1)

        for i, value in enumerate(to_list):
            select = CTkButton(self, text=value, corner_radius=20,
                               command=lambda value=value: master.select(value))
            select.grid(row=i, column=0, pady=(10, 0), sticky="ew")
            master.buttons[value] = select


class FrameBase(CTkFrame):
    """Base Class for frames in this program"""

    def __init__(self, master) -> None:
        super().__init__(master)

        # Objects
        self.app: APP = master
        self.frame_manager: FrameManager = master.frame_manager
        self.config: lib_file.Settings = master.config
        self.projects_do: lib_file.Project = master.projects_do
        # Variables
        self.page_title: CTkLabel
        self.selected: str = ""
        self.last_selection: str = ""
        self.buttons: dict = {}
        self.static_buttons: dict = {}
        self.list_frame: ScrollList
        self.on_selection_flag: bool
        self.columns = 3
        self.rows = 3
        self.list_c_span = 3
        self.list_r_span = 1
        self.list_row = 2
        self.list_col = 0
        self.button_row = 2

    def configure_frame(self, columns=3, rows=3, list_c_span=3, list_r_span=1, list_row=1, list_col=0, button_row=2, has_list=True):
        """Specifies the frame parameters"""
        self.columns = columns
        self.rows = rows

        for column in range(self.columns):
            self.grid_columnconfigure(column, weight=1)
        for row in range(self.rows):
            self.grid_rowconfigure(row, weight=1)

        self.list_c_span = list_c_span
        self.list_r_span = list_r_span
        self.list_row = list_row
        if has_list:
            self.grid_rowconfigure(self.list_row, weight=2)
        self.list_col = list_col
        self.button_row = button_row

    def set_title(self, title, font_size=32):
        """Sets the Title for the frame

        Args:
            title (string): The frame title
            font_size (int): The font size
        """
        self.page_title = CTkLabel(
            self, text=title, font=("Mogra", font_size))
        self.page_title.grid(
            row=0, column=0, columnspan=self.columns, sticky="ew")

    def button_auto_grid(self):
        """Places buttons in the list "self.static_buttons" on the frame"""
        for i, button in enumerate(self.static_buttons.values()):
            button.grid(row=self.button_row, column=i, padx=5, sticky="ew")

    def list_data(self):
        """Function used to get the data to list, Should be overwritten by child class"""
        raise NotImplementedError

    def fresh_list(self, to_list=""):
        """Creates a scrollable list

        Args:
            to_list (list): Items to be listed, if omitted then the self.list_data method is used
        """
        if hasattr(self, "list_frame"):  # If a list frame already exists it will be destroyed
            self.list_frame.destroy()

        if to_list == "":
            to_list = self.list_data()

        logging.info("Scroll list: %s", to_list)

        self.list_frame = ScrollList(master=self, to_list=to_list)
        self.list_frame.grid(row=self.list_row, column=self.list_col, rowspan=self.list_r_span, columnspan=self.list_c_span,
                             padx=10, pady=5, sticky="nsew")

    def on_selection(self):
        """Handles button selection, Should be overwritten by child class"""
        raise NotImplementedError

    def select(self, selection):
        """Selects a list item and enables buttons requiring a selection to function

        Args:
            selection (any): New selection
        """

        self.selected = selection

        if self.on_selection_flag is True:
            self.on_selection()

        logging.info("selected %s", selection)

        # Checks for current selection and deselects it
        if self.last_selection:
            logging.info("Last selected %s", self.last_selection)
            self.buttons[self.last_selection].configure(state=NORMAL)

        self.buttons[self.selected].configure(state=DISABLED)

        # Enables buttons that require a selection to function
        for button in self.static_buttons.values():
            if button.cget("state") == DISABLED:
                button.configure(state=NORMAL)

        self.last_selection = self.selected

    def clear_select(self):
        """Clears the current selection and disables buttons (except those marked with "_")"""
        self.selected = ""
        self.last_selection = ""

        # Disables buttons when there is no selection
        for name, button in self.static_buttons.items():
            if button.cget("state") == NORMAL and "_" not in name:
                button.configure(state=DISABLED)


class StartFrame(CTkFrame):
    """Start 'Page' where user selects working directory"""

    def __init__(self, app):
        super().__init__(app)

        self.grid_rowconfigure((0, 1), weight=1)  # configure grid system
        self.grid_columnconfigure((0, 1, 2), weight=1)

        self.logo = CTkImage(light_image=Image.open("Logos/Light-Mode.png"),
                             dark_image=Image.open("Logos/Dark-Mode.png"),
                             size=(783, 126))
        # display image with a CTkLabel
        self.image_logo = CTkLabel(self, image=self.logo, text="")
        self.image_logo.grid(row=0, column=1)

        self.open_db = CTkButton(
            self, text="Open", corner_radius=20, command=app.open_dir)
        self.open_db.grid(row=1, column=1)


class FilesFrame(FrameBase):
    """Project 'Page' for managing project files"""

    def __init__(self, master):
        super().__init__(master)
        self.on_selection_flag = False

        # configure frame
        self.configure_frame(columns=3, rows=3, list_c_span=3,
                             list_r_span=1, list_row=1, list_col=0, button_row=2, has_list=True)

        # Title
        self.set_title(title="Project Files:")

        # Project files list
        self.fresh_list()

        # Buttons
        create_db = CTkButton(
            self, text="Create", corner_radius=20, command=self.create_file)
        self.static_buttons["_create"] = create_db

        open_db = CTkButton(
            self, text="Open", corner_radius=20, state=DISABLED, command=self.open_file)
        self.static_buttons["open"] = open_db

        remove_db = CTkButton(
            self, text="Delete", corner_radius=20, state=DISABLED, command=self.remove_file)
        self.static_buttons["remove"] = remove_db

        self.button_auto_grid()

    def list_data(self):
        files = self.projects_do.list_db()
        logging.info("Files Found: %s", files)
        return files

    def open_file(self):
        """Opens the file passed as a parameter and progress to Projects frame"""
        file_name = self.selected + ".db"
        try:
            self.projects_do.open_db(file_name)
        except FileNotFoundError:
            messagebox.showerror(title="Open Error",
                                 message="File not found")
            return False

        # Destroy files frame and show login_frame
        self.frame_manager.show_frame(
            "login_frame", "files_frame", destroy=True)

        return True

    def create_file(self):
        """Creates a new Projects database file and refreshes list frame"""
        dialog = CTkInputDialog(text="Name the file:",
                                title="New Projects File")
        file_name = dialog.get_input()  # waits for input
        if file_name:
            try:
                file_name = file_name + ".db"
                if not self.projects_do.create_db(file_name):
                    messagebox.showwarning(
                        title="Create Error", message="Unable to create file, Please check error log")
            except FileExistsError:
                messagebox.showwarning(
                    title="Create Error", message="File Exists")

        self.fresh_list()

    def remove_file(self):
        """Deletes the file passed as a parameter"""
        file_name = self.selected + ".db"
        try:
            self.projects_do.delete_db(file_name)
            messagebox.showinfo(title="Delete File", message="File Deleted")
        except PermissionError:
            messagebox.showerror(title="Delete File",
                                 message="Unable to Delete File")

        self.fresh_list()
        self.clear_select()


class LoginFrame(CTkFrame):
    """Login frame"""

    def __init__(self, app):
        super().__init__(app)
        self.frame_manager: FrameManager = app.frame_manager
        self.projects_do: lib_file.Project = app.projects_do
        self.app: APP = app

        self.grid_rowconfigure((0, 5), weight=1)  # configure grid system
        self.grid_columnconfigure((1, 2), weight=1)

        self.page_title = CTkLabel(
            self, text="Login:", font=("Mogra", 36))
        self.page_title.grid(row=0, column=1, columnspan=2, sticky="sew")

        self.username_entry = CTkEntry(self, placeholder_text="Username")
        self.username_entry.grid(
            row=1, column=1, columnspan=2, sticky="s", pady=(5, 3))

        self.password_entry = CTkEntry(
            self, show="*", placeholder_text="Password")
        self.password_entry.grid(row=2, column=1, columnspan=2, sticky="ns")
        # lambda used to prevent passing "event" to app.login()
        self.password_entry.bind("<Return>", lambda event: self.login())

        self.login_button = CTkButton(
            self, text="Login", corner_radius=20, command=self.login)
        self.login_button.grid(
            row=3, column=1, columnspan=2, sticky="ns", pady=(3, 3))

        self.new_user_button = CTkButton(
            self, text="New User", corner_radius=20, command=self.user_create)
        self.new_user_button.grid(row=4, column=1, columnspan=2, sticky="n")

    def login(self):
        """pass credentials to backend and progresses to the home frame if login successful"""
        username = self.username_entry.get()
        password = self.password_entry.get()
        if self.projects_do.login(username, password) is False:
            messagebox.showerror(title="Login",
                                 message="Incorrect username or password")
            return 0
        self.app.set_username(username)
        self.frame_manager.show_frame(
            "home_frame", "login_frame", destroy=True)

    def user_create(self):
        """pass credentials to backend and creates a new user"""
        username = self.username_entry.get()
        password = self.password_entry.get()
        if username and password:
            if self.projects_do.create_user(username, password) is False:
                messagebox.showerror(title="User Creation",
                                     message="Unable to create user, perhaps they already exist?")
                return False
            messagebox.showinfo(title="User Creation",
                                message="User created ✔")
            logging.info("""User created: "%s" ✔""", username)
            return True
        else:
            messagebox.showerror(title="User Creation",
                                 message="Unable to create user, Please enter a Username AND Password")
            return False


class HomeFrame(CTkFrame):
    """Home Frame"""

    def __init__(self, master):
        super().__init__(master)
        self.app: APP = master
        self.frame_manager = master.frame_manager
        self.projects_do: lib_file.Project = master.projects_do

        # configure grid system
        self.grid_rowconfigure((0, 1, 2, 3), weight=1)
        self.grid_columnconfigure((0, 1), weight=4)
        self.grid_columnconfigure((2, 3), weight=1)

        self.page_title = CTkLabel(
            self, text="Home:", font=("Mogra", 36))
        self.page_title.grid(row=0, column=0, columnspan=4, sticky="sew")

        self.username_entry = CTkEntry(self, placeholder_text="Username")
        self.username_entry.grid(
            row=1, column=0, columnspan=2, sticky="nsew", pady=3)

        self.password_entry = CTkEntry(
            self, show="*", placeholder_text="Password")
        self.password_entry.grid(
            row=2, column=0, columnspan=2, sticky="nsew", pady=3)

        self.edit_button = CTkButton(
            self, text="Edit", corner_radius=20, command=self.user_edit)
        self.edit_button.grid(
            row=3, column=0, columnspan=1, sticky="ew", padx=(6, 3))

        self.remove_button = CTkButton(
            self, text="Remove", corner_radius=20, command=self.user_remove)
        self.remove_button.grid(
            row=3, column=1, columnspan=1, sticky="ew", padx=(3, 3))

        self.groups_button = CTkButton(self, text="Groups", corner_radius=20,
                                       command=lambda: self.frame_manager.show_frame("groups_frame", "home_frame"))
        self.groups_button.grid(
            row=3, column=2, columnspan=1, sticky="ew", padx=(3, 3))

        self.settings_button = CTkButton(
            self, text="Settings", corner_radius=20, command=lambda: self.frame_manager.show_frame("settings_frame", "home_frame"))
        self.settings_button.grid(
            row=3, column=3, sticky="ew", padx=(3, 6))

        self.goto_projects_button = CTkButton(
            self, text="View Projects", corner_radius=20, command=lambda: self.frame_manager.show_frame("projects_frame", "home_frame"))
        self.goto_projects_button.grid(
            row=1, column=2, columnspan=2, sticky="nsew", padx=(3, 6), pady=3)

        self.logout_button = CTkButton(
            self, text="Logout", corner_radius=20, command=self.logout)
        self.logout_button.grid(
            row=2, column=2, columnspan=2, sticky="nsew", padx=(3, 6), pady=3)

    def user_edit(self):
        """Edits the user using parameters in entry boxes"""
        name = self.username_entry.get()
        password = self.password_entry.get()
        self.projects_do.edit_user(name, password)
        self.logout()

    def user_remove(self):
        """Deletes the logged in user"""
        if self.projects_do.remove_user() is False:
            logging.error("Unable to remove user!")
            messagebox.showerror(title="User Deletion",
                                 message="Unable to delete user, See log")
        self.logout()

    def logout(self):
        """Destroy all frames and show start frame"""
        self.frame_manager.show_frame("start_frame", "all", destroy=True)

        self.projects_do.logout()


class GroupsFrame(FrameBase):
    """Frame for managing groups"""

    def __init__(self, app):
        super().__init__(app)
        self.on_selection_flag = False

        # configure frame
        self.configure_frame(columns=4, rows=3, list_c_span=4,
                             list_r_span=1, list_row=1, list_col=0, button_row=2, has_list=True)

        # Title
        self.set_title(title="Groups:")

        # Project files list
        self.fresh_list()

        # Buttons
        create_group_button = CTkButton(
            self, text="Create", corner_radius=20, command=self.create_group)
        self.static_buttons["_create"] = create_group_button

        add_to_group_button = CTkButton(
            self, text="Add User", corner_radius=20, state=DISABLED, command=self.join_group)
        self.static_buttons["add"] = add_to_group_button

        leave_group_button = CTkButton(
            self, text="Leave", corner_radius=20, state=DISABLED, command=self.leave_group)
        self.static_buttons["leave"] = leave_group_button

        back_button = CTkButton(
            self, text="Back", corner_radius=20, command=lambda: self.master.frame_manager.show_frame("home_frame", "groups_frame"))
        self.static_buttons["_back"] = back_button

        self.button_auto_grid()

    def list_data(self) -> list:
        groups: list = self.projects_do.list_groups()
        logging.info("Member of groups: %s", groups)
        return groups

    def create_group(self) -> None:
        """Prompts for user input of group name and creates the group"""
        dialog = CTkInputDialog(text="Name the group:",
                                title="New Group")
        group_name = dialog.get_input()  # waits for input
        if group_name:
            self.projects_do.create_group(self.app.username, group_name)
            self.fresh_list()

    def join_group(self) -> None:
        """Prompts for a username to grant access to the group"""
        dialog = CTkInputDialog(text="Enter the Username to add:",
                                title="Add to group")
        username_to_add = dialog.get_input()  # waits for input
        if username_to_add:
            if self.projects_do.join_group(username_to_add, self.selected[1]) is not True:
                messagebox.showerror(title="Add to Group",
                                     message="No user with that name")

    def leave_group(self) -> None:
        """Removes the logged in user from the group"""
        # self.selected[0] represents the group ID and is the same number as displayed next to the Group name in the GUI
        self.projects_do.leave_group(self.selected[0])
        self.fresh_list()


class ThemesSubFrame(FrameBase):
    """Sub Frame intended to be placed on another frame, used for selecting the theme to use"""

    def __init__(self, master, app):
        super().__init__(master)
        self.on_selection_flag = True
        self.app: APP = app
        self.config: lib_file.Settings = app.config
        # configure frame
        self.configure_frame(columns=1, rows=2, list_c_span=1,
                             list_r_span=1, list_row=1, list_col=0, button_row=2, has_list=True)

        self.set_title("Themes:", font_size=25)
        self.fresh_list()

    def list_data(self):
        return ["System", "Light", "Dark"]

    def on_selection(self):
        theme = self.selected
        self.app.change_theme(theme)
        logging.info("set appearance mode to %s", theme)
        self.config.settings["Theme"] = theme


class DebugSubFrame(FrameBase):
    """Sub Frame intended to be placed on another frame, used for selecting the debug level"""

    def __init__(self, master, app):
        super().__init__(master)
        self.on_selection_flag = True
        self.app: APP = app
        self.config = app.config

        # configure frame
        self.configure_frame(columns=1, rows=2, list_c_span=1,
                             list_r_span=1, list_row=1, list_col=0, button_row=2, has_list=True)

        self.set_title("Debug Level:", font_size=25)
        self.fresh_list()

    def list_data(self):
        return ["Debug", "Info", "Warning",
                "Error", "Critical"]

    def on_selection(self):
        match self.selected:
            case "Debug":
                self.config.settings["Debug"] = logging.DEBUG
            case "Info":
                self.config.settings["Debug"] = logging.INFO
            case "Warning":
                self.config.settings["Debug"] = logging.WARNING
            case "Error":
                self.config.settings["Debug"] = logging.ERROR
            case "Critical":
                self.config.settings["Debug"] = logging.CRITICAL


class SettingsFrame(CTkFrame):
    def __init__(self, app):
        super().__init__(app)
        self.app: APP = app
        self.config: lib_file.Settings = app.config
        self.frame_manager: FrameManager = app.frame_manager
        self.projects_do: lib_file.Project = app.projects_do

        self.grid_rowconfigure((0, 2), weight=1)  # configure grid system
        self.grid_rowconfigure(1, weight=2)
        self.grid_columnconfigure((0, 1), weight=1)

        self.page_title = CTkLabel(
            self, text="Settings:", font=("Mogra", 36))
        self.page_title.grid(row=0, column=0, columnspan=2, sticky="sew")

        self.themes = ThemesSubFrame(self, self.app)
        self.themes.grid(column=0, row=1, sticky="nsew")

        self.debug = DebugSubFrame(self, self.app)
        self.debug.grid(column=1, row=1, sticky="nsew")

        self.save_button = CTkButton(
            self, text="Save", corner_radius=20, command=self.config.write)
        self.save_button.grid(row=2, column=0, padx=5, sticky="ew")

        self.back_button = CTkButton(
            self, text="Back", corner_radius=20, command=lambda: self.frame_manager.show_frame("home_frame", "settings_frame"))
        self.back_button.grid(row=2, column=1, padx=5, sticky="ew")


class ProjectData(CTkFrame):
    """Frame for creating and editing tasks"""

    def __init__(self, master, groups: list, name_text="Name"):
        super().__init__(master)

        self.name_var = StringVar(value=name_text)
        self.desc_var = StringVar(value="Description")
        self.group_var = StringVar(value="Default")
        self.percentage_complete_var = StringVar(value="0% Complete")

        # configure grid system
        self.grid_rowconfigure((0, 1, 2, 3), weight=1)
        self.grid_columnconfigure(0, weight=1)

        self.name = CTkEntry(
            self, textvariable=self.name_var, corner_radius=5)
        self.name.grid(column=0, row=0, sticky="nsew")

        self.desc = CTkEntry(
            self, textvariable=self.desc_var, corner_radius=5)
        self.desc.grid(column=0, row=1, sticky="nsew", pady=10)

        self.group_select = CTkOptionMenu(
            self, values=groups, variable=self.group_var, corner_radius=5)
        self.group_select.grid(column=0, row=2, sticky="nsew", pady=10)

        self.percentage_complete = CTkLabel(
            self, textvariable=self.percentage_complete_var, corner_radius=5)
        self.percentage_complete.grid(column=0, row=3, sticky="nsew", pady=10)

    def get_name(self):
        """
        Returns:
            String: Name from entry box
        """
        return self.name_var.get()

    def get_desc(self):
        """
        Returns:
            String: Description from entry box
        """
        return self.desc_var.get()

    def get_group(self):
        """
        Returns:
            String: Group Name
        """
        return self.group_var.get()

    def set_name(self, name_text):
        """Displays the passed "name_text" in the Project Name entry box

        Args:
            name_text (String): The text to be displayed
        """
        self.name_var.set(name_text)

    def set_desc(self, desc_text):
        """Displays the passed "desc_text" in the Project Description entry box

        Args:
            desc_text (String): The text to be displayed
        """
        self.desc_var.set(desc_text)

    def set_group(self, group_name):
        """Displays the passed "group_text" in the Project group entry box
        Args:
            group_name (String): The text to be displayed
        """
        self.group_var.set(group_name)

    def set_percentage_complete(self, percentage):
        self.percentage_complete_var.set(f"{percentage}% Complete")


class ProjectFrame(FrameBase):
    """Project 'Page' for managing projects in file"""

    def __init__(self, app):
        super().__init__(app)
        self.on_selection_flag = True

        # configure frame
        self.configure_frame(columns=5, rows=3, list_c_span=3,
                             list_r_span=1, list_row=2, list_col=0, button_row=3, has_list=True)

        # Title
        self.set_title(title="Projects:")

        # Search
        self.search_bar = CTkEntry(
            self, placeholder_text="Search", corner_radius=5)
        self.search_bar.grid(row=1, columnspan=5,
                             sticky="nsew", padx=10)
        self.search_bar.bind(
            '<Return>', self.search_projects)

        # Project in file
        self.fresh_list()

        # Create Project
        groups = self.projects_do.de_tuple(
            self.projects_do.list_groups())
        self.project_data = ProjectData(self, groups, name_text="Project Name")
        self.project_data.grid(row=2, column=3, columnspan=2,
                               padx=10, pady=5, sticky="nsew")

        # Buttons
        new_project_button = CTkButton(
            self, text="New", corner_radius=20, command=self.create_project)
        self.static_buttons["_new"] = new_project_button

        open_project_button = CTkButton(
            self, text="Open", corner_radius=20, state=DISABLED, command=lambda: self.open_project(self.selected))
        self.static_buttons["open"] = open_project_button

        edit_project_button = CTkButton(
            self, text="Edit", corner_radius=20, state=DISABLED, command=self.edit_project)
        self.static_buttons["edit"] = edit_project_button

        remove_project_button = CTkButton(
            self, text="Delete", corner_radius=20, state=DISABLED, command=self.remove_project)
        self.static_buttons["remove"] = remove_project_button

        home_button = CTkButton(
            self, text="home", corner_radius=20, command=lambda: self.frame_manager.show_frame("home_frame", "projects_frame", destroy=True))
        self.static_buttons["_home"] = home_button

        self.button_auto_grid()

    def list_data(self):
        projects = self.projects_do.list_project()
        logging.info("Projects Found: %s", projects)
        return projects

    def search_projects(self, event):
        """Updates the project list with projects meeting search in self.search_bar

        Args:
            event: passed by tk bind, logged for debug purposes
        """
        logging.debug(event)

        projects = self.projects_do.search_projects(
            self.search_bar.get())
        logging.info("Projects Found: %s", projects)
        self.fresh_list(projects)

    def on_selection(self):
        """Updates fields in project_data frame with currently selected project data"""
        data = self.projects_do.project_data(self.selected[0])
        name: str = data[0]
        desc: str = data[1]
        group: str = data[2]
        completeness: int = data[3]
        self.project_data.set_name(name_text=name)
        self.project_data.set_desc(desc_text=desc)
        self.project_data.set_group(group_name=group)
        self.project_data.set_percentage_complete(completeness)

    def open_project(self, selected):
        """Open the selected project and progress to tasks frame"""
        project_id = selected[0]
        project_name = selected[1]

        self.projects_do.current_project(project_id, project_name)

        self.frame_manager.show_frame(
            "tasks_frame", "projects_frame", destroy=True)

    def create_project(self):
        """Creates a new Projects database file and refreshes list frame"""
        project_name: str = self.project_data.get_name()
        project_description: str = self.project_data.get_desc()
        group_name: str = self.project_data.get_group()
        group_id = self.projects_do.get_group_id(group_name)

        if project_name:
            if self.projects_do.create_project(project_name, project_description, group_id) is not True:
                messagebox.showwarning(
                    title="Create Error", message="File Exists")

        projects = self.projects_do.list_project()
        logging.info("Projects Found: %s", projects)
        self.fresh_list(projects)

    def edit_project(self):
        """Edits the selected project with the data entered in the project_data frame"""
        project_name: str = self.project_data.get_name()
        project_description: str = self.project_data.get_desc()
        group_name: str = self.project_data.get_group()
        group_id = self.projects_do.get_group_id(group_name)

        if project_name:
            if self.projects_do.edit_project(project_name, project_description, group_id, self.selected[0]) is not True:
                messagebox.showerror(title="Edit Project",
                                     message="Unable to Edit project")

        projects = self.projects_do.list_project()
        logging.info("Projects Found: %s", projects)
        self.fresh_list(projects)
        self.clear_select()

    def remove_project(self):
        """Deletes the project passed as a parameter"""
        if self.projects_do.delete_project(self.selected[0]) is True:
            messagebox.showinfo(title="Delete Project",
                                message="Project Deleted")
        else:
            messagebox.showerror(title="Delete Project",
                                 message="Unable to Delete project")

        projects = self.projects_do.list_project()
        logging.info("Projects Found: %s", projects)
        self.fresh_list(projects)
        self.clear_select()


class TaskData(CTkFrame):
    """Frame for creating and editing tasks"""

    def __init__(self, master, name_text="Name"):
        super().__init__(master)

        self.name_var = StringVar(value=name_text)
        self.desc_var = StringVar(value="Description")

        self.grid_rowconfigure((0, 2, 3, 4), weight=1)  # configure grid system
        self.grid_rowconfigure(1, weight=2)
        self.grid_columnconfigure((0, 1), weight=1)

        self.name = CTkEntry(
            self, textvariable=self.name_var, corner_radius=5)
        self.name.grid(column=0, row=0, sticky="nsew",
                       columnspan=2, pady=(10, 0))

        self.desc = CTkEntry(
            self, textvariable=self.desc_var, corner_radius=5)
        self.desc.grid(column=0, row=1, sticky="nsew", pady=10, columnspan=2)

        self.date_due_label = CTkLabel(self, text="Date Due:")
        self.date_due_label.grid(column=0, row=2, sticky="nsew", pady=10)

        self.date_due = DateEntry(self, date_pattern='dd/MM/yyyy')
        self.date_due.grid(column=1, row=2, sticky="nsew", pady=10)

        self.complete = CTkCheckBox(self, text="Complete")
        self.complete.grid(column=0, row=3, sticky="nsew",
                           pady=10, columnspan=2)

    def get_name(self):
        """
        Returns:
            String: string in name entry
        """
        return self.name_var.get()

    def get_desc(self):
        """
        Returns:
            String: string in description entry
        """
        return self.desc_var.get()

    def get_due(self):
        """
        Returns:
            datetime.date: the date entered
        """
        return self.date_due.get_date()

    def get_status(self) -> bool:
        """
        Returns:
            bool: project complete status
        """
        return bool(self.complete.get())

    def set_name(self, name_text):
        """Displays the passed "name_text" in the Project Name entry box

        Args:
            name_text (String): The text to be displayed
        """
        self.name_var.set(name_text)

    def set_desc(self, desc_text):
        """Displays the passed "desc_text" in the Project Description entry box

        Args:
            desc_text (String): The text to be displayed
        """
        self.desc_var.set(desc_text)

    def set_due(self, due_date):
        """Displays the due date"""
        self.date_due.set_date(datetime.strptime(due_date, "%Y-%m-%d"))

    def set_status(self, complete):
        """Displays the status of the task"""
        if complete:
            self.complete.select()
        else:
            self.complete.deselect()


class TasksFrame(FrameBase):
    """Tasks 'Page' for managing tasks in project"""

    def __init__(self, app):
        super().__init__(app)

        self.on_selection_flag = True

        # configure grid system
        self.configure_frame(columns=4, rows=4, list_c_span=2,
                             list_r_span=1, list_row=2, list_col=0, button_row=3, has_list=True)

        # Title
        self.set_title(title="Tasks:")

        # Search
        self.search_bar = CTkEntry(
            self, placeholder_text="Search", corner_radius=5)
        self.search_bar.grid(row=1, columnspan=4, sticky="nsew", padx=10)
        self.search_bar.bind(
            '<Return>', self.search_tasks)

        # Tasks in project
        tasks = self.projects_do.list_tasks()
        logging.info("Tasks Found: %s", tasks)
        self.fresh_list(tasks)

        # Create task
        self.task_data = TaskData(master=self, name_text="Task Name")
        self.task_data.grid(row=2, column=2, columnspan=2,
                            padx=10, sticky="nsew")

        # Buttons
        new_task_button = CTkButton(
            self, text="New", corner_radius=20, command=self.create_task)
        self.static_buttons["_new"] = new_task_button

        edit_project_button = CTkButton(
            self, text="Edit", corner_radius=20, state=DISABLED, command=self.edit_task)
        self.static_buttons["edit"] = edit_project_button

        remove_project_button = CTkButton(
            self, text="Delete", corner_radius=20, state=DISABLED, command=self.remove_task)
        self.static_buttons["remove"] = remove_project_button

        back_button = CTkButton(
            self, text="Back", corner_radius=20, command=lambda: self.frame_manager.show_frame("projects_frame", "tasks_frame", destroy=True))
        self.static_buttons["_back"] = back_button

        self.button_auto_grid()

    def search_tasks(self, event):
        """Updates the tasks list with tasks meeting search in self.search_bar

        Args:
            event: passed by tk bind, logged for debug purposes
        """
        logging.debug(event)

        tasks = self.projects_do.search_tasks(
            self.search_bar.get())
        logging.info("Tasks Found: %s", tasks)
        self.fresh_list(tasks)

    def create_task(self):
        """Creates a task with the parameters given in the TaskData frame"""
        task_name: str = self.task_data.get_name()
        task_description: str = self.task_data.get_desc()
        task_set: date = date.today()
        task_due: date = self.task_data.get_due()
        complete: bool = self.task_data.get_status()

        if task_name and task_due >= task_set:
            if self.projects_do.create_task(task_name, task_description, task_set, task_due, complete) is not True:
                messagebox.showwarning(
                    title="Create Error", message="Unable to create task")

        tasks = self.projects_do.list_tasks()
        logging.info("Projects Found: %s", tasks)
        self.fresh_list(tasks)

    def edit_task(self):
        """Edits a existing task with the parameters given in the TaskData frame"""
        task_id: int = int(self.selected[0])
        task_name: str = self.task_data.get_name()
        task_description: str = self.task_data.get_desc()
        task_due: date = self.task_data.get_due()
        complete: bool = self.task_data.get_status()

        if task_name:
            if self.projects_do.edit_task(task_id, task_name, task_description, task_due, complete) is not True:
                messagebox.showwarning(
                    title="Edit Error", message="Unable to edit task")

        tasks = self.projects_do.list_tasks()
        logging.info("Projects Found: %s", tasks)
        self.fresh_list(tasks)
        self.clear_select()

    def remove_task(self):
        """Removes the selected task from the project"""
        if self.projects_do.delete_task(self.selected[0]) is True:
            messagebox.showinfo(title="Delete Task",
                                message="Task Deleted")
        else:
            messagebox.showerror(title="Delete Task",
                                 message="Unable to Delete Task")

        tasks = self.projects_do.list_tasks()
        logging.info("Tasks Found: %s", tasks)
        self.fresh_list(tasks)
        self.clear_select()

    def on_selection(self):
        data = self.projects_do.task_data(self.selected[0])
        self.task_data.set_name(data[0])
        self.task_data.set_desc(data[1])
        self.task_data.set_due(data[2])
        self.task_data.set_status(data[3])


class FrameManager():
    """Class used to manages frames"""

    def __init__(self, master):
        self.app = master

        # Primary Frames in project
        self.start_frame: CTkFrame
        self.files_frame: FrameBase
        self.login_frame: CTkFrame
        self.home_frame: CTkFrame
        self.groups_frame: CTkFrame
        self.settings_frame: CTkFrame
        self.projects_frame: FrameBase
        self.tasks_frame: FrameBase

        self.frames: tuple = ("start_frame", "files_frame", "login_frame",
                              "home_frame", "groups_frame", "settings_frame", "projects_frame", "tasks_frame")
        self.existing_frames: dict = {}

    def __create_frame(self, frame_name):
        """Creates the frame passed as a argument"""
        match frame_name:
            case "start_frame":
                self.start_frame = StartFrame(self.app)
                self.existing_frames[frame_name] = self.start_frame
            case "files_frame":
                self.files_frame = FilesFrame(self.app)
                self.existing_frames[frame_name] = self.files_frame
            case "login_frame":
                self.login_frame = LoginFrame(self.app)
                self.existing_frames[frame_name] = self.login_frame
            case "home_frame":
                self.home_frame = HomeFrame(self.app)
                self.existing_frames[frame_name] = self.home_frame
            case "settings_frame":
                self.settings_frame = SettingsFrame(self.app)
                self.existing_frames[frame_name] = self.settings_frame
            case "groups_frame":
                self.groups_frame = GroupsFrame(self.app)
                self.existing_frames[frame_name] = self.groups_frame
            case "projects_frame":
                self.projects_frame = ProjectFrame(self.app)
                self.existing_frames[frame_name] = self.projects_frame
            case "tasks_frame":
                self.tasks_frame = TasksFrame(self.app)
                self.existing_frames[frame_name] = self.tasks_frame
            case _: raise NameError

    def show_frame(self, frame_name, from_frame="", destroy=False):
        """Shows the frame passed as a argument, destroys the current frame if destroy is True"""
        if frame_name in self.frames:  # Checks if valid frame name

            if frame_name not in self.existing_frames:  # Creates the frame if it does not exist
                self.__create_frame(frame_name)

            self.existing_frames[frame_name].grid(
                row=0, column=0, padx=20, pady=20, sticky="nsew")

            if from_frame == "all":  # if from_frame is set to "all" then destroy all frames
                for frame in list(self.existing_frames):
                    if frame != "start_frame":
                        self.existing_frames.pop(frame).destroy()
            elif from_frame:  # Otherwise only destroy the from_frame if destroy is True
                if destroy:
                    self.existing_frames.pop(from_frame).destroy()
                else:
                    self.existing_frames[from_frame].grid_forget()


class APP(CTk):
    """GUI Code"""

    def __init__(self, program_name, version_number, config):
        super().__init__()
        self.frame_manager = FrameManager(self)
        self.projects_do = lib_file.Project()
        self.config = config

        self.username = ""

        set_appearance_mode(self.config.settings["Theme"])

        self.title(f"{program_name} (Version: {version_number})")
        self.geometry("900x450")
        self.minsize(900, 450)

        self.grid_rowconfigure(0, weight=1)  # configure grid system
        self.grid_columnconfigure(0, weight=1)

        # Opens the Frame where the user select the working directory
        self.frame_manager.show_frame("start_frame")

    def open_dir(self):
        """Instantiates Project class and progress to Project files frame"""
        db_directory = filedialog.askdirectory()  # Prompts user for project directory
        logging.info("Directory selected: %s", db_directory)

        if db_directory == "":
            logging.warning("No directory selected")
            return 0

        self.projects_do.set_dir(db_directory)

        # hides the start frame and shows the files frame
        self.frame_manager.show_frame("files_frame", "start_frame")

    def set_username(self, username):
        """Set username from outside the class"""
        self.username = username

    def change_theme(self, theme):
        """Allows changing the theme from outside the class"""
        set_appearance_mode(theme)


def main():
    """Main Function holding setup code"""

    # Used to read and write settings to config file
    config = lib_file.Settings()

    # Logging setup:
    logging.basicConfig(format='%(levelname)s (%(asctime)s): %(message)s \
                        (Line: %(lineno)d [%(filename)s])',
                        datefmt='%d/%m/%Y %I:%M:%S %p',
                        level=config.settings["Debug"],
                        filename='Latest.log',
                        encoding='utf-8',
                        filemode='w')

    # Main app code
    app = APP(PROGRAM_NAME, VERSION_NUMBER, config)
    app.mainloop()


# Checks if running as a import, only runs if ran directly
if __name__ == "__main__":
    main()
