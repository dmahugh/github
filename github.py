"""GitHub helper functions.

basic_auth() -> Credentials for basic authentication.
get_repos() --> Get all public repos for an organization or user.
link_url() ---> Extract link URL from HTTP header returned by GitHub API.
"""
import collections
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
def get_repos(org=None, user=None, verbose=False):
    """Get all public repos for an organization or user.

    org = organization
    user = username (ignored if an organization is provided)
    verbose = flag for whether to display status information to console

    Returns a list of namedtuple objects, one per repo.
    """
    FIELDS = ['full_name', 'watchers', 'forks', 'open_issues', 'default_branch']
    if org:
        endpoint = 'https://api.github.com/orgs/' + org + '/repos'
    else:
        endpoint = 'https://api.github.com/users/' + user + '/repos'

    if verbose:
        print('get_repo() -> ', 'API endpoint:', endpoint)

    repolist = [] # the list that will be returned
    Repo = collections.namedtuple('Repo', ' '.join(FIELDS)) # namedtuple factory
    totpages = 0

    while True:
        response = requests.get(endpoint, auth=basic_auth())
        if response.ok:
            totpages += 1
            thispage = json.loads(response.text)
            for repo_json in thispage:
                repo_nt = Repo(repo_json['full_name'], repo_json['watchers'],
                               repo_json['forks'], repo_json['open_issues'],
                               repo_json['default_branch'])
                repolist.append(repo_nt)

        endpoint = link_url(response, 'next') # get URL for next page of results
        if not endpoint:
            break # there are no more results to process

    if verbose:
        print('get_repo() -> ', 'pages processed:', totpages)
        print('get_repo() -> ', 'repos returned:', len(repolist))
        for header in ['X-RateLimit-Limit', 'X-RateLimit-Remaining']:
            print('get_repo() -> ', header + ':', response.headers[header])

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

# if running standalone, run a few simple tests --------------------------------
if __name__ == "__main__":

    print('-'*40 + '\n' + 'basic_auth() test' + '\n' + '-'*40)
    print(basic_auth())

    print('-'*40 + '\n' + 'link_url() test' + '\n' + '-'*40)
    TESTLINKS = "<https://api.github.com/organizations/6154722/" + \
        "repos?page=2>; rel=\"next\", <https://api.github.com/" + \
        "organizations/6154722/repos?page=18>; rel=\"last\""
    for reltype in ['first', 'prev', 'next', 'last']:
        URL = link_url(TESTLINKS, reltype)
        print(reltype, URL)

    print('-'*40 + '\n' + 'get_repos() test' + '\n' + '-'*40)
    ms_repos = get_repos(user='octocat', verbose=True)
    for repo in ms_repos:
        print(repo)
    print('Total repos: ', len(ms_repos))