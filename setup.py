from setuptools import setup


classifiers = [
    'Development Status :: 5 - Production/Stable',
    'Programming Language :: Python :: 2.7',
    'Programming Language :: Python :: 3',
    'License :: OSI Approved :: Apache Software License',
    'Intended Audience :: Developers',
]

kw = {
    'name':             'tornado-http-auth',
    'version':          '1.1.0',
    'description':      'Digest and basic authentication for tornado',
    'long_description': open('README.rst').read(),
    'author':           'Georgi Valkov',
    'author_email':     'georgi.t.valkov@gmail.com',
    'license':          'Apache License 2.0',
    'url':              'https://github.com/gvalkov/tornado-http-auth',
    'keywords':         'tornado digest-auth basic-auth',
    'py_modules':       ['tornado_http_auth'],
    'classifiers':      classifiers,
    'install_requires': ['tornado>=4.0.0'],
}

if __name__ == '__main__':
    setup(**kw)
