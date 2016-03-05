# github

Tools for working with the GitHub API.

This is a very early version, will be fleshed out with a bunch of things in the next few weeks.

Here's an example of listing all public repos in the Microsoft organization:

![MicrosoftRepos](images/MicrosoftRepos.png)

## authentication
You can use this module to retrieve public information from GitHub without any authentication, but the 60 requests per hour rate limit
will be enforced. You can bump that up to 5000 requests per hour by using authentication.

Only basic authentication via username and PAT (Personal Access Token) is supported at this time. To use it, put your GitHub username and a PAT in environment variables named *GitHubUser* and *GitHubPAT*, respectively.
