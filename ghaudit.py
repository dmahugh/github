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

   # create the ORG data file, list of organizations to be audited
   # Below is inline automation of this command:
   #   gitdata orgs -amsftgits -sa -nghaudit/orgs.csv -flogin/user/id
    orgfile = 'ghaudit/orgs.csv'
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
    gd.data_write(orgfile, sorted_data)

    # create the TEAM and REPO data files, iterating over ORGs
    teamfile = 'ghaudit/teams.csv'
    repofile = 'ghaudit/repos.csv'
    open(teamfile, 'w').write('///header') # initialize data file
    open(repofile, 'w').write('///header') # initialize data file
    for line in open(orgfile, 'r').readlines():
        orgname = line.split(',')[0]
        #/// get team data for this org
        open(teamfile, 'a').write('///org=' + orgname)
        #/// get repo data for this org
        open(repofile, 'a').write('///org=' + orgname)

    # create the COLLAB data file, iterating over REPOs
    #/// step through repofile to create the collabs list:
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
