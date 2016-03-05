# gitinfo

A collection of Python 3.x helper functions that make it easy to retrieve information via the GitHub API.

What it is:

* Optimized for ease of use.
* A module with one external dependency - the [requests](https://pypi.python.org/pypi/requests) library.
* Work in progress; much more to come.

What it's not:

* A complete wrapper for the GitHub API - only a few common use cases are currently supported.
* A way to do automated updates and changes; all functions are read-only.

## sample usage

Here's an example of the code for retrieving all public repos in the Microsoft organization:

![MicrosoftRepos](images/MicrosoftRepos.png)

And here's the beginning of the output for that example:

![MicrosoftReposOutput](images/MicrosoftReposOutput.png)

## authentication
You can use this module to retrieve public information from GitHub without any authentication, but the 60 requests per hour rate limit
will be enforced. You can bump that up to 5000 requests per hour by using authentication.

Only basic authentication via username and PAT (Personal Access Token) is supported at this time. To use it, put your GitHub username and a PAT in environment variables named *GitHubUser* and *GitHubPAT*, respectively.
