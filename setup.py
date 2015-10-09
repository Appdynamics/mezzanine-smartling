import os
from setuptools import setup

with open(os.path.join(os.path.dirname(__file__), 'README.rst')) as readme:
    README = readme.read()

# allow setup.py to be run from any path
os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))
#os.system("pip install -e 'git+https://github.com/Smartling/api-sdk-python/tarball/master#egg=SmartlingApiSdk-1.2.5'")
setup(
    name='mezzanine-smartling',
    version='0.1',
    packages=['mezzanine_smartling'],
    include_package_data=True,
    license='Apache License 2.0',
    description='Send Mezzanine Page and Django model contents to Smartling for translations. When the translation is finished the page is saved into an admin view in which it pends for site specific approval.',
    install_requires = [
        'Mezzanine>=3.1.8',
        'SmartlingApiSdk'
    ],
    dependency_links=[
        'https://github.com/Smartling/api-sdk-python/tarball/master#egg=SmartlingApiSdk-1.2.5'
    ],
    long_description=README,
    url='',
    author='Craig Williams',
    author_email='craigdub746@gmail.com',
    classifiers=[
        'Environment :: Web Environment',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.2',
        'Programming Language :: Python :: 3.3',
        'License :: OSI Approved :: Apache Software License',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
    ],
)