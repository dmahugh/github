# gitinfo - Python 3.x library for GitHub REST API

This is a simple wrapper optimized for ease of use, supporting a subset of the GitHub API. Intended for use in automating common administrative and monitoring activities.

## installation

Gitinfo has one external dependency - the [requests](https://pypi.python.org/pypi/requests) library. Follow these steps to get up and running:

* Install Python 3.5 from [Python.org](https://www.python.org/).
* Clone the [Gitinfo repo](https://github.com/dmahugh/gitinfo).
* Install requests: ```pip install requests```

## overview

The core functions (```members()```, ```repos()```, ```orgteams()```, ```repoteams()```) each return a list of namedtuple objects, and these namedtuples may contain a set of default fields or you can specify the fields to be returned. Pagination is handled automatically &mdash; the core functions return complete data sets.

The GitHub API requires authentication to access certain information, and to allow for more than 60 API calls per hour. You can store authentication credentials (username/PAT) in a JSON file as described below, then use ```auth_config()``` specify the username for subsequent API calls.  

By default, gitinfo displays status information on the console. You can turn this on or off, or direct this information to a log file, through settings managed by ```log_config()```. The ```session_start()``` and ```session_end()``` functions can be used to identify a gitinfo session for the purpose of tracking number of API calls, bytes returned, and elapsed time. You can use the ```log_msg()``` function to add your own information to the logs.

The rest of this page shows a few typical use cases. There is also detailed information in the docstrings in the [source code](https://github.com/dmahugh/gitinfo/blob/master/gitinfo.py).

## sample usage

Here's an example of how to retrieve and display repos by *organization*:

```
import gitinfo as gi
ms_repos = gi.repos(org='microsoft')
for repo in ms_repos:
    print(repo)
```

And here's the output for that example:

![MicrosoftReposOutput](images/MicrosoftReposOutput.png)

Similar syntax to get repos by *user*:

```
import gitinfo as gi
oct_repos = gi.repos(user='octocat')
for repo in oct_repos:
    print(repo)
```

And here's the output for that example:

![OctocatRepos2](images/OctocatRepos2.png)

## logging output
By default, all functions in gitinfo run in "verbose mode" and display various status information on the console. You can switch verbose mode on or off via the ```log_config()``` function, and you can also send verbose output to a disk file. Console and file output are controlled independently, by the ```verbose``` and ```logfile``` parameters:

```
import gitinfo as gi
gi.log_config(verbose=False, logfile='gitinfo.log') # send status info to a logfile, but don't display it
```

There are also ```session_start()``` and ```session_end()``` functions that you can put before and after a block of code to get a summary of how many API calls were made, how many bytes returned, API rate-limit status, elapsed time, etc. Here's an example of typical output to a log file using all of these options:

![logfile](images/logfile.jpg)

Note that Personal Access Tokens are not displayed or written to log files - just the first 2 and last 2 characters, to help identify which PAT was used.

## retrieving repos by user, specifying fields
Here's an example of how to retrieve the public repos for a specified user (Octocat) instead of organization, and how to specify fields to be returned (full_name and default_branch):

![OctocatRepos](images/OctocatRepos.png)

Some fields, such as ```license```, return a JSON document, which is inconvenient for saving to a CSV file. You can include a specific subfield instead of the entire JSON document by using dot notation. For example:

![SubfieldExample](images/subfields.png)

Note that the field name ```license.name``` was transformed to ```license_name``` in the returned tuples above, because you can't have periods embedded in namedtuple identifiers.

## retrieving information for multiple orgs or users
If you want to get a list of all repos in multiple org or under multiple users, you can simply pass a list instead of a single value for the ```org=``` or ```user=``` parameter in the ```repos()``` function. For example, these sorts of syntax return what you'd expect:

```
import gitinfo as gi
repolist = gi.repos(user=['octocat', 'dmahugh'])
repolist = gi.repos(org=['Azure', 'dotnet', 'Microsoft', 'OfficeDev'])
```

Note that you can also pass a list of orgs to the ```members()``` function, to return member information for multiple organizations:

```
import gitinfo as gi
memberlist = gi.members(org=['Azure', 'dotnet', 'Microsoft', 'OfficeDev'])
```

The ```members()``` function also supports an optional ```team=``` parameter, which can contain either a single team ID or a list of teams.

## auditing members for 2FA
The GitHub API supports a filter that can be used to audit the members of organizations to determine who doesn't have GitHub two-factor authentication (2FA) enabled. The ```members()``` function supports an optional ```audit2fa=``` parameter to take advantage of this filter.

You must be *authenticated as an owner of an organization* to get this information. For example, if you've configured PAT for ```admin-user``` (as described in the next section below), and that user is an owner of organzation ```org-name```, here's how you would get a list of members who don't have 2FA enabled:

```
import gitinfo as gi
gi.auth_user('admin-user')
no2fa = gi.members(org='org-name', audit2fa=True)
```

## authentication
You can use this module to retrieve public information from GitHub without any authentication, but the 60 requests per hour rate limit
will be enforced. You can bump that up to 5000 requests per hour by using authentication.

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

## saving results
The ```members()``` and ```repos()``` functions return a list of _namedtuple_ objects. The ```write_csv()``` function can be used to write these lists to a CSV file:

```
import gitinfo as gi
ms_members = gi.members(org='microsoft')
gi.write_csv(ms_members, 'MicrosoftMembers.csv')
```

To learn more, see the [source code](https://github.com/dmahugh/gitinfo/blob/master/gitinfo.py), the [gitinfo.html](https://github.com/dmahugh/gitinfo/blob/master/gitinfo.html) documentation file, or the [GitHub V3 API documentation](https://developer.github.com/v3/). If you have suggestions for improvement, pull requests and issues are gladly accepted!
