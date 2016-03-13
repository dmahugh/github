#gitinfo
    Helper functions for retrieving data via the GitHub API.  
      
    auth_config() ------> Configure authentication settings.  
    auth_user() --------> Return credentials for use in GitHub API calls.  
    github_api() -------> Call the GitHub API (wrapper for requests.get()).  
    log_apistatus() ----> Display current API rate-limit status.  
    log_config() -------> Configure message logging settings.  
    log_msg() ----------> Log a status message.  
    memberfields() -----> Get field values for a member/user.  
    members() ----------> Get members of one or more organizations.  
    membersget() -------> Get member info for a specified organization.  
    pagination() -------> Parse 'link' HTTP header returned by GitHub API.  
    repofields() -------> Get field values for a repo.  
    repos() ------------> Get repo information for organizations or users.  
    reposget() ---------> Get repo information from specified API endpoint.  
    repoteamfields() ---> Get field values for a repo's team.  
    repoteams() --------> Get teams associated with one or more repositories.  
    repoteamsget() -----> Get repo info for a specified repo.  
    session_end() ------> Log summary of completed gitinfo "session."  
    session_start() ----> Initiate a gitinfo session for logging/tracking purposes.  
    teamfields() -------> Get field values for an organization's team.  
    teams() ------------> Get teams for one or more organizations.  
    teamsget() ---------> Get team info for a specified organization.  
    timestamp() --------> Return current timestamp as YYYY-MM-DD HH:MM:SS  
    write_csv() --------> Write a list of namedtuples to a CSV file.
##auth_config(settings=None):

    Configure authentication settings.  
      
    1st parameter = dictionary of configuration settings; see config_settings  
                    below for settings managed by this function.  
      
    Returns dictionary of current settings - call auth_config() with no  
    parameters to get status.
##auth_user():

    Credentials for basic authentication.  
      
    Returns the tuple used for API calls, based on current settings.  
    Returns None if no GitHub username/PAT is currently set.
##github_api(endpoint=None, auth=None, headers=None):

    Call the GitHub API (wrapper for requests.get()).  
      
    endpoint = the HTTP endpoint to call  
    auth = optional tuple for authentication  
    headers = optional dictionary of HTTP headers to pass
##log_apistatus():

    Display (via log_msg()) the rate-limit status after the last API call.  
        
##log_config(settings=None):

    Configure message logging settings.  
      
    1st parameter = dictionary of configuration settings; see config_settings  
                    below for settings managed by this function.  
      
    Returns dictionary of current settings - call log_config() with no  
    parameters to get status.
##log_msg(*args):

    Log a status message.  
      
    parameters = message to be displayed if log_config(True) is set.  
      
    NOTE: can pass any number of parameters, which will be displayed as a single  
    string delimited by spaces.
##memberfields(member_json, fields, org):

    Get field values for a member/user.  
      
    1st parameter = member's json representation as returned by GitHub API  
    2nd parameter = list of names of desired fields  
    3rd parameter = organization ID  
      
    Returns a namedtuple containing the desired fields and their values.  
    NOTE: in addition to the specified fields, always returns an 'org' field  
    to distinguish between orgs in multi-org lists returned by members().
##members(org=None, team=None, fields=None, audit2fa=False):

    Get members for one or more teams or organizations.  
      
    org = an organization ID or list of organizations  
    team = a team ID or list of teams; if provided, org is ignored  
    fields = list of field names to be returned; names must be the same as  
             returned by the GitHub API (see below).  
    audit2fa = whether to only return members with 2FA disabled. You must be  
               authenticated via auth_config() as an admin of the org(s) to use  
               this option.  
      
    Returns a list of namedtuple objects, one per member.  
      
    GitHub API fields (as of March 2016):  
    id                  events_url          organizations_url  
    login               followers_url       received_events_url  
    site_admin          following_url       repos_url  
    type                gists_url           starred_url  
    url                 gravatar_id         subscriptions_url  
    avatar_url          html_url
##membersget(org=None, team=None, fields=None, audit2fa=False):

    Get member info for a specified organization.  
      
    org = organization ID (ignored if a team is specified)  
    team = team ID  
    fields = list of fields to be returned  
    audit2fa = whether to only return members with 2FA disabled. This option  
               is only available when retrieving members by organization.  
               Note: for audit2fa=True, you must be authenticated via  
               auth_config() as an admin of the org(s).  
      
    Returns a list of namedtuples containing the specified fields.
##pagination(link_header):

    Parse values from the 'link' HTTP header returned by GitHub API.  
      
    1st parameter = either of these options ...  
                    - 'link' HTTP header passed as a string  
                    - response object returned by requests.get()  
      
    Returns a dictionary with entries for the URLs and page numbers parsed  
    from the link string: firstURL, firstpage, prevURL, prevpage, nextURL,  
    nextpage, lastURL, lastpage.
##repofields(repo_json, fields, org, user):

    Get field values for a repo.  
      
    1st parameter = repo's json representation as returned by GitHub API  
    2nd parameter = list of names of desired fields  
    3rd parameter = organization (for including in output fields)  
    4th parameter = username (for including in output fields)  
      
    Returns a namedtuple containing the desired fields and their values.
##repos(org=None, user=None, fields=None):

    Get repo information for one or more organizations or users.  
      
    org    = organization; an organization or list of organizations  
    user   = username; a username or list of usernames (if org is provided,  
             user is ignored)  
    fields = list of fields to be returned; names must be the same as  
             returned by the GitHub API (see below).  
             Note: dot notation for embedded elements is supported.  
             For example, pass a field named 'license.name' to get the 'name'  
             element of the 'license' entry for each repo.  
      
    Returns a list of namedtuple objects, one per repo.
##reposget(org=None, user=None, fields=None):

    Get repo information for a specified org or user.  
      
    org = organization name  
    user = username (ignored if org is provided)  
    fields = list of fields to be returned  
      
    Returns a list of namedtuples containing the specified fields.
##repoteamfields(team_json, fields, org, repo):

    Get field values for a repo's team.  
      
    1st parameter = team's json representation as returned by GitHub API  
    2nd parameter = list of names of desired fields  
    3rd parameter = organization ID  
    4th parameter = repo name  
      
    Returns a namedtuple containing the desired fields and their values.  
    NOTE: in addition to the specified fields, always returns 'org' and  
    'repo' fields to clarify which org/repo this team is associated with.
##repoteams(org=None, repo=None, fields=None):

    Get teams for one or more repositories.  
      
    org = organization ID (required)  
    repo = repo name, list of repo names, or None for all repos in this org  
    fields = list of field names to be returned; names must be the same as  
             returned by the GitHub API (see below).  
      
    Note: to access team information, you must be authenticated as a member of  
    the Owners team for the team's organization.  
      
    Returns a list of namedtuple objects, one per team.  
      
    GitHub API fields (as of March 2016): description, id, members_url, name,  
        permission, privacy, repositories_url, slug, url
##repoteamsget(org, repo, fields):

    Get team info for a specified repo.  
      
    1st parameter = organization ID  
    2nd parameter = repo name  
    3rd parameter = list of fields to be returned  
      
    Returns a list of namedtuples containing the specified fields.
##session_end(msg=None):

    Log summary of completed gitinfo session.  
      
    1st parameter = optional message to include in logfile/console output
##session_start(msg=None):

    Initiate a gitinfo "session" for logging/tracking purposes.  
      
    1st parameter = optional message to include in logfile/console output
##teamfields(team_json, fields, org):

    Get field values for an organization's team.  
      
    1st parameter = team's json representation as returned by GitHub API  
    2nd parameter = list of names of desired fields  
    3rd parameter = organization ID  
      
    Returns a namedtuple containing the desired fields and their values.  
    NOTE: in addition to the specified fields, always returns an 'org' field  
    to distinguish between orgs in multi-org lists returned by teams().
##teams(org=None, fields=None):

    Get teams for one or more organizations.  
      
    org = organization ID, or a list of organizations  
    fields = list of field names to be returned; names must be the same as  
             returned by the GitHub API (see below).  
      
    Note: to access team information, you must be authenticated as a member of  
    the Owners team for the team's organization.  
      
    Returns a list of namedtuple objects, one per team.  
      
    GitHub API fields (as of March 2016): description, id, members_url, name,  
        permission, privacy, repositories_url, slug, url
##teamsget(org, fields):

    Get team info for a specified organization.  
      
    1st parameter = organization ID  
    2nd parameter = list of fields to be returned  
      
    Returns a list of namedtuples containing the specified fields.
##timestamp():

    Return current timestamp as a string - YYYY-MM-DD HH:MM:SS  
        
##write_csv(listobj, filename):

    Write a list of namedtuples to a CSV file.  
      
    1st parameter = the list  
    2nd parameter = name of CSV file to be written