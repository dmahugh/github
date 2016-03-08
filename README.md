# gitinfo

Python 3.x helper functions to make it easy to retrieve information via the GitHub API.

What it is:

* Optimized for ease of use.
* A module with one external dependency - the [requests](https://pypi.python.org/pypi/requests) library.
* Work in progress; much more to come.

What it isn't:

* A complete wrapper for the GitHub API - many calls not supported (yet).
* A way to do automated updates and changes; all functions are read-only.

## sample usage

Here's an example of how to retrieve all public repos in the Microsoft organization:

```
import gitinfo as gi
ms_repos = gi.get_repos(org='microsoft')
for repo in ms_repos:
    print(repo)
```

And here's the output for that example:

![MicrosoftReposOutput](images/MicrosoftReposOutput.png)

You can set "verbose mode" on to get status information displayed to the console. For example:

```
import gitinfo as gi
gi.verbose(True)
ms_repos = gi.get_repos(org='microsoft')
for repo in ms_repos:
    print(repo)
```

... displays this console output:

![MicrosoftReposOutputVerbose](images/MicrosoftReposOutput2.png)


Here's an example of how to retrieve the public repos for a specified user (Octocat) instead of organization, and how to specify fields to be returned (full_name and default_branch):

![OctocatRepos](images/OctocatRepos.png)

Some fields, such as ```license```, return a JSON document, which is inconvenient for saving to a CSV file. You can include a specific subfield instead of the entire JSON document by using dot notation. For example:

![SubfieldExample](images/subfields.png)

## authentication
You can use this module to retrieve public information from GitHub without any authentication, but the 60 requests per hour rate limit
will be enforced. You can bump that up to 5000 requests per hour by using authentication.

Only basic authentication via username and PAT (Personal Access Token) is supported at this time. To set up a default user for API calls, put the GitHub username and a PAT in environment variables named *GitHubUser* and *GitHubPAT*, respectively.

You can also store GitHub usernames and PATs in a ```github_users.json``` file in the ```private``` subfolder. For example:

```
{
    "user1": "Personal Access Token for user1",
    "user2": "Personal Access Token for user2"
}
```
Then you can use the user() function to set the username for subsquent operations. For example:

```
import gitingo as gi
gi.user('user1')
# make GitHub API calls as user1
gi.user('user2')
# make GitHub API calls as user2
```

## saving results
The ```get_members()``` and ```get_repos()``` functions return a list of _namedtuple_ objects. The ```write_csv()``` function can be used to write these lists to a CSV file:

```
import gitinfo as gi
ms_members = gi.get_members(org='microsoft')
gi.write_csv(ms_members, 'MicrosoftMembers.csv')
```
