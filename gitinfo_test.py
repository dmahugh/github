"""Test suite for gitinfo module
"""
import pytest
# pragma pylint: disable=R0201,C0103,C0111,W0621

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

