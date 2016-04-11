"""Helper functions for retrieving data via the GitHub API.

auth_config() --------> Configure authentication settings.
auth_user() ----------> Return credentials for use in GitHub API calls.
collaborators() ------> Get collaborators for one or more repos.
collaboratorsget() ---> Get collaborator info for a specified repo.
json_read() ----------> Read a .json file into a Python object.
json_write() ---------> Write a Python object to a .json file.
github_api() ---------> Call the GitHub API (wrapper for requests.get()).
githubapi_to_file() --> Call GitHub API, handle pagination, write to file.
log_apistatus() ------> Display current API rate-limit status.
log_config() ---------> Configure message logging settings.
log_msg() ------------> Log a status message.
members() ------------> Get members of one or more organizations.
membersget() ---------> Get member info for a specified organization.
minimize_json() ------> Remove the *_url properties from a json data file.
pagination() ---------> Parse 'link' HTTP header returned by GitHub API.
ratelimit_status() ---> Display current rate-limit status.
readme_content() -----> Retrieve contents of preferred readme for a repo.
readme_tag_parser() --> Extract LandingPageTags values from a readme line.
remove_github_urls() -> Remove *_url entries from a dictionary.
repo_admins() --------> Get administrators for a repo.
repo_tags() ----------> Retrieve metadata tags from a repo's readme.
repofields() ---------> Get field values for a repo.
repos() --------------> Get repo information for organizations or users.
reposget() -----------> Get repo information for a specified org or user.
repoteams() ----------> Get teams associated with one or more repositories.
repoteamsget() -------> Get team info for a specified repo.
session_end() --------> Log summary of completed gitinfo "session."
session_start() ------> Initiate a gitinfo session for logging/tracking purposes.
teammembers() --------> Get team members for specified team.
teams() --------------> Get teams for one or more organizations.
teamsget() -----------> Get team info for a specified organization.
timestamp() ----------> Return current timestamp as YYYY-MM-DD HH:MM:SS
write_csv() ----------> Write a list of namedtuples to a CSV file.

Note: some classes and functions have been omitted from the above list because
they're only used internally and don't expose useful functionality.
"""
import collections
import csv
import datetime
import inspect
import json
import os
import time

import requests
import pytest # only required for running tests

#------------------------------------------------------------------------------
class _settings:
    """This class exists to provide a namespace used for global settings.
    Use auth_config() or log_config() to change these settings.
    """

    # authentication settings used by auth_*() functions
    username = '' # default = no GitHub authentication
    accesstoken = '' # auth_config() may set this from the 'private' folder

    # logging settings used by log_*() functions
    verbose = True # default = messages displayed to console
    logfile = None # default = messages not logged to a file

    # initialize gitinfo session settings
    start_time = time.time() # session start time (seconds)
    tot_api_calls = 0 # number of API calls made through gitinfo
    tot_api_bytes = 0 # total bytes returned by these API calls
    last_ratelimit = 0 # API rate limit for the most recent API call
    last_remaining = 0 # remaining portion of rate limit after last API call

#-------------------------------------------------------------------------------
def auth_config(settings=None):
    """Configure authentication settings.

    1st parameter = dictionary of configuration settings; see config_settings
                    below for settings managed by this function.

    Returns dictionary of current settings - call auth_config() with no
    parameters to get status.
    """
    config_settings = ['username', 'accesstoken']

    # if username is specified but no accesstoken specified, look up this
    # user's PAT in github_users.json
    if settings and 'username' in settings and not 'accesstoken' in settings:
        with open('private/github_users.json', 'r') as jsonfile:
            github_users = json.load(jsonfile)
            settings['accesstoken'] = github_users[settings['username']]

    if settings:
        for setting in config_settings:
            if setting in settings:
                setattr(_settings, setting, settings[setting])

    retval = dict()
    for setting in config_settings:
        retval[setting] = getattr(_settings, setting)

    username = _settings.username
    accesstoken = _settings.accesstoken
    if accesstoken:
        # if a PAT is stored, only display first 2 and last 2 characters
        pat = accesstoken[0:2] + '...' + accesstoken[-2:]
    else:
        pat = "*none*"
    log_msg('username:', username + ', PAT:', pat)

    return retval

#------------------------------------------------------------------------------
def auth_user():
    """Credentials for basic authentication.

    Returns the tuple used for API calls, based on current settings.
    Returns None if no GitHub username/PAT is currently set.
    <internal>
    """
    if not _settings.username:
        return None

    username = _settings.username
    access_token = _settings.accesstoken

    return (username, access_token)

#-------------------------------------------------------------------------------
def collaboratorfields(collab_json, fields, owner, repo):
    """Get field values for a collaborator.

    1st parameter = collaborator JSON representation as returned by GitHub API
    2nd parameter = list of names of desired fields
    3rd parameter = owner (for including in output fields)
    4th parameter = repo (for including in output fields)

    Returns a namedtuple containing the desired fields and their values.
    <internal>
    """
    if not fields:
        # if no fields specified, use default field list
        fields = ['id', 'login', 'type', 'permissions.admin']

    # change '.' to '_' because can't have '.' in an identifier
    fldnames = [_.replace('.', '_') for _ in fields]

    values = {}
    values['owner'] = owner
    values['repo'] = repo
    collab_tuple = collections.namedtuple('collab_tuple', 'owner repo ' + ' '.join(fldnames))

    for fldname in fields:
        if '.' in fldname:
            # special case - embedded field within a JSON object
            try:
                values[fldname.replace('.', '_')] = \
                    collab_json[fldname.split('.')[0]][fldname.split('.')[1]]
            except (TypeError, KeyError):
                values[fldname.replace('.', '_')] = None
        else:
            # simple case: copy a value from the JSON to the namedtuple
            values[fldname] = collab_json[fldname]

    return collab_tuple(**values)

#-------------------------------------------------------------------------------
def collaborators(owner=None, repo=None, fields=None):
    """Get collaborators for one or more repos with the same owner.

    owner = the repo owner (org or user)
    repo = repo name or list of repo names
    fields = list of field names to be returned; names must be the same as
             returned by the GitHub API (see below).

    Note: to access collaborator information, you must be authenticated as a
    person with admin access to the repo.

    Returns a list of namedtuple objects, one per team.
    """
    # GitHub API fields (as of March 2016):
    # avatar_url          events_url          followers_url
    # gravatar_id         id                  login
    # permissions.admin   permissions.pull    permissions.push
    # site_admin          type
    # Note that URL fields have been removed, to reduce the size of these
    # data files.
    if not owner or not repo:
        log_msg('ERROR: collaborators() called without required parameters.')
        return []
    collablist = [] # the list of collaborators that will be returned

    if isinstance(repo, str):
        # get collaborators for a single repo
        collablist.extend(collaboratorsget(owner, repo, fields))
    else:
        # get collaborators for a list of repos
        for reponame in repo:
            collablist.extend(collaboratorsget(owner, reponame, fields))

    return collablist

#------------------------------------------------------------------------------
def collaboratorsget(owner, repo, fields):
    """Get collaborator info for a specified repo. Called by collaborators() to
    aggregate collaborator information for multiple repos.

    1st parameter = owner
    2nd parameter = repo name
    3rd parameter = list of fields to be returned

    Returns a list of namedtuples containing the specified fields.
    """
    endpoint = 'https://api.github.com/repos/' + owner + '/' + repo + '/collaborators'
    retval = [] # the list to be returned
    totpages = 0

    while True:

        response = github_api(endpoint, auth=auth_user())
        if response.ok:
            totpages += 1
            thispage = json.loads(response.text)
            for collab_json in thispage:
                retval.append(collaboratorfields(collab_json, fields, owner, repo))

        pagelinks = pagination(response)
        endpoint = pagelinks['nextURL']
        if not endpoint:
            break # no more results to process

        log_msg('processing page {0} of {1}'. \
                       format(pagelinks['nextpage'], pagelinks['lastpage']))

    log_msg('pages processed: {0}, total members: {1}'. \
        format(totpages, len(retval)))

    return retval

#-------------------------------------------------------------------------------
def github_api(endpoint=None, auth=None, headers=None):
    """Call the GitHub API (wrapper for requests.get()).

    endpoint = the HTTP endpoint to call
    auth = optional tuple for authentication
    headers = optional dictionary of HTTP headers to pass

    Returns the response object.
    API call through this function update session totals.
    """
    if not endpoint:
        log_msg('ERROR: github_api() called with no endpoint')
        return

    # make the API call, get response object
    if not auth and not headers:
        response = requests.get(endpoint)
    elif auth and not headers:
        response = requests.get(endpoint, auth=auth)
    elif not auth and headers:
        response = requests.get(endpoint, headers=headers)
    else:
        response = requests.get(endpoint, auth=auth, headers=headers)

    # update session settings
    _settings.tot_api_calls += 1
    _settings.tot_api_bytes += len(response.content)
    try:
        _settings.last_ratelimit = int(response.headers['X-RateLimit-Limit'])
        _settings.last_remaining = int(response.headers['X-RateLimit-Remaining'])
    except KeyError:
        # This is the strange and rare case (which we've encountered) where
        # an API call that normally returns the rate-limit headers doesn't
        # return them. Since these values are only used for monitoring, we
        # use nonsensical values here that will show it happened, but won't
        # crash a long-running process.
        _settings.last_ratelimit = 999999
        _settings.last_remaining = 999999

    return response

#-------------------------------------------------------------------------------
def githubapi_to_file(endpoint=None, filename=None, headers=None):
    """Call GitHub API, consolidate pagination, write to output file.

    endpoint = GitHub API endpoint to call
    filename = file to write consolidated output to
    headers = optional dictionary of HTTP headers to send with the request

    The output file is written as a single JSON list, containing all pages of
    data if there is more than one.
    """
    totpages = 0
    master_json = [] # consolidated master list to be written to output file

    while True:

        response = github_api(endpoint=endpoint, auth=auth_user(), headers=headers)
        if response.ok:
            totpages += 1
            thispage = json.loads(response.text)
            master_json.extend(thispage)

        pagelinks = pagination(response)
        endpoint = pagelinks['nextURL']
        if not endpoint:
            break # there are no more results to process

        print('processing page {0} of {1}'. \
                       format(pagelinks['nextpage'], pagelinks['lastpage']))

    print('pages processed: {0}, total members: {1}'. \
        format(totpages, len(master_json)))

    json_write(source=master_json, filename=filename)
    print('data file written -> ' + filename)

#-------------------------------------------------------------------------------
def json_read(filename=None):
    """Read .json file into a Python object.

    filename = the filename
    Returns the object that has been serialized to the .json file (list, etc).
    """
    with open(filename, 'r') as datafile:
        retval = json.loads(datafile.read())
    return retval

#-------------------------------------------------------------------------------
def json_write(source=None, filename=None):
    """Write Python object to a .json file.

    source = the object to be serialized
    filename = the filename (will be over-written if it already exists)
    """
    if not source or not filename:
        return # nothing to do

    with open(filename, 'w') as fhandle:
        fhandle.write(json.dumps(source, indent=4, sort_keys=True))

#-------------------------------------------------------------------------------
def log_apistatus():
    """Display (via log_msg()) the rate-limit status after the last API call.
    """
    remaining = _settings.last_remaining
    used = _settings.last_ratelimit - remaining
    log_msg('API rate limit = {0}/hour ({1} used, {2} remaining)'. \
        format(_settings.last_ratelimit, used, remaining))

#-------------------------------------------------------------------------------
def log_config(settings=None):
    """Configure message logging settings.

    1st parameter = dictionary of configuration settings; see config_settings
                    below for settings managed by this function.

    Returns dictionary of current settings - call log_config() with no
    parameters to get status.
    """
    config_settings = ['verbose', 'logfile']

    if settings:
        for setting in config_settings:
            if setting in settings:
                setattr(_settings, setting, settings[setting])

    retval = dict()
    for setting in config_settings:
        retval[setting] = getattr(_settings, setting)

    return retval
#-------------------------------------------------------------------------------
def log_msg(*args):
    """Log a status message.

    parameters = message to be displayed if log_config(True) is set.

    NOTE: can pass any number of parameters, which will be displayed as a single
    string delimited by spaces.
    """
    # convert all arguments to strings, so they can be .join()ed
    string_args = [str(_) for _ in args]

    # get the caller of log_msg(), which is displayed with the message
    # Note: we populate a complete callstack list here, just because it
    # may be useful at times in the future.
    callstack = []
    frame = inspect.currentframe()
    while True:
        frame = frame.f_back
        name = frame.f_code.co_name
        if name[0] == '<':
            break
        callstack.append(name)
    caller = callstack[0]
    msg = (caller + '() ').ljust(20, '-') + '> ' + ' '.join(string_args)

    if _settings.verbose:
        print(msg)

    if _settings.logfile:
        with open(_settings.logfile, 'a') as fhandle:
            fhandle.write(timestamp() + ' ' + msg + '\n')

#-------------------------------------------------------------------------------
def memberfields(member_json, fields, org):
    """Get field values for a member/user.

    1st parameter = member's json representation as returned by GitHub API
    2nd parameter = list of names of desired fields
    3rd parameter = organization ID

    Returns a namedtuple containing the desired fields and their values.
    NOTE: in addition to the specified fields, always returns an 'org' field
    to distinguish between orgs in multi-org lists returned by members().
    <internal>
    """
    if not fields:
        # if no fields specified, use default field list
        fields = ['login', 'id', 'type', 'site_admin']

    values = {}
    values['org'] = org
    for fldname in fields:
        values[fldname] = member_json[fldname]

    member_tuple = collections.namedtuple('member_tuple',
                                          'org ' + ' '.join(fields))
    return member_tuple(**values)

#-------------------------------------------------------------------------------
def members(org=None, team=None, fields=None, audit2fa=False):
    """Get members for one or more teams or organizations.

    org = an organization ID or list of organizations
    team = a team ID or list of teams; if provided, org is ignored
    fields = list of field names to be returned; names must be the same as
             returned by the GitHub API (see below).
    audit2fa = whether to only return members with 2FA disabled. You must be
               authenticated via auth_config() as an admin of the org(s) to use
               this option.

    Returns a list of namedtuple objects, one per member.

    GitHub API fields (as of March 2016):
    id                  events_url          organizations_url
    login               followers_url       received_events_url
    site_admin          following_url       repos_url
    type                gists_url           starred_url
    url                 gravatar_id         subscriptions_url
    avatar_url          html_url
    """
    memberlist = [] # the list of members that will be returned

    if team:
        # get members by team
        if isinstance(team, str):
            # one team
            memberlist.extend(membersget(team=team, fields=fields))
        else:
            # list of teams
            for teamid in team:
                memberlist.extend(membersget(team=teamid, fields=fields))
    else:
        # get members by organization
        if isinstance(org, str):
            # one organization
            memberlist.extend( \
                membersget(org=org, fields=fields, audit2fa=audit2fa))
        else:
            # list of organizations
            for orgid in org:
                memberlist.extend( \
                    membersget(org=orgid, fields=fields, audit2fa=audit2fa))

    return memberlist

#------------------------------------------------------------------------------
def membersget(org=None, team=None, fields=None, audit2fa=False):
    """Get member info for a specified organization. Called by members() to
    aggregate member info for multiple organizations.

    org = organization ID (ignored if a team is specified)
    team = team ID
    fields = list of fields to be returned
    audit2fa = whether to only return members with 2FA disabled. This option
               is only available when retrieving members by organization.
               Note: for audit2fa=True, you must be authenticated via
               auth_config() as an admin of the org(s).

    Returns a list of namedtuples containing the specified fields.
    """
    if team:
        endpoint = 'https://api.github.com/teams/' + team + '/members'
    else:
        endpoint = 'https://api.github.com/orgs/' + org + '/members' + \
            ('?filter=2fa_disabled' if audit2fa else '')

    retval = [] # the list to be returned
    totpages = 0

    while True:

        response = github_api(endpoint, auth=auth_user())
        if response.ok:
            totpages += 1
            thispage = json.loads(response.text)
            for member_json in thispage:
                retval.append(memberfields(member_json, fields, org))

        pagelinks = pagination(response)
        endpoint = pagelinks['nextURL']
        if not endpoint:
            break # no more results to process

        log_msg('processing page {0} of {1}'. \
                       format(pagelinks['nextpage'], pagelinks['lastpage']))

    log_msg('pages processed: {0}, total members: {1}'. \
        format(totpages, len(retval)))

    return retval

#------------------------------------------------------------------------------
def minimize_json(infile=None, outfile=None):
    """Remove all *_url properties from a json data file.

    infile = the input json file (as returned by the GitHub API)
    outfile = the new minimized file with *_url removed.

    This function is intended for use with data files that contain captured
    GitHub API responses as a list of dictionaries. It removes *_url entries
    from the dictionaries in the list.
    """
    print('Minimizing ' + infile + ', output file = ' + outfile)

    with open(infile, 'r') as inputfile:
        dictlist = json.loads(inputfile.read())

    outputlist = []
    for dictobj in dictlist:
        outputlist.append(remove_github_urls(dictobj))

    with open(outfile, 'w') as outputfile:
        outputfile.write(json.dumps(outputlist, sort_keys=True))

    print('Output file contains {0} entries.'.format(len(outputlist)))

#------------------------------------------------------------------------------
def pagination(link_header):
    """Parse values from the 'link' HTTP header returned by GitHub API.

    1st parameter = either of these options ...
                    - 'link' HTTP header passed as a string
                    - response object returned by requests.get()

    Returns a dictionary with entries for the URLs and page numbers parsed
    from the link string: firstURL, firstpage, prevURL, prevpage, nextURL,
    nextpage, lastURL, lastpage.
    <internal>
    """
    # initialize the dictionary
    retval = {'firstpage':0, 'firstURL':None, 'prevpage':0, 'prevURL':None,
              'nextpage':0, 'nextURL':None, 'lastpage':0, 'lastURL':None}

    if isinstance(link_header, str):
        link_string = link_header
    else:
        # link_header is a response object, get its 'link' HTTP header
        try:
            link_string = link_header.headers['Link']
        except KeyError:
            return retval # no Link HTTP header found, nothing to parse

    links = link_string.split(',')
    for link in links:
        # link format = '<url>; rel="type"'
        linktype = link.split(';')[-1].split('=')[-1].strip()[1:-1]
        url = link.split(';')[0].strip()[1:-1]
        pageno = url.split('?')[-1].split('=')[-1].strip()

        retval[linktype + 'page'] = pageno
        retval[linktype + 'URL'] = url

    return retval

#-------------------------------------------------------------------------------
def ratelimit_status(user=None):
    """Displays current rate-limit status.

    user = GitHub user name for authentication (optional)

    Returns a tuple, first value is rate limit for this user and second value
    is number of remaining/unused API calls available.
    """
    #/// write tests, add to gitinfo_test.py
    #/// add to repo documentation

    if user:
        auth_config({'username': user})

    response = requests.get('https://api.github.com/users/octocat', auth=auth_user())

    try:
        ratelimit = int(response.headers['X-RateLimit-Limit'])
        remaining = int(response.headers['X-RateLimit-Remaining'])
        linegraph = ('X'*int((60 * (ratelimit - remaining)/ratelimit))).ljust(60, '-')
        statusmsg = 'User: ' + str(user) + ' - Rate limit: ' + str(ratelimit) + \
            ' - Remaining: ' + str(remaining) + '\n' + linegraph
    except KeyError:
        # This is the strange and rare case (which we've encountered) where
        # an API call that normally returns the rate-limit headers doesn't
        # return them.
        ratelimit = 0
        remaining = 0
        statusmsg = 'User: ' + str(user) + ' - rate limit info not returned!'

    print(statusmsg)
    return (ratelimit, remaining) 

#-------------------------------------------------------------------------------
def readme_content(owner=None, repo=None):
    """Retrieve contents of preferred readme for a repo.

    owner = org or username
    repo = repo name

    Returns the contents of the readme file for this repo (if any).
    """
    import base64
    endpoint = 'https://api.github.com/repos/' + owner + '/' + repo + '/readme'
    headers = {'content-type': 'application/vnd.github.v3.html'}
    response = github_api(endpoint=endpoint, auth=auth_user(), headers=headers)
    if response.ok:
        return base64.b64decode(json.loads(response.text)['content'])
    else:
        return ''

#-------------------------------------------------------------------------------
def readme_tag_parser(line):
    """Extract LandingPageTags values from a line of text from a readme file.

    line = a string in this format:
           <properties prop1='xxx' LandingPageTags="XXX,YYY,ZZZ" prop2="yyy" />

    Returns a list of the LandingPageTags values. In the example above, would
    return ['xxx', 'yyy', 'zzz']. Note that all returned values are converted
    to lower case.
    """
    retval = []

    tokens = line.split(' ')
    for token in tokens:
        if '=' in token:
            if token.split('=')[0].lower() == 'landingpagetags':
                tags = token.lower().split('=')[1].replace('"', '').replace("'", '')
                for tag in tags.split(','):
                    if tag.strip():
                        retval.append(tag.strip())
    return retval

#-------------------------------------------------------------------------------
def remove_github_urls(dict_in):
    """Remove URL entries (as returned by GitHub API) from a dictionary.

    1st parameter = dictionary

    Returns a copy of the dictionary, but with no entries named *_url or url.
    """
    if not dict_in:
        return {}
    return {key: dict_in[key] for key in dict_in if \
        not key.endswith('_url') and not key == 'url'}

#-------------------------------------------------------------------------------
def repo_admins(org=None, repo=None):
    """Get administrators for a repo.

    org = organization name
    repo = repo name

    Returns a list of dictionaries, with each dictionary describing a person
    with admin rights for this repo. These keys are included in the
    dictionaries:
    admintype -> either 'AdminTeamMember' or 'AdminCollaborator'
    teamname --> team name (for admintype=='AdminTeamMember')
    teamid ----> GitHub team ID (for admintype=='AdminTeamMember')
    login -----> GitHub login name
    email -----> email address (if a Microsoft employee)
    """
    retval = []

	# get AdminTeamMembers
    endpoint = 'https://api.github.com/repos/' + org + '/' + repo + '/teams'
    totpages = 0
    while True:
        response = github_api(endpoint=endpoint, auth=auth_user())
        if response.ok:
            totpages += 1
            thispage = json.loads(response.text)
            for member in thispage:
                if member['permission'] == 'admin':
                    adminmembers = teammembers(teamid=member['id'])
                    for adminmember in adminmembers:
                        retval.append({'admintype': 'AdminTeamMember',
                                       'teamname': member['name'],
                                       'teamid': member['id'],
                                       'login': adminmember.login,
                                       'email': adminmember.email})

        pagelinks = pagination(response)
        endpoint = pagelinks['nextURL']
        if not endpoint:
            break # there are no more results to process

        print('processing page {0} of {1}'. \
                       format(pagelinks['nextpage'], pagelinks['lastpage']))

    print('pages processed: {0}, total members: {1}'. \
        format(totpages, len(retval)))

    return retval

#-------------------------------------------------------------------------------
def repo_tags(owner=None, repo=None):
    """Retrieve metadata tags from a repo's readme.

    owner = org or username
    repo = repo name

    Returns a list of tags.
    """
    retval = []

    readme = readme_content(owner=owner, repo=repo)
    if not readme:
        return retval

    lines = readme.split(b'\n')
    for line in lines:
        thisline = line.decode()
        if thisline.lower().startswith('<properties '):
            retval.extend(readme_tag_parser(thisline))
        else:
            break

    return retval

#-------------------------------------------------------------------------------
def repofields(repo_json, fields, org, user):
    """Get field values for a repo.

    1st parameter = repo's json representation as returned by GitHub API
    2nd parameter = list of names of desired fields
    3rd parameter = organization (for including in output fields)
    4th parameter = username (for including in output fields)

    Returns a namedtuple containing the desired fields and their values.
    <internal>
    """
    if not fields:
        # if no fields specified, use default field list
        fields = ['full_name', 'watchers', 'forks', 'license.name', 'private']

    # change '.' to '_' because can't have '.' in an identifier
    fldnames = [_.replace('.', '_') for _ in fields]

    values = {}
    values['org'] = org
    values['user'] = user
    repo_tuple = collections.namedtuple('repo_tuple', 'org user ' + ' '.join(fldnames))

    for fldname in fields:
        if '.' in fldname:
            # special case - embedded field within a JSON object
            try:
                values[fldname.replace('.', '_')] = \
                    repo_json[fldname.split('.')[0]][fldname.split('.')[1]]
            except (TypeError, KeyError):
                values[fldname.replace('.', '_')] = None
        else:
            # simple case: copy a value from the JSON to the namedtuple
            values[fldname] = repo_json[fldname]

    return repo_tuple(**values)

#-------------------------------------------------------------------------------
def repos(org=None, user=None, fields=None):
    """Get repo information for one or more organizations or users.

    org    = organization; an organization or list of organizations
    user   = username; a username or list of usernames (if org is provided,
             user is ignored)
    fields = list of fields to be returned; names must be the same as
             returned by the GitHub API (see below).
             Note: dot notation for embedded elements is supported.
             For example, pass a field named 'license.name' to get the 'name'
             element of the 'license' entry for each repo.

    Returns a list of namedtuple objects, one per repo.
    """
    # GitHub API fields (as of March 2016):
    # archive_url         git_tags_url         open_issues
    # assignees_url       git_url              open_issues_count
    # blobs_url           has_downloads        private
    # branches_url        has_issues           pulls_url
    # clone_url           has_pages            pushed_at
    # collaborators_url   has_wiki             releases_url
    # commits_url         homepage             size
    # compare_url         hooks_url            ssh_url
    # contents_url        html_url             stargazers_count
    # contributors_url    id                   stargazers_url
    # created_at          issue_comment_url    statuses_url
    # default_branch      issue_events_url     subscribers_url
    # deployments_url     issues_url           subscription_url
    # description         keys_url             svn_url
    # downloads_url       labels_url           tags_url
    # events_url          language             teams_url
    # fork                languages_url        trees_url
    # forks               master_branch        updated_at
    # forks_count         merges_url           url
    # forks_url           milestones_url       watchers
    # full_name           mirror_url           watchers_count
    # git_commits_url     name
    # git_refs_url        notifications_url
    # -------------------------------------------------------------
    # license.featured              permissions.admin
    # license.key                   permissions.pull
    # license.name                  permissions.push
    # license.url
    # -------------------------------------------------------------
    # owner.avatar_url              owner.organizations_url
    # owner.events_url              owner.received_events_url
    # owner.followers_url           owner.repos_url
    # owner.following_url           owner.site_admin
    # owner.gists_url               owner.starred_url
    # owner.gravatar_id             owner.subscriptions_url
    # owner.html_url                owner.type
    # owner.id                      owner.url
    # owner.login

    repolist = [] # the list that will be returned

    if org:
        # get repos by organization
        if isinstance(org, str):
            # one organization
            repolist.extend(reposget(org=org, fields=fields))
        else:
            # list of organizations
            for orgid in org:
                repolist.extend(reposget(org=orgid, fields=fields))
    else:
        # get repos by user
        if isinstance(user, str):
            # one user
            repolist.extend(reposget(user=user, fields=fields))
        else:
            # list of users
            for userid in user:
                repolist.extend(reposget(user=userid, fields=fields))

    return repolist

#-------------------------------------------------------------------------------
def reposget(org=None, user=None, fields=None):
    """Get repo information for a specified org or user. Called by repos() to
    aggregate repo information for multiple orgs or users.

    org = organization name
    user = username (ignored if org is provided)
    fields = list of fields to be returned

    Returns a list of namedtuples containing the specified fields.
    """
    if org:
        endpoint = 'https://api.github.com/orgs/' + org + '/repos'
    else:
        endpoint = 'https://api.github.com/users/' + user + '/repos'

    totpages = 0
    retval = [] # the list to be returned

    # custom header to retrieve license info while License API is in preview
    headers = {'Accept': 'application/vnd.github.drax-preview+json'}

    while True:

        response = github_api(endpoint, auth=auth_user(), headers=headers)
        if response.ok:
            totpages += 1
            thispage = json.loads(response.text)
            for repo_json in thispage:
                retval.append(repofields(repo_json, fields, org, user))

        pagelinks = pagination(response)
        endpoint = pagelinks['nextURL']
        if not endpoint:
            break # there are no more results to process

        log_msg('processing page {0} of {1}'. \
                       format(pagelinks['nextpage'], pagelinks['lastpage']))

    log_msg('pages processed: {0}, total members: {1}'. \
        format(totpages, len(retval)))

    return retval

#-------------------------------------------------------------------------------
def repoteamfields(team_json, fields, org, repo):
    """Get field values for a repo's team.

    1st parameter = team's json representation as returned by GitHub API
    2nd parameter = list of names of desired fields
    3rd parameter = organization ID
    4th parameter = repo name

    Returns a namedtuple containing the desired fields and their values.
    NOTE: in addition to the specified fields, always returns 'org' and
    'repo' fields to clarify which org/repo this team is associated with.
    <internal>
    """
    if not fields:
        # if no fields specified, use default field list
        fields = ['name', 'id', 'privacy', 'permission']

    values = {}
    values['org'] = org
    values['repo'] = repo
    for fldname in fields:
        values[fldname] = team_json[fldname]

    team_tuple = collections.namedtuple('team_tuple',
                                        'org repo ' + ' '.join(fields))
    return team_tuple(**values)

#-------------------------------------------------------------------------------
def repoteams(org=None, repo=None, fields=None):
    """Get teams for one or more repositories.

    org = organization ID (required)
    repo = repo name, list of repo names, or None for all repos in this org
    fields = list of field names to be returned; names must be the same as
             returned by the GitHub API (see below).

    Note: to access team information, you must be authenticated as a member of
    the Owners team for the team's organization.

    Returns a list of namedtuple objects, one per team.

    GitHub API fields (as of March 2016): description, id, members_url, name,
        permission, privacy, repositories_url, slug, url
    """
    teamlist = [] # the list of members that will be returned

    if not repo:
        # no repos specified, so create a list of all repos for this org
        repo = [_.name for _ in repos(org=org, fields=['name'])]

    if isinstance(repo, str):
        # get teams for a single repo
        teamlist.extend(repoteamsget(org, repo, fields))
    else:
        # get teams for a list of repos
        for reponame in repo:
            teamlist.extend(repoteamsget(org, reponame, fields))

    return teamlist

#------------------------------------------------------------------------------
def repoteamsget(org, repo, fields):
    """Get team info for a specified repo. Called by repoteams() to aggregate
    team information for multiple repos.

    1st parameter = organization ID
    2nd parameter = repo name
    3rd parameter = list of fields to be returned

    Returns a list of namedtuples containing the specified fields.
    """
    endpoint = 'https://api.github.com/repos/' + org + '/' + repo + '/teams'
    retval = [] # the list to be returned
    totpages = 0

    while True:

        response = github_api(endpoint, auth=auth_user())
        if response.ok:
            totpages += 1
            thispage = json.loads(response.text)
            for team_json in thispage:
                retval.append(repoteamfields(team_json, fields, org, repo))

        pagelinks = pagination(response)
        endpoint = pagelinks['nextURL']
        if not endpoint:
            break # no more results to process

        log_msg('processing page {0} of {1}'. \
                       format(pagelinks['nextpage'], pagelinks['lastpage']))

    log_msg('pages processed: {0}, total members: {1}'. \
        format(totpages, len(retval)))

    return retval

#-------------------------------------------------------------------------------
def session_end(msg=None):
    """Log summary of completed gitinfo session.

    1st parameter = optional message to include in logfile/console output
    """
    log_msg('Elapsed time (seconds): {0}'. \
        format(time.time() - _settings.start_time))

    log_msg('Total API calls: {0}, total bytes returned: {1}'. \
        format(_settings.tot_api_calls, _settings.tot_api_bytes))

    log_apistatus()

    msgline = 60*'-' if not msg else (' ' + msg + ' ').center(60, '-')
    log_msg(msgline)

#-------------------------------------------------------------------------------
def session_start(msg=None):
    """Initiate a gitinfo "session" for logging/tracking purposes.

    1st parameter = optional message to include in logfile/console output
    """
    # initialize gitinfo session settings
    _settings.start_time = time.time() # session start time (seconds)
    _settings.tot_api_calls = 0 # number of API calls made through gitinfo
    _settings.tot_api_bytes = 0 # total bytes returned by these API calls
    _settings.last_ratelimit = 0 # API rate limit for the most recent API call
    _settings.last_remaining = 0 # remaining available portion of rate limit

    msgline = 60*'-' if not msg else (' ' + msg + ' ').center(60, '-')
    log_msg(msgline)
    log_msg('filename:', os.path.abspath(__file__))

#-------------------------------------------------------------------------------
def teamfields(team_json, fields, org):
    """Get field values for an organization's team.

    1st parameter = team's json representation as returned by GitHub API
    2nd parameter = list of names of desired fields
    3rd parameter = organization ID

    Returns a namedtuple containing the desired fields and their values.
    NOTE: in addition to the specified fields, always returns an 'org' field
    to distinguish between orgs in multi-org lists returned by teams().
    <internal>
    """
    if not fields:
        # if no fields specified, use default field list
        fields = ['name', 'id', 'privacy', 'permission']

    values = {}
    values['org'] = org
    for fldname in fields:
        values[fldname] = team_json[fldname]

    team_tuple = collections.namedtuple('team_tuple',
                                        'org ' + ' '.join(fields))
    return team_tuple(**values)

#-------------------------------------------------------------------------------
def teammembers(teamid=None):
    """Get members of a specified team.

    teamid = the GitHub ID for the team (either integer or string)

    Returns a list of namedtuples with info about the members of the team.

    NOTE: this function uses msgithub.py (if available) to get Microsoft email
    address associated with GitHub logins. If msgithub.py is not available, the
    email addresses are blank.
    """
    try:
        import msgithub
        ms_emails = True # do have access to MS email mappings
    except ImportError:
        ms_emails = False # don't have access to MS email mappings

    # allow for integer or string teamid
    teamstr = teamid if isinstance(teamid, str) else str(teamid)
    endpoint = 'https://api.github.com/teams/' + teamstr + '/members'

    teamlist = [] # members of this team
    totpages = 0
    member_tuple = collections.namedtuple('member_tuple', 'login site_admin email')

    while True:

        response = github_api(endpoint=endpoint, auth=auth_user())
        if response.ok:
            totpages += 1
            thispage = json.loads(response.text)
            for member in thispage:
                values = {}
                values['login'] = member['login']
                values['site_admin'] = member['site_admin']
                if ms_emails:
                    values['email'] = msgithub.ms_email(member['login'])
                else:
                    values['email'] = ''
                teamlist.append(member_tuple(**values))

        pagelinks = pagination(response)
        endpoint = pagelinks['nextURL']
        if not endpoint:
            break # there are no more results to process

        print('processing page {0} of {1}'. \
                    format(pagelinks['nextpage'], pagelinks['lastpage']))

    return teamlist

#-------------------------------------------------------------------------------
def teams(org=None, fields=None):
    """Get teams for one or more organizations.

    org = organization ID, or a list of organizations
    fields = list of field names to be returned; names must be the same as
             returned by the GitHub API (see below).

    Note: to access team information, you must be authenticated as a member of
    the Owners team for the team's organization.

    Returns a list of namedtuple objects, one per team.

    GitHub API fields (as of March 2016): description, id, members_url, name,
        permission, privacy, repositories_url, slug, url
    """
    teamlist = [] # the list of members that will be returned

    # org may be a single value as a string, or a list of values
    if isinstance(org, str):
        teamlist.extend(teamsget(org, fields))
    else:
        for orgid in org:
            teamlist.extend(teamsget(orgid, fields))

    return teamlist

#------------------------------------------------------------------------------
def teamsget(org, fields):
    """Get team info for a specified organization. Called by teams() to
    aggregate team information for multiple organizations.

    1st parameter = organization ID
    2nd parameter = list of fields to be returned

    Returns a list of namedtuples containing the specified fields.
    """
    endpoint = 'https://api.github.com/orgs/' + org + '/teams'
    retval = [] # the list to be returned
    totpages = 0

    while True:

        response = github_api(endpoint, auth=auth_user())
        if response.ok:
            totpages += 1
            thispage = json.loads(response.text)
            for team_json in thispage:
                retval.append(teamfields(team_json, fields, org))

        pagelinks = pagination(response)
        endpoint = pagelinks['nextURL']
        if not endpoint:
            break # no more results to process

        log_msg('processing page {0} of {1}'. \
                       format(pagelinks['nextpage'], pagelinks['lastpage']))

    log_msg('pages processed: {0}, total members: {1}'. \
        format(totpages, len(retval)))

    return retval

#-------------------------------------------------------------------------------
def timestamp():
    """Return current timestamp as a string - YYYY-MM-DD HH:MM:SS
    """
    return '{:%Y-%m-%d %H:%M:%S}'.format(datetime.datetime.now())

#-------------------------------------------------------------------------------
def write_csv(listobj, filename):
    """Write a list of namedtuples to a CSV file.

    1st parameter = the list
    2nd parameter = name of CSV file to be written
    """
    csvfile = open(filename, 'w', newline='')

    csvwriter = csv.writer(csvfile, dialect='excel')
    header_row = listobj[0]._fields
    csvwriter.writerow(header_row)

    for row in listobj:
        values = []
        for fldname in header_row:
            values.append(getattr(row, fldname))
        csvwriter.writerow(values)

    csvfile.close()

    log_msg('filename:', filename)
    log_msg('columns:', header_row)
    log_msg('total rows:', len(listobj))

# if running standalone, run tests ---------------------------------------------
if __name__ == '__main__':
    pytest.main(['-v'])
