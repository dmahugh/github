"""GitHub query CLI.

cli() ----------------> Handle command-line arguments.

admins() -------------> /// NOT IMPLEMENTED
collaborators --------> /// NOT IMPLEMENTED
commits --------------> /// NOT IMPLEMENTED
files ----------------> /// NOT IMPLEMENTED
members() ------------> /// NOT IMPLEMENTED
repos() --------------> Get repo info for an org or user.
repos_listfields() ---> List valid field names for repos().
teams ----------------> /// NOT IMPLEMENTED
"""
import os

import click
from click.testing import CliRunner

import gitinfo as gi

#------------------------------------------------------------------------------
CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])
@click.group(context_settings=CONTEXT_SETTINGS, options_metavar='')
@click.version_option(version='1.0', prog_name='Photerino')
def cli():
    """\b
    _____  GitData - retrieves data via GitHub REST API
     |___
       |_  syntax help: gitdata COMMAND -h/--help
    """
    pass # this is just for grouping, all functionality is in subcommands

#------------------------------------------------------------------------------
@cli.command()
def admins():
    """/// NOT IMPLEMENTED
    """
    click.echo('/// NOT IMPLEMENTED: admins()')

#------------------------------------------------------------------------------
@cli.command()
def collaborators():
    """/// NOT IMPLEMENTED
    """
    click.echo('/// NOT IMPLEMENTED: collaborators()')

#------------------------------------------------------------------------------
@cli.command()
def commits():
    """/// NOT IMPLEMENTED
    """
    click.echo('/// NOT IMPLEMENTED: commits()')

#------------------------------------------------------------------------------
@cli.command()
def files():
    """/// NOT IMPLEMENTED
    """
    click.echo('/// NOT IMPLEMENTED: files()')

#------------------------------------------------------------------------------
@cli.command()
def members():
    """/// NOT IMPLEMENTED
    """
    click.echo('/// NOT IMPLEMENTED: members()')

#------------------------------------------------------------------------------
@cli.command()
@click.option('-o', '--org', default='',
              help='GitHub organization', metavar='')
@click.option('-u', '--user', default='',
              help='GitHub user', metavar='')
@click.option('-a', '--authuser', default='',
              help='authentication username', metavar='')
@click.option('-v', '--view', default='',
              help='D=data, A=API calls, H=HTTP status codes, R=rate-limit status', metavar='')
@click.option('-n', '--filename', default='',
              help='output filename', metavar='')
@click.option('-j', '--json', is_flag=True,
              help='JSON format (default=CSV)')
@click.option('-f', '--fields', default='',
              help='fields to include', metavar='<fld1/fld2/etc>')
@click.option('-l', '--fieldlist', is_flag=True,
              help='list available GitHub fields')
def repos(org, user, authuser, view, filename, json, fields, fieldlist):
    """Get repository information.
    """
    if fieldlist:
        repos_listfields()
        return

    if not org and not user:
        click.echo('ERROR: must specify an org or user')
        return

    view = 'd' if not view else view

    if authuser:
        gi.auth_config({'username': authuser})

    if fields:
        repolist = gi.repos(org=org, user=user, fields=fields.split('/'), view_options=view)
    else:
        repolist = gi.repos(org=org, user=user, view_options=view)

    if 'd' in view.lower():
        # display data on the console
        for repo in repolist:
            values = [str(item) for item in repo]
            click.echo(click.style(','.join(values), fg='cyan'))

#------------------------------------------------------------------------------
def repos_listfields():
    """List valid field names for repos().
    """
    click.echo(click.style('\n     specified fields -->  --fields=', fg='white'), nl=False)
    click.echo(click.style('fld1/fld2/etc', fg='cyan'))
    click.echo(click.style('           ALL fields -->  --fields=', fg='white'), nl=False)
    click.echo(click.style('*', fg='cyan'))
    click.echo(click.style('              No URLs -->  --fields=', fg='white'), nl=False)
    click.echo(click.style('nourls', fg='cyan'))
    click.echo(click.style('            Only URLs -->  --fields=', fg='white'), nl=False)
    click.echo(click.style('urls', fg='cyan'))
    click.echo(click.style(60*'-', fg='blue'))
    click.echo(click.style('archive_url         git_tags_url         open_issues', fg='cyan'))
    click.echo(click.style('assignees_url       git_url              open_issues_count', fg='cyan'))
    click.echo(click.style('blobs_url           has_downloads        private', fg='cyan'))
    click.echo(click.style('branches_url        has_issues           pulls_url', fg='cyan'))
    click.echo(click.style('clone_url           has_pages            pushed_at', fg='cyan'))
    click.echo(click.style('collaborators_url   has_wiki             releases_url', fg='cyan'))
    click.echo(click.style('commits_url         homepage             size', fg='cyan'))
    click.echo(click.style('compare_url         hooks_url            ssh_url', fg='cyan'))
    click.echo(click.style('contents_url        html_url             stargazers_count', fg='cyan'))
    click.echo(click.style('contributors_url    id                   stargazers_url', fg='cyan'))
    click.echo(click.style('created_at          issue_comment_url    statuses_url', fg='cyan'))
    click.echo(click.style('default_branch      issue_events_url     subscribers_url', fg='cyan'))
    click.echo(click.style('deployments_url     issues_url           subscription_url', fg='cyan'))
    click.echo(click.style('description         keys_url             svn_url', fg='cyan'))
    click.echo(click.style('downloads_url       labels_url           tags_url', fg='cyan'))
    click.echo(click.style('events_url          language             teams_url', fg='cyan'))
    click.echo(click.style('fork                languages_url        trees_url', fg='cyan'))
    click.echo(click.style('forks               master_branch        updated_at', fg='cyan'))
    click.echo(click.style('forks_count         merges_url           url', fg='cyan'))
    click.echo(click.style('forks_url           milestones_url       watchers', fg='cyan'))
    click.echo(click.style('full_name           mirror_url           watchers_count', fg='cyan'))
    click.echo(click.style('git_commits_url     name', fg='cyan'))
    click.echo(click.style('git_refs_url        notifications_url', fg='cyan'))
    click.echo(click.style(60*'-', fg='blue'))
    click.echo(click.style('license.featured              owner.login', fg='cyan'))
    click.echo(click.style('license.key                   owner.organizations_url', fg='cyan'))
    click.echo(click.style('license.name                  owner.received_events_url', fg='cyan'))
    click.echo(click.style('license.url                   owner.repos_url', fg='cyan'))
    click.echo(click.style('owner.avatar_url              owner.site_admin', fg='cyan'))
    click.echo(click.style('owner.events_url              owner.starred_url', fg='cyan'))
    click.echo(click.style('owner.followers_url           owner.subscriptions_url', fg='cyan'))
    click.echo(click.style('owner.following_url           owner.type', fg='cyan'))
    click.echo(click.style('owner.gists_url               owner.url', fg='cyan'))
    click.echo(click.style('owner.gravatar_id             permissions.admin', fg='cyan'))
    click.echo(click.style('owner.html_url                permissions.pull', fg='cyan'))
    click.echo(click.style('owner.id                      permissions.push', fg='cyan'))

#------------------------------------------------------------------------------
def teams():
    """/// NOT IMPLEMENTED
    """
    click.echo('/// NOT IMPLEMENTED: teams()')

# code to execute when running standalone: -------------------------------------
if __name__ == '__main__':
    print('/// need to implement tests here')
