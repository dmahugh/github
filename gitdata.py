"""GitHub query CLI.

Entry point:
cli() ----------------> Handle command-line arguments.

access_token() -------> Get GitHub access token from private settings.
auth_config() --------> Configure authentication settings.
auth_status() --------> Display status for GitHub username.
auth_user() ----------> Return credentials for use in GitHub API calls.

collabs() ------------> not implemented

data_display() -------> Display data on console.
data_fields() --------> Get dictionary of values from GitHub API JSON payload.
data_write() ---------> Write output file.

filename_valid() -----> Check passed filename for valid file type.

files() --------------> not implemented

github_api() ---------> Call the GitHub API (wrapper for requests library).
github_data() --------> Consolidate data returned by GitHub API.

inifile_name() -------> Return name of INI file where GitHub tokens are stored.

members() ------------> Main handler for "members" subcommand.
members_listfields() -> List valid field names for members().
membersdata() --------> Get member information for orgs or teams.
membersget() ---------> Get member info for a specified organization.

pagination() ---------> Parse pagination URLs from 'link' HTTP header.

repos() --------------> Main handler for "repos" subcommand.
repos_listfields() ---> List valid field names for repos().
reposdata() ----------> Get repo information for organizations or users.
reposget() -----------> Get repo information for a specified org or user.

teams() --------------> Main handler for "teams" subcommand.
teams_listfields() ---> List valid field names for teams().

timestamp() ----------> Get current timestamp 'YYYY-MM-DD HH:MM:SS''
token_abbr() ---------> Get abbreviated access token (for display purposes).
unknown_fields() -----> List unknown field names encountered this session.

write_csv() ----------> Write list of dictionaries to a CSV file.
write_json() ---------> Write list of dictionaries to a JSON file.
"""
import collections
import configparser
import csv
import datetime
import json
import os
import time

import click
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
Get repo/member/team/file/collaborator data from GitHub REST API
----------------------------------------------------------------
subcommand help: gitdata <subcommand> -h"""
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

    # logging settings used by log_*() functions
    verbose = False # default = messages displayed to console
    logfile = None # default = messages not logged to a file

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
    if _settings.username:
        return (_settings.username, _settings.accesstoken)

    return None

#------------------------------------------------------------------------------
@cli.command(help='not implemented yet')
def collabs():
    """NOT IMPLEMENTED
    """
    click.echo('NOT IMPLEMENTED: collabs()')

#-------------------------------------------------------------------------------
def data_fields(*, entity=None, jsondata=None, fields=None, defaults=None):
    """Get dictionary of desired values from GitHub API JSON payload.

    entity   = entity type ('repo', 'member')
    jsondata = a JSON payload returned by the GitHub API
    fields   = list of names of fields (entries) to include from the JSON data,
               or one of these shorthand values:
               '*' -------> return all fields returned by GitHub API
               'nourls' --> return all non-URL fields (not *_url or url)
               'urls' ----> return all URL fields (*_url and url)
    defaults = dictionary of fieldnames/values to include in dictionary

    Returns a dictionary of fieldnames/values.
    """
    if not fields:
        # if no fields specified, use default field list
        if entity == 'member':
            fields = ['login', 'id', 'type', 'site_admin']
        elif entity == 'repo':
            fields = ['owner.login', 'name']
        elif entity == 'team':
            fields = ['name', 'id', 'privacy', 'permission']
        else:
            fields = ['name']

    values = collections.OrderedDict()

    if defaults:
        for fldname in defaults:
            values[fldname] = defaults[fldname]

    if fields[0] in ['*', 'urls', 'nourls']:
        # special cases to return all fields or all url/non-url fields
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
            if '.' in fldname:
                # special case - embedded field within a JSON object
                try:
                    values[fldname.replace('.', '_')] = \
                        jsondata[fldname.split('.')[0]][fldname.split('.')[1]]
                except (TypeError, KeyError):
                    # change '.' to '_' because can't have '.' in an identifier
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
def data_display(view_options=None, datasource=None):
    """Display data on console.

    view_options = string containing 'd' to display data
    datasource   = list of dictionaries
    """
    if not view_options:
        return

    if not 'd' in view_options.lower():
        return

    for data_item in datasource:
        values = [str(value) for _, value in data_item.items()]
        click.echo(click.style(','.join(values), fg='cyan'))

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
@cli.command(help='not implemented yet')
def files():
    """NOT IMPLEMENTED
    """
    click.echo('NOT IMPLEMENTED: files()')

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
def github_api(*, endpoint=None, auth=None, headers=None, view_options=None):
    """Call the GitHub API.

    endpoint     = the HTTP endpoint to call
    auth         = optional tuple for authentication
    headers      = optional dictionary of HTTP headers to pass
    view_options = optional string containing 'a' (API calls), 'h' (HTTP status
                   codes), 'r' (rate-limit status), or 'd' (data).

    Returns a tuple containing the response object and the session object.

    NOTE: sends the Accept header to use version V3 of the GitHub API. This can
    be explicitly overridden by passing a different Accept header if desired.
    """
    if not endpoint:
        click.echo('ERROR: github_api() called with no endpoint')
        return (None, None)

    if view_options and 'a' in view_options.lower():
        click.echo('  Endpoint: ', nl=False)
        click.echo(click.style(endpoint, fg='white'))

    # set auth to empty tuple if not used
    auth = auth if auth else ()

    # add the V3 Accept header to the dictionary
    headers = {} if not headers else headers
    headers_dict = {**{"Accept": "application/vnd.github.v3+json"}, **headers}

    # make the API call
    sess = requests.session()
    sess.auth = auth
    response = sess.get(endpoint, headers=headers_dict)

    if view_options and 'a' in view_options.lower():
        click.echo(click.style(12*' ' +  str(sess), fg='cyan'))

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

    if view_options and 'r' in view_options.lower():
        # display rate-limite status
        if auth_user():
            username = '(user = ' + auth_user()[0] + ')'
        else:
            username = '(non-authenticated)'
        click.echo('Rate Limit: ' + str(_settings.last_ratelimit) + ' - ' + \
              str(_settings.last_ratelimit - _settings.last_remaining) +\
              ' used', nl=False)
        click.echo(click.style(', ' + str(_settings.last_remaining) +
                               ' remaining ' + username, fg='cyan'))

    return (response, sess)

#-------------------------------------------------------------------------------
def github_data(*, endpoint=None, entity=None, fields=None, defaults=None,
                headers=None, view_options=None):
    """Get data from GitHub API.
    endpoint     = HTTP endpoint for GitHub API call
    entity       = entity type ('repo', 'member')
    fields       = list of fields to be returned
    defaults     = dictionary of fieldnames/values to include in dictionaries
    headers      = HTTP headers to be included with API call
    view_options = optional string containing 'a' (API calls), 'h' (HTTP status
                   codes), 'r' (rate-limit status), or 'd' (data).

    Returns a list of dictionaries containing the specified fields.
    Returns a complete data set - if this endpoint does pagination, all pages
    are retrieved and aggregated.
    """
    headers = {} if not headers else headers

    retval = [] # the list to be returned
    totpages = 0

    while True:

        response, sess = github_api(endpoint=endpoint, auth=auth_user(),
                                    view_options=view_options, headers=headers)

        if view_options and 'h' in view_options.lower():
            click.echo('    Status: ' + str(response), nl=False)
            click.echo(click.style(', ' + str(len(response.text)) + ' bytes returned', fg='cyan'))

        if response.ok:
            totpages += 1
            thispage = json.loads(response.text)
            for json_item in thispage:
                retval.append(data_fields(entity=entity, jsondata=json_item,
                                          fields=fields, defaults=defaults))

        pagelinks = pagination(response)
        endpoint = pagelinks['nextURL']
        if not endpoint:
            break # no more results to process

    return retval

#-------------------------------------------------------------------------------
def inifile_name():
    """Return full name of INI file where GitHub tokens are stored.
    Note that this file is stored in a 'private' subfolder under the location of
    the gitinfo module.
    """
    return os.path.join(os.path.dirname(os.path.realpath(__file__)),
                        '../_private/github_users.ini')

#------------------------------------------------------------------------------
@cli.command(help='Get member information by org or team ID.')
@click.option('-o', '--org', default='',
              help='organizations', metavar='org1/org2/etc')
@click.option('-t', '--team', default='',
              help='teams', metavar='teamID1/teamID2/etc')
@click.option('--audit2fa', is_flag=True,
              help='include only 2FA-not-enabled members')
@click.option('-a', '--authuser', default='',
              help='authentication username', metavar='')
@click.option('-v', '--view', default='',
              help='D=data, A=API calls, H=HTTP status codes, ' +
              'R=rate-limit status, *=ALL', metavar='')
@click.option('-n', '--filename', default='',
              help='output filename (.CSV or .JSON)', metavar='')
@click.option('-f', '--fields', default='',
              help='fields to include', metavar='<fld1/fld2/etc>')
@click.option('-l', '--fieldlist', is_flag=True,
              help='list available GitHub fields')
def members(org, team, audit2fa, authuser, view, filename, fields, fieldlist):
    """Get member info for an organization or team.
    """
    if fieldlist:
        members_listfields()
        return

    if not org and not team:
        click.echo('ERROR: must specify an org or team ID')
        return

    if not filename_valid(filename=filename):
        return

    view = 'd' if not view else view
    view = 'dahr' if view == '*' else view

    auth_config({'username': authuser})
    fldnames = fields.split('/') if fields else None
    memberlist = membersdata(org=org, team=team, audit2fa=audit2fa,
                             fields=fldnames, view_options=view)
    data_display(view, memberlist)
    data_write(filename, memberlist)
    unknown_fields() # list unknown field names (if any)

#------------------------------------------------------------------------------
def members_listfields():
    """List valid field names for members().
    """
    click.echo(click.style('\n     specified fields -->  --fields=',
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
    click.echo(click.style('id                  avatar_url          ' +
                           'html_url', fg='cyan'))
    click.echo(click.style('login               events_url          ' +
                           'organizations_url', fg='cyan'))
    click.echo(click.style('site_admin          followers_url       ' +
                           'received_events_url', fg='cyan'))
    click.echo(click.style('type                following_url       ' +
                           'repos_url', fg='cyan'))
    click.echo(click.style('url                 gists_url           ' +
                           'starred_url', fg='cyan'))
    click.echo(click.style('                    gravatar_id         ' +
                           'subscriptions_url', fg='cyan'))

#-------------------------------------------------------------------------------
def membersdata(*, org=None, team=None, fields=None, audit2fa=False,
                view_options=None):
    """Get members for one or more teams or organizations.

    org = a /-delimited list of organizations
    team = a /-delimited list of teams; if provided, org is ignored
    fields = list of field names to be returned; names must be the same as
             returned by the GitHub API (see members_listfields() for the list).
    audit2fa = whether to only return members with 2FA disabled. You must be
               authenticated via auth_config() as an admin of the org(s) to use
               this option.
    view_options = optional string containing 'a' (API calls), 'h' (HTTP status
                   codes), 'r' (rate-limit status), or 'd' (data).

    Returns a list of dictionary objects, one per member.
    """
    memberlist = [] # the list of members that will be returned

    if team:
        # get members by team
        for teamid in team.split('/'):
            memberlist.extend(membersget(team=teamid, fields=fields,
                                         view_options=view_options))
    else:
        # get members by organization
        for orgid in org.split('/'):
            memberlist.extend( \
                membersget(org=orgid, fields=fields, audit2fa=audit2fa,
                           view_options=view_options))

    return memberlist

#------------------------------------------------------------------------------
def membersget(*, org=None, team=None, fields=None, audit2fa=False,
               view_options=None):
    """Get member info for a specified organization. Called by members() to
    aggregate member info for multiple organizations.

    org = organization ID (ignored if a team is specified)
    team = team ID
    fields = list of fields to be returned
    audit2fa = whether to only return members with 2FA disabled. This option
               is only available when retrieving members by organization.
               Note: for audit2fa=True, you must be authenticated via
               auth_config() as an admin of the org(s).
    view_options = optional string containing 'a' (API calls), 'h' (HTTP status
                   codes), 'r' (rate-limit status), or 'd' (data).

    Returns a list of dictionaries containing the specified fields.
    <internal>
    """
    if team:
        endpoint = 'https://api.github.com/teams/' + team + '/members'
    else:
        endpoint = 'https://api.github.com/orgs/' + org + '/members' + \
            ('?filter=2fa_disabled' if audit2fa else '')

    return github_data(endpoint=endpoint, entity='member', fields=fields,
                       defaults={"org": org}, headers={},
                       view_options=view_options)

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

#------------------------------------------------------------------------------
@cli.command(help='Get repo information by org or user/owner.')
@click.option('-o', '--org', default='',
              help='GitHub organization', metavar='')
@click.option('-u', '--user', default='',
              help='GitHub user', metavar='')
@click.option('-a', '--authuser', default='',
              help='authentication username', metavar='')
@click.option('-v', '--view', default='',
              help='D=data, A=API calls, H=HTTP status codes, ' +
              'R=rate-limit status, *=ALL', metavar='')
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

    if not filename_valid(filename):
        return

    view = 'd' if not view else view
    view = 'dahr' if view == '*' else view

    auth_config({'username': authuser})
    fldnames = fields.split('/') if fields else None
    repolist = reposdata(org=org, user=user, fields=fldnames, view_options=view)
    data_display(view, repolist)
    data_write(filename, repolist)
    unknown_fields() # list unknown field names (if any)

#-------------------------------------------------------------------------------
def reposdata(*, org=None, user=None, fields=None, view_options=None):
    """Get repo information for one or more organizations or users.

    org    = organization; an organization or list of organizations
    user   = username; a username or list of usernames (if org is provided,
             user is ignored)
    fields = list of fields to be returned; names must be the same as
             returned by the GitHub API (see repos_listfields() for the list).
             Dot notation for embedded elements is supported. For example,
             pass a field named 'license.name' to get the 'name' element of
             the 'license' entry for each repo.
             These special cases are also supported:
             fields=['*'] -------> return all fields returned by GitHub API
             fields=['nourls'] -> return all non-URL fields (not *_url or url)
             fields=['urls'] ----> return all URL fields (*_url and url)
    view_options = optional string containing 'a' (API calls), 'h' (HTTP status
                   codes), 'r' (rate-limit status), or 'd' (data).

    Returns a list of dictionary objects, one per repo.
    """
    repolist = [] # the list of repos that will be returned

    if org:
        # get repos by organization
        if isinstance(org, str):
            # one organization
            repolist.extend(reposget(org=org, fields=fields,
                                     view_options=view_options))
        else:
            # list of organizations
            for orgid in org:
                repolist.extend(reposget(org=orgid, fields=fields,
                                         view_options=view_options))
    else:
        # get repos by user
        if isinstance(user, str):
            # one user
            repolist.extend(reposget(user=user, fields=fields,
                                     view_options=view_options))
        else:
            # list of users
            for userid in user:
                repolist.extend(reposget(user=userid, fields=fields,
                                         view_options=view_options))

    return repolist

#-------------------------------------------------------------------------------
def reposget(*, org=None, user=None, fields=None, view_options=None):
    """Get repo information for a specified org or user. Called by repos() to
    aggregate repo information for multiple orgs or users.

    org = organization name
    user = username (ignored if org is provided)
    fields = list of fields to be returned
    view_options = optional string containing 'a' (API calls), 'h' (HTTP status
                   codes), 'r' (rate-limit status), or 'd' (data).

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

    # custom header to retrieve license info while License API is in preview
    headers = {'Accept': 'application/vnd.github.drax-preview+json'}

    return github_data(endpoint=endpoint, entity='repo', fields=fields,
                       headers=headers, view_options=view_options)

#------------------------------------------------------------------------------
def repos_listfields():
    """List valid field names for repos().
    """
    click.echo(click.style('\n     specified fields -->  --fields=',
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

#------------------------------------------------------------------------------
@cli.command(help='Get team information for an organization.')
@click.option('-o', '--org', default='',
              help='GitHub organization', metavar='')
@click.option('-a', '--authuser', default='',
              help='authentication username', metavar='')
@click.option('-v', '--view', default='',
              help='D=data, A=API calls, H=HTTP status codes, ' +
              'R=rate-limit status, *=ALL', metavar='')
@click.option('-n', '--filename', default='',
              help='output filename (.CSV or .JSON)', metavar='')
@click.option('-f', '--fields', default='',
              help='fields to include', metavar='<fld1/fld2/etc>')
@click.option('-l', '--fieldlist', is_flag=True,
              help='list available GitHub fields')
def teams(org, authuser, view, filename, fields, fieldlist):
    """get team information for an organization.
    """
    if fieldlist:
        teams_listfields()
        return

    if not org:
        click.echo('ERROR: must specify an org')
        return

    if not filename_valid(filename):
        return

    view = 'd' if not view else view
    view = 'dahr' if view == '*' else view

    auth_config({'username': authuser})
    fldnames = fields.split('/') if fields else None
    teamlist = github_data(
        endpoint='https://api.github.com/orgs/' + org + '/teams', entity='team',
        fields=fldnames, defaults={"org": org}, headers={},
        view_options=view)

    data_display(view, teamlist)
    data_write(filename, teamlist)
    unknown_fields() # list unknown field names (if any)

#-------------------------------------------------------------------------------
def teams_listfields():
    """List valid field names for teams().
    """
    click.echo(click.style('\n     specified fields -->  --fields=',
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
    click.echo(click.style('description', fg='cyan'))
    click.echo(click.style('id', fg='cyan'))
    click.echo(click.style('members_url', fg='cyan'))
    click.echo(click.style('name', fg='cyan'))
    click.echo(click.style('permission', fg='cyan'))
    click.echo(click.style('privacy', fg='cyan'))
    click.echo(click.style('repositories_url', fg='cyan'))
    click.echo(click.style('slug', fg='cyan'))
    click.echo(click.style('url', fg='cyan'))

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
    ENDPOINT = 'https://api.github.com/api/v3/enterprise/stats/all'
    RESPONSE, _ = github_api(endpoint=ENDPOINT, auth=auth_user(), view_options='adhr')
    print(str(RESPONSE))
