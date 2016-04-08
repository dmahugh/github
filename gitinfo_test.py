"""Test suite for gitinfo module

NOTE: some of these tests require msftgits GitHub credentials, so they won't
pass on a machine that doesn't have those credentials configured.

Test_auth_user() -----------> Tests for gitinfo.auth_user() function.
Test_pagination() ----------> Tests for gitinfo.pagination() function.
Test_readme_content() ------> Tests for gitinfo.readme_content() function.
Test_repo_tags() -----------> Tests for gitinfo.readme_tags() function.
Test_repos() ---------------> Tests for gitinfo.repos() function.
Test_remove_github_urls() --> Tests for gitinfo.remove_github_urls() function.
Test_teammembers() ---------> Tests for gitinfo.teammembers() function.
"""
import pytest
# pragma pylint: disable=no-self-use,invalid-name,missing-docstring,redefined-outer-name

import gitinfo as gi

#-------------------------------------------------------------------------------
class Test_auth_user():
    """Tests for gitinfo.auth_user() function.
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
class Test_pagination():
    """Tests for gitinfo.pagination() function.
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
    """Test data for testing gitinfo.pagination() function.
    """
    return "<https://api.github.com/organizations/6154722/" + \
        "repos?page=2>; rel=\"next\", <https://api.github.com/" + \
        "organizations/6154722/repos?page=18>; rel=\"last\""

#-------------------------------------------------------------------------------
class Test_readme_content():
    """Tests for gitinfo.readme_content() function.
    """
    def test_gitinforeadme(self):
        readme = gi.readme_content(owner='dmahugh', repo='gitinfo')
        assert b'[gitinfo](images/gitinfo.png)' in readme

#-------------------------------------------------------------------------------
class Test_repo_tags():
    """Tests for gitinfo.readme_tags() function.
    """
    def test_gitinforepo(self):
        taglist = gi.repo_tags(owner='dmahugh', repo='gitinfo')
        assert 'python' in taglist
        assert 'github' in taglist
        assert 'rest' in taglist

#-------------------------------------------------------------------------------
class Test_repos():
    """Tests for gitinfo.repos() function.
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
class Test_remove_github_urls():
    """Tests for gitinfo.remove_github_urls() function.
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
class Test_teammembers():
    """Tests for gitinfo.teammembers() function.
    """
    def test_team652356(self):
        gi.auth_config({'username': 'msftgits'})
        memberlist = gi.teammembers(teamid=652356)
        members = [member.login for member in memberlist]
        assert 'msftgits' in members
