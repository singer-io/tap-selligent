"""Tests for the redirect SSRF protection in tap_selligent.request().

``request`` does not follow redirects (``allow_redirects=False`` plus an explicit
3xx rejection), so an attacker-controlled ``base_url`` cannot redirect the tap to
an internal address. base_url internal-IP validation is handled upstream by
connections-service, so it is not re-tested here.

No network or live server is used: ``requests.get`` is patched.
"""

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


class RequestRedirectTest(unittest.TestCase):
    """request(): redirect handling and the allow_redirects=False contract."""

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


if __name__ == "__main__":
    unittest.main()
