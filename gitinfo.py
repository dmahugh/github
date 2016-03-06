"""Helper functions for retrieving data via the GitHub API.

basic_auth() -----> Credentials for basic authentication.
get_members() ----> Get members of an organization.
get_repos() ------> Get all public repos for an organization or user.
pagination() -----> Parse values from 'link' HTTP header returned by GitHub API.
write_csv() ------> Write a list of namedtuples to a CSV file.
verbose() --------> Set verbose mode on/off.
verbose_output() -> Display status info in verbose mode.
"""
import collections
import csv
import json
import os
import requests
import traceback

#------------------------------------------------------------------------------
class _verbose:
    """Used for the verbose-mode setting. Should not be accessed directly -
    use the verbose() function to change the setting.
    """
    setting = False # default value

#------------------------------------------------------------------------------
def basic_auth():
    """Credentials for basic authentication.

    Returns the tuple used for API calls. GitHub username and PAT are stored
    in environment variables GitHubUser and GitHubPAT.
    """
    return (os.getenv('GitHubUser'), os.getenv('GitHubPAT'))

#-------------------------------------------------------------------------------
def get_members(org=None, fields=None):
    """Get members for an organization.

    org = organization
    fields = list of field names to be returned; names must be the same as
             returned by the GitHub API

    Returns a list of namedtuple objects, one per member.
    """
    if not fields:
        # default fields to be returned if none specified
        fields = ['login', 'id', 'type', 'site_admin']

    endpoint = 'https://api.github.com/orgs/' + org + '/members'
    verbose_output('API endpoint:', endpoint)

    memberlist = [] # the list that will be returned
    member_tuple = collections.namedtuple('member_tuple', ' '.join(fields))
    totpages = 0

    while True:
        response = requests.get(endpoint, auth=basic_auth())
        if response.ok:
            totpages += 1
            thispage = json.loads(response.text)
            for member_json in thispage:
                values = {}
                for fldname in fields:
                    values[fldname] = member_json[fldname]
                member_nt = member_tuple(**values)
                memberlist.append(member_nt)

        pagelinks = pagination(response)
        endpoint = pagelinks['nextURL']
        if not endpoint:
            break # there are no more results to process
        verbose_output('processing page {0} of {1}'. \
                       format(pagelinks['nextpage'], pagelinks['lastpage']))

    verbose_output('pages processed:', totpages)
    verbose_output('members returned:', len(memberlist))
    for header in ['X-RateLimit-Limit', 'X-RateLimit-Remaining']:
        verbose_output(header + ':', response.headers[header])

    return memberlist

#-------------------------------------------------------------------------------
def get_repos(org=None, user=None, fields=None):
    """Get all public repos for an organization or user.

    org = organization
    user = username (ignored if an organization is provided)
    fields = list of field names to be returned; names must be the same as
             returned by the GitHub API

    Returns a list of namedtuple objects, one per repo.
    """
    if not fields:
        # default fields to be returned if none specified
        fields = ['full_name', 'watchers', 'forks', 'open_issues']

    if org:
        endpoint = 'https://api.github.com/orgs/' + org + '/repos'
    else:
        endpoint = 'https://api.github.com/users/' + user + '/repos'
    verbose_output('API endpoint:', endpoint)

    repolist = [] # the list that will be returned
    repo_tuple = collections.namedtuple('Repo', ' '.join(fields))
    totpages = 0

    while True:
        response = requests.get(endpoint, auth=basic_auth())
        if response.ok:
            totpages += 1
            thispage = json.loads(response.text)
            for repo_json in thispage:
                values = {}
                for fldname in fields:
                    values[fldname] = repo_json[fldname]
                repo_nt = repo_tuple(**values)
                repolist.append(repo_nt)

        pagelinks = pagination(response)
        endpoint = pagelinks['nextURL']
        if not endpoint:
            break # there are no more results to process
        verbose_output('processing page {0} of {1}'. \
                       format(pagelinks['nextpage'], pagelinks['lastpage']))

    verbose_output('pages processed:', totpages)
    verbose_output('repos returned:', len(repolist))
    for header in ['X-RateLimit-Limit', 'X-RateLimit-Remaining']:
        verbose_output(header + ':', response.headers[header])

    return repolist

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

#-------------------------------------------------------------------------------
def verbose(*args):
    """Set verbose mode on/off.
    
    1st parameter = True for verbose mode, False to turn verbose mode off.
    
    Returns the current verbose mode setting as True/False. To query the
    current setting, call verbose() with no parameters.
    """
    if len(args) == 1:
        _verbose.setting = args[0]
    return _verbose.setting

#-------------------------------------------------------------------------------
def verbose_output(*args):
    """Display status information in verbose mode.

    parameters = message to be displayed if verbose(True) is set.

    NOTE: can pass any number of parameters, which will be displayed as a single
    string delimited by spaces.
    """
    if not _verbose.setting:
        return # verbose mode is off, nothing to do

    # convert all to strings, to allow for non-string parameters
    string_args = [str(_) for _ in args]

    caller = traceback.format_stack()[1].split(',')[2].strip().split()[1]
    print(caller + '() ->', ' '.join(string_args))


# if running standalone, run a few examples/tests ------------------------------
if __name__ == "__main__":

    verbose(True) # turn on verbose mode

    print('-'*40 + '\n' + 'basic_auth() test' + '\n' + '-'*40) #----------------
    print(basic_auth())

    print('-'*40 + '\n' + 'pagination() test' + '\n' + '-'*40) #------------------
    TESTLINKS = "<https://api.github.com/organizations/6154722/" + \
        "repos?page=2>; rel=\"next\", <https://api.github.com/" + \
        "organizations/6154722/repos?page=18>; rel=\"last\""
    print(pagination(TESTLINKS))

    print('-'*40 + '\n' + 'get_repos() test' + '\n' + '-'*40) #-----------------
    OCT_REPOS = get_repos(user='octocat',
                          fields=['full_name', 'default_branch'])
    for repo in OCT_REPOS:
        print(repo)
    print('Total repos: ', len(OCT_REPOS))
    write_csv(OCT_REPOS, 'OctocatRepos.csv')

    print('-'*40 + '\n' + 'get_members() test' + '\n' + '-'*40) #-----------------
    AD_MEMBERS = get_members(org='AzureADSamples')
    print('Total members in AzureADSamples org: ', len(AD_MEMBERS))
    write_csv(AD_MEMBERS, 'AzureADSamplesMembers.csv')
