"""GitHub query CLI.

cli() --------------> Handle command-line arguments.
"""
import os

import click
from click.testing import CliRunner

#------------------------------------------------------------------------------
@click.group()
@click.version_option(version='1.0', prog_name='Photerino')
def cli():
    """\b
    ---------------
     | ? | ? | ? |      /// gitdata
    ---------------
     | ? | ? | ? |      Retrieve data via GitHub REST API.
    ---------------
    """
    hexdump(filename=file, offset=offset, totbytes=nbytes)

#------------------------------------------------------------------------------
@cli.command()
def members():
    click.echo('/// members subcommand')

#------------------------------------------------------------------------------
@cli.command()
def repos():
    click.echo('/// repos subcommand')

# code to execute when running standalone: -------------------------------------
if __name__ == '__main__':
    print('/// need to implement tests here')
