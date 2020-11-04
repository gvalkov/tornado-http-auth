from base64 import b64encode
from tornado_http_auth import DigestAuthMixin, BasicAuthMixin, auth_required

from tornado.testing import AsyncHTTPTestCase
from tornado.web import Application, RequestHandler


credentials = {
    'user1': 'pass1',
    'user2': 'pass2',
}


class BasicAuthHandler(BasicAuthMixin, RequestHandler):
    @auth_required(realm='Protected', auth_func=credentials.get)
    def get(self):
        self.write('Hello %s' % self._current_user)

class BasicAuthWithPwdHandler(BasicAuthMixin, RequestHandler):
    @auth_required(realm='Protected', auth_func=lambda u, p: p == credentials[u])
    def get(self):
        self.write('Hello %s' % self._current_user)

class DigestAuthHandler(DigestAuthMixin, RequestHandler):
    @auth_required(realm='Protected', auth_func=credentials.get)
    def get(self):
        self.write('Hello %s' % self._current_user)

class DigestAuthWithPwdHandler(DigestAuthMixin, RequestHandler):
    @auth_required(realm='Protected', auth_func=lambda u, p: p == credentials[u])
    def get(self):
        self.write('Hello %s' % self._current_user)

class AuthTest(AsyncHTTPTestCase):
    def get_app(self):
        urls = [
            ('/digest', DigestAuthHandler),
            ('/digestpw', DigestAuthWithPwdHandler),
            ('/basic', BasicAuthHandler),
            ('/basicpw', BasicAuthWithPwdHandler),
        ]
        return Application(urls, http_client=self.http_client)

    def test_digest_auth(self):
        res = self.fetch('/digest')
        self.assertEqual(res.code, 401)
        # TODO: Add digest authentication to HTTPClient in order to test this.

    def test_digest_auth_with_pw(self):
        res = self.fetch('/digestpw')
        self.assertEqual(res.code, 401)
        # TODO: Add digest authentication to HTTPClient in order to test this.

    def test_basic_auth(self):
        res = self.fetch('/basic')
        self.assertEqual(res.code, 401)

        auth = '%s:%s' % ('user1', 'pass1')
        auth = b64encode(auth.encode('ascii'))
        hdr = {'Authorization': 'Basic %s' % auth.decode('utf8')}
        res = self.fetch('/basic', headers=hdr)
        self.assertEqual(res.code, 200)

    def test_basic_auth_with_pw(self):
        res = self.fetch('/basicpw')
        self.assertEqual(res.code, 401)

        auth = '%s:%s' % ('user1', 'pass1')
        auth = b64encode(auth.encode('ascii'))
        hdr = {'Authorization': 'Basic %s' % auth.decode('utf8')}
        res = self.fetch('/basicpw', headers=hdr)
        self.assertEqual(res.code, 200)
