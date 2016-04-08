"""Test suite for gitinfo module

NOTE: some of these tests require msftgits GitHub credentials, so they won't
pass on a machine that doesn't have those credentials configured.

Test_auth_user() -----------> Tests for gitinfo.auth_user().
Test_collaborators() -------> Tests for gitinfo.collaborators().
Test_members() -------------> Tests for gitinfo.members().
Test_pagination() ----------> Tests for gitinfo.pagination().
Test_readme_content() ------> Tests for gitinfo.readme_content().
Test_remove_github_urls() --> Tests for gitinfo.remove_github_urls().
Test_repo_admins() ---------> Tests for gitinfo.repo_admins().
Test_repo_tags() -----------> Tests for gitinfo.readme_tags().
Test_repos() ---------------> Tests for gitinfo.repos().
Test_repoteams() -----------> Tests for gitinfo.repoteams().
Test_teammembers() ---------> Tests for gitinfo.teammembers().
Test_teams() ---------------> Tests for gitinfo.teams().
"""
import pytest
# pragma pylint: disable=no-self-use,invalid-name,missing-docstring,redefined-outer-name

import gitinfo as gi

#-------------------------------------------------------------------------------
class Test_auth_user():
    """Tests for gitinfo.auth_user().
    """
    def test_noconfig(self):
        assert gi.auth_user() is None

    def test_msftgits(self):
        gi.auth_config({'username': 'msftgits'})
        authtuple = gi.auth_user()
        assert len(authtuple) == 2
        assert authtuple[0] == 'msftgits'
        assert len(authtuple[1]) == 40

#-------------------------------------------------------------------------------
class Test_collaborators():
    """Tests for gitinfo.collaborators().
    """
    def test_galaxyexplorer(self):
        gi.auth_config({'username': 'msftgits'})
        collabtest = gi.collaborators(owner='microsoft', repo='galaxyexplorer')
        logins = [collab.login for collab in collabtest]
        assert 'msftclas' in logins
        assert 'msftgits' in logins

#-------------------------------------------------------------------------------
class Test_members():
    """Tests for gitinfo.members().
    """
    def test_odata(self, linkheader):
        gi.auth_config({'username': 'msftgits'})
        membertest = gi.members(org=['odata'], audit2fa=True)
        logins = [member.login.lower() for member in membertest]
        assert 'odatabot' in logins

#-------------------------------------------------------------------------------
class Test_pagination():
    """Tests for gitinfo.pagination().
    """
    def test_first(self, linkheader):
        linkdict = gi.pagination(linkheader)
        assert linkdict['firstpage'] == 0
        assert linkdict['firstURL'] is None

    def test_last(self, linkheader):
        linkdict = gi.pagination(linkheader)
        assert linkdict['lastpage'] == '18'
        assert linkdict['lastURL'] == 'https://api.github.com/organizations/6154722/repos?page=18'

    def test_next(self, linkheader):
        linkdict = gi.pagination(linkheader)
        assert linkdict['nextpage'] == '2'
        assert linkdict['nextURL'] == 'https://api.github.com/organizations/6154722/repos?page=2'

    def test_prev(self, linkheader):
        linkdict = gi.pagination(linkheader)
        assert linkdict['prevpage'] == 0
        assert linkdict['prevURL'] is None

@pytest.fixture
def linkheader():
    """Test data for testing gitinfo.pagination().
    """
    return "<https://api.github.com/organizations/6154722/" + \
        "repos?page=2>; rel=\"next\", <https://api.github.com/" + \
        "organizations/6154722/repos?page=18>; rel=\"last\""

#-------------------------------------------------------------------------------
class Test_readme_content():
    """Tests for gitinfo.readme_content().
    """
    def test_gitinforeadme(self):
        readme = gi.readme_content(owner='dmahugh', repo='gitinfo')
        assert b'[gitinfo](images/gitinfo.png)' in readme

#-------------------------------------------------------------------------------
class Test_remove_github_urls():
    """Tests for gitinfo.remove_github_urls().
    """
    def test_typical(self):
        testdict = {
            "avatar_url": "https://avatars.githubusercontent.com/u/12345?v=3",
            "events_url": "https://api.github.com/users/username/events{/privacy}",
            "followers_url": "https://api.github.com/users/username/followers",
            "following_url": "https://api.github.com/users/username/following{/other_user}",
            "gists_url": "https://api.github.com/users/username/gists{/gist_id}",
            "gravatar_id": "",
            "html_url": "https://github.com/username",
            "id": 12345,
            "login": "username",
            "org": "orgname",
            "organizations_url": "https://api.github.com/users/username/orgs",
            "permissions": {
                "admin": False,
                "pull": True,
                "push": True
            },
            "received_events_url": "https://api.github.com/users/username/received_events",
            "repo": "reponame",
            "repos_url": "https://api.github.com/users/username/repos",
            "site_admin": False,
            "starred_url": "https://api.github.com/users/username/starred{/owner}{/repo}",
            "subscriptions_url": "https://api.github.com/users/username/subscriptions",
            "type": "User",
            "url": "https://api.github.com/users/username"
        }
        minimized = gi.remove_github_urls(testdict)
        assert minimized == {
            "gravatar_id": "",
            "id": 12345,
            "login": "username",
            "org": "orgname",
            "permissions": {
                "admin": False,
                "pull": True,
                "push": True
            },
            "repo": "reponame",
            "site_admin": False,
            "type": "User"
        }

    def test_emptydict(self):
        assert gi.remove_github_urls({}) == {}

    def test_None(self):
        assert gi.remove_github_urls(None) == {}

#-------------------------------------------------------------------------------
class Test_repo_admins():
    """Tests for gitinfo.repo_admins().
    """
    def test_dclrepo(self):
        gi.auth_config({'username': 'msftgits'})
        testadmins = gi.repo_admins(org='microsoft', repo='dotnet-client-library')
        logins = [admin['login'].lower() for admin in testadmins]
        assert 'kschaab' in logins

#-------------------------------------------------------------------------------
class Test_repo_tags():
    """Tests for gitinfo.readme_tags().
    """
    def test_gitinforepo(self):
        taglist = gi.repo_tags(owner='dmahugh', repo='gitinfo')
        assert 'python' in taglist
        assert 'github' in taglist
        assert 'rest' in taglist

#-------------------------------------------------------------------------------
class Test_repos():
    """Tests for gitinfo.repos().
    """
    def test_octocatrepo(self):
        oct_repos = gi.repos(user=['octocat'], fields= \
            ['full_name', 'license.name', 'license', 'permissions.admin'])
        reponames = [repo.full_name for repo in oct_repos]
        assert 'octocat/octocat.github.io' in reponames
        assert 'octocat/Spoon-Knife' in reponames
        licenses = [repo.license_name for repo in oct_repos]
        assert 'MIT License' in licenses

#-------------------------------------------------------------------------------
class Test_repoteams():
    """Tests for gitinfo.repoteams().
    """
    def test_msiot(self):
        gi.auth_config({'username': 'msftgits'})
        testteams = gi.repoteams(org='ms-iot', repo=['serial-wiring'])
        teamnames = [team.name.lower() for team in testteams]
        assert 'msftclas-write' in teamnames

#-------------------------------------------------------------------------------
class Test_teammembers():
    """Tests for gitinfo.teammembers().
    """
    def test_team652356(self):
        gi.auth_config({'username': 'msftgits'})
        memberlist = gi.teammembers(teamid=652356)
        members = [member.login for member in memberlist]
        assert 'msftgits' in members

#-------------------------------------------------------------------------------
class Test_teams():
    """Tests for gitinfo.teams().
    """
    def test_team_msiot(self):
        gi.auth_config({'username': 'msftgits'})
        teamtest = gi.teams(org=['ms-iot'])
        teamnames = [team.name.lower() for team in teamtest]
        assert 'msftclas-write' in teamnames
        assert 'cpub' in teamnames

#--------------------------------- END OF FILE ---------------------------------
