"""Helper functions for retrieving data via the GitHub API.

auth_config() --------> Configure authentication settings.
auth_user() ----------> Return credentials for use in GitHub API calls.
collaboratorfields() -> Get field values for a collaborator.
collaborators() ------> Get collaborators for one or more repos.
collaboratorsget() ---> Get collaborator info for a specified repo.
github_api() ---------> Call the GitHub API (wrapper for requests.get()).
log_apistatus() ------> Display current API rate-limit status.
log_config() ---------> Configure message logging settings.
log_msg() ------------> Log a status message.
memberfields() -------> Get field values for a member/user.
members() ------------> Get members of one or more organizations.
membersget() ---------> Get member info for a specified organization.
pagination() ---------> Parse 'link' HTTP header returned by GitHub API.
repofields() ---------> Get field values for a repo.
repos() --------------> Get repo information for organizations or users.
reposget() -----------> Get repo information for a specified org or user.
repoteamfields() -----> Get field values for a repo's team.
repoteams() ----------> Get teams associated with one or more repositories.
repoteamsget() -------> Get team info for a specified repo.
session_end() --------> Log summary of completed gitinfo "session."
session_start() ------> Initiate a gitinfo session for logging/tracking purposes.
teamfields() ---------> Get field values for an organization's team.
teams() --------------> Get teams for one or more organizations.
teamsget() -----------> Get team info for a specified organization.
timestamp() ----------> Return current timestamp as YYYY-MM-DD HH:MM:SS
write_csv() ----------> Write a list of namedtuples to a CSV file.
"""
import collections
import csv
import datetime
import inspect
import json
import os
import time

import requests

#------------------------------------------------------------------------------
class _settings: # pylint: disable=R0903
    """This class is just a namespace used for global settings.
    Use auth_config() or log_config() to change these settings.
    """

    # authentication settings used by auth_*() functions
    username = None # default = no GitHub authentication
    accesstoken = None # auth_config() may set this from the 'private' folder

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

    if access_token:
        # if a PAT is stored, only display first 2 and last 2 characters
        pat = access_token[0:2] + '...' + \
            access_token[-2:] # pylint: disable=E1136
    else:
        pat = "*none*"
    log_msg('username:', username + ', PAT:', pat)

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
    """
    GitHub API fields (as of March 2016):
    avatar_url          permissions.admin
    events_url          permissions.pull
    followers_url       permissions.push
    following_url       received_events_url
    gists_url           repos_url
    gravatar_id         site_admin
    html_url            starred_url
    id                  subscriptions_url
    login               type
    organizations_url   url
    """
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
    _settings.last_ratelimit = int(response.headers['X-RateLimit-Limit'])
    _settings.last_remaining = int(response.headers['X-RateLimit-Remaining'])

    return response

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
        fields = ['full_name', 'watchers', 'forks', 'open_issues']

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
    """ (separate docstring to keep the popup tooltip for repos() smaller)
    GitHub API fields (as of March 2016):
    archive_url         git_tags_url         open_issues
    assignees_url       git_url              open_issues_count
    blobs_url           has_downloads        private
    branches_url        has_issues           pulls_url
    clone_url           has_pages            pushed_at
    collaborators_url   has_wiki             releases_url
    commits_url         homepage             size
    compare_url         hooks_url            ssh_url
    contents_url        html_url             stargazers_count
    contributors_url    id                   stargazers_url
    created_at          issue_comment_url    statuses_url
    default_branch      issue_events_url     subscribers_url
    deployments_url     issues_url           subscription_url
    description         keys_url             svn_url
    downloads_url       labels_url           tags_url
    events_url          language             teams_url
    fork                languages_url        trees_url
    forks               master_branch        updated_at
    forks_count         merges_url           url
    forks_url           milestones_url       watchers
    full_name           mirror_url           watchers_count
    git_commits_url     name
    git_refs_url        notifications_url
    -------------------------------------------------------------
    license.featured              permissions.admin
    license.key                   permissions.pull
    license.name                  permissions.push
    license.url
    -------------------------------------------------------------
    owner.avatar_url              owner.organizations_url
    owner.events_url              owner.received_events_url
    owner.followers_url           owner.repos_url
    owner.following_url           owner.site_admin
    owner.gists_url               owner.starred_url
    owner.gravatar_id             owner.subscriptions_url
    owner.html_url                owner.type
    owner.id                      owner.url
    owner.login
    """
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

#===============================================================================
#------------------------------------ TESTS ------------------------------------
#===============================================================================

#-------------------------------------------------------------------------------
def test_auth_user():
    """Simple test for auth_user() function.
    """
    print(auth_user())

#-------------------------------------------------------------------------------
def test_collaborators():
    """Simple test for collaborators() function.
    """
    collabtest = collaborators(owner='microsoft', repo=['galaxyexplorer', 'dotnet-blog'])
    for collab in collabtest:
        print(collab)

#-------------------------------------------------------------------------------
def test_members():
    """Simple test for members() function.
    """
    membertest = members(org=['bitstadium', 'ms-iot'], audit2fa=True)
    for member in membertest:
        print(member)
    print('total members returned:', len(membertest))

#-------------------------------------------------------------------------------
def test_teams():
    """Simple test for teams() function.
    """
    teamtest = teams(org=['bitstadium', 'ms-iot'])
    for team in teamtest:
        print(team)
    print('total teams returned:', len(teamtest))


#-------------------------------------------------------------------------------
def test_pagination():
    """Simple test for pagination() function.
    """
    testlinks = "<https://api.github.com/organizations/6154722/" + \
        "repos?page=2>; rel=\"next\", <https://api.github.com/" + \
        "organizations/6154722/repos?page=18>; rel=\"last\""
    print(pagination(testlinks))

#-------------------------------------------------------------------------------
def test_repos():
    """Simple test for repos() function.
    """
    oct_repos = repos(user=['octocat'], fields= \
        ['full_name', 'license.name', 'license', 'permissions.admin'])
    for repo in oct_repos:
        print(repo)
    deployr_repos = repos(org='deployr', fields= \
        ['full_name', 'license.name', 'license', 'permissions.admin'])
    for repo in deployr_repos:
        print(repo)

#-------------------------------------------------------------------------------
def test_repoteams():
    """Simple test for repoteams() function.
    """
    teams = repoteams(org='ms-iot', repo=['serial-wiring', 'remote-sensor'])
    for team in teams:
        print(team)

# if running standalone, run tests ---------------------------------------------
if __name__ == "__main__":

    log_config({'verbose': True, 'logfile': 'gitinfo.log'})
    auth_config({'username': 'msftgits'})
    session_start('inline tests')

    #test_auth_user()
    test_collaborators()
    #test_members()
    #test_repos()
    #test_pagination()
    #test_teams()
    #test_repoteams()

    session_end()
