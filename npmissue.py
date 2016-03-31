"""One-time report for the repos identified as having a potential vulnerability
due the NPM "unpublishing of leftpad et al" fiasco in March 2016.

Uses the npmissues.txt data file (which is not published in the repo).

gen_orgadmins() ---> Print the site admins for all affected organizations.
gen_repoadmins() --> Generate a CSV file of the repo admin team members.
npmissue_orgs() ---> Returns the list of unique orgs for affected repos.
npmissues() -------> Returns the list of repos identified by MSRC.
"""
import gitinfo
import msgithub

#-------------------------------------------------------------------------------
def gen_orgadmins():
    """Print the site admins for all affected organizations.
    """
    orglist = npmissue_orgs()
    for orgname in orglist:
        orgmembs = msgithub.orgmembers(org=orgname)
        for member in orgmembs:
            if member['site_admin']:
                print(member)

#-------------------------------------------------------------------------------
def gen_repoadmins():
    """Generate a CSV file of the repo admin team members.
    """
    npmlist = npmissues()

    gitinfo.log_config({'verbose': True, 'logfile': 'gitinfo.log'})
    gitinfo.auth_config({'username': 'msftgits'})
    gitinfo.session_start('npm issues report for MSRC')

    fhandle = open('npmissue-repoadmins.csv', 'w')
    fhandle.write('org, repo, team, teamid, login, email' + '\n')

    for repo in npmlist:
        orgname = repo.split('/')[0].rstrip()
        reponame = repo.split('/')[1].rstrip()
        print('>>>', orgname, reponame)
        admins = gitinfo.repo_admins(org=orgname, repo=reponame)
        gitinfo.log_apistatus()
        for admin in admins:
            thisline = orgname + ', ' + reponame + ', ' + \
                admin['teamname'] + ', ' + str(admin['teamid']) + ', ' + \
                admin['login'] + ', ' + admin['email']
            print(thisline)
            fhandle.write(thisline + '\n')

    fhandle.close()
    gitinfo.session_end()

#-------------------------------------------------------------------------------
def npmissue_orgs():
    """Returns a list of unique orgs for the MSRC-identified repos.
    """
    retval = [] # list of orgnames

    with open('npmissue.txt', 'r') as fhandle:
        while True:
            # read a line
            thisline = fhandle.readline().lower()[19:].replace('.git', '').rstrip()
            if not thisline:
                break
            orgname = thisline.split('/')[0].rstrip()
            if not orgname in retval:
                retval.append(orgname)

    return retval

#-------------------------------------------------------------------------------
def npmissues():
    """Returns a list of 'orgname/reponame' strings for the repos identified by
    MSRC as being potentially involved in the unpublishing issue.
    """
    retval = [] # list of orgname/reponames to be returned

    with open('npmissue.txt', 'r') as fhandle:
        while True:
            # read a line
            thisline = fhandle.readline().lower()[19:].replace('.git', '').rstrip()
            if not thisline:
                break
            retval.append(thisline)

    return retval

#-------------------------------------------------------------------------------
if __name__ == '__main__':

    #gen_repoadmins()
    gen_orgadmins()
