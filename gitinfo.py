"""Helper functions for retrieving data via the GitHub API.

auth_config() ----> Configure authentication settings.
auth_user() ------> Return credentials for use in GitHub API calls.
github_api() -----> Call the GitHub API (wrapper for requests.get())
log_apistatus() --> Display the rate-limit status after the last API call.
log_config() -----> Configure message logging settings.
log_msg() --------> Log a status message.
memberfields() ---> Get field values for a member/user.
members() --------> Get members of one or more organizations.
membersget() -----> Get member info for a specified organization.
pagination() -----> Parse 'link' HTTP header returned by GitHub API.
repofields() -----> Get field values for a repo.
repos() ----------> Get repo information for organization(s) or user(s).
reposget() -------> Get repo information from specified API endpoint.
session_end() ----> Log summary of completed gitinfo "session."
session_start() --> Initiate a gitinfo session for logging/tracking purposes.
teamfields() -----> Get field values for a team.
teams() ----------> Get teams for one or more organizations.
teamsget() -------> Get team info for a specified organization.
timestamp() ------> Return current timestamp as a string - YYYY-MM-DD HH:MM:SS
write_csv() ------> Write a list of namedtuples to a CSV file.
"""
import collections
import csv
import datetime
import inspect
import json
import os
import time
import traceback

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
    """
    if not _settings.username:
        return None

    username = _settings.username
    access_token = _settings.accesstoken

    log_msg('username:', username + ', PAT:',
            access_token[0:2] + '...' + access_token[-2:])

    return (username, access_token)

#-------------------------------------------------------------------------------
def github_api(endpoint=None, auth=None, headers=None):
    """Call the GitHub API (wrapper for requests.get()).

    endpoint = the HTTP endpoint to call
    auth = optional tuple for authentication
    headers = optional dictionary of HTTP headers to pass
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
    """
    values = {}
    values['org'] = org
    for fldname in fields:
        values[fldname] = member_json[fldname]

    member_tuple = collections.namedtuple('member_tuple',
                                          'org ' + ' '.join(fields))
    return member_tuple(**values)

#-------------------------------------------------------------------------------
def members(org=None, fields=None, audit2fa=False):
    """Get members for one or more organizations.

    org = an organization ID or list of organizations
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
    if not fields:
        fields = ['login', 'id', 'type', 'site_admin'] # default field list

    memberlist = [] # the list of members that will be returned

    # org may be a single value as a string, or a list of values
    if isinstance(org, str):
        memberlist.extend(membersget(org, fields, audit2fa))
    else:
        for orgid in org:
            memberlist.extend(membersget(orgid, fields, audit2fa))

    return memberlist

#------------------------------------------------------------------------------
def membersget(org, fields, audit2fa=False):
    """Get member info for a specified organization.

    1st parameter = organization ID
    2nd parameter = list of fields to be returned
    audit2fa = whether to only return members with 2FA disabled.
               Note: for audit2fa=True, you must be authenticated via
               auth_config() as an admin of the org(s).

    Returns a list of namedtuples containing the specified fields.
    """
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
def repofields(repo_json, fields):
    """Get field values for a repo.

    1st parameter = repo's json representation as returned by GitHub API
    2nd parameter = list of names of desired fields

    Returns a namedtuple containing the desired fields and their values.
    """

    # change '.' to '_' because can't have '.' in an identifier
    fldnames = [_.replace('.', '_') for _ in fields]

    repo_tuple = collections.namedtuple('Repo', ' '.join(fldnames))

    values = {}
    for fldname in fields:
        if '.' in fldname:
            # special case - embedded field within a JSON object
            try:
                values[fldname.replace('.', '_')] = \
                    repo_json[fldname.split('.')[0]][fldname.split('.')[1]]
            except TypeError:
                values[fldname.replace('.', '_')] = None
        else:
            # simple case: copy a value from the JSON to the namedtuple
            values[fldname] = repo_json[fldname]

    return repo_tuple(**values)

#-------------------------------------------------------------------------------
def repos(org=None, user=None, fields=None):
    """Get repo information for organization(s) or user(s).

    org    = organization; an organization or list of organizations
    user   = username; a username or list of usernames
    fields = list of fields to be returned; names must be the same as
             returned by the GitHub API (see below).
             Note: dot notation for embedded elements is supported.
             For example, pass a field named 'license.name' to get the 'name'
             element of the 'license' entry for each repo.

    Returns a list of namedtuple objects, one per repo.

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
    if not fields:
        fields = ['full_name', 'watchers', 'forks', 'open_issues'] # default

    repolist = [] # the list that will be returned

    if org:
        # get repos by organization
        if isinstance(org, str):
            # one organization
            endpoint = 'https://api.github.com/orgs/' + org + '/repos'
            repolist.extend(reposget(endpoint, fields))
        else:
            # list of organizations
            for orgid in org:
                endpoint = 'https://api.github.com/orgs/' + orgid + '/repos'
                repolist.extend(reposget(endpoint, fields))
    else:
        # get repos by user
        if isinstance(user, str):
            # one user
            endpoint = 'https://api.github.com/users/' + user + '/repos'
            repolist.extend(reposget(endpoint, fields))
        else:
            # list of users
            for userid in user:
                endpoint = 'https://api.github.com/users/' + userid + '/repos'
                repolist.extend(reposget(endpoint, fields))

    return repolist

#-------------------------------------------------------------------------------
def reposget(endpoint, fields):
    """Get repo information from specified API endpoint.

    1st parameter = GitHub API endpoint
    2nd parameter = list of fields to be returned

    Returns a list of namedtuples containing the specified fields.
    """
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
                retval.append(repofields(repo_json, fields))

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
    _settings.last_remaining = 0 # remaining portion of rate limit after last API call

    msgline = 60*'-' if not msg else (' ' + msg + ' ').center(60, '-')
    log_msg(msgline)
    log_msg('filename:', os.path.abspath(__file__))

#-------------------------------------------------------------------------------
def teamfields(team_json, fields, org):
    """Get field values for a team.

    1st parameter = team's json representation as returned by GitHub API
    2nd parameter = list of names of desired fields
    3rd parameter = organization ID

    Returns a namedtuple containing the desired fields and their values.
    NOTE: in addition to the specified fields, always returns an 'org' field
    to distinguish between orgs in multi-org lists returned by teams().
    """
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

    GitHub API fields (as of March 2016):
    description
    id
    members_url
    name
    permission
    privacy
    repositories_url
    slug
    url
    """
    if not fields:
        fields = ['name', 'id', 'privacy', 'permission'] # default field list

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
    """Get team info for a specified organization.

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
def test_members():
    """Simple test for members() function.
    """
    membertest = members(org=['bitstadium', 'ms-iot'])
    print('total members returned:', len(membertest))

#-------------------------------------------------------------------------------
def test_repos():
    """Simple test for repos() function.
    """
    oct_repos = repos(user=['octocat'],
                      fields=['full_name', 'license.name', 'license', 'permissions.admin'])
    for repo in oct_repos:
        print(repo)

#-------------------------------------------------------------------------------
def test_pagination():
    """Simple test for pagination() function.
    """
    testlinks = "<https://api.github.com/organizations/6154722/" + \
        "repos?page=2>; rel=\"next\", <https://api.github.com/" + \
        "organizations/6154722/repos?page=18>; rel=\"last\""
    print(pagination(testlinks))

#-------------------------------------------------------------------------------
def test_teams():
    """Simple test for teams() function.
    """
    teamtest = teams(org=['bitstadium', 'ms-iot'])
    for team in teamtest:
        print(team)
    print('total teams returned:', len(teamtest))

# if running standalone, run tests ---------------------------------------------
if __name__ == "__main__":

    log_config({'verbose': True, 'logfile': 'gitinfo.log'})
    auth_config({'username': 'msftgits'})
    session_start('inline tests')
    #test_auth_user()
    #test_members()
    #test_repos()
    #test_pagination()
    test_teams()
    session_end()
