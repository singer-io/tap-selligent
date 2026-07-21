"""Tests for the SSRF protections in tap_selligent.

Covers the two pieces added to defend against the Bugcrowd-reported SSRF:

  * ``_assert_public_host`` — rejects hosts that resolve to internal/link-local
    addresses (the metadata endpoint, RFC1918, loopback, ...).
  * ``request`` — does not follow redirects (``allow_redirects=False`` plus an
    explicit 3xx rejection) and refuses to issue any request when the guard trips.

No network or live server is used: ``requests.get`` is patched, and only literal
IPs (which ``socket.getaddrinfo`` resolves without DNS) are used for the guard.
"""

import socket
import unittest
from unittest import mock

import requests

import tap_selligent as t


CONFIG = {"user_agent": "x", "api_key": "k", "organization": "o"}


def make_response(status_code, headers=None, json_body=None):
    """Build a fake requests.Response-like object for request() to consume."""
    resp = mock.Mock(name="Response")
    resp.status_code = status_code
    resp.headers = headers or {}
    resp.json.return_value = json_body
    # raise_for_status mimics requests: raises HTTPError on 4xx/5xx, else no-op.
    if 400 <= status_code < 600:
        resp.raise_for_status.side_effect = requests.exceptions.HTTPError(
            "{} Error".format(status_code))
    else:
        resp.raise_for_status.return_value = None
    return resp


class AssertPublicHostTest(unittest.TestCase):
    """_assert_public_host: which destinations are allowed vs blocked."""

    def assert_blocked(self, url):
        with self.assertRaises(ValueError):
            t._assert_public_host(url)

    def test_blocks_link_local_metadata_ip(self):
        # The exact address from the Bugcrowd report.
        self.assert_blocked("http://169.254.169.254/latest/meta-data/")

    def test_blocks_loopback(self):
        self.assert_blocked("http://127.0.0.1/sm/rest/v1/x/")

    def test_blocks_private_rfc1918(self):
        self.assert_blocked("http://10.0.0.1/x")
        self.assert_blocked("http://192.168.1.1/x")
        self.assert_blocked("http://172.16.0.1/x")

    def test_blocks_ipv6_loopback(self):
        self.assert_blocked("http://[::1]/x")

    def test_blocks_unspecified(self):
        self.assert_blocked("http://0.0.0.0/x")

    def test_allows_public_literal_ip(self):
        # Should not raise.
        t._assert_public_host("http://8.8.8.8/sm/rest/v1/x/")

    def test_rejects_url_without_host(self):
        self.assert_blocked("not-a-url")

    def test_rejects_unresolvable_host(self):
        with mock.patch("tap_selligent.socket.getaddrinfo",
                        side_effect=socket.gaierror("no such host")):
            self.assert_blocked("http://does-not-resolve.example/x")

    def test_blocks_public_hostname_resolving_to_internal(self):
        # A public-looking hostname whose DNS answer is an internal IP is still
        # blocked. (The residual DNS-rebinding gap is the *second* resolution
        # done by requests at connect time, which is out of scope.)
        internal = [(socket.AF_INET, socket.SOCK_STREAM, 6, "",
                     ("169.254.169.254", 0))]
        with mock.patch("tap_selligent.socket.getaddrinfo", return_value=internal):
            self.assert_blocked("http://sneaky.example.com/x")


class RequestRedirectTest(unittest.TestCase):
    """request(): redirect handling and the allow_redirects=False contract.

    The host guard is patched to a no-op here so we exercise the redirect logic
    in isolation (see GuardBeforeRequestTest for the guard-integration case).
    """

    def setUp(self):
        guard_patcher = mock.patch("tap_selligent._assert_public_host",
                                   return_value=None)
        self.mock_guard = guard_patcher.start()
        self.addCleanup(guard_patcher.stop)

    def test_get_is_called_with_allow_redirects_false(self):
        with mock.patch("tap_selligent.requests.get",
                        return_value=make_response(200)) as mock_get:
            t.request("https://api.example.com/sm/rest/v1/x/", CONFIG)
        self.assertFalse(mock_get.call_args.kwargs["allow_redirects"])

    def test_302_raises_and_names_the_redirect_target(self):
        location = "http://169.254.169.254/latest/meta-data/"
        resp = make_response(302, headers={"Location": location})
        with mock.patch("tap_selligent.requests.get", return_value=resp):
            with self.assertRaises(RuntimeError) as ctx:
                t.request("https://api.example.com/sm/rest/v1/x/", CONFIG)
        self.assertIn("Refusing to follow redirect", str(ctx.exception))
        self.assertIn(location, str(ctx.exception))
        # The 3xx branch must fire before raise_for_status (which ignores 3xx).
        resp.raise_for_status.assert_not_called()

    def test_301_also_refused(self):
        resp = make_response(301, headers={"Location": "https://elsewhere/"})
        with mock.patch("tap_selligent.requests.get", return_value=resp):
            with self.assertRaises(RuntimeError):
                t.request("https://api.example.com/sm/rest/v1/x/", CONFIG)

    def test_200_returns_response(self):
        resp = make_response(200, json_body={"data": [{"id": 1}]})
        with mock.patch("tap_selligent.requests.get", return_value=resp):
            out = t.request("https://api.example.com/sm/rest/v1/x/", CONFIG)
        self.assertIs(out, resp)
        self.assertEqual(out.json()["data"][0]["id"], 1)

    def test_500_still_raises_http_error(self):
        resp = make_response(500)
        with mock.patch("tap_selligent.requests.get", return_value=resp):
            with self.assertRaises(requests.exceptions.HTTPError):
                t.request("https://api.example.com/sm/rest/v1/x/", CONFIG)


class GuardBeforeRequestTest(unittest.TestCase):
    """The guard runs before any network call, so an internal base_url never
    results in an outbound request."""

    def test_internal_url_makes_no_outbound_request(self):
        with mock.patch("tap_selligent.requests.get") as mock_get:
            with self.assertRaises(ValueError):
                t.request("http://169.254.169.254/sm/rest/v1/x/", CONFIG)
        mock_get.assert_not_called()


if __name__ == "__main__":
    unittest.main()
