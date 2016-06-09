"""GitHub query CLI.

cli() ----------------> Handle command-line arguments.
members() ------------> Get member info for an org or repo.
members_listfields() -> List valid field names for members().
repos() --------------> Get repo info for an org or user.
repos_listfields() ---> List valid field names for repos().
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
@click.option('-o', '--org', default='',
              help='GitHub organization', metavar='')
@click.option('-r', '--repo', default='',
              help='GitHub repo', metavar='')
@click.option('-a', '--authuser', default='',
              help='authentication username', metavar='')
@click.option('-v', '--view', default='',
              help='D=data, A=API calls, H=HTTP status', metavar='')
@click.option('-n', '--filename', default='',
              help='output filename', metavar='')
@click.option('-j', '--json', is_flag=True,
              help='JSON format (default=CSV)')
@click.option('-f', '--fields', default='',
              help='fields to include', metavar='<fld1/fld2/etc>')
@click.option('-l', '--fieldlist', is_flag=True,
              help='list available GitHub fields')
def members(org, repo, authuser, view, filename, json, fields, fieldlist):
    """Get member info for an org or repo.
    """
    if fieldlist:
        members_listfields()
        return

    if not org:
        click.echo('ERROR: must specify an org')
        return

    if authuser:
        gi.auth_config({'username': authuser})

    click.echo('/// members subcommand')

#------------------------------------------------------------------------------
def members_listfields():
    """List valid field names for members().
    """
    click.echo('\nValid GitHub API field names for MEMBERS:\n' + 60*'-')
    click.echo('id                  events_url          organizations_url')
    click.echo('login               followers_url       received_events_url')
    click.echo('site_admin          following_url       repos_url')
    click.echo('type                gists_url           starred_url')
    click.echo('url                 gravatar_id         subscriptions_url')
    click.echo('avatar_url          html_url')

#------------------------------------------------------------------------------
@cli.command()
@click.option('-o', '--org', default='',
              help='GitHub organization', metavar='')
@click.option('-u', '--user', default='',
              help='GitHub user', metavar='')
@click.option('-a', '--authuser', default='',
              help='authentication username', metavar='')
@click.option('-v', '--view', default='',
              help='D=data, A=API calls, H=HTTP status', metavar='')
@click.option('-n', '--filename', default='',
              help='output filename', metavar='')
@click.option('-j', '--json', is_flag=True,
              help='JSON format (default=CSV)')
@click.option('-f', '--fields', default='',
              help='fields to include', metavar='<fld1/fld2/etc>')
@click.option('-l', '--fieldlist', is_flag=True,
              help='list available GitHub fields')
def repos(org, user, authuser, view, filename, json, fields, fieldlist):
    """Get repo info for an org or user.
    """
    if fieldlist:
        repos_listfields()
        return

    if not org and not user:
        click.echo('ERROR: must specify an org or user')
        return

    if authuser:
        gi.auth_config({'username': authuser})

    if fields:
        repolist = gi.repos(org=org, user=user, fields=fields.split('/'))
    else:
        repolist = gi.repos(org=org, user=user)

    for repo in repolist:
        values = [str(item) for item in repo]
        click.echo(click.style(','.join(values), fg='cyan'))

#------------------------------------------------------------------------------
def repos_listfields():
    """List valid field names for repos().
    """
    click.echo(click.style('\n     specified fields -->  --fields=fld1/fld2/etc', fg='cyan'))
    click.echo(click.style('           ALL fields -->  --fields=*', fg='cyan'))
    click.echo(click.style('              No URLs -->  --fields=nourls', fg='cyan'))
    click.echo(click.style('            Only URLs -->  --fields=urls', fg='cyan'))
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
    click.echo(click.style('license.featured              permissions.admin', fg='cyan'))
    click.echo(click.style('license.key                   permissions.pull', fg='cyan'))
    click.echo(click.style('license.name                  permissions.push', fg='cyan'))
    click.echo(click.style('license.url', fg='cyan'))
    click.echo(click.style(60*'-', fg='blue'))
    click.echo(click.style('owner.avatar_url              owner.organizations_url', fg='cyan'))
    click.echo(click.style('owner.events_url              owner.received_events_url', fg='cyan'))
    click.echo(click.style('owner.followers_url           owner.repos_url', fg='cyan'))
    click.echo(click.style('owner.following_url           owner.site_admin', fg='cyan'))
    click.echo(click.style('owner.gists_url               owner.starred_url', fg='cyan'))
    click.echo(click.style('owner.gravatar_id             owner.subscriptions_url', fg='cyan'))
    click.echo(click.style('owner.html_url                owner.type', fg='cyan'))
    click.echo(click.style('owner.id                      owner.url', fg='cyan'))
    click.echo(click.style('owner.login', fg='cyan'))

# code to execute when running standalone: -------------------------------------
if __name__ == '__main__':
    print('/// need to implement tests here')
