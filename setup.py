import atexit
import os
from setuptools import setup, find_packages
from setuptools.command.install import install

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()


setup(
    name='django-automatic-crud',
    version='2.0.1',
    packages=find_packages(),
    package_data={
        'automatic_crud': ['locale/*/LC_MESSAGES/*.mo', ]
    },
    include_package_data=True,
    license='BSD License',
    description='Django Automatic CRUDs',
    long_description=long_description,
    long_description_content_type="text/markdown",
    url='https://github.com/developerpe/django-automatic-crud',
    author='Oliver Sandoval, Andrés Vanegas',
    author_email='developerpeperu@gmail.com, wandres.vanegas@gmail.com',
    install_requires=[
        'Django>=3.0',
        'openpyxl==3.0.7',
    ],
    classifiers=[
        'Environment :: Web Environment',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3.3'
    ]
)
