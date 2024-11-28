from pathlib import Path
from types import NoneType

import customtkinter
from CTkMenuBar import CTkMenuBar
from CTkMessagebox import CTkMessagebox
from CTkTable import CTkTable
from PIL import Image
from customtkinter import CTk, CTkButton, CTkToplevel, CTkFrame, CTkLabel, CTkEntry, CTkInputDialog, CTkOptionMenu, \
    CTkScrollableFrame, CTkTextbox, CTkImage
from github import Github, BadCredentialsException

import global_variables as gv
from funcs import validate_data, define_exception, save_tracked_file, download_file, delete_tracked_file, \
    search_location_by_link, authenticate_token, read_credentials, fabricate_links, str_to_link
from global_variables import GeneralException, DOWNLOADED_DIRECTORY_PATH
from main import return_manual, parse_link, validate_path


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
        self.appearance_mode_option_menu = CTkOptionMenu(self, values=['Dark', 'Light', 'System'],
                                                         command=self.change_appearance_mode_event)
        self.appearance_mode_option_menu.grid(row=1, column=0, padx=20, pady=(10, 10))

        self.scaling_label = customtkinter.CTkLabel(self, text='UI Scaling', anchor='w')
        self.scaling_label.grid(row=0, column=1, padx=10, pady=(10, 0))
        self.scaling_option_menu = customtkinter.CTkOptionMenu(self, values=['80%', '90%', '100%', '110%', '120%'],
                                                               command=self.change_scaling_event)
        self.scaling_option_menu.grid(row=1, column=1, padx=20, pady=(10, 10))

        self.configure(fg_color='transparent')

    @staticmethod
    def change_appearance_mode_event(new_appearance_mode: str) -> None:
        customtkinter.set_appearance_mode(new_appearance_mode)

    @staticmethod
    def change_scaling_event(new_scaling: str) -> None:
        new_scaling_float = int(new_scaling.replace('%', '')) / 100
        customtkinter.set_widget_scaling(new_scaling_float)


class TableFrame(CTkScrollableFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)

        self.row_buttons = {}

        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=0)
        self.grid_columnconfigure(2, weight=0)

        self.delete_button_image = CTkImage(
            dark_image=Image.open('resources/delete_white.png'),
            light_image=Image.open('resources/delete_black.png'),
            size=(20, 20))
        self.update_button_image = CTkImage(
            dark_image=Image.open('resources/update_white.png'),
            light_image=Image.open('resources/update_black.png'),
            size=(20, 20))

        try:
            links = fabricate_links()
            self.table = CTkTable(master=self, row=len(links), column=2, values=links)
            # self.initialize_buttons(links)
        except (FileNotFoundError, IndexError):
            self.table = CTkTable(master=self, row=0, column=2, values=[[]])
        self.table.add_row(['Link', 'Stored'], 0)
        self.table.delete_row(1)

        self.table.grid(row=0, column=0, padx=10, pady=0, sticky='nsew')

    def initialize_buttons(self, links: list[list[str]]) -> None:
        for i, link in enumerate(links, start=1):
            owner_name, repo_name, branch, path = parse_link(link[0])
            self.add_buttons(i, owner_name, repo_name, branch, path, link[1])

    def change_indexes(self, index: int):
        temp = dict()
        for key, val in self.row_buttons.items():
            if key >= index:
                temp[key - 1] = 0
            else:
                temp[key] = val

    def add_buttons(self, index: int, owner_name: str, repo_name: str, branch: str, path: str, location: str) -> None:
        def wrap():
            try:
                download_file(owner_name, repo_name, branch, path, location)
            except GeneralException as e:
                define_exception(e, self.master.master.master)

        update_button = CTkButton(master=self,
                                  text="",
                                  image=self.update_button_image,
                                  height=20,
                                  width=20,
                                  command=lambda: wrap())
        update_button.grid(row=index, column=1, padx=5, pady=0)

        delete_button = CTkButton(master=self,
                                  text="",
                                  image=self.delete_button_image,
                                  height=20,
                                  width=20,
                                  command=lambda: self.delete_buttons(index, owner_name, repo_name, branch, path,
                                                                      path.split('/')[-1]))
        delete_button.grid(row=index, column=2, padx=5, pady=0)

        self.row_buttons[index] = [update_button, delete_button]

    def delete_buttons(self, index: int, owner_name: str, repo_name: str, branch: str, path: str, name: str):
        if index in self.row_buttons:
            button1, button2 = self.row_buttons[index]
            button1.destroy()
            button2.destroy()
            del self.row_buttons[index]
            self.table.delete_row(index)
            self.change_indexes(index)
            try:
                delete_tracked_file(f'{owner_name}{repo_name}{branch}{path}', name)
            except GeneralException as e:
                define_exception(e, self.master.master.master)


class InputFrame(CTkFrame):
    def __init__(self, master, table: TableFrame, **kwargs):
        super().__init__(master, **kwargs)
        self.grid_columnconfigure(0, weight=1)

        self.entry = CTkEntry(master=self, placeholder_text='Enter a link')
        self.add_button = CTkButton(master=self, text='add', command=lambda: self.add_file_open_window(table),
                                    width=70)
        self.update_button = CTkButton(master=self, text='update', command=self.window_update_file, width=70)
        self.download_button = CTkButton(master=self, text='download',
                                         command=self.window_download_file_without_tracking, width=70)
        self.delete_button = CTkButton(master=self, text='delete', command=lambda: self.window_delete_file(table),
                                       width=70)

        self.entry.grid(row=0, column=0, padx=10, pady=0, sticky='we', columnspan=3)
        self.update_button.grid(row=0, column=3, padx=5, pady=0, sticky='e')
        self.add_button.grid(row=0, column=4, padx=5, pady=0, sticky='e')
        self.download_button.grid(row=0, column=5, padx=5, pady=0, sticky='e')
        self.delete_button.grid(row=0, column=6, padx=5, pady=0, sticky='e')

        self.configure(fg_color='transparent')

    def add_file_open_window(self, table: TableFrame) -> None:
        try:
            owner_name, repo_name, branch, path, location, location_warning = self.ask_user_for_data()
        except TypeError:
            return
        save_tracked_file(owner_name, repo_name, branch, path, location)
        table.table.add_row([str_to_link(owner_name, repo_name, branch, path), location], len(table.table.values))
        table.add_buttons(len(table.table.values) - 1, owner_name, repo_name, branch, path, location)

        if location is NoneType or location_warning is None or location_warning is NoneType or location_warning.get():
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
            CTkMessagebox(master=self.master, title='Error', message='Wrong link format.', icon='cancel')
            return

        try:
            validate_data(owner_name, repo_name, branch, path)
        except GeneralException as e:
            define_exception(e, self.master)
            return

        location_input_dialog = CTkInputDialog(text='Enter a path where you want to store a file.', title='Path')
        location_file = location_input_dialog.get_input()
        location = validate_path(Path(location_file))

        location_warning = None
        if location == DOWNLOADED_DIRECTORY_PATH:
            location_warning = CTkMessagebox(master=self.master,
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
            return define_exception(e, self.master)

    def window_delete_file(self, table: TableFrame) -> None:
        try:
            owner_name, repo_name, branch, path = parse_link(self.entry.get())
        except ValueError:
            CTkMessagebox(master=self.master,
                          title='Error',
                          message='Wrong link format.',
                          icon='cancel')
            return

        try:
            result, index = delete_tracked_file(f'{owner_name}{repo_name}{branch}{path}', path.split('/')[-1])
        except GeneralException as e:
            define_exception(e, self.master)
            return

        if index == -1:
            CTkMessagebox(master=self.master,
                          title='Error',
                          message=result,
                          icon='cancel')
        else:
            table.table.delete_row(index + 1)
            table.delete_buttons(index + 1, owner_name, repo_name, branch, path, path.split('/')[-1])
            CTkMessagebox(master=self.master,
                          title='Success',
                          message=result,
                          icon='check')

    def window_update_file(self) -> None:
        try:
            owner_name, repo_name, branch, path = parse_link(self.entry.get())
        except ValueError:
            CTkMessagebox(master=self.master, title='Error', message='Wrong link format.', icon='cancel')
            return

        try:
            location = search_location_by_link(f'{owner_name}{repo_name}{branch}{path}', path.split('/')[-1])
        except GeneralException as e:
            define_exception(e, self.master)
            return

        try:
            download_file(owner_name, repo_name, branch, path, location)
        except GeneralException as e:
            define_exception(e, self.master)
            return

        CTkMessagebox(master=self.master,
                      title='Success',
                      message=f'File "{path}" was successfully updated.',
                      icon='check')


class App(CTk):
    def __init__(self):
        super().__init__()

        self.geometry(center_window(self, self._get_window_scaling()))
        self.title("GitHub downloader")
        # self.iconbitmap('installation/logo.ico')
        customtkinter.set_appearance_mode("dark")

        self.grid_rowconfigure(3, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self.menubar = CTkMenuBar(master=self)
        self.menubar.grid(row=0, column=0, padx=0, pady=0, sticky='we')
        self.menubar.add_cascade('Credentials', lambda: self.open_authentication())
        self.menubar.add_cascade('Manual', self.open_manual)

        self.login = CTkTextbox(master=self, height=30, width=200, corner_radius=5)
        self.login.grid(row=1, column=0, sticky='w', padx=40, pady=5)

        image = CTkImage(light_image=Image.open('resources/profile_black.png'),
                         dark_image=Image.open('resources/profile_white.png'),
                         size=(30, 30))
        self.label = CTkLabel(self, image=image, text='')
        self.label.grid(row=1, column=0, sticky='w', padx=5, pady=5)

        self.table = TableFrame(master=self)
        self.table.grid(row=3, column=0, padx=5, pady=5, sticky="nsew")

        self.input_frame = InputFrame(master=self, table=self.table)
        self.input_frame.grid(row=2, column=0, pady=5, sticky='ew')

        self.appearance_frame = AppearanceFrame(master=self)
        self.appearance_frame.grid(row=5, column=0, padx=5, pady=5, sticky="ew")

        self.toplevel_window = None
        self.authenticate_on_start()

    def open_manual(self) -> None:
        if (self.toplevel_window is None or
                not self.toplevel_window.winfo_exists()):
            self.toplevel_window = ManualWindow(self)
        else:
            self.toplevel_window.focus_force()

    def authenticate_on_start(self) -> None:
        if not gv.AUTH_FILE_PATH.exists():
            self.open_authentication()
        else:
            try:
                gv.git = Github(read_credentials())
                gv.git.get_user().login
                self.show_login()
            except BadCredentialsException:
                self.open_authentication()

    def show_login(self) -> None:
        self.login.configure(state='normal')
        self.login.insert("0.0", f'Logged in as {gv.git.get_user().login}')
        self.login.configure(state='disabled')

    def open_authentication(self) -> None:
        token_input = CTkInputDialog(
            text='''Read about personal access token here and generate it to start use this application.
                    Link: https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens#creating-a-personal-access-token-classic''',
            title='Authentication')
        token = token_input.get_input()

        if token is NoneType or token is None and gv.AUTH_FILE_PATH.exists():
            try:
                gv.git = Github(read_credentials())
                gv.git.get_user().login
            except BadCredentialsException:
                message = CTkMessagebox(title='Error',
                                        message='You entered invalid secure token.',
                                        icon='Cancel')

                if message is NoneType or message.get():
                    self.open_authentication()
        else:
            try:
                authenticate_token(token)

            except GeneralException as e:
                message = define_exception(e, self.master)

                if message is NoneType or message.get():
                    self.open_authentication()

        CTkMessagebox(title='Success',
                      message=f'Token was successfully updated.',
                      icon='check')
        self.show_login()


# credits to this young man: https://github.com/TomSchimansky/CustomTkinter/discussions/1820
def center_window(window: App | ManualWindow, scaling: float, width=1024, height=786) -> str:
    screen_width = window.winfo_screenwidth()
    screen_height = window.winfo_screenheight()

    x = int(((screen_width / 2) - (width / 2)) * scaling)
    y = int(((screen_height / 2) - (height / 1.5)) * scaling)

    return f"{width}x{height}+{x}+{y}"


def app_creator() -> CTk:
    app = App()
    return app


def main() -> None:
    app = app_creator()
    app.mainloop()


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('Thank you for using this application.')
    except ConnectionError:
        CTkMessagebox(title='Error',
                      message='No connection with Github. Please check your network connection or try again later.',
                      icon='cancel')
