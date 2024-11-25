from pathlib import Path
from types import NoneType

import customtkinter
from CTkMenuBar import CTkMenuBar
from CTkMessagebox import CTkMessagebox
from customtkinter import CTk, CTkButton, CTkToplevel, CTkFrame, CTkLabel, CTkEntry, CTkInputDialog, CTkOptionMenu
from github import Github, BadCredentialsException

from funcs import validate_data, define_exception, save_tracked_file, download_file, delete_tracked_file, \
    search_location_by_link, authenticate_token, read_credentials
from global_variables import GeneralException, DOWNLOADED_DIRECTORY_PATH
from main import return_manual, parse_link, validate_path
import global_variables as gv


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
    def change_appearance_mode_event(new_appearance_mode: str):
        customtkinter.set_appearance_mode(new_appearance_mode)

    @staticmethod
    def change_scaling_event(new_scaling: str):
        new_scaling_float = int(new_scaling.replace('%', '')) / 100
        customtkinter.set_widget_scaling(new_scaling_float)


class InputFrame(CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.grid_columnconfigure(0, weight=1)

        self.entry = CTkEntry(master=self, placeholder_text='Enter a link')
        self.add_button = CTkButton(master=self, text='add', command=self.add_file_open_window, width=70)
        self.update_button = CTkButton(master=self, text='update', command=self.window_update_file, width=70)
        self.download_button = CTkButton(master=self, text='download',
                                         command=self.window_download_file_without_tracking, width=70)
        self.delete_button = CTkButton(master=self, text='delete', command=self.window_delete_file, width=70)

        self.entry.grid(row=0, column=0, padx=10, pady=0, sticky='we', columnspan=3)
        self.update_button.grid(row=0, column=3, padx=5, pady=0, sticky='e')
        self.add_button.grid(row=0, column=4, padx=5, pady=0, sticky='e')
        self.download_button.grid(row=0, column=5, padx=5, pady=0, sticky='e')
        self.delete_button.grid(row=0, column=6, padx=5, pady=0, sticky='e')

        self.configure(fg_color='transparent')

    def add_file_open_window(self) -> None:
        try:
            owner_name, repo_name, branch, path, location, location_warning = self.ask_user_for_data()
        except TypeError:
            return

        save_tracked_file(owner_name, repo_name, branch, path, location)

        if location is NoneType or location_warning.get():
            CTkMessagebox(title='Success',
                          message=f'File "{path}" was successfully added to the list of tracked files.',
                          icon='check')

        try:
            download_file(owner_name, repo_name, branch, path, location)
        except GeneralException:
            pass

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
        location_file = location_input_dialog.get_input()
        location = validate_path(Path(location_file))

        location_warning = None
        if location == DOWNLOADED_DIRECTORY_PATH:
            location_warning = CTkMessagebox(master=self,
                                             title='Warning',
                                             message=f'Location "{location_file}" does not exist. File will be stored in the "{DOWNLOADED_DIRECTORY_PATH}"',
                                             icon='warning')

        return owner_name, repo_name, branch, path, location, location_warning

    def window_download_file_without_tracking(self) -> None:
        try:
            owner_name, repo_name, branch, path, location, location_warning = self.ask_user_for_data()
        except TypeError:
            return

        if location is NoneType or location_warning.get():
            self.window_download_file(owner_name, repo_name, branch, path, location)

    def window_download_file(self, owner_name: str, repo_name: str, branch: str, path: str,
                             location: str) -> CTkMessagebox:
        try:
            download_file(owner_name, repo_name, branch, path, location)
        except GeneralException as e:
            return define_exception(e, self)

    def window_delete_file(self) -> None:
        try:
            owner_name, repo_name, branch, path = parse_link(self.entry.get())
        except ValueError:
            CTkMessagebox(master=self, title='Error', message='Wrong link format.', icon='cancel')
            return

        try:
            delete_tracked_file(f'{owner_name}{repo_name}{branch}{path}', path.split('/')[-1])
        except GeneralException as e:
            define_exception(e, self)
            return

        CTkMessagebox(title='Success',
                      message=f'File "{path}" was successfully deleted from the list of tracked files.',
                      icon='check')

    def window_update_file(self) -> None:
        try:
            owner_name, repo_name, branch, path = parse_link(self.entry.get())
        except ValueError:
            CTkMessagebox(master=self, title='Error', message='Wrong link format.', icon='cancel')
            return

        try:
            location = search_location_by_link(f'{owner_name}{repo_name}{branch}{path}', path.split('/')[-1])
        except GeneralException as e:
            define_exception(e, self)
            return

        try:
            download_file(owner_name, repo_name, branch, path, location)
        except GeneralException as e:
            define_exception(e, self)
            return

        CTkMessagebox(title='Success',
                      message=f'File "{path}" was successfully updated.',
                      icon='check')


class App(CTk):
    def __init__(self):
        super().__init__()

        self.geometry(center_window(self, self._get_window_scaling()))
        self.title("GitHub downloader")
        self.iconbitmap('installation/logo.ico')
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

        self.menubar.add_cascade('Credentials', lambda: self.open_authentication(self))
        self.menubar.add_cascade('Manual', self.open_manual)

        self.input_frame = InputFrame(master=self)
        self.input_frame.grid(row=1, column=0, padx=0, pady=20, sticky='wen')

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
    def open_authentication(master: CTk) -> None:
        token_input = CTkInputDialog(
            text='''Read about personal access token here and generate it to start use this application.
                    Link: https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens#creating-a-personal-access-token-classic''',
            title='Authentication')
        token = token_input.get_input()

        # if token is NoneType or token is None:
        #     try:
        #         gv.git = Github(read_credentials())
        #         gv.git.get_user().login
        #     except BadCredentialsException:
        #         App.open_authentication(master)
        #         return

        try:
            authenticate_token(token)
        except GeneralException as e:
            message = define_exception(e, master)

            if message is NoneType or message.get():
                App.open_authentication(master)

            return

        CTkMessagebox(title='Success',
                      message=f'Token was successfully updated.',
                      icon='check')


# credits to this young man: https://github.com/TomSchimansky/CustomTkinter/discussions/1820
def center_window(window: App | ManualWindow, scaling: float, width=800, height=600) -> str:
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
    # App.open_authentication(app)
    app.mainloop()


if __name__ == '__main__':
    main()
