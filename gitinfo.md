#gitinfo documentation
    Helper functions for retrieving data via the GitHub API.  
      
    auth_config() --------> Configure authentication settings.  
    auth_user() ----------> Return credentials for use in GitHub API calls.  
    collaborators() ------> Get collaborators for one or more repos.  
    commits() ------------> Get commits for repo's default branch.  
    files() --------------> Get filenames for a repo.  
    githubapi_to_file() --> Call GitHub API, handle pagination, write to file.  
    log_apistatus() ------> Display current API rate-limit status.  
    log_config() ---------> Configure message logging settings.  
    log_msg() ------------> Log a status message.  
    members() ------------> Get members of one or more organizations.  
    minimize_json() ------> Remove the *_url properties from a json data file.  
    ratelimit_status() ---> Display current rate-limit status.  
    readme_content() -----> Retrieve contents of preferred readme for a repo.  
    readme_tag_parser() --> Extract LandingPageTags values from a readme line.  
    remove_github_urls() -> Remove *_url entries from a dictionary.  
    repo_admins() --------> Get administrators for a repo.  
    repo_tags() ----------> Retrieve metadata tags from a repo's readme.  
    repos() --------------> Get repo information for organizations or users.  
    repoteams() ----------> Get teams associated with one or more repositories.  
    session_end() --------> Log summary of completed gitinfo "session."  
    session_start() ------> Initiate a gitinfo session for logging/tracking purposes.  
    teammembers() --------> Get team members for specified team.  
    teams() --------------> Get teams for one or more organizations.  
    write_csv() ----------> Write a list of namedtuples to a CSV file.  
      
    Note: some classes and functions have been omitted from the above list because  
    they're only used internally and don't expose useful functionality.
##teammembers
    Get members of a specified team.  
      
    teamid = the GitHub ID for the team (either integer or string)  
      
    Returns a list of namedtuples with info about the members of the team.  
      
    NOTE: this function uses msgithub.py (if available) to get Microsoft email  
    address associated with GitHub logins. If msgithub.py is not available, the  
    email addresses are blank.
##log_apistatus
    Display (via log_msg()) the rate-limit status after the last API call.  
        
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
##ratelimit_status
    Displays current rate-limit status.  
      
    user = GitHub user name for authentication (optional)  
      
    Returns a tuple, first value is rate limit for this user and second value  
    is number of remaining/unused API calls available.
##readme_tag_parser
    Extract LandingPageTags values from a line of text from a readme file.  
      
    line = a string in this format:  
           <properties prop1='xxx' LandingPageTags="XXX,YYY,ZZZ" prop2="yyy" />  
      
    Returns a list of the LandingPageTags values. In the example above, would  
    return ['xxx', 'yyy', 'zzz']. Note that all returned values are converted  
    to lower case.
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
##commits
    Get commits for repo's default branch (usually MASTER).  
      
    owner  = user or organization that owns the repo (required)  
    repo   = repo name (required)  
    fields = list of field names to be returned; names must be the same as  
             returned by the GitHub API as documented here:  
             https://developer.github.com/v3/repos/commits/#list-commits-on-a-repository  
      
    Returns a list of namedtuple objects, one per commit.
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
##minimize_json
    Remove all *_url properties from a json data file.  
      
    infile = the input json file (as returned by the GitHub API)  
    outfile = the new minimized file with *_url removed.  
      
    This function is intended for use with data files that contain captured  
    GitHub API responses as a list of dictionaries. It removes *_url entries  
    from the dictionaries in the list.
##write_csv
    Write a list of namedtuples to a CSV file.  
      
    1st parameter = the list  
    2nd parameter = name of CSV file to be written
##repo_admins
    Get administrators for a repo.  
      
    org = organization name  
    repo = repo name  
      
    Returns a list of dictionaries, with each dictionary describing a person  
    with admin rights for this repo. These keys are included in the  
    dictionaries:  
    admintype -> either 'AdminTeamMember' or 'AdminCollaborator'  
    teamname --> team name (for admintype=='AdminTeamMember')  
    teamid ----> GitHub team ID (for admintype=='AdminTeamMember')  
    login -----> GitHub login name  
    email -----> email address (if a Microsoft employee)
##auth_config
    Configure authentication settings.  
      
    1st parameter = dictionary of configuration settings; see config_settings  
                    below for settings managed by this function.  
      
    Returns dictionary of current settings - call auth_config() with no  
    parameters to get status.
##githubapi_to_file
    Call GitHub API, consolidate pagination, write to output file.  
      
    endpoint = GitHub API endpoint to call  
    filename = file to write consolidated output to  
    headers = optional dictionary of HTTP headers to send with the request  
      
    The output file is written as a single JSON list, containing all pages of  
    data if there is more than one.
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
##files
    Get list of files currently in the default branch of a repo.  
      
    owner  = user or organization that owns the repo (required)  
    repo   = repo name (required)  
    fields = list of field names to be returned; names must be the same as  
             returned by the GitHub API as documented here:  
             https://developer.github.com/v3/git/trees/  
      
    Returns a list of namedtuple objects, one per file in the tree. Note that  
    this wrapper is different from the others and returns a predetermined set of  
    fields (see below).
##repo_tags
    Retrieve metadata tags from a repo's readme.  
      
    owner = org or username  
    repo = repo name  
      
    Returns a list of tags.
##remove_github_urls
    Remove URL entries (as returned by GitHub API) from a dictionary.  
      
    1st parameter = dictionary  
      
    Returns a copy of the dictionary, but with no entries named *_url or url.
##log_config
    Configure message logging settings.  
      
    1st parameter = dictionary of configuration settings; see config_settings  
                    below for settings managed by this function.  
      
    Returns dictionary of current settings - call log_config() with no  
    parameters to get status.
##readme_content
    Retrieve contents of preferred readme for a repo.  
      
    owner = org or username  
    repo = repo name  
      
    Returns the contents of the readme file for this repo (if any).
##session_end
    Log summary of completed gitinfo session.  
      
    1st parameter = optional message to include in logfile/console output
##log_msg
    Log a status message.  
      
    parameters = message to be displayed if log_config(True) is set.  
      
    NOTE: can pass any number of parameters, which will be displayed as a single  
    string delimited by spaces.
##session_start
    Initiate a gitinfo "session" for logging/tracking purposes.  
      
    1st parameter = optional message to include in logfile/console output
##collaborators
    Get collaborators for one or more repos with the same owner.  
      
    owner = the repo owner (org or user)  
    repo = repo name or list of repo names  
    fields = list of field names to be returned; names must be the same as  
             returned by the GitHub API (see below).  
      
    Note: to access collaborator information, you must be authenticated as a  
    person with admin access to the repo.  
      
    Returns a list of namedtuple objects, one per team.