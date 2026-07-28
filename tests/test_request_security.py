import unittest
from unittest.mock import Mock, patch

import tap_selligent


class RequestSecurityTests(unittest.TestCase):
    def setUp(self):
        self.config = {
            'user_agent': 'tap-selligent (security@test.local)',
            'api_key': 'test-api-key',
            'organization': 'test-org'
        }
        self.url = 'https://example.selligent.test/sm/rest/v1/programs/'

    @patch('tap_selligent.requests.get')
    def test_request_disables_redirect_following(self, get_mock):
        response = Mock()
        response.status_code = 200
        response.is_redirect = False
        response.raise_for_status = Mock()
        get_mock.return_value = response

        tap_selligent.request(self.url, self.config, {})

        _, kwargs = get_mock.call_args
        self.assertFalse(kwargs['allow_redirects'])
        response.raise_for_status.assert_called_once_with()

    @patch('tap_selligent.logger.fatal')
    @patch('tap_selligent.requests.get')
    def test_request_blocks_redirect_responses(self, get_mock, logger_fatal_mock):
        response = Mock()
        response.status_code = 302
        response.is_redirect = True
        response.headers = {
            'Location': 'http://169.254.169.254/latest/meta-data/iam/security-credentials/'
        }
        response.raise_for_status = Mock()
        get_mock.return_value = response

        with self.assertRaises(RuntimeError):
            tap_selligent.request(self.url, self.config, {})

        response.raise_for_status.assert_not_called()
        logger_fatal_mock.assert_called_once()

    @patch('tap_selligent.requests.get')
    def test_request_follows_same_origin_redirect_with_limit(self, get_mock):
        redirect_response = Mock()
        redirect_response.status_code = 302
        redirect_response.is_redirect = True
        redirect_response.headers = {
            'Location': '/sm/rest/v1/programs/?page=1'
        }
        redirect_response.raise_for_status = Mock()

        ok_response = Mock()
        ok_response.status_code = 200
        ok_response.is_redirect = False
        ok_response.headers = {}
        ok_response.raise_for_status = Mock()

        get_mock.side_effect = [redirect_response, ok_response]

        config = dict(self.config)
        config['max_redirects'] = 1

        result = tap_selligent.request(self.url, config, {'limit': 10000})

        self.assertEqual(result, ok_response)
        self.assertEqual(get_mock.call_count, 2)

    @patch('tap_selligent.logger.fatal')
    @patch('tap_selligent.requests.get')
    def test_request_blocks_excessive_redirect_chain(self, get_mock, logger_fatal_mock):
        redirect_response_1 = Mock()
        redirect_response_1.status_code = 302
        redirect_response_1.is_redirect = True
        redirect_response_1.headers = {
            'Location': '/sm/rest/v1/programs/?page=1'
        }
        redirect_response_1.raise_for_status = Mock()

        redirect_response_2 = Mock()
        redirect_response_2.status_code = 302
        redirect_response_2.is_redirect = True
        redirect_response_2.headers = {
            'Location': '/sm/rest/v1/programs/?page=2'
        }
        redirect_response_2.raise_for_status = Mock()

        get_mock.side_effect = [redirect_response_1, redirect_response_2]

        config = dict(self.config)
        config['max_redirects'] = 1

        with self.assertRaises(RuntimeError):
            tap_selligent.request(self.url, config, {})

        self.assertEqual(get_mock.call_count, 2)
        logger_fatal_mock.assert_called_once()


if __name__ == '__main__':
    unittest.main()