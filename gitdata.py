"""GitHub query CLI.

cli() --------------> Handle command-line arguments.
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
    ---------------
     | ? | ? | ? |      /// gitdata
    ---------------
     | ? | ? | ? |      Retrieve data via GitHub REST API.
    ---------------
    """
    click.echo('/// NOT IMPLEMENTED')

#------------------------------------------------------------------------------
@cli.command()
@click.option('-a', '--auth', default='', help='GitHub username', metavar='<str>')
def members(auth):
    click.echo('/// members subcommand')

#------------------------------------------------------------------------------
@cli.command()
@click.option('-a', '--auth', default='', help='GitHub username', metavar='<str>')
def repos(auth):
    click.echo('/// repos subcommand')

# code to execute when running standalone: -------------------------------------
if __name__ == '__main__':
    print('/// need to implement tests here')
