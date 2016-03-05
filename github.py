"""GitHub helper functions.

github_link -> Extract link URL from HTTP header returned by GitHub API.
"""

#------------------------------------------------------------------------------
def github_link(link_header, linktype='next'):
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
    links = "<https://api.github.com/organizations/6154722/repos?page=2>; rel=\"next\", <https://api.github.com/organizations/6154722/repos?page=18>; rel=\"last\""

    for reltype in ['first', 'prev', 'next', 'last']:
        URL = github_link(links, reltype)
        print(reltype, URL)
