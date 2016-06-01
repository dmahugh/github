"""Setup program for gitinfo
"""
from setuptools import setup

setup(
    name='Gitinfo',
    version='1.0',
    license='MIT License',
    author='Doug Mahugh',
    py_modules=['gitinfo'],
    install_requires=[
        'requests', 'pytest',
    ],
    entry_points='''
    '''
)