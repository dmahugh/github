"""ghaudit.py
Audit GitHub account for Microsoft users.
"""
import configparser
import gzip
import json
import os
import sys

import gitdata as gd

#-------------------------------------------------------------------------------
def appendcollabs_org(filename, org=None):
    """Append collaborator info for an org to collabs.csv data file.

    Special case: if no org provided, initialize the data file.
    """
    if not org:
        open(filename, 'w').write('org,repo,collaborator\n')
        return

    headers_dict = {"Accept": "application/vnd.github.korra-preview"}
    endpoint = '/orgs/' + org + '/outside_collaborators?per_page=100'
    collabdata = gdwrapper(endpoint=endpoint, \
        filename=None, entity='collab', authuser='msftgits', \
        fields=['*'], headers=headers_dict)
    for collab in collabdata:
        line = org + ',,' + collab['login']
        open(filename, 'a').write(line + '\n')

#-------------------------------------------------------------------------------
def appendcollabs_repo(filename, org, repo):
    """Append collaborator info for an org/repo to collabs.csv data file.

    Org/repo required - assumes data file already initialized by appendcollab_org().
    """
    headers_dict = {"Accept": "application/vnd.github.korra-preview"}
    endpoint = '/repos/' + org + '/' + repo + '/collaborators?per_page=100&affiliation=outside'
    collabdata = gdwrapper(endpoint=endpoint, \
        filename=None, entity='collab', authuser='msftgits', \
        fields=['login', 'repo', 'id'], headers=headers_dict)
    for collab in collabdata:
        line = org + ',' + repo + ',' + collab['login']
        open(filename, 'a').write(line + '\n')

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
def appendteammembers(filename, team=None):
    """Append member info for a team to teammembers.csv data file.

    Special case: if no team provided, initialize the data file.
    """
    if not team:
        open(filename, 'w').write('teamid,login,type,site_admin,linked\n')
        return

    memberdata = gdwrapper(endpoint='/teams/' + team + '/members', filename=None, \
        entity='teammember', authuser='msftgits', \
        fields=['login', 'type', 'site_admin'], headers={})
    for member in memberdata:
        site_admin = 'True' if member['site_admin'] else 'False'
        linked = 'True' if islinked(member['login']) else 'False'
        open(filename, 'a').write(team + ',' + member['login'] + ',' + \
            member['type'] + ',' + site_admin + ',' + \
            linked + '\n')

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
def azure_setting(section, setting):
    """Get Azure setting from private INI data.

    section = section within the INI file
    setting = the setting to return from within that section

    Returns the setting's value, or None if not found.
    """
    source_folder = os.path.dirname(os.path.realpath(__file__))
    datafile = os.path.join(source_folder, '../_private/azure.ini')
    config = configparser.ConfigParser()
    config.read(datafile)
    try:
        retval = config.get(section, setting)
    except configparser.NoSectionError:
        retval = None
    return retval

#-------------------------------------------------------------------------------
def collabapis(orgname, filename=None):
    """Testing/comparison of the repo-level and org-level collaborator APIs.

    If filename specified, appends the collaborators to that CSV file.
    """

    # REPO-level collaborators ...
    repodata = gdwrapper(endpoint='/orgs/' + orgname + '/repos?per_page=100', filename=None, \
        entity='repo', authuser='msftgits', \
        fields=['name', 'owner.login', 'private', 'fork'], headers={})
    for repo in repodata:
        if repo['private'] == 'private':
            continue # skip private repos
        reponame = repo['name']
        endpoint = '/repos/' + orgname + '/' + reponame + '/collaborators?per_page=100'
        collabdata = gdwrapper(endpoint=endpoint, \
            filename=None, entity='collab', authuser='msftgits', \
            fields=['login', 'repo', 'id'], headers={})
        for collab in collabdata:
            line = orgname + ',' + reponame + ',' + collab['login']
            print(line)
            if filename:
                open(filename, 'a').write(line + '\n')

    # ORG-level collaborators ...
    headers_dict = {"Accept": "application/vnd.github.korra-preview"}
    endpoint = '/orgs/' + orgname + '/outside_collaborators?per_page=100'
    collabdata = gdwrapper(endpoint=endpoint, \
        filename=None, entity='collab', authuser='msftgits', \
        fields=['*'], headers=headers_dict)
    for collab in collabdata:
        line = orgname + ',,' + collab['login']
        print(line)
        if filename:
            open(filename, 'a').write(line + '\n')

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

    # display rate-limit status
    used = gd._settings.last_ratelimit - gd._settings.last_remaining
    print('Rate Limit: ' + str(gd._settings.last_remaining) +
                    ' available, ' + str(used) +
                    ' used, ' + str(gd._settings.last_ratelimit) + ' total')

    return sorted_data

#-------------------------------------------------------------------------------
def islinked(username):
    """Returns True if passed GitHub username is a linked Microsoft account.
    """
    if not hasattr(gd._settings, 'linked'):
        gd._settings.linked = []
        firstline = True
        for line in open('ghaudit/linkdata.csv', 'r').readlines():
            if firstline:
                firstline = False
                continue
            gd._settings.linked.append(line.split(',')[0].lower())

    return (username.lower() in gd._settings.linked)

#-------------------------------------------------------------------------------
def latestlinkdata():
    """Returns the most recent filename for Azure blobs that contain linkdata.
    """
    azure_acct = azure_setting('linkingdata', 'account')
    azure_key = azure_setting('linkingdata', 'key')
    azure_container = azure_setting('linkingdata', 'container')

    from azure.storage.blob import BlockBlobService
    block_blob_service = BlockBlobService(account_name=azure_acct, account_key=azure_key)
    blobs = block_blob_service.list_blobs(azure_container)
    latest = ''
    for blob in blobs:
        latest = blob.name if blob.name > latest else latest
    return latest if latest else None

#-------------------------------------------------------------------------------
def printhdr(acct, msg):
    """Print a header for a section of the audit report.
    """
    ndashes = 65 - len(msg)
    print('>> ' + msg + ' <<' + ndashes*'-' + ' account: ' + acct.upper())

#-------------------------------------------------------------------------------
def updatelinkdata():
    """Retrieve the latest Microsoft linking data from Azure blob storage
    and store in the ghaudit folder.
    """
    azure_acct = azure_setting('linkingdata', 'account')
    azure_key = azure_setting('linkingdata', 'key')
    azure_container = azure_setting('linkingdata', 'container')
    azure_blobname = latestlinkdata()
    gzfile = 'ghaudit/' + azure_blobname
    print('retrieving link data: ' + azure_blobname)

    # download the Azure blob
    from azure.storage.blob import BlockBlobService
    block_blob_service = BlockBlobService(account_name=azure_acct, account_key=azure_key)
    block_blob_service.get_blob_to_path(azure_container, azure_blobname, gzfile)

    # decompress the JSON file and write to linkdata.csv
    outfile = 'ghaudit/linkdata.csv'
    with open(outfile, 'w') as fhandle:
        fhandle.write('githubuser,email\n')
        for line in gzip.open(gzfile).readlines():
            jsondata = json.loads(line.decode('utf-8'))
            outline = jsondata['ghu'] + ',' + jsondata['aadupn']
            fhandle.write(outline + '\n')

#-------------------------------------------------------------------------------
def updatemsdata():
    """Retrieve/refresh all Microsoft data needed for audit reports.
    """
    orgfile = 'ghaudit/orgs.csv'
    teamfile = 'ghaudit/teams.csv'
    repofile = 'ghaudit/repos.csv'
    collabfile = 'ghaudit/collabs.csv'
    tmembersfile = 'ghaudit/teammembers.csv'

    # these variables control which data files are generated (for testing, etc.)
    write_orgs = False
    write_teams = False
    write_repos = False
    write_collabs = False
    write_linkdata = False
    write_teammembers = True

    if write_orgs:
        # create the ORG data file, list of organizations to be audited
        # Below is inline automation of this command:
        #   gitdata orgs -amsftgits -sa -nghaudit/orgs.csv -flogin/user/id
        gdwrapper(endpoint='/user/orgs', filename=orgfile, entity='org', \
            authuser='msftgits', fields=['login', 'user', 'id'], headers={})

    # create the TEAM and REPO data files, iterating over ORGs
    if write_teams:
        appendteams(teamfile) # initialize data file
    if write_repos:
        appendrepos(repofile) # initialize data file
    if write_collabs:
        appendcollabs_org(collabfile) # initialize data file
    firstline = True
    for line in open(orgfile, 'r').readlines():
        if firstline:
            firstline = False
            continue
        orgname = line.split(',')[0]
        #print('ORG = ' + orgname)
        if write_teams:
            appendteams(teamfile, orgname)
        if write_repos:
            appendrepos(repofile, orgname)
        if write_collabs:
            appendcollabs_org(collabfile, orgname)

    if write_collabs:
        # iterate over REPOs to add repo-level collaborators
        firstline = True
        for line in open(repofile, 'r').readlines():
            if firstline:
                firstline = False
                continue
            orgname = line.split(',')[0]
            reponame = line.split(',')[1]
            print('REPO = ' + orgname + '/' + reponame)
            appendcollabs_repo(collabfile, orgname, reponame)

    if write_linkdata:
        updatelinkdata() # get latest Microsoft linking data

    if write_teammembers:
        appendteammembers(tmembersfile) # initialize data file
        firstline = True
        for line in open(teamfile, 'r').readlines():
            if firstline:
                firstline = False
                continue
            print(line.strip())
            teamid = line.split(',')[2]
            appendteammembers(tmembersfile, teamid)

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
    sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf8', buffering=1)
    updatemsdata()
