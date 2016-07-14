"""GitData 2.0 - GitHub query CLI

Entry point:
cli() --------------------> Handle command-line arguments.

access_token() -----------> Get GitHub access token from private settings.
auth_config() ------------> Configure authentication settings.
auth_status() ------------> Display status for GitHub username.
auth_user() --------------> Return credentials for use in GitHub API calls.

cache_exists() -----------> Check whether cached data exists for an endpoint.
cache_filename() ---------> Get cache filename for specified user/endpoint.
cache_update() -----------> Updated cached data for specified endpoint.

collabs() ----------------> Main handler for "collabs" subcommand.

data_display() -----------> Display data on console.
data_fields() ------------> Get dictionary of values from GitHub API JSON payload.
data_sort() --------------> Sort function for data_display().

data_write() -------------> Write output file.

default_fields() ---------> Get default field names for an entity.

elapsed_time() -----------> Display elapsed time.
filename_valid() ---------> Check passed filename for valid file type.

github_api() -------------> Call the GitHub API (wrapper for requests library).
github_data() ------------> Get data for specified GitHub API endpoint.
github_data_from_api() ---> Get data from GitHub REST API.
github_data_from_cache() -> Get data from local cache file.

inifile_name() -----------> Return name of INI file.

list_fields() ------------> Display available field names for an entity.

members() ----------------> Main handler for "members" subcommand.
membersdata() ------------> Get member information for orgs or teams.
membersget() -------------> Get member info for a specified organization.

orgs() -------------------> Main handler for "orgs" subcommand.

pagination() -------------> Parse pagination URLs from 'link' HTTP header.

read_json() --------------> Read serialized object from JSON file.

repos() ------------------> Main handler for "repos" subcommand.
reposdata() --------------> Get repo information for organizations or users.
reposget() ---------------> Get repo information for a specified org or user.

teams() ------------------> Main handler for "teams" subcommand.

timestamp() --------------> Get current timestamp or a file timestamp.
token_abbr() -------------> Get abbreviated access token (for display purposes).
unknown_fields() ---------> List unknown field names encountered this session.

wildcard_fields() --------> Display wildcard field options.

write_csv() --------------> Write list of dictionaries to a CSV file.
write_json() -------------> Write list of dictionaries to a JSON file.
"""
import collections
import configparser
import csv
import json
import os
import sys
import time
from timeit import default_timer

import click
import requests

#------------------------------------------------------------------------------
CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])
@click.group(context_settings=CONTEXT_SETTINGS, options_metavar='[options]',
             invoke_without_command=True)
@click.option('-a', '--auth', default='',
              help='GitHub username (for configuring access)', metavar='<str>')
@click.option('-t', '--token', default='',
              help='store access token for specified username', metavar='<str>')
@click.option('-d', '--delete', default=False,
              help='delete specified username', is_flag=True, metavar='')
@click.version_option(version='1.0', prog_name='Gitdata')
@click.pass_context
def cli(ctx, auth, token, delete):
    """\b
------------------------------------
Get information from GitHub REST API
------------------------------------
syntax help: gitdata <subcommand> -h"""
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
    accesstoken = '' # auth_config() may set this from '../_private' folder

    datasource = 'p' # a=API, c=cache, p=prompt user to select

    # current session object from requests library
    requests_session = None

    verbose = False # whether to display status information on console
    display_data = True # whether to display retrieved data on console

    # initialize gitinfo session settings
    start_time = time.time() # session start time (seconds)
    tot_api_calls = 0 # number of API calls made through gitinfo
    tot_api_bytes = 0 # total bytes returned by these API calls
    last_ratelimit = 0 # API rate limit for the most recent API call
    last_remaining = 0 # remaining portion of rate limit after last API call

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
        if not settings['username']:
            settings['accesstoken'] = None
        else:
            settings['accesstoken'] = access_token(settings['username'])
            if not settings['accesstoken']:
                click.echo('Unknown authentication username: ' +
                           settings['username'])

    if settings:
        for setting in config_settings:
            if setting in settings:
                setattr(_settings, setting, settings[setting])

    retval = dict()
    for setting in config_settings:
        retval[setting] = getattr(_settings, setting)

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

#------------------------------------------------------------------------------
def auth_user():
    """Credentials for basic authentication.

    Returns the tuple used for API calls, based on current settings.
    Returns None if no GitHub username/PAT is currently set.
    <internal>
    """
    if _settings.username:
        return (_settings.username, _settings.accesstoken)

    return None

#------------------------------------------------------------------------------
def cache_exists(endpoint, auth=None):
    """Check whether cached data exists for an endpoint.

    endpoint = GitHub REST API endpoint
    auth = GitHub authentication username

    Returns True if local cached data exists, False if not.
    """
    return os.path.isfile(cache_filename(endpoint, auth))

#------------------------------------------------------------------------------
def cache_filename(endpoint, auth=None):
    """Get cache filename for specified user/endpoint.

    endpoint = the endpoint at https://api.github.com (starts with /)
    auth = authentication username

    Returns the filename for caching data returned from this API call.
    """
    if not auth:
        auth = _settings.username if _settings.username else '_anon'

    source_folder = os.path.dirname(os.path.realpath(__file__))
    filename = auth + '_' + endpoint.replace('/', '-').strip('-') + '.json'

    return os.path.join(source_folder, 'gh_cache/' + filename)

#------------------------------------------------------------------------------
def cache_update(endpoint, payload, constants):
    """Update cached data.

    endpoint  = the API endpoint (e.g., '/repos/org')
    payload   = the list of dictionaries returned from API endpoint
    constants = dictionary of fieldnames/values to be included in the
                cached data (e.g., criteria used in the API call)

    Writes the cache file for this endpoint. Overwrites existing cached data.
    """

    if constants:
        # add the constants to the API payload
        cached_data = []
        for data_item in payload:
            for fldname in constants:
                data_item[fldname] = constants[fldname]
            cached_data.append(data_item)
    else:
        cached_data = payload # no constants to be added

    filename = cache_filename(endpoint)
    write_json(source=payload, filename=filename) # write cached data

    if _settings.verbose:
        nameonly = os.path.basename(filename)
        click.echo('Cache update: ', nl=False)
        click.echo(click.style(nameonly, fg='cyan'))

#------------------------------------------------------------------------------
@cli.command(help='Get collaborator information for a repo')
@click.option('-o', '--owner', default='',
              help='owner (org or user)', metavar='<str>')
@click.option('-r', '--repo', default='',
              help='repo name', metavar='<str>')
@click.option('-a', '--authuser', default='',
              help='authentication username', metavar='<str>')
@click.option('-s', '--source', default='p',
              help='data source - a/API, c/cache, or p/prompt', metavar='<str>')
@click.option('-n', '--filename', default='',
              help='output filename (.CSV or .JSON)', metavar='<str>')
@click.option('-f', '--fields', default='',
              help='fields to include', metavar='<str>')
@click.option('-d', '--display', is_flag=True, default=True,
              help="Don't display retrieved data")
@click.option('-v', '--verbose', is_flag=True, default=False,
              help="Display verbose status info")
@click.option('-l', '--listfields', is_flag=True,
              help='list available fields and exit.')
def collabs(owner, repo, authuser, source, filename, fields, display, verbose, listfields):
    """Get collaborator information for a repo.
    """
    if listfields:
        list_fields('collab')
        return

    if not owner or not repo:
        click.echo('ERROR: must specify owner and repo')
        return

    if not filename_valid(filename):
        return

    _settings.display_data = display
    _settings.verbose = verbose
    # for source option, store the 1st character, lower-case
    source = source if source else 'p'
    _settings.datasource = source.lower()[0]

    start_time = default_timer()
    auth_config({'username': authuser})
    fldnames = fields.split('/') if fields else None
    collablist = github_data(
        endpoint='/repos/' + owner + '/' + repo + '/collaborators', entity='collab',
        fields=fldnames, constants={"owner": owner, "repo": repo}, headers={})
    sorted_data = sorted(collablist, key=data_sort) # sort the data
    data_display(sorted_data)
    data_write(filename, sorted_data)
    unknown_fields() # list unknown field names (if any)
    elapsed_time(start_time)

#-------------------------------------------------------------------------------
def data_fields(*, entity=None, jsondata=None, fields=None, constants=None):
    """Get dictionary of desired values from GitHub API JSON payload.

    entity   = entity type ('repo', 'member')
    jsondata = a JSON payload returned by the GitHub API
    fields   = list of names of fields (entries) to include from the JSON data,
               or one of these shorthand values:
               '*' -------> return all fields returned by GitHub API
               'nourls' --> return all non-URL fields (not *_url or url)
               'urls' ----> return all URL fields (*_url and url)
    constants = dictionary of fieldnames/values that can be included in the
                specified fields but aren't returned by GitHub API (these are
                typically criteria used in the API call)

    Returns a dictionary of fieldnames/values.
    """

    if not fields:
        fields = default_fields(entity)

    values = collections.OrderedDict()

    if fields[0] in ['*', 'urls', 'nourls']:
        # special cases to return all fields or all url/non-url fields
        if constants and fields[0] in ['*', 'nourls']:
            values.update(constants)
        for fldname in jsondata:
            if fields[0] == '*' or \
                (fields[0] == 'urls' and fldname.endswith('url')) or \
                (fields[0] == 'nourls' and not fldname.endswith('url')):
                this_item = jsondata[fldname]
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
        for fldname in fields:

            if constants and fldname in constants:
                values[fldname] = constants[fldname]
            elif '.' in fldname:
                # special case - embedded field within a JSON object
                try:
                    values[fldname.replace('.', '_')] = \
                        jsondata[fldname.split('.')[0]][fldname.split('.')[1]]
                except (TypeError, KeyError):
                    values[fldname.replace('.', '_')] = None
            else:
                # simple case: copy a field/value pair
                try:
                    values[fldname] = jsondata[fldname]
                    if fldname.lower() == 'private':
                        values[fldname] = 'private' if jsondata[fldname] else 'public'
                except KeyError:
                    _settings.unknownfieldname = fldname

    return values

#------------------------------------------------------------------------------
def data_display(datasource=None):
    """Display data on console.

    datasource   = list of dictionaries

    If _settings.display_data, displays the data in console output
    """
    if not _settings.display_data:
        return

    for data_item in datasource:
        values = [str(value) for _, value in data_item.items()]
        click.echo(click.style(','.join(values), fg='cyan'))

#------------------------------------------------------------------------------
def data_sort(datadict):
    """Sort function for output lists.

    takes an OrderedDict object as input, returns lower-case version of the
    first value in the OrderedDict, for use as a sort key.
    """
    sortkey = list(datadict.keys())[0]
    sortvalue = str(datadict[sortkey]).lower()
    return sortvalue

#------------------------------------------------------------------------------
def data_write(filename=None, datasource=None):
    """Write output file.

    filename   = output filename
    datasource = list of dictionaries
    """
    if not filename:
        return

    _, file_ext = os.path.splitext(filename)

    if file_ext.lower() == '.json':
        write_json(source=datasource, filename=filename) # write JSON file
    else:
        write_csv(datasource, filename) # write CSV file

    click.echo('Output file written: ' + filename)

#------------------------------------------------------------------------------
def default_fields(entity=None):
    """Get default field names for an entity.

    entity = the entity/data type (e.g., "team" or "repo")

    Returns a list of the default field names for this entity.
    """
    if entity == 'member':
        return ['login', 'id', 'type', 'site_admin']
    elif entity == 'repo':
        return ['name', 'owner.login']
    elif entity == 'team':
        return ['name', 'id', 'privacy', 'permission']
    elif entity == 'org':
        return ['login', 'user']
    elif entity == 'collab':
        return ['login', 'owner', 'repo', 'id']

    return ['name'] # if unknown entity type, use name

#------------------------------------------------------------------------------
def elapsed_time(starttime):
    """Display elapsed time.

    starttime    = time to measure from, as returned by default_timer()

    If _settings.verbose, displays elapsed time in seconds.
    """
    if _settings.verbose:
        click.echo('Elapsed time: ', nl=False)
        elapsed = default_timer() - starttime
        click.echo(click.style("{0:.2f}".format(elapsed) + ' seconds', fg='cyan'))

#-------------------------------------------------------------------------------
def filename_valid(filename=None):
    """Check filename for valid file type.

    filename = output filename passed on command line

    Returns True if valid, False if not.
    """
    if not filename:
        return True # filename is optional

    _, file_ext = os.path.splitext(filename)
    if file_ext.lower() not in ['.csv', '.json']:
        click.echo('ERROR: output file must be .CSV or .JSON')
        return False

    return True

#-------------------------------------------------------------------------------
def github_api(*, endpoint=None, auth=None, headers=None):
    """Call the GitHub API.

    endpoint     = the HTTP endpoint to call; if it start with /, will be
                   appended to https://api.github.com

    auth         = optional tuple for authentication
    headers      = optional dictionary of HTTP headers to pass

    Returns the response object.

    NOTE: sends the Accept header to use version V3 of the GitHub API. This can
    be explicitly overridden by passing a different Accept header if desired.
    """
    if not endpoint:
        click.echo('ERROR: github_api() called with no endpoint')
        return None

    # set auth to empty tuple if not used
    auth = auth if auth else ()

    # add the V3 Accept header to the dictionary
    headers = {} if not headers else headers
    headers_dict = {**{"Accept": "application/vnd.github.v3+json"}, **headers}

    # make the API call
    if _settings.requests_session:
        sess = _settings.requests_session
    else:
        sess = requests.session()
        _settings.requests_session = sess

    sess.auth = auth
    full_endpoint = 'https://api.github.com' + endpoint if endpoint[0] == '/' \
        else endpoint
    response = sess.get(full_endpoint, headers=headers_dict)

    if _settings.verbose:
        click.echo('    Endpoint: ', nl=False)
        click.echo( \
            click.style(endpoint, fg='cyan'))

    # update rate-limit settings
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

    if _settings.verbose:
        # display rate-limite status
        if auth_user():
            username = '(user = ' + auth_user()[0] + ')'
        else:
            username = '(non-authenticated)'

        click.echo('  Rate Limit: ', nl=False)
        used = _settings.last_ratelimit - _settings.last_remaining
        click.echo(
            click.style(str(_settings.last_remaining) +
                        ' available, ' + str(used) +
                        ' used, ' + str(_settings.last_ratelimit) + ' total ' +
                        username, fg='cyan'))

    return response

#-------------------------------------------------------------------------------
def github_data(*, endpoint=None, entity=None, fields=None, constants=None,
                headers=None):
    """Get data for specified GitHub API endpoint.
    endpoint     = HTTP endpoint for GitHub API call
    entity       = entity type ('repo', 'member')
    fields       = list of fields to be returned
    constants    = dictionary of fieldnames/values that can be included in the
                   specified fields but aren't returned by GitHub API (these are
                   typically criteria used in the API call)
    headers      = HTTP headers to be included with API call

    Returns a list of dictionaries containing the specified fields.
    Returns a complete data set - if this endpoint does pagination, all pages
    are retrieved and aggregated.
    """
    # _settings.datasource contains one of these three values:
    # 'a' = call the GitHub REST API to get the data
    # 'c' = get data from the locally cached data for this endpoint/username
    # 'p' (or None) = prompt the user for which data to use

    if _settings.datasource == 'c' and not cache_exists(endpoint):
        click.echo('ERROR: cached data requested, but none found.')
        return []

    if _settings.datasource == 'a':
        read_from = 'a'
    elif _settings.datasource == 'c':
        read_from = 'c'
    else:
        # prompt user for which data source to use
        if cache_exists(endpoint):
            filetime = timestamp(cache_filename(endpoint))
            click.echo('Cached data found -->> ' + filetime)
            read_from = \
                click.prompt('Read from API (a), cache (c) or exit (x)?').lower()
        else:
            click.echo('Cached data not available.')
            read_from = click.prompt('Read from API (a) or exit (x)?').lower()

    if read_from == 'x':
        sys.exit(0)

    if read_from == 'a':
        all_fields = github_data_from_api(endpoint=endpoint, headers=headers)
        cache_update(endpoint, all_fields, constants)
    elif read_from == 'c':
        all_fields = github_data_from_cache(endpoint=endpoint)
        if _settings.verbose:
            nameonly = os.path.basename(cache_filename(endpoint))
            click.echo(' Data source: ', nl=False)
            click.echo(click.style(nameonly, fg='cyan'))
    else:
        all_fields = []

    # extract the requested fields and return them
    retval = []
    for json_item in all_fields:
        retval.append(data_fields(entity=entity, jsondata=json_item,
                                  fields=fields, constants=constants))
    return retval

#-------------------------------------------------------------------------------
def github_data_from_api(endpoint=None, headers=None):
    """Get data from GitHub REST API.

    endpoint     = HTTP endpoint for GitHub API call
    headers      = HTTP headers to be included with API call

    Returns the data as a list of dictionaries. Pagination is handled by this
    function, so the complete data set is returned.
    """
    headers = {} if not headers else headers

    payload = [] # the full data set (all fields, all pages)
    page_endpoint = endpoint # endpoint of each page in the loop below

    while True:
        response = github_api(endpoint=page_endpoint, auth=auth_user(),
                              headers=headers)
        if _settings.verbose or response.status_code != 200:
            # note that status code is always displayed if not 200/OK
            click.echo('      Status: ', nl=False)
            click.echo(click.style(str(response) + ', ' + str(len(response.text)) +
                                   ' bytes returned', fg='cyan'))
        if response.ok:
            thispage = json.loads(response.text)
            payload.extend(thispage)

        pagelinks = pagination(response)
        page_endpoint = pagelinks['nextURL']
        if not page_endpoint:
            break # no more results to process

    return payload

#-------------------------------------------------------------------------------
def github_data_from_cache(endpoint=None):
    """Get data from local cache file.

    endpoint = GitHub API endpoint
    """
    filename = cache_filename(endpoint)
    return read_json(filename)

#-------------------------------------------------------------------------------
def inifile_name():
    """Return full name of INI file where GitHub tokens are stored.
    Note that this file is stored in a 'private' subfolder under the parent
    folder of the gitinfo module.
    """
    source_folder = os.path.dirname(os.path.realpath(__file__))
    return os.path.join(source_folder, '../_private/github_users.ini')

#------------------------------------------------------------------------------
def list_fields(entity=None):
    """Display available field names for an entity.

    entity = the entity type (e.g., 'org' or 'team')

    Displays to the console a list of available field names for this entity.
    """
    click.echo('\nDefault fields for ' + entity.upper() + 'S: ', nl=False)
    click.echo(click.style('/'.join(default_fields(entity)), fg='cyan'))
    click.echo(click.style(60*'-', fg='blue'))
    wildcard_fields()

    if entity == 'collab':
        click.echo(click.style('avatar_url'.ljust(27) + 'organizations_url', fg='cyan'))
        click.echo(click.style('events_url'.ljust(27) + 'received_events_url', fg='cyan'))
        click.echo(click.style('followers_url'.ljust(27) + 'repos_url', fg='cyan'))
        click.echo(click.style('following_url'.ljust(27) + 'site_admin', fg='cyan'))
        click.echo(click.style('gists_url'.ljust(27) + 'starred_url', fg='cyan'))
        click.echo(click.style('gravatar_id'.ljust(27) + 'subscriptions_url', fg='cyan'))
        click.echo(click.style('html_url'.ljust(27) + 'type', fg='cyan'))
        click.echo(click.style('id'.ljust(27) + 'url', fg='cyan'))
        click.echo(click.style('login', fg='cyan'))
    elif entity == 'member':
        click.echo(click.style('id                  avatar_url          ' +
                               'html_url', fg='cyan'))
        click.echo(click.style('login               events_url          ' +
                               'organizations_url', fg='cyan'))
        click.echo(click.style('org                 followers_url       ' +
                               'received_events_url', fg='cyan'))
        click.echo(click.style('site_admin          following_url       ' +
                               'repos_url', fg='cyan'))
        click.echo(click.style('type                gists_url           ' +
                               'starred_url', fg='cyan'))
        click.echo(click.style('url                 gravatar_id         ' +
                               'subscriptions_url', fg='cyan'))
    elif entity == 'org':
        click.echo(click.style('avatar_url', fg='cyan'))
        click.echo(click.style('description', fg='cyan'))
        click.echo(click.style('events_url', fg='cyan'))
        click.echo(click.style('hooks_url', fg='cyan'))
        click.echo(click.style('id', fg='cyan'))
        click.echo(click.style('issues_url', fg='cyan'))
        click.echo(click.style('login', fg='cyan'))
        click.echo(click.style('members_url', fg='cyan'))
        click.echo(click.style('public_members_url', fg='cyan'))
        click.echo(click.style('repos_url', fg='cyan'))
        click.echo(click.style('url', fg='cyan'))
        click.echo(click.style('user', fg='cyan'))
    elif entity == 'repo':
        click.echo(click.style('archive_url         git_tags_url         ' +
                               'open_issues', fg='cyan'))
        click.echo(click.style('assignees_url       git_url              ' +
                               'open_issues_count', fg='cyan'))
        click.echo(click.style('blobs_url           has_downloads        ' +
                               'private', fg='cyan'))
        click.echo(click.style('branches_url        has_issues           ' +
                               'pulls_url', fg='cyan'))
        click.echo(click.style('clone_url           has_pages            ' +
                               'pushed_at', fg='cyan'))
        click.echo(click.style('collaborators_url   has_wiki             ' +
                               'releases_url', fg='cyan'))
        click.echo(click.style('commits_url         homepage             ' +
                               'size', fg='cyan'))
        click.echo(click.style('compare_url         hooks_url            ' +
                               'ssh_url', fg='cyan'))
        click.echo(click.style('contents_url        html_url             ' +
                               'stargazers_count', fg='cyan'))
        click.echo(click.style('contributors_url    id                   ' +
                               'stargazers_url', fg='cyan'))
        click.echo(click.style('created_at          issue_comment_url    ' +
                               'statuses_url', fg='cyan'))
        click.echo(click.style('default_branch      issue_events_url     ' +
                               'subscribers_url', fg='cyan'))
        click.echo(click.style('deployments_url     issues_url           ' +
                               'subscription_url', fg='cyan'))
        click.echo(click.style('description         keys_url             ' +
                               'svn_url', fg='cyan'))
        click.echo(click.style('downloads_url       labels_url           ' +
                               'tags_url', fg='cyan'))
        click.echo(click.style('events_url          language             ' +
                               'teams_url', fg='cyan'))
        click.echo(click.style('fork                languages_url        ' +
                               'trees_url', fg='cyan'))
        click.echo(click.style('forks               master_branch        ' +
                               'updated_at', fg='cyan'))
        click.echo(click.style('forks_count         merges_url           ' +
                               'url', fg='cyan'))
        click.echo(click.style('forks_url           milestones_url       ' +
                               'watchers', fg='cyan'))
        click.echo(click.style('full_name           mirror_url           ' +
                               'watchers_count', fg='cyan'))
        click.echo(click.style('git_commits_url     name', fg='cyan'))
        click.echo(click.style('git_refs_url        notifications_url', fg='cyan'))
        click.echo(click.style(60*'-', fg='blue'))
        click.echo(click.style('license.featured              ' +
                               'owner.login', fg='cyan'))
        click.echo(click.style('license.key                   ' +
                               'owner.organizations_url', fg='cyan'))
        click.echo(click.style('license.name                  ' +
                               'owner.received_events_url', fg='cyan'))
        click.echo(click.style('license.url                   ' +
                               'owner.repos_url', fg='cyan'))
        click.echo(click.style('owner.avatar_url              ' +
                               'owner.site_admin', fg='cyan'))
        click.echo(click.style('owner.events_url              ' +
                               'owner.starred_url', fg='cyan'))
        click.echo(click.style('owner.followers_url           ' +
                               'owner.subscriptions_url', fg='cyan'))
        click.echo(click.style('owner.following_url           ' +
                               'owner.type', fg='cyan'))
        click.echo(click.style('owner.gists_url               ' +
                               'owner.url', fg='cyan'))
        click.echo(click.style('owner.gravatar_id             ' +
                               'permissions.admin', fg='cyan'))
        click.echo(click.style('owner.html_url                ' +
                               'permissions.pull', fg='cyan'))
        click.echo(click.style('owner.id                      ' +
                               'permissions.push', fg='cyan'))
    elif entity == 'team':
        click.echo(click.style('description', fg='cyan'))
        click.echo(click.style('id', fg='cyan'))
        click.echo(click.style('members_url', fg='cyan'))
        click.echo(click.style('name', fg='cyan'))
        click.echo(click.style('org', fg='cyan'))
        click.echo(click.style('permission', fg='cyan'))
        click.echo(click.style('privacy', fg='cyan'))
        click.echo(click.style('repositories_url', fg='cyan'))
        click.echo(click.style('slug', fg='cyan'))
        click.echo(click.style('url', fg='cyan'))

#------------------------------------------------------------------------------
@cli.command(help='Get member information by org or team ID')
@click.option('-o', '--org', default='',
              help='organization name', metavar='')
@click.option('-t', '--team', default='',
              help='team ID', metavar='<str>')
@click.option('--audit2fa', is_flag=True,
              help='include only 2FA-not-enabled members')
@click.option('-a', '--authuser', default='',
              help='authentication username', metavar='<str>')
@click.option('-s', '--source', default='p',
              help='data source - a/API, c/cache, or p/prompt', metavar='<str>')
@click.option('-n', '--filename', default='',
              help='output filename (.CSV or .JSON)', metavar='<str>')
@click.option('-f', '--fields', default='',
              help='fields to include', metavar='<str>')
@click.option('-d', '--display', is_flag=True, default=True,
              help="Don't display retrieved data")
@click.option('-v', '--verbose', is_flag=True, default=False,
              help="Display verbose status info")
@click.option('-l', '--listfields', is_flag=True,
              help='list available fields and exit.')
def members(org, team, audit2fa, authuser, source, filename, fields, display, verbose, listfields):
    """Get member info for an organization or team.
    """
    if listfields:
        list_fields('member')
        return

    if not org and not team:
        click.echo('ERROR: must specify an org or team ID')
        return

    if not filename_valid(filename=filename):
        return

    _settings.display_data = display
    _settings.verbose = verbose
    # for source option, store the 1st character, lower-case
    source = source if source else 'p'
    _settings.datasource = source.lower()[0]

    start_time = default_timer()
    auth_config({'username': authuser})
    fldnames = fields.split('/') if fields else None
    memberlist = membersdata(org=org, team=team, audit2fa=audit2fa,
                             fields=fldnames)
    sorted_data = sorted(memberlist, key=data_sort) # sort the data
    data_display(sorted_data)
    data_write(filename, sorted_data)
    unknown_fields() # list unknown field names (if any)
    elapsed_time(start_time)

#-------------------------------------------------------------------------------
def membersdata(*, org=None, team=None, fields=None, audit2fa=False):
    """Get members for one or more teams or organizations.

    org = organization name
    team = team ID; if provided, org is ignored
    fields = list of field names to be returned; names must be the same as
             returned by the GitHub API (see list_fields()).
    audit2fa = whether to only return members with 2FA disabled. You must be
               authenticated via auth_config() as an admin of the org(s) to use
               this option.

    Returns a list of dictionary objects, one per member.
    """
    memberlist = [] # the list of members that will be returned

    if team:
        # get members by team
        memberlist.extend(membersget(team=team, fields=fields))
    else:
        # get members by organization
        memberlist.extend(membersget(org=org, fields=fields, audit2fa=audit2fa))

    return memberlist

#------------------------------------------------------------------------------
def membersget(*, org=None, team=None, fields=None, audit2fa=False):
    """Get member info for a specified organization. Called by members() to
    aggregate member info for multiple organizations.

    org =          organization ID (ignored if a team is specified)
    team =         team ID
    fields =       list of fields to be returned
    audit2fa =     whether to only return members with 2FA disabled. This
                   option is only available when retrieving members by
                   organization.
                   Note: for audit2fa=True, you must be authenticated via
                   auth_config() as an admin of the org(s).

    Returns a list of dictionaries containing the specified fields.
    <internal>
    """
    if team:
        endpoint = '/teams/' + team + '/members'
    else:
        endpoint = '/orgs/' + org + '/members' + \
            ('?filter=2fa_disabled' if audit2fa else '')

    return github_data(endpoint=endpoint, entity='member', fields=fields,
                       constants={"org": org}, headers={})

#------------------------------------------------------------------------------
@cli.command(help='Get org memberships for a user')
@click.option('-a', '--authuser', default='',
              help='authentication username', metavar='<str>')
@click.option('-s', '--source', default='p',
              help='data source - a/API, c/cache, or p/prompt', metavar='<str>')
@click.option('-n', '--filename', default='',
              help='output filename (.CSV or .JSON)', metavar='<str>')
@click.option('-f', '--fields', default='',
              help='fields to include', metavar='<str>')
@click.option('-d', '--display', is_flag=True, default=True,
              help="Don't display retrieved data")
@click.option('-v', '--verbose', is_flag=True, default=False,
              help="Display verbose status info")
@click.option('-l', '--listfields', is_flag=True,
              help='list available fields and exit.')
def orgs(authuser, source, filename, fields, display, verbose, listfields):
    """Get organization information.
    """
    if listfields:
        list_fields('org')
        return

    if not authuser:
        click.echo('ERROR: authentication username is required')
        return

    if not filename_valid(filename):
        return

    _settings.display_data = display
    _settings.verbose = verbose
    # for source option, store the 1st character, lower-case
    source = source if source else 'p'
    _settings.datasource = source.lower()[0]

    start_time = default_timer()
    auth_config({'username': authuser})
    fldnames = fields.split('/') if fields else None
    orglist = github_data(
        endpoint='/user/orgs', entity='org', fields=fldnames,
        constants={"user": authuser}, headers={})
    sorted_data = sorted(orglist, key=data_sort) # sort the data
    data_display(sorted_data)
    data_write(filename, sorted_data)
    unknown_fields() # list unknown field names (if any)
    elapsed_time(start_time)

#------------------------------------------------------------------------------
def pagination(link_header):
    """Parse values from the 'link' HTTP header returned by GitHub API.

    1st parameter = either of these options ...
                    - 'link' HTTP header passed as a string
                    - response object returned by requests library

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
def read_json(filename=None):
    """Read .json file into a Python object.

    filename = the filename
    Returns the object that has been serialized to the .json file (list, etc).
    <internal>
    """
    with open(filename, 'r') as datafile:
        retval = json.loads(datafile.read())
    return retval

#------------------------------------------------------------------------------
@cli.command(help='Get repo information by org or user/owner')
@click.option('-o', '--org', default='',
              help='GitHub organization', metavar='<str>')
@click.option('-u', '--user', default='',
              help='GitHub user', metavar='<str>')
@click.option('-a', '--authuser', default='',
              help='authentication username', metavar='<str>')
@click.option('-s', '--source', default='p',
              help='data source - a/API, c/cache, or p/prompt', metavar='<str>')
@click.option('-n', '--filename', default='',
              help='output filename (.CSV or .JSON)', metavar='<str>')
@click.option('-f', '--fields', default='',
              help='fields to include', metavar='<str>')
@click.option('-d', '--display', is_flag=True, default=True,
              help="Don't display retrieved data")
@click.option('-v', '--verbose', is_flag=True, default=False,
              help="Display verbose status info")
@click.option('-l', '--listfields', is_flag=True,
              help='list available fields and exit.')
def repos(org, user, authuser, source, filename, fields, display, verbose, listfields):
    """Get repository information.
    """
    if listfields:
        list_fields('repo')
        return

    if not org and not user:
        click.echo('ERROR: must specify an org or user')
        return

    if not filename_valid(filename):
        return

    _settings.display_data = display
    _settings.verbose = verbose
    # for source option, store the 1st character, lower-case
    source = source if source else 'p'
    _settings.datasource = source.lower()[0]

    start_time = default_timer()
    auth_config({'username': authuser})
    fldnames = fields.split('/') if fields else None
    repolist = reposdata(org=org, user=user, fields=fldnames)
    sorted_data = sorted(repolist, key=data_sort) # sort the data
    data_display(sorted_data)
    data_write(filename, sorted_data)
    unknown_fields() # list unknown field names (if any)
    elapsed_time(start_time)

#-------------------------------------------------------------------------------
def reposdata(*, org=None, user=None, fields=None):
    """Get repo information for one or more organizations or users.

    org    = organization; an organization or list of organizations
    user   = username; a username or list of usernames (if org is provided,
             user is ignored)
    fields = list of fields to be returned; names must be the same as
             returned by the GitHub API (see list_fields()).
             Dot notation for embedded elements is supported. For example,
             pass a field named 'license.name' to get the 'name' element of
             the 'license' entry for each repo.
             These special cases are also supported:
             fields=['*'] -------> return all fields returned by GitHub API
             fields=['nourls'] -> return all non-URL fields (not *_url or url)
             fields=['urls'] ----> return all URL fields (*_url and url)

    Returns a list of dictionary objects, one per repo.
    """
    repolist = [] # the list of repos that will be returned

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
def reposget(*, org=None, user=None, fields=None):
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
        endpoint = '/orgs/' + org + '/repos'
    else:
        endpoint = '/users/' + user + '/repos'

    # custom header to retrieve license info while License API is in preview
    headers = {'Accept': 'application/vnd.github.drax-preview+json'}

    return github_data(endpoint=endpoint, entity='repo', fields=fields,
                       headers=headers)

#------------------------------------------------------------------------------
@cli.command(help='Get team information for an organization')
@click.option('-o', '--org', default='',
              help='GitHub organization', metavar='<str>')
@click.option('-a', '--authuser', default='',
              help='authentication username', metavar='<str>')
@click.option('-s', '--source', default='p',
              help='data source - a/API, c/cache, or p/prompt', metavar='<str>')
@click.option('-n', '--filename', default='',
              help='output filename (.CSV or .JSON)', metavar='<str>')
@click.option('-f', '--fields', default='',
              help='fields to include', metavar='<str>')
@click.option('-d', '--display', is_flag=True, default=True,
              help="Don't display retrieved data")
@click.option('-v', '--verbose', is_flag=True, default=False,
              help="Display verbose status info")
@click.option('-l', '--listfields', is_flag=True,
              help='list available fields and exit.')
def teams(org, authuser, source, filename, fields, display, verbose, listfields):
    """get team information for an organization.
    """
    if listfields:
        list_fields('team')
        return

    if not org:
        click.echo('ERROR: must specify an org')
        return

    if not filename_valid(filename):
        return

    _settings.display_data = display
    _settings.verbose = verbose
    # for source option, store the 1st character, lower-case
    source = source if source else 'p'
    _settings.datasource = source.lower()[0]

    start_time = default_timer()
    auth_config({'username': authuser})
    fldnames = fields.split('/') if fields else None
    teamlist = github_data(
        endpoint='/orgs/' + org + '/teams', entity='team',
        fields=fldnames, constants={"org": org}, headers={})
    sorted_data = sorted(teamlist, key=data_sort) # sort the data
    data_display(sorted_data)
    data_write(filename, sorted_data)
    unknown_fields() # list unknown field names (if any)
    elapsed_time(start_time)

#-------------------------------------------------------------------------------
def timestamp(filename=None):
    """Return timestamp as a string.

    filename = optional file, if passed then timestamp is returned for the file

    Otherwise, returns current timestamp.
    <internal>
    """
    if filename:
        unixtime = os.path.getmtime(filename)
        return time.strftime('%m/%d/%Y %H:%M:%S', time.localtime(unixtime))
    else:
        return time.strftime('%m/%d/%Y %H:%M:%S', time.localtime(time.time()))

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
def unknown_fields():
    """List unknown field names encountered in this session.
    """
    try:
        if _settings.unknownfieldname:
            click.echo('Unknown field name: ' + _settings.unknownfieldname)
    except AttributeError:
        # no unknown fields have been logged
        pass

#-------------------------------------------------------------------------------
def wildcard_fields():
    """Display wildcard field options.
    """
    click.echo(click.style('       specify fields -->  --fields=',
                           fg='white'), nl=False)
    click.echo(click.style('fld1/fld2/etc', fg='cyan'))
    click.echo(click.style('           ALL fields -->  --fields=',
                           fg='white'), nl=False)
    click.echo(click.style('*', fg='cyan'))
    click.echo(click.style('              No URLs -->  --fields=',
                           fg='white'), nl=False)
    click.echo(click.style('nourls', fg='cyan'))
    click.echo(click.style('            Only URLs -->  --fields=',
                           fg='white'), nl=False)
    click.echo(click.style('urls', fg='cyan'))
    click.echo(click.style(60*'-', fg='blue'))

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
    auth_config({'username': 'msftgits'})
    ENDPOINT = '/v3/enterprise/stats/all'
    RESPONSE = github_api(endpoint=ENDPOINT, auth=auth_user())
    print(str(RESPONSE))
