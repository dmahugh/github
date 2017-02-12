"""ghaudit.py
Audit a GitHub account.

1st command-line argument = username to be audited

Displays a summary of this user's repos and roles across Microsoft orgs.
"""
import json
import sys

import gitdata as gd

#-------------------------------------------------------------------------------
def authenticate():
    """Set up gitdata authentication.
    Currently using msftgits for all auditing of Microsoft accounts.
    """
    gd.auth_config({'username': 'msftgits'})

#-------------------------------------------------------------------------------
def printhdr(acct, msg):
    """Print a header for a section of the audit report.
    """
    ndashes = 65 - len(msg)
    print('>> ' + msg + ' <<' + ndashes*'-' + ' account: ' + acct.upper())

#-------------------------------------------------------------------------------
def userrepos(acct):
    """Print summary of user repositories for an account.
    """
    printhdr(acct, 'user repositories')

    authenticate()
    endpoint = '/users/' + acct + '/repos'
    response = gd.github_api(endpoint=endpoint, auth=gd.auth_user())
    jsondata = json.loads(response.text)
    for repo in jsondata:
        owner = repo['owner']['login']
        reponame = repo['name']
        print(owner + '/' + reponame)

#-------------------------------------------------------------------------------
if __name__ == '__main__':

    if len(sys.argv) == 2:
        username = sys.argv[1].lower()
    else:
        username = 'ikofish' # default for testing

    userrepos(username)
    printhdr(username, 'END REPORT')
