"""ghaudit.py
Tools used for ad-hoc audit of GitHub accounts for Microsoft users.
"""
import configparser
import gzip
import json
import os
import sys

import gitdata as gd

def appendcollabs_org(filename, org=None): #---------------------------------<<<
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

def appendcollabs_repo(filename, org, repo): #-------------------------------<<<
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

def appendorgmembers(filename, org=None): #----------------------------------<<<

    """Append member info for an organization to orgmembers.csv data file.

    Special case: if no org provided, initialize the data file.
    """
    if not org:
        open(filename, 'w').write('org,login,type,site_admin,linked\n')
        return

    memberdata = gdwrapper(endpoint='/orgs/' + org + '/members?per_page=100', filename=None, \
        entity='member', authuser='msftgits', \
        fields=['login', 'type', 'site_admin'], headers={})
    for member in memberdata:
        site_admin = 'True' if member['site_admin'] else 'False'
        linked = 'True' if islinked(member['login']) else 'False'
        open(filename, 'a').write(org + ',' + member['login'] + ',' + \
            member['type'] + ',' + site_admin + ',' + \
            linked + '\n')

def appendrepos(filename, org=None): #---------------------------------------<<<
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

def appendrepoteams(filename, teamid=None): #--------------------------------<<<
    """Append teamp-repo info for a teamp to repoteams.csv data file.

    Special case: if no teamid provided, initialize the data file.
    """
    if not teamid:
        open(filename, 'w').write('org,repo,teamid,admin,push,pull\n')
        return

    repodata = gdwrapper(endpoint='/teams/' + teamid + '/repos?per_page=100',\
        filename=None, entity='repo', authuser='msftgits', \
        fields=['full_name','permissions.admin','permissions.push','permissions.pull'], \
        headers={})
    for repo in repodata:
        orgname, reponame = repo['full_name'].split('/')
        open(filename, 'a').write(orgname + ',' + reponame + ',' + teamid + ',' + \
            str(repo['permissions_admin']) + ',' + \
            str(repo['permissions_push']) + ',' + \
            str(repo['permissions_pull']) + '\n')

def appendteammembers(filename, team=None): #--------------------------------<<<
    """Append member info for a team to teammembers.csv data file.

    Special case: if no team provided, initialize the data file.
    """
    if not team:
        open(filename, 'w').write('teamid,login,type,site_admin,linked\n')
        return

    memberdata = gdwrapper(endpoint='/teams/' + team + '/members?per_page=100', \
        filename=None, entity='teammember', authuser='msftgits', \
        fields=['login', 'type', 'site_admin'], headers={})
    for member in memberdata:
        site_admin = 'True' if member['site_admin'] else 'False'
        linked = 'True' if islinked(member['login']) else 'False'
        open(filename, 'a').write(team + ',' + member['login'] + ',' + \
            member['type'] + ',' + site_admin + ',' + \
            linked + '\n')

def appendteams(filename, org=None): #---------------------------------------<<<
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

def audituser(username): #---------------------------------------------------<<<
    """Show which repos/orgs/teams a GitHub user is associated with.
    """
    print('\nGitHub username:'.ljust(80, '-'))
    print(username + \
        ' (linked to ' + linkedemail(username) + ')' if islinked(username) \
        else ' (not linked)')

    print('ORG memberships:'.ljust(80, '-'))
    for org in orgmemberships(username):
        print(org)

    print('TEAM memberships:'.ljust(80, '-'))
    lastline = '*none*' # used to avoid re-printing of an org after first time
    for teamid in teammemberships(username):
        thisline = teamdesc(teamid)
        if thisline.split('/')[0][26:] == lastline.split('/')[0][26:]:
            # repetition of same org, so remove org from printed line
            permpriv = thisline[:26]
            reponame = thisline.split('/')[1]
            print(permpriv.ljust(len(thisline) - len(reponame) - 1) + '/' + reponame, end='')
        else:
            print(thisline, end='')
        lastline = thisline
        repolist = teamrepos(teamid)
        print(' (' + str(len(repolist)) + ' repos)')

    print('COLLABORATOR relationships:'.ljust(80, '-'))
    for collab in collaborations(username):
        if '/' in collab:
            print('repo: ' + collab)
        else:
            print('org:  ' + collab)

    #/// for each repo: last update, readme, contributing, license, code of conduct

def authenticate(): #--------------------------------------------------------<<<
    """Set up gitdata authentication.
    Currently using msftgits for all auditing of Microsoft accounts.
    """
    gd.auth_config({'username': 'msftgits'})

def azure_setting(section, setting): #---------------------------------------<<<
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

def collabapis(orgname, filename=None): #------------------------------------<<<
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

def collaborations(username): #----------------------------------------------<<<
    """Return list of orgs and/or repos that user has a collaborator
    relationship with.
    """
    collabs = []
    firstline = True
    for line in open('ghaudit/collabs.csv', 'r').readlines():
        if firstline:
            firstline = False
            continue
        org = line.split(',')[0]
        repo = line.split(',')[1]
        user = line.split(',')[2].strip()
        if username.lower() == user.lower():
            if repo:
                collabs.append(org + '/' + repo)
            else:
                collabs.append(org)
    return sorted(collabs)

def gdwrapper(*, endpoint, filename, entity, authuser, #---------------------<<<
              fields, headers, verbose=True):
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

    if verbose:
        # display rate-limit status
        used = gd._settings.last_ratelimit - gd._settings.last_remaining
        print('Rate Limit: ' + str(gd._settings.last_remaining) +
                        ' available, ' + str(used) +
                        ' used, ' + str(gd._settings.last_ratelimit) + ' total')

    return sorted_data

def islinked(username): #----------------------------------------------------<<<
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

def latestlinkdata(): #------------------------------------------------------<<<
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

def linkedemail(username): #-------------------------------------------------<<<
    """Returned linked email address (if any) for specified GitHub username.
    """
    if not hasattr(gd._settings, 'linkedemail'):
        gd._settings.linkedemail = dict()
        firstline = True
        for line in open('ghaudit/linkdata.csv', 'r').readlines():
            if firstline:
                firstline = False
                continue
            gd._settings.linkedemail[line.split(',')[0].lower()] = line.split(',')[1].strip()

    return gd._settings.linkedemail.get(username.lower(), None)

def orgmemberships(username): #----------------------------------------------<<<
    """Return list of orgs that user is member of.
    """
    orgs = []
    firstline = True
    for line in open('ghaudit/orgmembers.csv', 'r').readlines():
        if firstline:
            firstline = False
            continue
        orgname = line.split(',')[0]
        user = line.split(',')[1]
        if username.lower() == user.lower():
            orgs.append(orgname)
    return orgs

def printhdr(acct, msg): #---------------------------------------------------<<<
    """Print a header for a section of the audit report.
    """
    ndashes = 65 - len(msg)
    print('>> ' + msg + ' <<' + ndashes*'-' + ' account: ' + acct.upper())

def teamdesc(teamid): #------------------------------------------------------<<<
    """Return a 1-liner description for specified team id.
    """
    if not hasattr(gd._settings, 'teamdescription'):
        gd._settings.teamdescription = dict()
        firstline = True
        for line in open('ghaudit/teams.csv', 'r').readlines():
            if firstline:
                firstline = False
                continue
            orgname = line.split(',')[0]
            teamname = line.split(',')[1]
            teamno = line.split(',')[2]
            privacy = line.split(',')[3]
            perms = line.split(',')[4].strip()
            gd._settings.teamdescription[teamno] = 'perm=' + perms.ljust(6) + \
                'privacy=' + privacy.ljust(7) + orgname + '/' + teamname

    return gd._settings.teamdescription.get(teamid, teamid + ' (unknown team id)')

def teammemberships(username): #---------------------------------------------<<<
    """Return list of teams that user is member of.
    """
    teams = []
    firstline = True
    for line in open('ghaudit/teammembers.csv', 'r').readlines():
        if firstline:
            firstline = False
            continue
        teamid = line.split(',')[0]
        user = line.split(',')[1]
        if username.lower() == user.lower():
            teams.append(teamid)
    return teams

def teamrepos(teamid): #-----------------------------------------------------<<<
    """Return list of repos that this team has rights to.
    """
    repos = []
    firstline = True
    for line in open('ghaudit/repoteams.csv', 'r').readlines():
        if firstline:
            firstline = False
            continue
        this_id = line.split(',')[2]
        if this_id == teamid:
            reponame = line.split(',')[1]
            repos.append(reponame)
    return repos

def updatelinkdata(): #------------------------------------------------------<<<
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

def updatemsdata(): #--------------------------------------------------------<<<
    """Retrieve/refresh all Microsoft data needed for audit reports.
    """
    orgfile = 'ghaudit/orgs.csv'
    teamfile = 'ghaudit/teams.csv'
    repofile = 'ghaudit/repos.csv'
    collabfile = 'ghaudit/collabs.csv'
    tmembersfile = 'ghaudit/teammembers.csv'
    omembersfile = 'ghaudit/orgmembers.csv'
    repoteamsfile = 'ghaudit/repoteams.csv'

    # these variables control which data files are generated (for testing, etc.)
    write_orgs = False
    write_teams = False
    write_repos = False
    write_collabs = False
    write_linkdata = False
    write_teammembers = False
    write_orgmembers = False
    write_repoteams = False

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
    if write_orgmembers:
        appendorgmembers(omembersfile) # initialize data file
    firstline = True
    for line in open(orgfile, 'r').readlines():
        if firstline:
            firstline = False
            continue
        orgname = line.split(',')[0]
        print('ORG = ' + orgname)
        if write_teams:
            appendteams(teamfile, orgname)
        if write_repos:
            appendrepos(repofile, orgname)
        if write_collabs:
            appendcollabs_org(collabfile, orgname)
        if write_orgmembers:
            appendorgmembers(omembersfile, orgname)

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

    if write_repoteams:
        appendrepoteams(repoteamsfile) # initialize data file
        firstline = True
        for line in open(teamfile, 'r').readlines():
            if firstline:
                firstline = False
                continue
            teamid = line.split(',')[2]
            appendrepoteams(repoteamsfile, teamid)

def userrepos(acct): #-------------------------------------------------------<<<
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

if __name__ == '__main__':
    sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf8', buffering=1)
    #updatemsdata()

    updatelinkdata()

    #if len(sys.argv) < 2:
    #    audituser('meganbradley')
    #else:
    #    for username in sys.argv[1:]:
    #        audituser(username)
