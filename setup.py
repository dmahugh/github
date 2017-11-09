"""Setup program for gitdata CLI
"""
from setuptools import setup

setup(
    name='GitData',
    version='2.0',
    license='MIT License',
    author='Doug Mahugh',
    py_modules=['gitdata'],
    install_requires=[
        'Click',
        'Requests'
    ],
    entry_points='''
        [console_scripts]
        gitdata=gitdata:cli
    '''
)