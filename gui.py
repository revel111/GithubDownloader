from pathlib import Path
from types import NoneType

import customtkinter
from CTkMenuBar import CTkMenuBar
from CTkMessagebox import CTkMessagebox
from customtkinter import CTk, CTkButton, CTkToplevel, CTkFrame, CTkLabel, CTkEntry, CTkInputDialog, CTkOptionMenu
from docutils.nodes import title
from github import Github

from funcs import validate_data, define_exception, save_tracked_file, download_file
from global_variables import GeneralException, DOWNLOADED_DIRECTORY_PATH
from main import return_manual, parse_link, validate_path, ask_user_for_data

git = Github()


class ManualWindow(CTkToplevel):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.geometry(center_window(self, self._get_window_scaling()))
        self.title('Manual')
        self.geometry('600x300')

        self.grid_columnconfigure(0, weight=1)

        self.text = customtkinter.CTkTextbox(self, fg_color='transparent')
        self.text.insert('0.0', return_manual())
        self.text.configure(state='disabled')
        self.text.grid(row=0, column=0, sticky='we')
        self.attributes('-topmost', True)


class AppearanceFrame(CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)

        self.appearance_mode_label = CTkLabel(self, text='Appearance Mode', anchor='w')
        self.appearance_mode_label.grid(row=0, column=0, padx=10, pady=(10, 0))
        self.appearance_mode_option_menu = CTkOptionMenu(self, values=['Light', 'Dark', 'System'],
                                                         command=self.change_appearance_mode_event)
        self.appearance_mode_option_menu.grid(row=1, column=0, padx=20, pady=(10, 10))

        self.scaling_label = customtkinter.CTkLabel(self, text='UI Scaling', anchor='w')
        self.scaling_label.grid(row=0, column=1, padx=10, pady=(10, 0))
        self.scaling_option_menu = customtkinter.CTkOptionMenu(self, values=['80%', '90%', '100%', '110%', '120%'],
                                                               command=self.change_scaling_event)
        self.scaling_option_menu.grid(row=1, column=1, padx=20, pady=(10, 10))

        self.configure(fg_color='transparent')

    @staticmethod
    def change_appearance_mode_event(new_appearance_mode):
        customtkinter.set_appearance_mode(new_appearance_mode)

    @staticmethod
    def change_scaling_event(new_scaling):
        new_scaling_float = int(new_scaling.replace('%', '')) / 100
        customtkinter.set_widget_scaling(new_scaling_float)


class InputFrame(CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)

        self.entry = CTkEntry(master=self, placeholder_text='Enter a link')
        self.add_button = CTkButton(master=self, text='add', command=self.add_file_open_window)
        self.download_button = CTkButton(master=self, text='download', command=poxuy)
        self.delete_button = CTkButton(master=self, text='delete', command=poxuy)

        self.entry.grid(row=0, column=0, padx=10, pady=0, sticky='we')
        self.add_button.grid(row=0, column=1, padx=10, pady=0, sticky='e')
        self.download_button.grid(row=0, column=2, padx=10, pady=0, sticky='e')
        self.delete_button.grid(row=0, column=3, padx=10, pady=0, sticky='e')

        self.configure(fg_color='transparent')

    def add_file_open_window(self) -> None:
        owner_name, repo_name, branch, path, location, location_warning = self.ask_user_for_data()

        save_tracked_file(owner_name, repo_name, branch, path, location)

        if location is NoneType or location_warning.get():
            CTkMessagebox(title='Success',
                          message=f'File "{path}" was successfully added to the list of tracked files.',
                          icon='check')

    def ask_user_for_data(self) -> tuple[str, str, str, str, Path, CTkMessagebox] | None:
        try:
            owner_name, repo_name, branch, path = parse_link(self.entry.get())
        except ValueError:
            CTkMessagebox(master=self, title='Error', message='Wrong link format.', icon='cancel')
            return

        try:
            validate_data(owner_name, repo_name, branch, path)
        except GeneralException as e:
            define_exception(e, self)
            return

        location_input_dialog = CTkInputDialog(text='Enter a path where you want to store a file.', title='Path')
        path = location_input_dialog.get_input()
        location = validate_path(Path(path))

        location_warning = None
        if location == DOWNLOADED_DIRECTORY_PATH:
            location_warning = CTkMessagebox(master=self,
                                             title='Warning',
                                             message=f'Location "{path}" does not exist. File will be stored in the "{DOWNLOADED_DIRECTORY_PATH}"',
                                             icon='warning')

        return owner_name, repo_name, branch, path, location, location_warning

    def window_download_file_without_tracking(self) -> None:
        try:
            owner_name, repo_name, branch, path, location = self.ask_user_for_data()
        except TypeError:
            return

        self.window_download_file(self, owner_name, repo_name, branch, path, location)

    def window_download_file(self, owner_name, repo_name, branch, path, location) -> None:
        try:
            download_file(owner_name, repo_name, branch, path, location)
        except GeneralException as e:
            define_exception(e, self)


# def delete_file(self) -> None:

# def ask_user_for_data() -> N


class App(CTk):
    def __init__(self):
        super().__init__()

        self.geometry(center_window(self, self._get_window_scaling()))
        self.title("GitHub downloader")
        customtkinter.set_appearance_mode("dark")

        # self.main_frame = customtkinter.CTkFrame(master=self)
        # self.main_frame.grid(row=0, column=0)

        # self.main_frame.update_idletasks()
        # width = self.main_frame.winfo_width()
        # height = self.main_frame.winfo_height()
        # self.geometry(f"{width}x{height}")

        self.grid_columnconfigure(0, weight=1)

        self.menubar = CTkMenuBar(master=self)
        self.menubar.grid(row=0, column=0, padx=0, pady=0, sticky='we')

        self.menubar.add_cascade('Credentials', self.open_authentication)
        self.menubar.add_cascade('Manual', self.open_manual)

        self.input_frame = InputFrame(master=self)
        self.input_frame.grid(row=1, column=0, padx=0, pady=20, sticky='en')

        self.appearance_frame = AppearanceFrame(master=self)
        self.appearance_frame.grid(row=5, column=0, rowspan=4, sticky="nsew")
        # self.appearance_frame.grid_rowconfigure(4, weight=1)
        self.toplevel_window = None

    def open_manual(self) -> None:
        if (self.toplevel_window is None or
                not self.toplevel_window.winfo_exists()):
            self.toplevel_window = ManualWindow(self)
        else:
            self.toplevel_window.focus_force()

    @staticmethod
    def open_authentication() -> None:
        token_input = CTkInputDialog(
            text='''Read about personal access token here and generate it to start use this application.
                    Link: https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens#creating-a-personal-access-token-classic''',
            title='Authentication')
        print(token_input.get_input())


# credits to this young man: https://github.com/TomSchimansky/CustomTkinter/discussions/1820
def center_window(window, scaling, width=800, height=600) -> str:
    screen_width = window.winfo_screenwidth()
    screen_height = window.winfo_screenheight()

    x = int(((screen_width / 2) - (width / 2)) * scaling)
    y = int(((screen_height / 2) - (height / 1.5)) * scaling)

    return f"{width}x{height}+{x}+{y}"


def poxuy():
    print('poxuy')


def app_creator() -> CTk:
    app = App()
    return app


def main() -> None:
    app = app_creator()
    app.mainloop()


if __name__ == '__main__':
    main()
