"""Helper functions for retrieving data via the GitHub API.

basic_auth() --> Credentials for basic authentication.
get_members() -> Get members of an organization.
get_repos() ---> Get all public repos for an organization or user.
link_url() ----> Extract link URL from HTTP header returned by GitHub API.
write_csv() ---> Write a list of namedtuples to a CSV file.
"""
import collections
import csv
import json
import os
import requests

#------------------------------------------------------------------------------
def basic_auth():
    """Credentials for basic authentication.

    Returns the tuple used for API calls. GitHub username and PAT are stored
    in environment variables GitHubUser and GitHubPAT.
    """
    return (os.getenv('GitHubUser'), os.getenv('GitHubPAT'))

#-------------------------------------------------------------------------------
def get_members(org=None, fields=None, verbose=False):
    """Get members for an organization.

    org = organization
    fields = list of field names to be returned; names must be the same as
             returned by the GitHub API
    verbose = flag for whether to display status information to console

    Returns a list of namedtuple objects, one per member.
    """
    if not fields:
        # default fields to be returned if none specified
        fields = ['login', 'id', 'type', 'site_admin']

    endpoint = 'https://api.github.com/orgs/' + org + '/members'

    if verbose:
        print('get_members() ->', 'API endpoint:', endpoint)

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

        endpoint = link_url(response, 'next') # get URL for next page of results
        if verbose:
            print('get_members() ->', 'next page:', endpoint)
        if not endpoint:
            break # there are no more results to process

    if verbose:
        print('get_members() -> ', 'pages processed:', totpages)
        print('get_members() -> ', 'members returned:', len(memberlist))
        for header in ['X-RateLimit-Limit', 'X-RateLimit-Remaining']:
            print('get_members() -> ', header + ':', response.headers[header])

    return memberlist

#-------------------------------------------------------------------------------
def get_repos(org=None, user=None, fields=None, verbose=False):
    """Get all public repos for an organization or user.

    org = organization
    user = username (ignored if an organization is provided)
    fields = list of field names to be returned; names must be the same as
             returned by the GitHub API
    verbose = flag for whether to display status information to console

    Returns a list of namedtuple objects, one per repo.
    """
    if not fields:
        # default fields to be returned if none specified
        fields = ['full_name', 'watchers', 'forks', 'open_issues']

    if org:
        endpoint = 'https://api.github.com/orgs/' + org + '/repos'
    else:
        endpoint = 'https://api.github.com/users/' + user + '/repos'

    if verbose:
        print('get_repos() ->', 'API endpoint:', endpoint)

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

        endpoint = link_url(response, 'next') # get URL for next page of results
        if verbose:
            print('get_repos() ->', 'next page:', endpoint)
        if not endpoint:
            break # there are no more results to process

    if verbose:
        print('get_repos() ->', 'pages processed:', totpages)
        print('get_repos() ->', 'repos returned:', len(repolist))
        for header in ['X-RateLimit-Limit', 'X-RateLimit-Remaining']:
            print('get_repos() ->', header + ':', response.headers[header])

    return repolist

#------------------------------------------------------------------------------
def link_url(link_header, linktype='next'):
    """Extract link URL from the 'link' HTTP header returned by GitHub API.

    1st parameter = the 'link' HTTP header passed as a string, or a
                    response object returned by the requests module
    linktype = the desired link type (default = 'next')
    """
    if isinstance(link_header, str):
        link_string = link_header
    else:
        try:
            link_string = link_header.headers['Link']
        except KeyError:
            return None # there is no Link HTTP header, nothing to do

    retval = None # default return value if linktype not found
    links = link_string.split(',') # each of these is '<url>; rel="type"'
    for link in links:
        if '"' + linktype + '"' in link:
            retval = link.split(';')[0].strip()[1:-1]
    return retval

#-------------------------------------------------------------------------------
def write_csv(listobj, filename, verbose=False):
    """Write a list of namedtuples to a CSV file.

    1st parameter = the list
    2nd parameter = name of CSV file to be written
    verbose = flag for whether to display status information to console
    """
    csvfile = open(filename, 'w', newline='')
    csvwriter = csv.writer(csvfile, dialect='excel')
    header_row = listobj[0]._fields
    csvwriter.writerow(header_row)

    if verbose:
        print('write_csv() ->', 'filename:', filename)
        print('write_csv() ->', 'columns:', header_row)

    for row in listobj:
        values = []
        for fldname in header_row:
            values.append(getattr(row, fldname))
        csvwriter.writerow(values)
    csvfile.close()

    if verbose:
        print('write_csv() ->', 'total rows:', len(listobj))

# if running standalone, run a few examples/tests ------------------------------
if __name__ == "__main__":

    print('-'*40 + '\n' + 'basic_auth() test' + '\n' + '-'*40) #----------------
    print(basic_auth())

    print('-'*40 + '\n' + 'link_url() test' + '\n' + '-'*40) #------------------
    TESTLINKS = "<https://api.github.com/organizations/6154722/" + \
        "repos?page=2>; rel=\"next\", <https://api.github.com/" + \
        "organizations/6154722/repos?page=18>; rel=\"last\""
    for reltype in ['first', 'prev', 'next', 'last']:
        URL = link_url(TESTLINKS, reltype)
        print(reltype, URL)

    print('-'*40 + '\n' + 'get_repos() test' + '\n' + '-'*40) #-----------------
    OCT_REPOS = get_repos(user='octocat',
                         fields=['full_name', 'default_branch'], verbose=True)
    for repo in OCT_REPOS:
        print(repo)
    print('Total repos: ', len(OCT_REPOS))
    write_csv(OCT_REPOS, 'OctocatRepos.csv', verbose=True)

    print('-'*40 + '\n' + 'get_members() test' + '\n' + '-'*40) #-----------------
    AD_MEMBERS = get_members(org='AzureADSamples', verbose=True)
    for member in AD_MEMBERS:
        print(member)
    print('Total members in AzureADSamples org: ', len(AD_MEMBERS))
    write_csv(AD_MEMBERS, 'AzureADSamplesMembers.csv', verbose=True)
