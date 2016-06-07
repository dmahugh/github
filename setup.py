"""Setup program for gitdata CLI
"""
from setuptools import setup

setup(
    name='GitData',
    version='1.0',
    license='MIT License',
    author='Doug Mahugh',
    py_modules=['gitdata'],
    install_requires=[
        'Click',
    ],
    entry_points='''
        [console_scripts]
        gitdata=gitdata:cli
    '''
)