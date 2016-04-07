#gitinfo documentation
    Helper functions for retrieving data via the GitHub API.  
      
    auth_config() --------> Configure authentication settings.  
    auth_user() ----------> Return credentials for use in GitHub API calls.  
    collaborators() ------> Get collaborators for one or more repos.  
    collaboratorsget() ---> Get collaborator info for a specified repo.  
    json_read() ----------> Read a .json file into a Python object.  
    json_write() ---------> Write a Python object to a .json file.  
    github_api() ---------> Call the GitHub API (wrapper for requests.get()).  
    githubapi_to_file() --> Call GitHub API, handle pagination, write to file.  
    log_apistatus() ------> Display current API rate-limit status.  
    log_config() ---------> Configure message logging settings.  
    log_msg() ------------> Log a status message.  
    members() ------------> Get members of one or more organizations.  
    membersget() ---------> Get member info for a specified organization.  
    minimize_json() ------> Remove the *_url properties from a json data file.  
    pagination() ---------> Parse 'link' HTTP header returned by GitHub API.  
    remove_github_urls() -> Remove *_url entries from a dictionary.  
    repofields() ---------> Get field values for a repo.  
    repos() --------------> Get repo information for organizations or users.  
    reposget() -----------> Get repo information for a specified org or user.  
    repoteams() ----------> Get teams associated with one or more repositories.  
    repoteamsget() -------> Get team info for a specified repo.  
    session_end() --------> Log summary of completed gitinfo "session."  
    session_start() ------> Initiate a gitinfo session for logging/tracking purposes.  
    teams() --------------> Get teams for one or more organizations.  
    teamsget() -----------> Get team info for a specified organization.  
    timestamp() ----------> Return current timestamp as YYYY-MM-DD HH:MM:SS  
    write_csv() ----------> Write a list of namedtuples to a CSV file.  
      
    Note: some classes and functions have been omitted from the above list because  
    they're only used internally and don't expose useful functionality.
##reposget
    Get repo information for a specified org or user. Called by repos() to  
    aggregate repo information for multiple orgs or users.  
      
    org = organization name  
    user = username (ignored if org is provided)  
    fields = list of fields to be returned  
      
    Returns a list of namedtuples containing the specified fields.
##auth_config
    Configure authentication settings.  
      
    1st parameter = dictionary of configuration settings; see config_settings  
                    below for settings managed by this function.  
      
    Returns dictionary of current settings - call auth_config() with no  
    parameters to get status.
###repoteamfields
    Get field values for a repo's team.  
      
    1st parameter = team's json representation as returned by GitHub API  
    2nd parameter = list of names of desired fields  
    3rd parameter = organization ID  
    4th parameter = repo name  
      
    Returns a namedtuple containing the desired fields and their values.  
    NOTE: in addition to the specified fields, always returns 'org' and  
    'repo' fields to clarify which org/repo this team is associated with.  
    <internal>
##timestamp
    Return current timestamp as a string - YYYY-MM-DD HH:MM:SS  
        
##remove_github_urls
    Remove URL entries (as returned by GitHub API) from a dictionary.  
      
    1st parameter = dictionary  
      
    Returns a copy of the dictionary, but with no entries named *_url or url.
###auth_user
    Credentials for basic authentication.  
      
    Returns the tuple used for API calls, based on current settings.  
    Returns None if no GitHub username/PAT is currently set.  
    <internal>
##write_csv
    Write a list of namedtuples to a CSV file.  
      
    1st parameter = the list  
    2nd parameter = name of CSV file to be written
##githubapi_to_file
    Call GitHub API, consolidate pagination, write to output file.  
      
    endpoint = GitHub API endpoint to call  
    filename = file to write consolidated output to  
      
    The output file is written as a single JSON list, containing all pages of  
    data if there is more than one.
##collaborators
    Get collaborators for one or more repos with the same owner.  
      
    owner = the repo owner (org or user)  
    repo = repo name or list of repo names  
    fields = list of field names to be returned; names must be the same as  
             returned by the GitHub API (see below).  
      
    Note: to access collaborator information, you must be authenticated as a  
    person with admin access to the repo.  
      
    Returns a list of namedtuple objects, one per team.
##repos
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
##repoteams
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
##members
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
##minimize_json
    Remove all *_url properties from a json data file.  
      
    infile = the input json file (as returned by the GitHub API)  
    outfile = the new minimized file with *_url removed.  
      
    This function is intended for use with data files that contain captured  
    GitHub API responses as a list of dictionaries. It removes *_url entries  
    from the dictionaries in the list.
##session_start
    Initiate a gitinfo "session" for logging/tracking purposes.  
      
    1st parameter = optional message to include in logfile/console output
##github_api
    Call the GitHub API (wrapper for requests.get()).  
      
    endpoint = the HTTP endpoint to call  
    auth = optional tuple for authentication  
    headers = optional dictionary of HTTP headers to pass  
      
    Returns the response object.  
    API call through this function update session totals.
##log_msg
    Log a status message.  
      
    parameters = message to be displayed if log_config(True) is set.  
      
    NOTE: can pass any number of parameters, which will be displayed as a single  
    string delimited by spaces.
##log_apistatus
    Display (via log_msg()) the rate-limit status after the last API call.  
        
##session_end
    Log summary of completed gitinfo session.  
      
    1st parameter = optional message to include in logfile/console output
##collaboratorsget
    Get collaborator info for a specified repo. Called by collaborators() to  
    aggregate collaborator information for multiple repos.  
      
    1st parameter = owner  
    2nd parameter = repo name  
    3rd parameter = list of fields to be returned  
      
    Returns a list of namedtuples containing the specified fields.
##teamsget
    Get team info for a specified organization. Called by teams() to  
    aggregate team information for multiple organizations.  
      
    1st parameter = organization ID  
    2nd parameter = list of fields to be returned  
      
    Returns a list of namedtuples containing the specified fields.
##json_write
    Write Python object to a .json file.  
      
    source = the object to be serialized  
    filename = the filename (will be over-written if it already exists)
##repoteamsget
    Get team info for a specified repo. Called by repoteams() to aggregate  
    team information for multiple repos.  
      
    1st parameter = organization ID  
    2nd parameter = repo name  
    3rd parameter = list of fields to be returned  
      
    Returns a list of namedtuples containing the specified fields.
###collaboratorfields
    Get field values for a collaborator.  
      
    1st parameter = collaborator JSON representation as returned by GitHub API  
    2nd parameter = list of names of desired fields  
    3rd parameter = owner (for including in output fields)  
    4th parameter = repo (for including in output fields)  
      
    Returns a namedtuple containing the desired fields and their values.  
    <internal>
##teams
    Get teams for one or more organizations.  
      
    org = organization ID, or a list of organizations  
    fields = list of field names to be returned; names must be the same as  
             returned by the GitHub API (see below).  
      
    Note: to access team information, you must be authenticated as a member of  
    the Owners team for the team's organization.  
      
    Returns a list of namedtuple objects, one per team.  
      
    GitHub API fields (as of March 2016): description, id, members_url, name,  
        permission, privacy, repositories_url, slug, url
###repofields
    Get field values for a repo.  
      
    1st parameter = repo's json representation as returned by GitHub API  
    2nd parameter = list of names of desired fields  
    3rd parameter = organization (for including in output fields)  
    4th parameter = username (for including in output fields)  
      
    Returns a namedtuple containing the desired fields and their values.  
    <internal>
##json_read
    Read .json file into a Python object.  
      
    filename = the filename  
    Returns the object that has been serialized to the .json file (list, etc).
###pagination
    Parse values from the 'link' HTTP header returned by GitHub API.  
      
    1st parameter = either of these options ...  
                    - 'link' HTTP header passed as a string  
                    - response object returned by requests.get()  
      
    Returns a dictionary with entries for the URLs and page numbers parsed  
    from the link string: firstURL, firstpage, prevURL, prevpage, nextURL,  
    nextpage, lastURL, lastpage.  
    <internal>
###teamfields
    Get field values for an organization's team.  
      
    1st parameter = team's json representation as returned by GitHub API  
    2nd parameter = list of names of desired fields  
    3rd parameter = organization ID  
      
    Returns a namedtuple containing the desired fields and their values.  
    NOTE: in addition to the specified fields, always returns an 'org' field  
    to distinguish between orgs in multi-org lists returned by teams().  
    <internal>
##log_config
    Configure message logging settings.  
      
    1st parameter = dictionary of configuration settings; see config_settings  
                    below for settings managed by this function.  
      
    Returns dictionary of current settings - call log_config() with no  
    parameters to get status.
###memberfields
    Get field values for a member/user.  
      
    1st parameter = member's json representation as returned by GitHub API  
    2nd parameter = list of names of desired fields  
    3rd parameter = organization ID  
      
    Returns a namedtuple containing the desired fields and their values.  
    NOTE: in addition to the specified fields, always returns an 'org' field  
    to distinguish between orgs in multi-org lists returned by members().  
    <internal>
##membersget
    Get member info for a specified organization. Called by members() to  
    aggregate member info for multiple organizations.  
      
    org = organization ID (ignored if a team is specified)  
    team = team ID  
    fields = list of fields to be returned  
    audit2fa = whether to only return members with 2FA disabled. This option  
               is only available when retrieving members by organization.  
               Note: for audit2fa=True, you must be authenticated via  
               auth_config() as an admin of the org(s).  
      
    Returns a list of namedtuples containing the specified fields.