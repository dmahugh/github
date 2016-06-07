"""Functions for caching GitHub API responses and running reports from them.

_adminteams_to_csv() ----> Write CSV file of all admin teams for private MS repos.
_azure_repo_report() ----> Custom report on Azure repo collaborator counts.
_capture_files() --------> Capture specified files to data/ subfolder.
_collaborators_to_csv() -> Write CSV file of all collaborators for MS repos.
_files_to_csv() ---------> Write CSV files of all filenames in public MS repos.
_orgmembers_to_csv() ----> Write CSV file of all members of Microsoft orgs.
_repos_to_csv() ---------> Write CSV file of all repos in Microsoft orgs.
_teammembers_to_csv() ---> Write CSV file of all admin team members.

adminteams() ------------> Get info about admin teams for org's private repos.
adminteams_update() -----> Update admin teams for specified org.
adminteams_update_all() -> Update admin teams for all Microsoft orgs.
cache_status() ----------> Print status of specified entity's cached data.
collaborators() ---------> Get collaborators for specified repo or org.
collaborators_update() --> Update saved collaborators for Microsoft repos.
datafile_latest() -------> Get most recent saved filename for specified entity.
datafile_next() ---------> Generate current datafile name for specified entity.
ms_email() --------------> Convert GitHub username to Microsoft email address.
orgmembers() ------------> Get org members for one or more organizations.
orgmembers_update() -----> Update saved members for Microsoft orgs.
orgs() ------------------> Get current list of Microsoft orgs on GitHub.
orgs_update() -----------> Update saved Microsoft orgs.
repos() -----------------> Get repos for one or more Microsoft orgs.
repos_update() ----------> Update saved repos for Microsoft orgs.
repos_update_all() ------> Update saved repos for all Microsoft orgs.
teammembers() -----------> Get members for specified team or username.
teammembers_update() ----> Update saved members for Microsoft teams.
teams() -----------------> Get teams for one or more organizations.
teams_update() ----------> Update saved teams for all Microsoft organizations.
"""
import datetime
import glob
import json

import gitinfo as gi

#------------------------------------------------------------------------------
class _settings:
    """This class exists to provide a namespace used for global settings.
    """
    email = {} # dictionary of GitHub usernames and Microsoft email addresses

#-------------------------------------------------------------------------------
def _adminteams_to_csv():
    """Write admin team data to CSV for all private Microsoft repos.

    output file = reports/AdminTeams.csv
    """
    teamlist = adminteams(org='MS*')

    fhandle = open('reports/AdminTeams.csv', 'w')
    fhandle.write('org, repo, permission, privacy, name, id' + '\n')
    for team in teamlist:
        csvline = team['org'] + ', ' + team['repo'] + ', ' + \
            team['permission'] + ', ' + team['privacy'] + ', ' + \
            team['name'] + ', ' + str(team['id'])
        fhandle.write(csvline + '\n')
    fhandle.close()

#-------------------------------------------------------------------------------
def _azure_repo_report():
    """Get collaborator counts for Azure repos.
    """

    fhandle = open('azure-collaborators.csv', 'w')

    for repo in repos(org='azure'):
        reponame = repo['repo'].lower()
        endpoint = 'https://api.github.com/repos/azure/' + reponame + '/collaborators'
        response = gi.github_api(endpoint=endpoint, auth=gi.auth_user())
        thispage = json.loads(response.text)
        collabs_page1 = len(thispage)

        pagelinks = gi.pagination(response)
        lastpage_url = pagelinks['lastURL']
        if lastpage_url:
            totpages = int(pagelinks['lastpage'])
            response = gi.github_api(endpoint=lastpage_url, auth=gi.auth_user())
            lastpage = json.loads(response.text)
            collabs_lastpage = len(lastpage)
        else:
            totpages = 1
            collabs_lastpage = collabs_page1

        if totpages == 1:
            totcollabs = collabs_page1
        else:
            totcollabs = collabs_lastpage + ((totpages-1) * collabs_page1)


        print(reponame + ', ' + ('Private' if repo['private'] else 'Public') + \
              ', ' + str(totcollabs))
        print(reponame + ', ' + ('Private' if repo['private'] else 'Public') + \
              ', ' + str(totcollabs), file=fhandle)
    fhandle.close()

#-------------------------------------------------------------------------------
def _capture_files(file_to_capture, capture_folder, fileext):
    """Capture specified files to data/ subfolder.

    file_to_capture = the filename to be captured (e.g., 'readme.md')
    capture_folder = the subfolder under .\data to capture files into.
    fileext = extension to use for saved file (should match extension of
              file_to_capture)
    """
    import codecs
    import requests

    datafiles = glob.glob('data/files-*.csv')
    for datafile in datafiles:
        print('>>>>', datafile)
        with open(datafile, 'r') as fhandle:
            header_row = True
            for datarow in fhandle:

                if header_row:
                    header_row = False
                    continue

                fields = datarow.split(',')
                org = fields[0]
                repo = fields[1]
                folder = fields[2]
                filename = fields[3]
                if filename.lower() != file_to_capture.lower() or folder:
                    continue

                url = 'https://raw.githubusercontent.com/' + \
                    org + '/' + repo + '/master/' + filename
                print('>>> ' + url)

                response = requests.get(url)
                outfile = 'data/' + capture_folder + '/' + org + '--' + repo + fileext
                with codecs.open(outfile, 'w', 'utf-8') as fhandle:
                    fhandle.write(response.text)

#-------------------------------------------------------------------------------
def _collaborators_to_csv():
    """Generate a CSV file containing all collaborators for all Microsoft repos.

    output file = reports/Collaborators.csv
    """
    fhandle = open('reports/Collaborators.csv', 'w')
    fhandle.write('org, repo, login, id, site_admin, type, admin_perm' + '\n')
    for org in orgs():
        collabs = collaborators(org=org)
        for collab in collabs:
            adminval = 'True' if collab['site_admin'] else 'False'
            adminval2 = 'True' if collab['permissions_admin'] else 'False'
            csvline = collab['org'] + ', ' + collab['repo'] + ', ' + \
                collab['login'] + ', ' + str(collab['id']) + ', ' + \
                adminval + ', ' + collab['type'] + ', ' + \
                adminval2
            fhandle.write(csvline + '\n')
        print('Collaborator data written for ' + org.upper())

    fhandle.close()

#-------------------------------------------------------------------------------
def _files_to_csv(skiporgs=None):
    """Write CSV file of all filenames from Microsoft public repos.

    skiporgs = an optional list of orgs to NOT have a CSV file generated. Can be
    used to skip already-handled orgs if this long-running process crashes in
    midstream. NOTE: should be lower-case.
    """
    # need to open CSV file with codecs.open to force utf-8 output, otherwise
    # will get UnicodeDecodeError on some filenames
    import codecs

    gi.auth_config({'username': 'msftgits'})
    gi.session_start('retrieve file trees')
    for org in orgs():
        if org.lower() in skiporgs:
            continue
        outfile = datafile_next('files-' + org, 'csv')
        print('writing file -> ' + outfile)
        fhandle = codecs.open(outfile, 'w', 'utf-8')
        fhandle.write('owner,repo,folder,filename,size,sha\n')
        for repo in repos(org=org, repotype='public'):
            filelist = gi.files(owner=org, repo=repo['repo'])
            for file in filelist:
                fhandle.write(file.owner + ',' + file.repo + ',' + \
                              file.folder + ',' + file.filename + \
                              ',' + str(file.size) + ',' + file.sha + '\n')
        fhandle.close()
    gi.session_end('retrieve file trees')

#-------------------------------------------------------------------------------
def _orgmembers_to_csv():
    """Write CSV file of all members of Microsoft orgs.
    """
    memberlist = orgmembers(org='MS*')

    fhandle = open('reports/OrgMembers.csv', 'w')
    fhandle.write('org,login,id,site_admin' + '\n')

    for member in memberlist:
        siteadmin = 'True' if member['site_admin'] else 'False'
        csvline = member['org'] + ',' + member['login'] + ',' + \
            str(member['id']) + ',' + siteadmin
        fhandle.write(csvline + '\n')

    fhandle.close()

#-------------------------------------------------------------------------------
def _repos_to_csv():
    """Write Microsoft repos to these files in the reports folder:

    - MicrosoftRepos.csv (list of all repos)
    - MicrosoftReposTotals.csv (totals by org)
    - MicrosoftReposNew.csv (all repos created since 4/5/2016)
    - MicrosoftReposNewTotals.csv (count of repos created since 4/5/2016)
    """
    repolist = repos(org='MS*')

    fhandle = open('reports/MicrosoftRepos.csv', 'w')
    fhandle.write('org, repo, type, created' + '\n')
    for repo in repolist:
        repotype = 'private' if repo['private'] else 'public'
        csvline = repo['org'] + ', ' + repo['repo'] + ', ' + repotype + \
            ', ' + repo['created_at'][:10]
        fhandle.write(csvline + '\n')
    fhandle.close()

    fhandle = open('reports/MicrosoftReposTotals.csv', 'w')
    fhandle.write('org, public, private' + '\n')
    for org in orgs():
        public = len([_ for _ in repolist if _['org'] == org and not _['private']])
        private = len([_ for _ in repolist if _['org'] == org and _['private']])
        csvline = org + ', ' + str(public) + ', ' + str(private)
        fhandle.write(csvline + '\n')
    fhandle.close()

    fhandle = open('reports/MicrosoftReposNew.csv', 'w')
    fhandle.write('org, repo, type, created' + '\n')
    for repo in repolist:
        created_date = datetime.datetime.strptime(repo['created_at'][:10], '%Y-%m-%d').date()
        if created_date < datetime.date(2016, 4, 5):
            continue
        repotype = 'private' if repo['private'] else 'public'
        csvline = repo['org'] + ', ' + repo['repo'] + ', ' + repotype + \
            ', ' + repo['created_at'][:10]
        fhandle.write(csvline + '\n')
    fhandle.close()

    fhandle = open('reports/MicrosoftReposNewTotals.csv', 'w')
    fhandle.write('org, public, private' + '\n')
    for org in orgs():
        public = 0
        private = 0
        for repo in repolist:
            if repo['org'] == org:
                created_date = datetime.datetime.strptime(repo['created_at'][:10],
                                                          '%Y-%m-%d').date()
                if created_date >= datetime.date(2016, 4, 5):
                    if repo['private']:
                        private += 1
                    else:
                        public += 1
        if private + public > 0:
            csvline = org + ', ' + str(public) + ', ' + str(private)
            fhandle.write(csvline + '\n')
    fhandle.close()

#-------------------------------------------------------------------------------
def _teammembers_to_csv():
    """Write CSV file of all admin team members.
    """
    teamlist = adminteams(org='MS*')

    fhandle = open('reports/TeamMembers.csv', 'w')
    fhandle.write('org,team_name,teamid,login,membid,site_admin' + '\n')
    for team in teamlist:
        print(team['org'] + ' -> ' + team['name'])
        members = teammembers(teamid=team['id'])
        for member in members:
            siteadmin = 'True' if member['site_admin'] else 'False'
            csvline = team['org'] + ', ' + member['team_name'] + ', ' + \
                str(team['id']) + ', ' + member['login'] + ', ' + \
                str(member['id']) + ', ' + siteadmin
            fhandle.write(csvline + '\n')

    fhandle.close()

#-------------------------------------------------------------------------------
def adminteams(org=None):
    """Get information about admin teams for an org's private repos.

    org = organization, list of organizations, or 'MS*' for all Microsoft orgs
    """
    if org == 'MS*':
        orglist = orgs() # all Microsoft orgs
    elif isinstance(org, str):
        orglist = [org] # convert single organization to a list
    else:
        orglist = org

    retval = [] # the list to be returned

    for org in orglist:
        filename = datafile_latest('adminteams-' + org)
        if not filename:
            print('No adminteam data found for org -> ' + org)
            continue
        teamlist = gi.json_read(filename)
        retval.extend([{"org": org, "repo": team['repo'], "name": team['name'],
                        "id": team['id'], "privacy": team['privacy'],
                        "permission": team['permission']} for team in teamlist])

    return sorted(retval, key=lambda x: x['org'].lower()+x['repo'].lower()+x['name'].lower())

#-------------------------------------------------------------------------------
def adminteams_update(org=None):
    """Update admin teams for specified organization's PRIVATE repos.

    org = organization name

    Writes data file adminteams-org-YYYY-MM-DD-HHMM.json
    """
    master_json = [] # consolidated master list to be written to output file

    for repo in repos(org=org, repotype='private'):
        endpoint = 'https://api.github.com/repos/' + org + '/' + repo['repo'] + '/teams'

        totpages = 0

        while True:

            response = gi.github_api(endpoint=endpoint, auth=gi.auth_user())
            if response.ok:
                totpages += 1
                thispage = json.loads(response.text)
                teamdata = []
                for team in thispage:
                    team.update({"org": repo['org']}) # add org to each entry
                    team.update({"repo": repo['repo']}) # add repo to each entry
                    teamdata.append(team)
                master_json.extend(teamdata)

            pagelinks = gi.pagination(response)
            endpoint = pagelinks['nextURL']
            if not endpoint:
                break # there are no more results to process

            print('processing page {0} of {1}'. \
                        format(pagelinks['nextpage'], pagelinks['lastpage']))

        print('pages processed: {0}, total teams: {1}'. \
            format(totpages, len(master_json)))

    filename = datafile_next('adminteams-' + org)
    gi.json_write(source=master_json, filename=filename)
    print('data file written -> ' + filename)

#-------------------------------------------------------------------------------
def adminteams_update_all():
    """Get admin teams for private repos in all Microsoft orgs.
    """
    for org in orgs():
        adminteams_update(org=org)
        gi.log_apistatus()

#-------------------------------------------------------------------------------
def cache_status(entity=None):
    """Print the status of the most recent saved data for specified entity.

    entity = the string that identifies the entity (e.g., 'orgs' or
             'repos-azure') or one of these special cases:
             'repos=*' -> display status of repos data for all Microsoft orgs
    """
    if entity == 'repos-*': # special case
        total_repos = 0
        for org in orgs():
            filename = datafile_latest('repos-' + org)
            json_data = gi.json_read(filename)
            print('Cached repos status for ' + (org + ' ').ljust(30, '-') + \
                '> {0} repos, {1} fields'.format(len(json_data), \
                len(json_data[0].keys())))
            total_repos += len(json_data)
        print('TOTAL REPOS '.ljust(54, '-') + '> {0}'.format(total_repos))
        return

    filename = datafile_latest(entity)

    if not filename:
        print('ERROR: no data file found for entity "' + entity + '".')
        return

    print('CACHE STATUS -------------> ' + entity)
    print('Most recent saved data ---> ' + filename)

    json_data = gi.json_read(filename)

    print('Total entities found -----> {0}'.format(len(json_data)))
    print('Fields for each entity ---> ' + ', '.join(json_data[0].keys()))

#-------------------------------------------------------------------------------
def collaborators(org=None, repo=None):
    """Get collaborators for specified repo or org.

    org = organization name (required)
    repo = repo name, or None for all repos in this org.
    """
    retval = []

    filename = datafile_latest('collaborators-' + org)
    if not filename:
        print('ERROR: no data file found for collaborators-' + org)
        return retval

    orgcollabs = gi.json_read(filename)

    for collab in orgcollabs:
        if not repo or collab['repo'].lower() == repo.lower():
            retval.append({"org":collab['org'],
                           "repo":collab['repo'],
                           "login":collab['login'],
                           "id":collab['id'],
                           "type":collab['type'],
                           "permissions_admin":collab['permissions']['admin'],
                           "site_admin":collab['site_admin']})
    return retval

#-------------------------------------------------------------------------------
def collaborators_update():
    """Update saved collaborators for private repos in Microsoft orgs.

    NOTE: to run this for all Microsoft orgs requires >5K API calls, so it is
    necessary to manually break it up into batches. And the 'azure' org has so
    many collaborators (>2400 for many repos) that it won't fit in memory by
    itself, and needs to be broken up into batches that then can be combined by
    collaborators() for queries. This whole mess should be automated; was done
    manually for a first pass at getting all of the data cached to disk.
    """
    for org in orgs():
        collab_data = [] # the master list to be written to a data file for this org
        for reponame in repos(org=org):
            print('Getting collaborators for ' + org + '-' + reponame)

            repo_collabs = [] # collaborator list for this repo
            perpage = '?per_page=100' # endpoint parameter to set page size to 100
            endpoint = 'https://api.github.com/repos/' + org + '/' + reponame + \
                '/collaborators' + perpage
            totpages = 0

            while True:

                response = gi.github_api(endpoint=endpoint, auth=gi.auth_user())
                if response.ok:
                    totpages += 1
                    thispage = json.loads(response.text)
                    for member in thispage:
                        minimized = gi.remove_github_urls(member)
                        minimized.update({"org": org})
                        minimized.update({"repo": reponame})
                        repo_collabs.append(minimized)

                pagelinks = gi.pagination(response)
                endpoint = pagelinks['nextURL']
                if not endpoint:
                    break # there are no more results to process

                print('processing page {0} of {1}'. \
                            format(pagelinks['nextpage'], pagelinks['lastpage']))

            collab_data.extend(repo_collabs)

        # write the teammembers data file for this org
        filename = datafile_next('collaborators-' + org)
        gi.json_write(source=collab_data, filename=filename)
        print('data file written -> ' + filename)

#-------------------------------------------------------------------------------
def datafile_latest(entity=None, filetype='json'):
    """Get the most recent saved datafile name for specified entity.

    entity = string identifier for the entity
    filetype = the file extension (default=json)
    """
    # Note the "-2" in the search expression below. This is because we found
    # that some Microsoft orgs have dashes embedded in them, and that can
    # make the wrong data file be returned here. So we're explicitly
    # assuming that the year of creation for data files is a year between
    # 2000 and 2999. Good for the next 9983 years or so.
    datafiles = glob.glob('data/' + entity + '-2*.' + filetype)

    if not datafiles:
        return None

    return sorted(datafiles)[-1]

#-------------------------------------------------------------------------------
def datafile_next(entity=None, filetype='json'):
    """Generate current datafile name for saving specified entity.

    entity = the string identifier for this file's entities
    filetype = the file extension (default=json)

    Returns a timestamped filename in the data folder, in this format:
    data/ENTITY-YYYY-MM-DD-HHMM.<filetype>
    """
    return 'data/' + entity + '-' + \
        '{:%Y-%m-%d-%H%M}'.format(datetime.datetime.now()) + '.' + filetype

#-------------------------------------------------------------------------------
def ms_email(username):
    """Convert GitHub username to Microsoft email address.

    1st parameter = username

    Returns the email address associated with this GitHub username, or an
    empty string if none found.
    """
    if not username:
        return ''

    if not _settings.email:
        # this code only runs on the first call, to load the dictionary
        _settings.email = gi.json_read('data/ms_email.json')

    lowername = username.lower()
    if lowername in _settings.email:
        return _settings.email[lowername]
    else:
        return ''

#-------------------------------------------------------------------------------
def orgmembers(org=None):
    """Get org members for one or more organizations.

    org = organization name or a list of organizations,
          or 'MS*' for all Microsoft orgs

    Returns a list of members as dictionaries.
    """

    if org == 'MS*':
        orglist = orgs() # all Microsoft orgs
    elif isinstance(org, str):
        orglist = [org] # convert single organization to a list
    else:
        orglist = org

    retval = [] # the list to be returned

    for org in orglist:
        filename = datafile_latest('members-' + org)
        if not filename:
            print('ERROR: missing data file -> members-' + org)
            continue

        memberlist = gi.json_read(filename)

        retval.extend(memberlist)

    return sorted(retval, key=lambda x: x['org'].lower()+x['login'].lower())


#-------------------------------------------------------------------------------
def orgmembers_update():
    """Update saved members for Microsoft orgs.
    """
    orglist = orgs()
    for org in orglist:
        gi.log_apistatus()
        print('Scanning for members of org ' + org.upper() + ' ...')
        filename = datafile_next('members-' + org)
        endpoint = 'https://api.github.com/orgs/' + org + '/members?per_page=100'

        members = [] # members of this org
        totpages = 0

        while True:

            response = gi.github_api(endpoint=endpoint, auth=gi.auth_user())
            if response.ok:
                totpages += 1
                thispage = json.loads(response.text)
                memberdata = []
                for member in thispage:
                    no_urls = gi.remove_github_urls(member)
                    no_urls.update({"org": org})
                    memberdata.append(no_urls)
                members.extend(memberdata)

            pagelinks = gi.pagination(response)
            endpoint = pagelinks['nextURL']
            if not endpoint:
                break # there are no more results to process

            print('processing page {0} of {1}'. \
                        format(pagelinks['nextpage'], pagelinks['lastpage']))

        # write the org members data file
        print('Total members for {0} = {1}'.format(org, len(members)))
        gi.json_write(source=members, filename=filename)
        print('data file written -> ' + filename)


#-------------------------------------------------------------------------------
def orgs():
    """Get the latest list of Microsoft organizations.

    Returns a list of the org names.
    """
    orgdata = gi.json_read(datafile_latest('orgs'))

    # returned list is sorted (case-insensitive)
    orglist = [org['login'].lower() for org in orgdata]
    return sorted(orglist)

#-------------------------------------------------------------------------------
def orgs_update():
    """Get the list of Microsoft orgs and save to a disk file.

    Output filename = data/orgs-YYYY-MM-DD-HHMM.json
    """

    endpoint = 'https://api.github.com/user/orgs'
    filename = datafile_next('orgs')

    # GitHub API call
    response = gi.github_api(endpoint=endpoint, auth=gi.auth_user())
    if not response.ok:
        print('ERROR: GitHub API call failed.')
        return

    # write the generated data file
    json_doc = json.loads(response.text)
    gi.json_write(source=json_doc, filename=filename)
    print('data file written -> ' + filename)

#-------------------------------------------------------------------------------
def repos(org=None, repotype=None):
    """Get current repos for a Microsoft org.

    org = organization name or a list of organizations,
          or 'MS*' for all Microsoft orgs

    repotype = 'public', 'private', or None for both

    Returns a list of dictionaries with entries for these fields:
    'org', 'repo', 'private', 'created_at', 'license_name'
    """
    if org == 'MS*':
        orglist = orgs() # all Microsoft orgs
    elif isinstance(org, str):
        orglist = [org] # convert single organization to a list
    else:
        orglist = org

    retval = [] # the list to be returned

    for org in orglist:
        filename = datafile_latest('repos-' + org)
        if not filename:
            continue
        repolist = gi.json_read(filename)
        for repodata in repolist:
            # determine whether to include this repo
            include_repo = False
            if repotype and repotype == 'private' and repodata['private']:
                include_repo = True
            elif repotype and repotype == 'public' and not repodata['private']:
                include_repo = True
            elif not repotype:
                include_repo = True

            if include_repo:
                licensedata = repodata['license']
                licensetype = licensedata['name'] if licensedata else ''
                retval.extend([{"org": org,
                                "repo": repodata['name'],
                                "private": repodata['private'],
                                "created_at": repodata['created_at'],
                                "license": licensetype}])

    return sorted(retval, key=lambda x: x['org'].lower()+x['repo'].lower())

#-------------------------------------------------------------------------------
def repos_update(org='MS*'):
    """Update saved repos for Microsoft orgs.

    org = an organization, list of orgs, or 'MS*' for all Microsoft orgs.

    Output filename = repos-orgname-YYYY-MM-DD-HHMM.json
    """
    if org == 'MS*':
        orglist = orgs() # all Microsoft orgs
    elif isinstance(org, str):
        orglist = [org] # convert single organization to a list
    else:
        orglist = org # pylint: disable=R0204

    orglist = [_.lower() for _ in orglist] # convert org names to lowercase

    for orgname in orglist:
        endpoint = 'https://api.github.com/orgs/' + orgname + '/repos'
        filename = datafile_next('repos-' + orgname)
        # custom header to retrieve license info while License API is in preview
        headers = {'Accept': 'application/vnd.github.drax-preview+json'}
        gi.githubapi_to_file(endpoint=endpoint, filename=filename, headers=headers)

#-------------------------------------------------------------------------------
def repos_update_all():
    """Update saved repos for all Microsoft orgs.

    Output filenames = repos-orgname-YYYY-MM-DD-HHMM.json
    """
    for org in orgs():
        print('Updating repo list for organization -> ' + org.upper())
        repos_update(org=org)
        gi.log_apistatus()

#-------------------------------------------------------------------------------
def teammembers(teamid=None, login=None):
    """Get members for specified team ID or GitHub username.

    teamid = team ID, to get members of a team (ignored if login is provided)
    login = GitHub username, to get teams this person is a member of

    Returns teammmembers data for specified team or person.
    """
    retval = []

    filename = datafile_latest('teammembers')
    if not filename:
        print('ERROR: no data file found for teammembers().')
        return retval

    # NOTE: if we use this function much, would be worth reading data file on
    # first call and keeping it in memory. See ms_email() for an example.
    allmembers = gi.json_read(filename)

    if login:
        # search by login name
        for member in allmembers:
            if member['login'] == login:
                retval.append({"org":member['org'],
                               "team_id":member['team_id'],
                               "team_name":member['team_name'],
                               "login":member['login'],
                               "id":member['id'],
                               "site_admin":member['site_admin']})
    else:
        # search by team ID
        for member in allmembers:
            if member['team_id'] == teamid:
                retval.append({"org":member['org'],
                               "team_id":member['team_id'],
                               "team_name":member['team_name'],
                               "login":member['login'],
                               "id":member['id'],
                               "site_admin":member['site_admin']})

    return retval

#-------------------------------------------------------------------------------
def teammembers_update():
    """Update saved members for Microsoft teams.

    Scans through the latest list of teams for Microsoft orgs and creates the
    teammembers-YYYY-MM-DD-HHMM.json data file.
    """
    allteams = gi.json_read(datafile_latest('teams'))
    master_json = [] # master list of team members to be saved

    for team in allteams:

        print('Finding members for team ' + team['org'] + '-' + str(team['id']))

        members = [] # members of this team
        endpoint = 'https://api.github.com/teams/' + str(team['id']) + '/members'
        totpages = 0

        while True:

            response = gi.github_api(endpoint=endpoint, auth=gi.auth_user())
            if response.ok:
                totpages += 1
                thispage = json.loads(response.text)
                memberdata = []
                for member in thispage:
                    member.update({"org": team['org']})
                    member.update({"team_id": team['id']})
                    member.update({"team_name": team['name']})
                    memberdata.append(member)
                members.extend(memberdata)

            pagelinks = gi.pagination(response)
            endpoint = pagelinks['nextURL']
            if not endpoint:
                break # there are no more results to process

            print('processing page {0} of {1}'. \
                        format(pagelinks['nextpage'], pagelinks['lastpage']))

        master_json.extend(members)

    # write the teammembers data file
    filename = datafile_next('teammembers')
    gi.json_write(source=master_json, filename=filename)
    print('data file written -> ' + filename)

#-------------------------------------------------------------------------------
def teams(org=None):
    """Get teams for one or more organizations.

    org = an organization, list of orgs, or 'MS*' for all Microsoft orgs.
    """
    if org == 'MS*':
        orglist = orgs() # all Microsoft orgs
    elif isinstance(org, str):
        orglist = [org] # convert single organization to a list
    else:
        orglist = org

    orglist = [_.lower() for _ in orglist] # convert org names to lowercase
    retval = [] # the list to be returned
    allteams = gi.json_read(datafile_latest('teams'))

    for team in allteams:
        if team['org'].lower() in orglist:
            retval.append({"org": team['org'], "id": team['id'],
                           "name": team['name'], "privacy": team['privacy'],
                           "permission": team['permission']})

    return retval

#-------------------------------------------------------------------------------
def teams_update():
    """Update saved team information for all Microsoft organizations.

    Saves all teams for all Microsoft orgs to teams-YYYY-MM-DD-HHMM.json
    """
    master_json = [] # consolidated master list to be written to output file

    for org in orgs():
        print('Getting teams for ' + org.upper() + ' ...')
        endpoint = 'https://api.github.com/orgs/' + org + '/teams'

        totpages = 0

        while True:

            response = gi.github_api(endpoint=endpoint, auth=gi.auth_user())
            if response.ok:
                totpages += 1
                thispage = json.loads(response.text)
                teamdata = []
                for team in thispage:
                    team.update({"org": org}) # add org to each entry
                    teamdata.append(team)
                master_json.extend(teamdata)

            pagelinks = gi.pagination(response)
            endpoint = pagelinks['nextURL']
            if not endpoint:
                break # there are no more results to process

            print('processing page {0} of {1}'. \
                        format(pagelinks['nextpage'], pagelinks['lastpage']))

        gi.log_apistatus()

    filename = datafile_next('teams')
    gi.json_write(source=master_json, filename=filename)
    print('data file written -> ' + filename)

#-------------------------------------------------------------------------------
if __name__ == '__main__':
    gi.auth_config({'username': 'msftgits'})
    gi.session_start('msgithub updates')
    #orgs_update()
    #repos_update_all()
    #gi.session_end()
    #_adminteams_to_csv()
    #_collaborators_to_csv()
    #_files_to_csv()
    #_orgmembers_to_csv()
    #repos_update_all()
    #_repos_to_csv()
    #_teammembers_to_csv()

    TODO = 4

    outfile = 'org_admins.csv'

    import requests
    for org in orgs():
        endpoint = 'https://api.github.com/orgs/' + org + '/members?role=admin'
        response = requests.get(endpoint, auth=gi.auth_user())
        members = json.loads(response.text)
        for member in members:
            login = member['login']
            email = ms_email(login)
            outputstr = org + ',' + login + ',' + email
            print(outputstr)
            with open(outfile, 'a') as fhandle:
                fhandle.write(org + ',' + login + ',' + email + '\n')

    gi.session_end('msgithub updates')

    #_capture_files('contribute.md', 'contribute_md', '.md')
