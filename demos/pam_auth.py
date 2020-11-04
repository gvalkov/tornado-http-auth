import tornado.ioloop
from tornado.web import RequestHandler, Application
from tornado_http_auth import DigestAuthMixin, BasicAuthMixin, auth_required

import pamela


class MainHandler(BasicAuthMixin, RequestHandler):
    @auth_required(realm="Protected", auth_func=pamela.authenticate)
    def get(self):
        self.write("Hello %s" % self._current_user)


app = Application(
    [
        (r"/", MainHandler),
    ]
)

app.listen(8888)
tornado.ioloop.IOLoop.current().start()
