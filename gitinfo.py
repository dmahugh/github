"""Helper functions for retrieving data via the GitHub API.

auth() -----------> Return credentials for use in GitHub API calls.
auth_reset() -----> Reset authentication settings to default values.
auth_user() ------> Set GitHub user for subsequent API calls.

memberfields() ---> Get field values for a member/user.
members() --------> Get members of one or more organizations.
membersget() -----> Get member info for a specified organization.

pagination() -----> Parse values from 'link' HTTP header returned by GitHub API.

repofields() -----> Get field values for a repo.
repos() ----------> Get repo information for organization(s) or user(s).
reposget() -------> Get repo information from specified API endpoint.

verbose() --------> Set verbose mode on/off.
verbose_output() -> Display status info in verbose mode.

write_csv() ------> Write a list of namedtuples to a CSV file.
"""
import collections
import csv
import json
import os
import traceback

import requests

#------------------------------------------------------------------------------
class _settings: # pylint: disable=R0903
    """Used for global settings. Should not be accessed directly - e.g.,
    use the verbose() function to change _settings.verbose, or the user()
    function to change _settings.github_username/accesstoken.
    """
    verbose = False # default = verbose mode off
    github_username = None
    github_accesstoken = None

#------------------------------------------------------------------------------
def auth():
    """Credentials for basic authentication.

    Returns the tuple used for API calls. If the GitHub username and PAT have
    not been set, reads them from environment variables GitHubUser/GitHubPAT.
    """
    # Note that "auth() ->" is explcitly added to the verbose_output()
    # calls below because auth() is typically used inline from other
    # functions, so it isn't the caller in the call stack.

    if not _settings.github_username:
        auth_reset()

    username = _settings.github_username
    access_token = _settings.github_accesstoken

    verbose_output('auth() ->', 'username:', username)
    verbose_output('auth() ->',
                   'PAT:', access_token[0:2] + '...' + access_token[-2:])

    return (username, access_token)

#-------------------------------------------------------------------------------
def auth_reset():
    """Reset authorization settings to default values.

    Sets username and acccess_token to the values stored in the  GitHubUser and
    GitHubPAT environment variables.
    """
    _settings.github_username = os.getenv('GitHubUser')
    _settings.github_accesstoken = os.getenv('GitHubPAT')

#-------------------------------------------------------------------------------
def auth_user(username=None):
    """Set GitHub user for subsequent API calls.

    username = a GitHub username stored in github_users.json in the
               /private subfolder. If omitted, the GitHub user settings are
               initialized from the GitHubUser/GitHubPAT environment variables.
    """
    if username:
        with open('private/github_users.json', 'r') as jsonfile:
            github_users = json.load(jsonfile)
            _settings.github_username = username
            _settings.github_accesstoken = github_users[username]
    else:
        # no username specified, so reset to defaults
        auth_reset()

#-------------------------------------------------------------------------------
def memberfields(member_json, fields, org):
    """Get field values for a member/user.

    1st parameter = member's json representation as returned by GitHub API
    2nd parameter = list of names of desired fields
    3rd parameter = organization ID

    Returns a namedtuple containing the desired fields and their values.
    NOTE: in addition to the specified fields, always returns an 'org' field
    to distinguish between organizations in lists returned by members().
    """
    member_tuple = collections.namedtuple('member_tuple', 'org ' + ' '.join(fields))
    values = {}
    values['org'] = org
    for fldname in fields:
        values[fldname] = member_json[fldname]
    return member_tuple(**values)

#-------------------------------------------------------------------------------
def members(org=None, fields=None, audit2fa=False):
    """Get members for one or more organizations.

    org = organization
    fields = list of field names to be returned; names must be the same as
             returned by the GitHub API
    audit2fa = whether to only return members with 2FA disabled. You must be
               authenticated via auth_user() as a member of the org(s) to use
               this option.

    Returns a list of namedtuple objects, one per member.
    """
    if not fields:
        # default fields to be returned if none specified
        fields = ['login', 'id', 'type', 'site_admin']

    memberlist = [] # the list that will be returned

    if isinstance(org, str):
        # one org ID passed as a string
        memberlist.extend(membersget(org, fields, audit2fa))
    else:
        # list of org IDs passed
        for orgid in org:
            memberlist.extend(membersget(orgid, fields, audit2fa))

    return memberlist

#------------------------------------------------------------------------------
def membersget(org, fields, audit2fa):
    """Get member info for a specified organization.

    1st parameter = organization ID
    2nd parameter = list of fields to be returned
    3rd parameter = whether to only return members with 2FA disabled. You must
                    be authenticated via auth_user() as a member of the org(s)
                    to use this option.

    Returns a list of namedtuples containing the specified fields.
    """
    totpages = 0
    retval = [] # the list to be returned

    suffix = '?filter=2fa_disabled' if audit2fa else ''
    endpoint = 'https://api.github.com/orgs/' + org + '/members' + suffix

    while True:
        response = requests.get(endpoint, auth=auth())
        if response.ok:
            totpages += 1
            thispage = json.loads(response.text)
            for member_json in thispage:
                retval.append(memberfields(member_json, fields, org))
        pagelinks = pagination(response)
        endpoint = pagelinks['nextURL']
        if not endpoint:
            break # there are no more results to process
        verbose_output('processing page {0} of {1}'. \
                       format(pagelinks['nextpage'], pagelinks['lastpage']))

    verbose_output('pages processed:', totpages)
    verbose_output('members returned:', len(retval))
    for header in ['X-RateLimit-Limit', 'X-RateLimit-Remaining']:
        verbose_output(header + ':', response.headers[header])

    return retval

#------------------------------------------------------------------------------
def pagination(link_header):
    """Parse values from the 'link' HTTP header returned by GitHub API.

    1st parameter = the 'link' HTTP header passed as a string, or a
                    response object returned by the requests module

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
        try:
            link_string = link_header.headers['Link']
        except KeyError:
            return retval # no Link HTTP header found, nothing to parse

    links = link_string.split(',') # each of these is '<url>; rel="type"'
    for link in links:
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
    fldnames = [_.replace('.', '_') for _ in fields] # periods to underscores
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
            values[fldname] = repo_json[fldname]
    return repo_tuple(**values)

#-------------------------------------------------------------------------------
def repos(org=None, user=None, fields=None):
    """Get repo information for organization(s) or user(s).

    org = organization; either a string containing a single organization ID, or
          a list of organization IDs to be included
    user = username (ignored if org argument is provided); either a string
           containing a single organization ID, or a list of organization IDs
           to be included
    fields = list of field names to be returned; names must be the same as
             returned by the GitHub API. Embedded elements are also supported:
             for example, pass a field named 'license.name' and it will
             return the 'name' element of the 'license' entry for each repo.
             Namedtuples don't allow embedded periods in identifiers, so in
             this case the column name will be 'license_name'.

    Returns a list of namedtuple objects, one per repo.
    """
    if not fields:
        # default fields to be returned if none specified
        fields = ['full_name', 'watchers', 'forks', 'open_issues']

    repolist = [] # the list that will be returned

    if org:
        # get repos by org
        if isinstance(org, str):
            # one org ID passed as a string
            endpoint = 'https://api.github.com/orgs/' + org + '/repos'
            repolist.extend(reposget(endpoint, fields))
        else:
            # list of org IDs passed
            for orgid in org:
                endpoint = 'https://api.github.com/orgs/' + orgid + '/repos'
                repolist.extend(reposget(endpoint, fields))
    else:
        # get repos by user
        if isinstance(user, str):
            # one user ID passed as a string
            endpoint = 'https://api.github.com/users/' + user + '/repos'
            repolist.extend(reposget(endpoint, fields))
        else:
            # list of user IDs passed
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
        response = requests.get(endpoint, auth=auth(), headers=headers)
        if response.ok:
            totpages += 1
            thispage = json.loads(response.text)
            for repo_json in thispage:
                retval.append(repofields(repo_json, fields))
        pagelinks = pagination(response)
        endpoint = pagelinks['nextURL']
        if not endpoint:
            break # there are no more results to process
        verbose_output('processing page {0} of {1}'. \
                       format(pagelinks['nextpage'], pagelinks['lastpage']))

    verbose_output('pages processed:', totpages)
    verbose_output('repos returned:', len(retval))
    for header in ['X-RateLimit-Limit', 'X-RateLimit-Remaining']:
        verbose_output(header + ':', response.headers[header])

    return retval

#-------------------------------------------------------------------------------
def verbose(*args):
    """Set verbose mode on/off.

    1st parameter = True for verbose mode, False to turn verbose mode off.

    Returns the current verbose mode setting as True/False. To query the
    current setting, call verbose() with no parameters.
    """
    if len(args) == 1:
        _settings.verbose = args[0]
    return _settings.verbose

#-------------------------------------------------------------------------------
def verbose_output(*args):
    """Display status information in verbose mode.

    parameters = message to be displayed if verbose(True) is set.

    NOTE: can pass any number of parameters, which will be displayed as a single
    string delimited by spaces.
    """
    if not _settings.verbose:
        return # verbose mode is off, nothing to do

    # convert all to strings, to allow for non-string parameters
    string_args = [str(_) for _ in args]

    caller = traceback.format_stack()[1].split(',')[2].strip().split()[1]
    print(caller + '() ->', ' '.join(string_args))

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

    verbose_output('filename:', filename)
    verbose_output('columns:', header_row)

    for row in listobj:
        values = []
        for fldname in header_row:
            values.append(getattr(row, fldname))
        csvwriter.writerow(values)
    csvfile.close()

    verbose_output('total rows:', len(listobj))

#===============================================================================
#------------------------------------ TESTS ------------------------------------
#===============================================================================

#-------------------------------------------------------------------------------
def test_auth():
    """Simple test for auth() function.
    """
    print(auth())

#-------------------------------------------------------------------------------
def test_members():
    """Simple test for members() function.
    """
    auth_user('msftgits')
    test_results = members(org=['bitstadium', 'liveservices'])
    for member in test_results:
        print(member)
    print('Total members:', len(test_results))

#-------------------------------------------------------------------------------
def test_repos():
    """Simple test for repos() function. Also tests write_csv().
    """
    oct_repos = repos(user=['octocat', 'dmahugh'],
                      fields=['full_name', 'license.name', 'license'])
    for repo in oct_repos:
        print(repo)
    print('Total repos: ', len(oct_repos))
    write_csv(oct_repos, 'data\OctocatRepos.csv')

#-------------------------------------------------------------------------------
def test_pagination():
    """Simple test for pagination() function.
    """
    testlinks = "<https://api.github.com/organizations/6154722/" + \
        "repos?page=2>; rel=\"next\", <https://api.github.com/" + \
        "organizations/6154722/repos?page=18>; rel=\"last\""
    print(pagination(testlinks))

# if running standalone, run tests ---------------------------------------------
if __name__ == "__main__":

    verbose(True) # turn on verbose mode
    #test_auth()
    test_members()
    #test_repos()
    #test_pagination()
