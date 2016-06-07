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
    _______________
      |____________  GitData CLI - retrieve data via GitHub REST API
      |____________
          |________  For command help: gitdata <command> -h/--help
          |________
    """
    click.echo('/// NOT IMPLEMENTED')

#------------------------------------------------------------------------------
@cli.command()
@click.option('-a', '--auth', default='', help='GitHub username', metavar='<str>')
@click.option('-f', '--fields', default='', help='fields to include', metavar='<fld1/fld2/etc>')
@click.option('-l', '--listfields', is_flag=True, help='list available GitHub fields')
@click.option('-o', '--output', default='', help='output file (.csv or .txt)', metavar='<filename>')
def members(auth, fields, fieldlist, output):
    click.echo('/// members subcommand')

#------------------------------------------------------------------------------
@cli.command()
@click.option('-a', '--auth', default='', help='GitHub username', metavar='<str>')
@click.option('-f', '--fields', default='', help='fields to include', metavar='<fld1/fld2/etc>')
@click.option('-l', '--listfields', is_flag=True, help='list available GitHub fields')
@click.option('-o', '--output', default='', help='output file (.csv or .txt)', metavar='<filename>')
def repos(auth, fields, output):
    click.echo('/// repos subcommand')

# code to execute when running standalone: -------------------------------------
if __name__ == '__main__':
    print('/// need to implement tests here')
