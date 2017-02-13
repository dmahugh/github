"""ghaudit.py
Audit GitHub account for Microsoft users.
"""
import json
import sys

import gitdata as gd

#-------------------------------------------------------------------------------
def appendrepos(filename, org=None):
    """Append repo info for an org to repos.csv data file.

    Special case: if no org provided, initialize the data file.
    """
    if not org:
        open(filename, 'w').write('org,repo,private,fork\n')
        return

    repodata = gdwrapper(endpoint='/orgs/' + org + '/repos', filename=None, \
        entity='repo', authuser='msftgits', \
        fields=['name', 'owner.login', 'private', 'fork'], headers={})
    for repo in repodata:
        open(filename, 'a').write(org + ',' + repo['name'] + ',' + \
            repo['private'] + ',' + str(repo['fork']) + '\n')

#-------------------------------------------------------------------------------
def appendteams(filename, org=None):
    """Append team info for an org to teams.csv data file.

    Special case: if no org provided, initialize the data file.
    """
    if not org:
        open(filename, 'w').write('org,name,id,privacy,permission\n')
        return

    teamdata = gdwrapper(endpoint='/orgs/' + org + '/teams', filename=None, \
        entity='team', authuser='msftgits', \
        fields=['name', 'id', 'privacy', 'permission'], headers={})
    for team in teamdata:
        open(filename, 'a').write(org + ',' + team['name'] + ',' + \
            str(team['id']) + ',' + team['privacy'] + ',' + \
            team['permission'] + '\n')

#-------------------------------------------------------------------------------
def authenticate():
    """Set up gitdata authentication.
    Currently using msftgits for all auditing of Microsoft accounts.
    """
    gd.auth_config({'username': 'msftgits'})

#-------------------------------------------------------------------------------
def gdwrapper(*, endpoint, filename, entity, authuser, fields, headers):
    """gitdata wrapper for automating gitdata calls
    """
    gd._settings.display_data = False
    gd._settings.verbose = False
    gd._settings.datasource = 'a'
    gd.auth_config({'username': authuser})
    templist = gd.github_data(
        endpoint=endpoint, entity=entity, fields=fields,
        constants={"user": authuser}, headers=headers)
    sorted_data = sorted(templist, key=gd.data_sort)
    gd.data_display(sorted_data)
    gd.data_write(filename, sorted_data)
    return sorted_data

#-------------------------------------------------------------------------------
def collabapis(orgname, filename):
    """Testing/comparison of the repo-level and org-level collaborator APIs.

    If filename specified, appends the collaborators to that CSV file.
    """

    # REPO-level collaborators ...
    repodata = gdwrapper(endpoint='/orgs/' + orgname + '/repos', filename=None, \
        entity='repo', authuser='msftgits', \
        fields=['name', 'owner.login', 'private', 'fork'], headers={})
    for repo in repodata:
        if repo['private'] == 'private':
            continue # skip private repos
        reponame = repo['name']
        endpoint = '/repos/' + orgname + '/' + reponame + '/collaborators'
        collabdata = gdwrapper(endpoint='/repos/' + orgname + '/' + reponame + '/collaborators', \
            filename=None, entity='collab', authuser='msftgits', \
            fields=['login', 'repo', 'id'], headers={})
        for collab in collabdata:
            print(orgname + ',' + reponame + ',' + collab['login'])

    # ORG-level collaborators ...
    headers_dict = {"Accept": "application/vnd.github.korra-preview"}
    collabdata = gdwrapper(endpoint='/orgs/' + orgname + '/outside_collaborators', \
        filename=None, entity='collab', authuser='msftgits', \
        fields=['*'], headers=headers_dict)
    for collab in collabdata:
        print(orgname + ',,' + collab['login'])

#-------------------------------------------------------------------------------
def getmsdata():
    """Retrieve/refresh all Microsoft data needed for audit reports.
    """
    orgfile = 'ghaudit/orgs.csv'
    teamfile = 'ghaudit/teams.csv'
    repofile = 'ghaudit/repos.csv'
    collabfile = 'ghaudit/collabs.csv'

    # create the ORG data file, list of organizations to be audited
    # Below is inline automation of this command:
    #   gitdata orgs -amsftgits -sa -nghaudit/orgs.csv -flogin/user/id
    gdwrapper(endpoint='/user/orgs', filename=orgfile, entity='org', \
        authuser='msftgits', fields=['login', 'user', 'id'])

    # create the TEAM and REPO data files, iterating over ORGs
    appendteams(teamfile) # initialize data file
    appendrepos(repofile) # initialize data file
    firstline = True
    for line in open(orgfile, 'r').readlines():
        if firstline:
            firstline = False
            continue
        orgname = line.split(',')[0]
        appendteams(teamfile, orgname)
        appendrepos(repofile, orgname)
        break #///

    # create the COLLAB data file, iterating over REPOs
    #/// initialize with appendcollabs()
    firstline = True
    for line in open(repofile, 'r').readlines():
        if firstline:
            firstline = False
            continue
        orgname = line.split(',')[0]
        reponame = line.split(',')[1]
        print('///appendcollabs(collabfile,' + orgname + ',' + reponame + ')')

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
    #getmsdata()

    #/// write header to collabapis.csv org,repo,collaborator
    collabapis('deployr')
    #/// for each MS* org, collabapis(orgname, 'collabapis.csv')
