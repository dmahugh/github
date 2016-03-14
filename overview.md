# gitinfo - overview

This page provides a summary of how to use gitinfo. There is also detailed information in the docstrings in the [source code](https://github.com/dmahugh/gitinfo/blob/master/gitinfo.py) and in the auto-generated [documentation](gitinfo.md).

## Table of Contents

* [basic concepts](#basic-concepts)
* [examples](#examples)
* [authentication](#authentication)
* [specifying fields](#specifying-fields)
* [auditing 2FA configuration](#auditing-2fa-configuration)
* [logging output](#logging-output)
* [writing CSV files](#writing-csv-files)

## basic concepts

The core functions (```members()```, ```repos()```, ```teams()```, ```repoteams()```, ```collaborators()```) each return a list of namedtuple objects, and these namedtuples may contain a set of default fields or you can specify the fields to be returned. You can specify one or more orgs, repos or teams and you get back a single consolidated list appropriate for reporting/auditing scenarios.

The GitHub API requires authentication to access certain information, and to allow for more than 60 API calls per hour. You can store authentication credentials (username/PAT) in a JSON file as described below, then use ```auth_config()``` specify the username for subsequent API calls.  

By default, gitinfo displays status information on the console. You can turn this on or off, or direct this information to a log file, through settings managed by ```log_config()```. The ```session_start()``` and ```session_end()``` functions can be used to identify a gitinfo session for the purpose of tracking number of API calls, bytes returned, and elapsed time. You can use the ```log_msg()``` function to add your own information to the logs as well.

## examples

For these examples, we'll assume you've imported ```gitinfo``` as ```gi```:

```
import gitinfo as gi
```

There are currently four main functions that provide most of the functionality, and the following are simple examples of how to use each of them.

### repos()
The examples below return public repos only. To return private repos, you need to be authenticated as a member of the repo's organization or the repo's owner.
```
# get all public repos for an organization
ms_repos = gi.repos(org='microsoft')

# get all public repos for a set of organizations
azure_repos = gi.repos(org=['Azure', 'Azure-Readiness', 'Azure-Samples', 'AzureAD', 'AzureADSamples'])

# get all repos for a user
octocat_repos = gi.repos(user='octocat')

# get all repos for a set of users
misc_repos = gi.repos(['kennethreitz', 'codelucas'])
```
### members()
Public members can be returned without authentication, but you need to be authenticated as a member of an organization to see concealed members.
```
gi.auth_config({'username': 'your-user-name'})

# get members of an organization
org_members = gi.members(org='your-org-name')

# get members of multiple organizations
org_members = gi.members(org=['org1', 'org2', 'org3']

# for team members, use the ID instead of the name
team_members = gi.members(team='123456')

# get members of multiple teams
team_members = gi.members(team=['111111', '222222', '333333'])
```
### teams()
To retrieve team information, you must be authenticated as a member of the Owners for the organization being managed.
```
gi.auth_config({'username': 'your-user-name'})

# get teams for one organization
teams = gi.teams(org='org-name')

# get teams for a set of organizations
teams = gi.teams(org=['org1', 'org2', 'org3'])
```

### repoteams()
This function returns information about teams associated with specific repos in an organization.
```
gi.auth_config({'username': 'your-user-name'})

# Note that the org parameter is required in all cases

# get team information for a single repo
teams = gi.repoteams(org='org-name', repo='repo-name')

# get team information for a set of repos
teams = gi.repoteams(org='org-name', repo=['repo1', 'repo2', 'repo3'])

# special case: omit repo parameter for ALL repos in an organization
teams = repoteams(org='org-name')
```

### collaborators()
This function returns information about collaborators associated with specific repos.
```
gi.auth_config({'username': 'your-user-name'})

# Note that the owner and repo parameters are both required

# get collaborator information for a single repo
teams = gi.collaborators(owner='org-name', repo='repo-name')

# get collaborator information for a set of repos
teams = gi.collaborators(org='org-name', repo=['repo1', 'repo2', 'repo3'])
```

## authentication
You can use gitinfo to retrieve public information from GitHub without any authentication, but the 60 requests per hour rate limit
will be enforced, and you won't have access to certain information as mentioned above. You can bump the API rate limit up to 5000 requests per hour by using authentication.

GitHub credentials (username/PAT) are stored in a ```github_users.json``` file in the ```private``` subfolder. Here's the format to use:

```
{
    "user1": "Personal Access Token for user1",
    "user2": "Personal Access Token for user2"
}
```
Then you can use the ```auth_config()``` function to set the username for subsquent operations. For example:

```
import gitingo as gi
gi.auth_config({'username': 'user1'})
# make GitHub API calls as user1
gi.auth_config({'username': 'user2'})
# make GitHub API calls as user2
gi.auth_config('username': None)
# make GitHub API calls without authentication
```
Only basic authentication via username and PAT (Personal Access Token) is supported at this time.

## specifying fields
Gitinfo functions return a list of namedtuples which contain either a default set of fields or a set of fields that you can specify. Here are the default fields for each of the major functions:

* repos() - org, user, full_name, watchers, forks, open_issues
* members() - org, login, id, type, site_admin
* teams() - org, name, id, privacy, permission
* repoteams() - org, repo, name, id, privacy, permission
* collaborators() - owner, repo, id, login, type, permissions.admin

Here's an example of how to specify fields to be returned:

![OctocatRepos](images/OctocatRepos.png)

Some fields, such as ```license```, return a JSON document, which is inconvenient for saving to a CSV file. You can include a specific subfield instead of the entire JSON document by using dot notation. For example:

![SubfieldExample](images/subfields.png)

Note that the field name ```license.name``` was transformed to ```license_name``` in the returned tuples above, because you can't have periods embedded in namedtuple identifiers.

## auditing 2FA configuration
The GitHub API supports a filter that can be used to audit the members of organizations to determine who doesn't have GitHub two-factor authentication (2FA) enabled. The ```members()``` function supports an optional ```audit2fa=``` parameter to take advantage of this filter.

You must be *authenticated as an owner of an organization* to get this information. For example, if you've configured PAT for ```admin-user```, and that user is an owner of organzation ```org-name```, here's how you would get a list of members who don't have 2FA enabled:

```
import gitinfo as gi
gi.auth_user('admin-user')
no2fa = gi.members(org='org-name', audit2fa=True)
```

## logging output
By default, all functions in gitinfo run in "verbose mode" and display various status information on the console. You can switch verbose mode on or off via the ```log_config()``` function, and you can also send verbose output to a disk file. Console and file output are controlled independently, by the ```verbose``` and ```logfile``` parameters:

```
import gitinfo as gi
gi.log_config(verbose=False, logfile='gitinfo.log') # send status info to a logfile, but don't display it
```

There are also ```session_start()``` and ```session_end()``` functions that you can put before and after a block of code to get a summary of how many API calls were made, how many bytes returned, API rate-limit status, elapsed time, etc. Here's an example of typical output to a log file using all of these options:

![logfile](images/logfile.jpg)

Note that Personal Access Tokens are not displayed or written to log files - just the first 2 and last 2 characters, to help identify which PAT was used.

## writing CSV files
Gitinfo query functions return a list of namedtuple objects, and the ```write_csv()``` function can be used to write these lists to a CSV file:

```
import gitinfo as gi
ms_members = gi.members(org='microsoft')
gi.write_csv(ms_members, 'MicrosoftMembers.csv')
```