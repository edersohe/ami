from setuptools import setup

requirements = open('requirements.txt').readlines()

setup(
    name='ami',
    version='0.0.1a',
    author='Eder Sosa',
    author_email='eder.sohe@gmail.com',
    description='Asterisk Manager Interface Client and Parser',
    py_modules=['ami'],
    install_requires=requirements,
    license='MIT',
    url='https://github.com/edersohe/ami'
)
