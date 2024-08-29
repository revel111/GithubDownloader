# Github downloader

## Console-based application for keeping tracked files from Github updated.

This project might be useful for people who want to have the most recent version of file from Github repositories.
For instance, I wanted to create an app for reading memory and I wasn't bothered manually updating file with the addreses when new update is out.

## This is how the main menu look like:
![image](https://github.com/user-attachments/assets/530fe2a8-8c47-48e7-850f-91916db1e96c)

## Why does this app ask for Github authentication token and is it dangerous?
**This app stores your token localy so your token won't be exposed to anyone. You can browse code and figure out it yourself. Your token is saved in "auth/auth.txt" which is located in the directory with scripts.**\
Github has restriced amount of requests per hour and for an unathorized user this amount is quite low, therefore the authentication is needed.

## Where can i find downloaded files?
You can find them in the "downloaded" directory which is located in the directory with scripts.

## How to use this appliation?
**In the repository you can find two scripts:**
  - main.py - is used for configuring your tracked files and authentication process.
  - auto_updater.py - is used for running on the background and once per 15 minutes try to update tracked files if new version is out.

## External libraries used:
[PyGithub](https://pypi.org/project/PyGithub)\
[tabulate](https://pypi.org/project/tabulate)

## How to install?
In the "installation" directory you can find two scripts: for Windows and for Linux respectively. These scripts download needed libraries and add "auto_updater.py" to the startup\
**This app was tested on Windows 10 and Lubuntu 24.04.**

## Plans for improvement:
  - Possibility of custom frequence of file updating;
  - Possibility of tracking directory;
  - Manage duplicated files;
  - Add possibility to provide path where user want to store file;
    
## Where to report problems and suggestions?
You can create an issue [here](https://github.com/revel111/GithubDownloader/issues). I will try to respond you as soon as possible.
