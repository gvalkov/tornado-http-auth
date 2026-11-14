import re
import time
import hashlib
from base64 import b64encode
from unittest import mock

from tornado_http_auth import DigestAuthMixin, BasicAuthMixin, auth_required

from tornado.testing import AsyncHTTPTestCase
from tornado.web import Application, RequestHandler


credentials = {
    'user1': 'pass1',
    'user2': 'pass2',
}


def md5(data):
    return hashlib.md5(data.encode('ascii')).hexdigest()


def parse_challenge(header):
    assert header.startswith('Digest ')
    return {k: q or b for k, q, b in re.findall(r'(\w+)=(?:"([^"]*)"|([^,\s]+))', header)}


def digest_authorization(challenge, username, password, opaque=None):
    '''Build an RFC 7616 Authorization header (MD5, qop=auth) for GET /digest.'''
    nc, cnonce, uri = '00000001', '0a4f113b', '/digest'
    ha1 = md5('%s:%s:%s' % (username, challenge['realm'], password))
    ha2 = md5('GET:%s' % uri)
    response = md5(':'.join((ha1, challenge['nonce'], nc, cnonce, 'auth', ha2)))
    return (
        'Digest username="%s", realm="%s", nonce="%s", uri="%s", qop=auth, '
        'nc=%s, cnonce="%s", response="%s", opaque="%s"'
        % (username, challenge['realm'], challenge['nonce'], uri,
           nc, cnonce, response, opaque or challenge['opaque'])
    )


class BasicAuthHandler(BasicAuthMixin, RequestHandler):
    @auth_required(realm='Protected', auth_func=credentials.get)
    def get(self):
        self.write('Hello %s' % self._current_user)


class DigestAuthHandler(DigestAuthMixin, RequestHandler):
    @auth_required(realm='Protected', auth_func=credentials.get)
    def get(self):
        self.write('Hello %s' % self._current_user)


class AuthTest(AsyncHTTPTestCase):
    def get_app(self):
        urls = [
            ('/digest', DigestAuthHandler),
            ('/basic', BasicAuthHandler),
        ]
        return Application(urls, http_client=self.http_client)

    def test_digest_auth(self):
        res = self.fetch('/digest')
        self.assertEqual(res.code, 401)
        self.assertNotIn('stale', res.headers['WWW-Authenticate'])

    def get_digest_challenge(self, age=0):
        '''Fetch a challenge as if it was issued `age` seconds ago.'''
        now = time.time() - age
        with mock.patch.object(DigestAuthMixin, 'get_time', lambda self: now):
            res = self.fetch('/digest')
        self.assertEqual(res.code, 401)
        return parse_challenge(res.headers['WWW-Authenticate'])

    def fetch_digest(self, challenge, username, password, opaque=None):
        headers = {'Authorization': digest_authorization(challenge, username, password, opaque)}
        return self.fetch('/digest', headers=headers)

    def assertChallenge(self, res, stale):
        self.assertEqual(res.code, 401)
        www = res.headers['WWW-Authenticate']
        if stale:
            self.assertIn('stale=true', www)
        else:
            self.assertNotIn('stale', www)

    def test_digest_auth_fresh_nonce(self):
        challenge = self.get_digest_challenge()

        res = self.fetch_digest(challenge, 'user1', 'pass1')
        self.assertEqual(res.code, 200)
        self.assertEqual(res.body, b'Hello user1')

        self.assertChallenge(self.fetch_digest(challenge, 'user1', 'wrong'), stale=False)
        self.assertChallenge(self.fetch_digest(challenge, 'nobody', 'pass1'), stale=False)

    def test_digest_auth_stale_nonce(self):
        age = DigestAuthMixin.DIGEST_CHALLENGE_TIMEOUT_SECONDS + 60
        challenge = self.get_digest_challenge(age)

        # Right password with an old nonce: ask the client to retry silently.
        self.assertChallenge(self.fetch_digest(challenge, 'user1', 'pass1'), stale=True)

        # Wrong password or unknown user: a normal challenge, not a stale one.
        self.assertChallenge(self.fetch_digest(challenge, 'user1', 'wrong'), stale=False)
        self.assertChallenge(self.fetch_digest(challenge, 'nobody', 'pass1'), stale=False)

    def test_digest_auth_forged_opaque(self):
        age = DigestAuthMixin.DIGEST_CHALLENGE_TIMEOUT_SECONDS + 60
        challenge = self.get_digest_challenge(age)
        forged = 'deadbeef-' + challenge['opaque'].split('-', 1)[1]

        res = self.fetch_digest(challenge, 'user1', 'pass1', opaque=forged)
        self.assertChallenge(res, stale=False)

    def test_basic_auth(self):
        res = self.fetch('/basic')
        self.assertEqual(res.code, 401)

        res = self.fetch('/basic', headers={'Authorization': 'Basic foo bar'})
        self.assertEqual(res.code, 401)

        auth = '%s:%s' % ('user1', 'pass1')
        auth = b64encode(auth.encode('ascii'))

        res = self.fetch('/basic', headers={'Authorization': 'Basic ___%s' % auth.decode('utf8')})
        self.assertEqual(res.code, 401)

        res = self.fetch('/basic', headers={'Authorization': 'Basic %s' % auth.decode('utf8')})
        self.assertEqual(res.code, 200)
