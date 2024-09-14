import textwrap


def return_manual() -> str:
    return textwrap.dedent('''
    Q: How to generate an access token?
    A: Link: https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens#creating-a-personal-access-token-classic
    
    Q: What format of link should i consider when I add a new file?
    A: This is how link should look like: https://github.com/revel111/GithubDownloader/blob/master/main.py
    
    Q: Where can I report about bugs and send any idea regarding this project?
    A: Link: https://github.com/revel111/GithubDownloader/issues 
    I ask you to report any kind of bugs. Each bug will be fixed and any idea will be reviewed.
    ''')
