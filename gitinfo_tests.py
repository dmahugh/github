"""Test suite for gitinfo.py
"""
import gitinfo as gi

#-------------------------------------------------------------------------------
def test_auth_user():
    """Simple test for auth_user() function.
    """
    print(gi.auth_user())

#-------------------------------------------------------------------------------
def test_collaborators():
    """Simple test for collaborators() function.
    """
    collabtest = gi.collaborators(owner='microsoft', repo='galaxyexplorer')
    for collab in collabtest:
        print(collab)

#-------------------------------------------------------------------------------
def test_members():
    """Simple test for members() function.
    """
    membertest = gi.members(org=['bitstadium', 'ms-iot'], audit2fa=True)
    for member in membertest:
        print(member)
    print('total members returned:', len(membertest))

#-------------------------------------------------------------------------------
def test_pagination():
    """Simple test for pagination() function.
    """
    testlinks = "<https://api.github.com/organizations/6154722/" + \
        "repos?page=2>; rel=\"next\", <https://api.github.com/" + \
        "organizations/6154722/repos?page=18>; rel=\"last\""
    print(gi.pagination(testlinks))

#-------------------------------------------------------------------------------
def test_readme_content():
    """Simple test for readme_content() function.
    """
    owner = 'dmahugh'
    repo = 'gitinfo'
    readme = gi.readme_content(owner=owner, repo=repo)
    print(readme)

#-------------------------------------------------------------------------------
def test_readme_tags():
    """Simple test for readme_tags() function.
    """
    owner = 'dmahugh'
    repo = 'gitinfo'
    taglist = gi.readme_tags(owner=owner, repo=repo)
    print(taglist)

#-------------------------------------------------------------------------------
def test_remove_github_urls():
    """Simple test for remove_github_urls() function.
    """
    testdict = {
        "avatar_url": "https://avatars.githubusercontent.com/u/54385?v=3",
        "events_url": "https://api.github.com/users/halter73/events{/privacy}",
        "followers_url": "https://api.github.com/users/halter73/followers",
        "following_url": "https://api.github.com/users/halter73/following{/other_user}",
        "gists_url": "https://api.github.com/users/halter73/gists{/gist_id}",
        "gravatar_id": "",
        "html_url": "https://github.com/halter73",
        "id": 54385,
        "login": "halter73",
        "org": "signalr",
        "organizations_url": "https://api.github.com/users/halter73/orgs",
        "permissions": {
            "admin": False,
            "pull": True,
            "push": True
        },
        "received_events_url": "https://api.github.com/users/halter73/received_events",
        "repo": "bower-signalr",
        "repos_url": "https://api.github.com/users/halter73/repos",
        "site_admin": False,
        "starred_url": "https://api.github.com/users/halter73/starred{/owner}{/repo}",
        "subscriptions_url": "https://api.github.com/users/halter73/subscriptions",
        "type": "User",
        "url": "https://api.github.com/users/halter73"
    }

    minimized = gi.remove_github_urls(testdict)

    print('>>> before minimizing:', str(testdict))
    print('-'*60)
    print('>>> after minimizing:', str(minimized))

#-------------------------------------------------------------------------------
def test_repo_admins():
    """Simple test for repo_admins() function.
    """
    retval = gi.repo_admins(org='microsoft', repo='edgediagnosticsadapter')
    print(retval)

#-------------------------------------------------------------------------------
def test_repos():
    """Simple test for repos() function.
    """
    oct_repos = gi.repos(user=['octocat'], fields= \
        ['full_name', 'license.name', 'license', 'permissions.admin'])
    for repo in oct_repos:
        print(repo)

#-------------------------------------------------------------------------------
def test_repoteams():
    """Simple test for repoteams() function.
    """
    testteams = gi.repoteams(org='ms-iot', repo=['serial-wiring', 'remote-sensor'])
    for team in testteams:
        print(team)

#-------------------------------------------------------------------------------
def test_teammembers():
    """Simple test for teammembers() function.
    """
    memberlist = gi.teammembers(teamid=652356)
    for member in memberlist:
        print('>>>', member)

#-------------------------------------------------------------------------------
def test_teams():
    """Simple test for teams() function.
    """
    teamtest = gi.teams(org=['bitstadium', 'ms-iot'])
    for team in teamtest:
        print(team)
    print('total teams returned:', len(teamtest))

# if running standalone, run tests ---------------------------------------------
if __name__ == "__main__":

    gi.log_config({'verbose': True, 'logfile': 'gitinfo.log'})
    gi.auth_config({'username': 'msftgits'})
    gi.session_start('inline tests')

    #test_auth_user()
    #test_collaborators()
    #test_members()
    #test_pagination()
    #test_readme_content()
    #test_readme_tags()
    #test_remove_github_urls()
    #test_repo_admins()
    test_repos()
    #test_repoteams()
    #test_teammembers()
    #test_teams()

    gi.session_end()
