"""GitHub helper functions.

link_url -> Extract link URL from HTTP header returned by GitHub API.
"""
import os

#------------------------------------------------------------------------------
def basic_auth():
    """Credentials for basic authentication.
    
    Returns the tuple used for API calls. GitHub username and PAT are stored
    in environment variables GitHubUser and GitHubPAT.
    """
    return (os.getenv('GitHubUser'), os.getenv('GitHubPAT'))

#------------------------------------------------------------------------------
def link_url(link_header, linktype='next'):
    """Extract link URL from the 'link' HTTP header returned by GitHub API.
    
    1st parameter = the 'link' HTTP header
    linktype = the desired link type (default = 'next')
    """
    retval = None # default return value if linktype not found
    links = link_header.split(',') # each of these is '<url>; rel="type"'
    for link in links:
        if '"' + linktype + '"' in link:
            retval = link.split(';')[0].strip()[1:-1]
    return retval

#------------------------------------------------------------------------------
if __name__ == "__main__":

    print('-'*40 + '\n' + 'basic_auth() test' + '\n' + '-'*40)
    print(basic_auth())

    print('-'*40 + '\n' + 'link_url() test' + '\n' + '-'*40)
    links = "<https://api.github.com/organizations/6154722/repos?page=2>; rel=\"next\", <https://api.github.com/organizations/6154722/repos?page=18>; rel=\"last\""
    for reltype in ['first', 'prev', 'next', 'last']:
        URL = link_url(links, reltype)
        print(reltype, URL)
