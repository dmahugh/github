# gitinfo - Python 3.x library for GitHub REST API

This is a simple wrapper optimized for ease of use, supporting a subset of the GitHub API. Intended for use in automating common administrative and monitoring activities.

/// simple example

For more information, see the [documentation](documentation.md).

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

