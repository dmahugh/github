<properties LandingPageTags="Python,GitHub,REST" />
![gitinfo](images/gitinfo.png)
# GitHub API helper functions

Gitinfo is a library for Python 3.x to simplify use of the GitHub REST API. It's a work in progress &mdash; pull requests, feature requests and issues welcome!

## sample usage

Here's a simple example of how to use gitinfo to write a CSV file containing a list of repos:

```python
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

## where to learn more
For more examples of how to use gitinfo, see the [overview](documentation/overview.md).

For usage details, see the [documentation](documentation/gitinfo.md).

For GitHub API details, see the [GitHub V3 API documentation](https://developer.github.com/v3/).

# gitinfo
This is the README.md that was added by clicking the "add a readme" button when viewing the ```gh-pages``` branch of ```gitinfo``` on GitHub.com.
