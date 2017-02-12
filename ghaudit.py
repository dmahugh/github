"""ghaudit.py
Audit GitHub account for Microsoft users.
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
def getmsdata():
    """Retrieve/refresh all Microsoft data needed for audit reports.
    """

   # orgs.csv
   # command line: gitdata orgs -amsftgits -sa -nghaudit/orgs.csv -flogin/user/id
    authuser = 'msftgits'
    gd._settings.display_data = True
    gd._settings.verbose = False
    gd._settings.datasource = 'a'
    gd.auth_config({'username': authuser})
    fldnames = ['login', 'user', 'id']
    templist = gd.github_data(
        endpoint='/user/orgs', entity='org', fields=fldnames,
        constants={"user": authuser}, headers={})
    sorted_data = sorted(templist, key=gd.data_sort)
    gd.data_display(sorted_data)
    gd.data_write('ghaudit/orgs.csv', sorted_data)

    #/// step through orgs.csv to handle these:
    #/// ghaudit/teams.csv = list of all teams for each org
    #/// ghaudit/repos.csv = list of all repos for each org

    #/// step through repos.csv to create the collabs list:
    #/// ghaudit/collabs.csv = all collaborators for each repo

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
    getmsdata()
