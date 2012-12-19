from setuptools import setup, find_packages

setup(
    name="chocolate",
    version="0.1",
    packages = find_packages(),
    package_data={
        'chocolate' : [
            '*.*',
        ]
    },
    requires=[
        'mock',
    ],
    install_requires=[
        'mock',
    ],
    long_description="Mockup data generation for django and django-tastypie"
)

