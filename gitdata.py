"""GitHub query CLI.

Entry point:
cli() ----------------> Handle command-line arguments.

access_token() -------> Get GitHub access token from private settings.
adminstats() ---------> not implemented
auth_config() --------> Configure authentication settings.
auth_status() --------> Display status for GitHub username.
auth_user() ----------> Return credentials for use in GitHub API calls.
collabs() ------------> not implemented
files() --------------> not implemented
github_api() ---------> Call the GitHub API (wrapper for requests.get()).
inifile_name() -------> Return name of INI file where GitHub tokens are stored.
log_msg() ------------> Log a status message.
members() ------------> not implemented
pagination() ---------> Parse pagination URLs from 'link' HTTP header.
repos() --------------> Get repo info for an org or user.
repofields() ---------> Get fields/values for a repo.
reposdata() ----------> Get repo information for organizations or users.
reposget() -----------> Get repo information for a specified org or user.
repos_listfields() ---> List valid field names for repos().
teams() --------------> not implemented
timestamp() ----------> Get current timestamp 'YYYY-MM-DD HH:MM:SS''
token_abbr() ---------> Get abbreviated access token (for display purposes).
write_csv() ----------> Write list of dictionaries to a CSV file.
write_json() ---------> Write list of dictionaries to a JSON file.
"""
import collections
import configparser
import csv
import datetime
import inspect
import json
import os
import time

import click
#from click.testing import CliRunner
import requests

#------------------------------------------------------------------------------
CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])
@click.group(context_settings=CONTEXT_SETTINGS, options_metavar='[options]',
             invoke_without_command=True)
@click.version_option(version='1.0', prog_name='Photerino')
@click.option('-a', '--auth', default='',
              help='check auth status for specified username', metavar='')
@click.option('-t', '--token', default='',
              help='store access token for specified username', metavar='')
@click.option('-d', '--delete', default=False,
              help='delete specified username', is_flag=True, metavar='')
@click.pass_context
def cli(ctx, auth, token, delete):
    """\b
--------------------------------------------------------
command syntax help --> gitdata COMMAND -h
--------------------------------------------------------"""
    if auth:
        auth_status(auth.lower(), token, delete)
        return

    if ctx.invoked_subcommand is None:
        click.echo('Nothing to do. Type gitdata -h for help.')

#------------------------------------------------------------------------------
class _settings:
    """This class exists to provide a namespace used for global settings.
    Use auth_config() or log_config() to change these settings.
    """

    # authentication settings used by auth_*() functions
    username = '' # default = no GitHub authentication
    accesstoken = '' # auth_config() may set this from the 'private' folder

    # logging settings used by log_*() functions
    verbose = False # default = messages displayed to console
    logfile = None # default = messages not logged to a file

    # initialize gitinfo session settings
    start_time = time.time() # session start time (seconds)
    tot_api_calls = 0 # number of API calls made through gitinfo
    tot_api_bytes = 0 # total bytes returned by these API calls
    last_ratelimit = 0 # API rate limit for the most recent API call
    last_remaining = 0 # remaining portion of rate limit after last API call

#------------------------------------------------------------------------------
@cli.command(help='syntax help: gitdata adminstats -h')
def adminstats():
    """NOT IMPLEMENTED
    """
    click.echo('NOT IMPLEMENTED: admins()')

#-------------------------------------------------------------------------------
def access_token(username):
    """Get GitHub access token from private INI data.

    username = GitHub username

    Returns the access token for this username, or None if not found.
    """
    datafile = inifile_name()

    config = configparser.ConfigParser()
    config.read(datafile)
    try:
        retval = config.get(username, 'PAT')
    except configparser.NoSectionError:
        retval = None

    return retval

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
    # user's PAT in github_users.ini
    if settings and 'username' in settings and not 'accesstoken' in settings:
        if settings['username'] is None:
            settings['accesstoken'] = None
        else:
            settings['accesstoken'] = access_token(settings['username'])

    if settings:
        for setting in config_settings:
            if setting in settings:
                setattr(_settings, setting, settings[setting])

    retval = dict()
    for setting in config_settings:
        retval[setting] = getattr(_settings, setting)

    username = str(_settings.username)
    accesstoken = _settings.accesstoken

    log_msg('username:', username + ', PAT:', token_abbr(accesstoken))

    return retval

#------------------------------------------------------------------------------
def auth_status(auth, token, delete):
    """Display status for a GitHub user.

    auth   = username
    token  = optional GitHub access token; if provided, the existing token in
             the INI file is replaced with this value.
    delete = flag for whether to delete the username from INI file
    """
    if token or delete:
        # both of these options write to the file, so initialize parser
        configfile = inifile_name()
        config = configparser.ConfigParser()
        config.read(configfile)
        if delete:
            config.remove_section(auth)
        else:
            # save this token; may need to create a new section
            if not auth in config.sections():
                config[auth] = {}
            config[auth]['PAT'] = token
        with open(configfile, 'w') as fhandle:
            config.write(fhandle)

    # display username and access token
    click.echo('  Username: ' + auth)
    click.echo('     Token: ' + token_abbr(access_token(auth)))

    # call GitHub API with 'r' view option to display current rate-limit status
    auth_config({'username': auth})
    github_api(endpoint='https://api.github.com', auth=auth_user(), view_options='r')

#------------------------------------------------------------------------------
def auth_user():
    """Credentials for basic authentication.

    Returns the tuple used for API calls, based on current settings.
    Returns None if no GitHub username/PAT is currently set.
    <internal>
    """
    if not _settings.username:
        return None

    return (_settings.username, _settings.accesstoken)

#------------------------------------------------------------------------------
@cli.command(help='syntax help: gitdata collabs -h')
def collabs():
    """NOT IMPLEMENTED
    """
    click.echo('NOT IMPLEMENTED: collabs()')

#------------------------------------------------------------------------------
@cli.command(help='syntax help: gitdata files -h')
def files():
    """NOT IMPLEMENTED
    """
    click.echo('NOT IMPLEMENTED: files()')

#-------------------------------------------------------------------------------
def github_api(*, endpoint=None, auth=None, headers=None, view_options=None):
    """Call the GitHub API (wrapper for requests.get()).

    endpoint = the HTTP endpoint to call
    auth = optional tuple for authentication
    headers = optional dictionary of HTTP headers to pass

    Returns the response object.
    API call through this function update session totals.
    NOTE: passes the Accept header to use version V3 of the GitHub API. This can
    be explicitly overridden by passing a different Accept header if desired.
    <internal>
    """
    if not endpoint:
        log_msg('ERROR: github_api() called with no endpoint')
        return

    # add the V3 Accept header to the dictionary
    headers = {} if not headers else headers
    headers_dict = {**{"Accept": "application/vnd.github.v3+json"}, **headers}

    # make the API call, get response object
    if auth:
        response = requests.get(endpoint, auth=auth, headers=headers_dict)
    else:
        response = requests.get(endpoint, headers=headers_dict)

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

    if view_options and 'r' in view_options.lower():
        print('Rate Limit: ' + str(_settings.last_ratelimit) + ' (' + \
              str(_settings.last_ratelimit - _settings.last_remaining) +\
              ' used, ' + str(_settings.last_remaining) + ' remaining)')

    return response

#-------------------------------------------------------------------------------
def inifile_name():
    """Return full name of INI file where GitHub tokens are stored.
    Note that this file is stored in a 'private' subfolder under the location of
    the gitinfo module.
    """
    return os.path.join(os.path.dirname(os.path.realpath(__file__)),
                        'private/github_users.ini')

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

#------------------------------------------------------------------------------
@cli.command(help='syntax help: gitdata members -h')
def members():
    """NOT IMPLEMENTED
    """
    click.echo('NOT IMPLEMENTED: members()')

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

#------------------------------------------------------------------------------
@cli.command(help='syntax help: gitdata repos -h')
@click.option('-o', '--org', default='',
              help='GitHub organization', metavar='')
@click.option('-u', '--user', default='',
              help='GitHub user', metavar='')
@click.option('-a', '--authuser', default='',
              help='authentication username', metavar='')
@click.option('-v', '--view', default='',
              help='D=data, A=API calls, H=HTTP status codes, R=rate-limit status', metavar='')
@click.option('-n', '--filename', default='',
              help='output filename (.CSV or .JSON)', metavar='')
@click.option('-f', '--fields', default='',
              help='fields to include', metavar='<fld1/fld2/etc>')
@click.option('-l', '--fieldlist', is_flag=True,
              help='list available GitHub fields')
def repos(org, user, authuser, view, filename, fields, fieldlist):
    """Get repository information.
    """
    if fieldlist:
        repos_listfields()
        return

    if not org and not user:
        click.echo('ERROR: must specify an org or user')
        return

    if filename:
        _, file_ext = os.path.splitext(filename)
        if file_ext.lower() not in ['.csv', '.json']:
            click.echo('ERROR: output file must be .CSV or .JSON')
            return

    view = 'd' if not view else view

    if authuser:
        xxx = auth_config({'username': authuser})
        if not xxx['accesstoken']:
            click.echo('Unknown authentication username: ' + authuser)

    if fields:
        repolist = reposdata(org=org, user=user, fields=fields.split('/'), view_options=view)
    else:
        repolist = reposdata(org=org, user=user, view_options=view)

    if 'd' in view.lower():
        # display data on the console
        for repo in repolist:
            values = [str(item) for _, item in repo.items()]
            click.echo(click.style(','.join(values), fg='cyan'))

    if filename:
        if file_ext.lower() == '.json':
            # write JSON file
            write_json(source=repolist, filename=filename)
        else:
            # write CSV file
            write_csv(repolist, filename)
        click.echo('Output file written: ' + filename)

    try:
        if _settings.unknownfieldname:
            click.echo('Unknown field name: ' + _settings.unknownfieldname)
    except AttributeError:
        # no unknown fields have been logged
        pass

#-------------------------------------------------------------------------------
def repofields(repo_json, fields):
    """Get field values for a repo.

    1st parameter = repo's json representation as returned by GitHub API
    2nd parameter = list of names of desired fields

    Returns a dictionary containing the desired fields and their values.
    Note special cases:
    fields=['*'] -------> return all fields returned by GitHub API
    fields=['nourls'] -> return all non-URL fields (not *_url or url)
    fields=['urls'] ----> return all URL fields (*_url and url)
    <internal>
    """
    if not fields:
        # if no fields specified, use default field list
        fields = ['owner.login', 'name']

    # handle special cases
    if fields[0] in ['*', 'urls', 'nourls']:
        # special cases to return all fields or all url/non-url fields
        values = collections.OrderedDict()
        for fldname in repo_json:
            if fields[0] == '*' or \
                (fields[0] == 'urls' and fldname.endswith('url')) or \
                (fields[0] == 'nourls' and not fldname.endswith('url')):
                this_item = repo_json[fldname]
                if str(this_item.__class__) == "<class 'dict'>" and \
                    fields[0] == 'nourls':
                    # this is an embedded dictionary, so for the 'nourls' case
                    # remove *url fields ...
                    values[fldname] = {key:value for
                                       (key, value) in this_item.items()
                                       if not key.endswith('url')}
                else:
                    values[fldname] = this_item
    else:
        # fields == an actual list of fieldnames, not a special case
        values = collections.OrderedDict()
        for fldname in fields:
            if '.' in fldname:
                # special case - embedded field within a JSON object
                try:
                    values[fldname.replace('.', '_')] = \
                        repo_json[fldname.split('.')[0]][fldname.split('.')[1]]
                except (TypeError, KeyError):
                    # change '.' to '_' because can't have '.' in an identifier
                    values[fldname.replace('.', '_')] = None
            else:
                # simple case: copy a field/value pair
                try:
                    values[fldname] = repo_json[fldname]
                    if fldname.lower() == 'private':
                        values[fldname] = 'private' if repo_json[fldname] else 'public'
                except KeyError:
                    _settings.unknownfieldname = fldname

    return values

#-------------------------------------------------------------------------------
def reposdata(*, org=None, user=None, fields=None, view_options=None):
    """Get repo information for one or more organizations or users.

    org    = organization; an organization or list of organizations
    user   = username; a username or list of usernames (if org is provided,
             user is ignored)
    fields = list of fields to be returned; names must be the same as
             returned by the GitHub API (see below).
             Dot notation for embedded elements is supported. For example,
             pass a field named 'license.name' to get the 'name' element of
             the 'license' entry for each repo.
             These special cases are also supported:
             fields=['*'] -------> return all fields returned by GitHub API
             fields=['nourls'] -> return all non-URL fields (not *_url or url)
             fields=['urls'] ----> return all URL fields (*_url and url)
    view_options = optional string containing either 'a' (to display API calls)
                   or 'h' (to display HTTP status codes)

    Returns a list of dictionary objects, one per repo.
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
            repolist.extend(reposget(org=org, fields=fields, view_options=view_options))
        else:
            # list of organizations
            for orgid in org:
                repolist.extend(reposget(org=orgid, fields=fields, view_options=view_options))
    else:
        # get repos by user
        if isinstance(user, str):
            # one user
            repolist.extend(reposget(user=user, fields=fields, view_options=view_options))
        else:
            # list of users
            for userid in user:
                repolist.extend(reposget(user=userid, fields=fields, view_options=view_options))

    return repolist

#-------------------------------------------------------------------------------
def reposget(*, org=None, user=None, fields=None, view_options=None):
    """Get repo information for a specified org or user. Called by repos() to
    aggregate repo information for multiple orgs or users.

    org = organization name
    user = username (ignored if org is provided)
    fields = list of fields to be returned

    Returns a list of dictionaries containing the specified fields.

    NOTE: if authenticated user is same as specified user, the returned data
    will NOT include their private repos. To get private repos, need to use
    the user/repos endpoint (and that includes every repo they have access to,
    in any org, in addition to their own repos)
    <internal>
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

        if view_options and 'a' in view_options.lower():
            print('  Endpoint: ' + endpoint)

        response = github_api(endpoint=endpoint, auth=auth_user(),
                              headers=headers, view_options=view_options)

        if view_options and 'h' in view_options.lower():
            print('    Status: ' + str(response))

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

#------------------------------------------------------------------------------
def repos_listfields():
    """List valid field names for repos().
    """
    click.echo(click.style('\n     specified fields -->  --fields=', fg='white'), nl=False)
    click.echo(click.style('fld1/fld2/etc', fg='cyan'))
    click.echo(click.style('           ALL fields -->  --fields=', fg='white'), nl=False)
    click.echo(click.style('*', fg='cyan'))
    click.echo(click.style('              No URLs -->  --fields=', fg='white'), nl=False)
    click.echo(click.style('nourls', fg='cyan'))
    click.echo(click.style('            Only URLs -->  --fields=', fg='white'), nl=False)
    click.echo(click.style('urls', fg='cyan'))
    click.echo(click.style(60*'-', fg='blue'))
    click.echo(click.style('archive_url         git_tags_url         open_issues', fg='cyan'))
    click.echo(click.style('assignees_url       git_url              open_issues_count', fg='cyan'))
    click.echo(click.style('blobs_url           has_downloads        private', fg='cyan'))
    click.echo(click.style('branches_url        has_issues           pulls_url', fg='cyan'))
    click.echo(click.style('clone_url           has_pages            pushed_at', fg='cyan'))
    click.echo(click.style('collaborators_url   has_wiki             releases_url', fg='cyan'))
    click.echo(click.style('commits_url         homepage             size', fg='cyan'))
    click.echo(click.style('compare_url         hooks_url            ssh_url', fg='cyan'))
    click.echo(click.style('contents_url        html_url             stargazers_count', fg='cyan'))
    click.echo(click.style('contributors_url    id                   stargazers_url', fg='cyan'))
    click.echo(click.style('created_at          issue_comment_url    statuses_url', fg='cyan'))
    click.echo(click.style('default_branch      issue_events_url     subscribers_url', fg='cyan'))
    click.echo(click.style('deployments_url     issues_url           subscription_url', fg='cyan'))
    click.echo(click.style('description         keys_url             svn_url', fg='cyan'))
    click.echo(click.style('downloads_url       labels_url           tags_url', fg='cyan'))
    click.echo(click.style('events_url          language             teams_url', fg='cyan'))
    click.echo(click.style('fork                languages_url        trees_url', fg='cyan'))
    click.echo(click.style('forks               master_branch        updated_at', fg='cyan'))
    click.echo(click.style('forks_count         merges_url           url', fg='cyan'))
    click.echo(click.style('forks_url           milestones_url       watchers', fg='cyan'))
    click.echo(click.style('full_name           mirror_url           watchers_count', fg='cyan'))
    click.echo(click.style('git_commits_url     name', fg='cyan'))
    click.echo(click.style('git_refs_url        notifications_url', fg='cyan'))
    click.echo(click.style(60*'-', fg='blue'))
    click.echo(click.style('license.featured              owner.login', fg='cyan'))
    click.echo(click.style('license.key                   owner.organizations_url', fg='cyan'))
    click.echo(click.style('license.name                  owner.received_events_url', fg='cyan'))
    click.echo(click.style('license.url                   owner.repos_url', fg='cyan'))
    click.echo(click.style('owner.avatar_url              owner.site_admin', fg='cyan'))
    click.echo(click.style('owner.events_url              owner.starred_url', fg='cyan'))
    click.echo(click.style('owner.followers_url           owner.subscriptions_url', fg='cyan'))
    click.echo(click.style('owner.following_url           owner.type', fg='cyan'))
    click.echo(click.style('owner.gists_url               owner.url', fg='cyan'))
    click.echo(click.style('owner.gravatar_id             permissions.admin', fg='cyan'))
    click.echo(click.style('owner.html_url                permissions.pull', fg='cyan'))
    click.echo(click.style('owner.id                      permissions.push', fg='cyan'))

#------------------------------------------------------------------------------
def teams():
    """NOT IMPLEMENTED
    """
    click.echo('NOT IMPLEMENTED: teams()')

#-------------------------------------------------------------------------------
def timestamp():
    """Return current timestamp as a string - YYYY-MM-DD HH:MM:SS
    <internal>
    """
    return '{:%Y-%m-%d %H:%M:%S}'.format(datetime.datetime.now())

#-------------------------------------------------------------------------------
def token_abbr(accesstoken):
    """Get abbreviated access token (for display purposes).

    Returns an abbreviated version of the passed access token, including only
    the first 2 and last 2 characters.
    """
    if accesstoken:
        return accesstoken[0:2] + '...' + accesstoken[-2:]
    else:
        return "*none*"

#-------------------------------------------------------------------------------
def write_csv(listobj, filename):
    """Write list of dictionaries to a CSV file.

    1st parameter = the list of dictionaries
    2nd parameter = name of CSV file to be written
    """
    csvfile = open(filename, 'w', newline='')

    # note that we assume all dictionaries in the list have the same keys
    csvwriter = csv.writer(csvfile, dialect='excel')
    header_row = [key for key, _ in listobj[0].items()]
    csvwriter.writerow(header_row)

    for row in listobj:
        values = []
        for fldname in header_row:
            values.append(row[fldname])
        csvwriter.writerow(values)

    csvfile.close()

    log_msg('filename:', filename)
    log_msg('columns:', header_row)
    log_msg('total rows:', len(listobj))

#-------------------------------------------------------------------------------
def write_json(source=None, filename=None):
    """Write list of dictionaries to a JSON file.

    source = the list of dictionaries
    filename = the filename (will be over-written if it already exists)
    <internal>
    """
    if not source or not filename:
        return # nothing to do

    with open(filename, 'w') as fhandle:
        fhandle.write(json.dumps(source, indent=4, sort_keys=True))

# code to execute when running standalone: -------------------------------------
if __name__ == '__main__':
    print('implement tests here')
