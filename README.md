![gitinfo](images/gitinfo.png)
# Python 3.x library for GitHub REST API

This is a simple wrapper optimized for ease of use, supporting a subset of the GitHub API. Intended for use in automating common administrative and monitoring activities. If you have suggestions for improvement, pull requests and issues are gladly accepted!

## sample usage

Here's a simple example of how to use gitinfo to write a CSV file containing a list of repos:

```
import gitinfo as gi
ms_repos = gi.repos(org='microsoft')
gi.write_csv(ms_repos, 'MicrosoftPublicRepos.csv')
```
The generated CSV file contains one row per public repo in the Microsoft organization on GitHub:

![MicrosoftPublicRepos](images/MicrosoftPublicRepos.png)

## installation

Gitinfo has one external dependency - the [requests](https://pypi.python.org/pypi/requests) library. Follow these steps to get up and running:

* Install Python 3.5 from [Python.org](https://www.python.org/).
* Clone the [Gitinfo repo](https://github.com/dmahugh/gitinfo).
* Install requests: ```pip install requests```

## learning more
For more examples of how to use gitinfo, see the [overview](overview.md).

For usage details, see the [documentation](gitinfo.md).

For GitHub API details, see the [GitHub V3 API documentation](https://developer.github.com/v3/).

