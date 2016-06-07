"""GitHub query CLI.

cli() --------------> Handle command-line arguments.
members() ----------> Get member info for an org or repo.
repos() ------------> Get repo info for an org or user.
"""
import os

import click
from click.testing import CliRunner

#------------------------------------------------------------------------------
CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])
@click.group(context_settings=CONTEXT_SETTINGS, options_metavar='<options>')
@click.version_option(version='1.0', prog_name='Photerino')
def cli():
    """\b
    _______________
      |____________  GitData CLI - retrieve data via GitHub REST API
      |____________
          |________  For command help: gitdata <command> -h/--help
          |________
    """
    click.echo('/// NOT IMPLEMENTED')

#------------------------------------------------------------------------------
@cli.command()
@click.option('-o', '--org', default='',
              help='GitHub organization', metavar='<str>')
@click.option('-r', '--repo', default='',
              help='GitHub repo', metavar='<str>')
@click.option('-a', '--auth', default='',
              help='authentication username', metavar='<str>')
@click.option('-n', '--filename', default='',
              help='output file (.csv or .txt)', metavar='<filename>')
@click.option('-f', '--fields', default='',
              help='fields to include', metavar='<fld1/fld2/etc>')
@click.option('-l', '--fieldlist', is_flag=True,
              help='list available GitHub fields')
def members(org, repo, auth, filename, fields, fieldlist):
    """Get member info for an org or repo.
    """
    click.echo('/// members subcommand')

#------------------------------------------------------------------------------
@cli.command()
@click.option('-o', '--org', default='',
              help='GitHub organization', metavar='<str>')
@click.option('-u', '--user', default='',
              help='GitHub user', metavar='<str>')
@click.option('-a', '--auth', default='',
              help='authentication username', metavar='<str>')
@click.option('-n', '--filename', default='',
              help='output file (.csv or .txt)', metavar='<filename>')
@click.option('-f', '--fields', default='',
              help='fields to include', metavar='<fld1/fld2/etc>')
@click.option('-l', '--fieldlist', is_flag=True,
              help='list available GitHub fields')
def repos(org, user, auth, filename, fields, fieldlist):
    """Get repo info for an org or user.
    """
    click.echo('/// repos subcommand')

# code to execute when running standalone: -------------------------------------
if __name__ == '__main__':
    print('/// need to implement tests here')
