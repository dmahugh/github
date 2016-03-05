"""REpo LIcense VERifier - verify licenses for GitHub repos.

///INCOMPLETE

Currently is hard-coded to just go through the public Microsoft repos.
Will make this a more generic tool after it's functionally complete.
"""
import json
import requests
import github as gh

# API call to get info about the public repos
url = 'https://api.github.com/orgs/microsoft/repos'
response = requests.get(url, auth=gh.basic_auth())

if response.ok:
    thispage = json.loads(response.text)
    for repo in thispage:
        #/// write these rows to a .CSV
        print(repo['full_name'], repo['watchers'], repo['forks'], 
              repo['open_issues'], repo['default_branch'])
        #/// determine whether license file exists, include this info

#/// concatenate all pages, to get 100% of the public repos
print('rel="next" link ->', gh.link_url(response, 'next'))

# show rate-limiting status
for header in ['X-RateLimit-Limit', 'X-RateLimit-Remaining']:
    print(header + ' -> ', response.headers[header])
