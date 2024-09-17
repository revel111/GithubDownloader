# Github downloader

## Console-based application for keeping tracked files from GitHub updated.

This project might be useful for people who want to have the most recent version of a file from GitHub repositories.
For instance, I wanted to create an app for reading memory,
and I wasn't bothered manually updating a file with the addresses when the new update is out.

## This is how the main menu looks like:
![image](https://github.com/user-attachments/assets/530fe2a8-8c47-48e7-850f-91916db1e96c)

## Why does this app ask for GitHub authentication token and is it dangerous?
**This app stores your token locally so your token won't be exposed to anyone.
You can browse code and figure it out yourself.
Your token is saved in "data/credentials.txt" which is located in the directory with scripts.**\
GitHub has restricted number of requests per hour, and for an unauthorized user this amount is quite low,
therefore, the authentication is needed.

## How to add a file to be tracked?
GitHub link should look like this: "https://github.com/revel111/GithubDownloader/blob/master/main.py".

## Where can I find downloaded files?
You can find them in the "downloaded" directory which is located in the directory with scripts or in directory which you specified.

## How to use this application?
**In the repository you can find two scripts:**
  - main.py - is used for configuring your tracked files and authentication process.
  - auto_updater.py - is used for running on the background and once per 15 minutes try to update tracked files if a new version is out.

## External libraries used:
[PyGithub](https://pypi.org/project/PyGithub)\
[tabulate](https://pypi.org/project/tabulate)

## How to install and uninstall?
In the "installation" directory you can find two scripts: for Windows and for Linux respectively.
These scripts download the necessary libraries and add "auto_updater.py" to the startup.
Uninstallation deletes script from the startup.\
**This app was tested on Windows 10 and Lubuntu 24.04.**

## Plans for improvement:
  - GUI;
  - Possibility of custom frequency of file updating;
  - Possibility of tracking directory;
  - Manage duplicated files;
    
## Where to report problems and suggestions?
You can create an issue [here](https://github.com/revel111/GithubDownloader/issues).
I will try to respond to you as soon as possible.
