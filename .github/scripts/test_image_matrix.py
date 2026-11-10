import base64
import unittest
from unittest.mock import patch

import image_matrix

REPO = 'Pinchana/telegram-bot-api'
RUN = {'id': 123, 'status': 'completed', 'conclusion': 'success', 'event': 'push',
       'head_branch': 'master', 'path': '.github/workflows/build.yml', 'head_sha': 'a' * 40,
       'head_repository': {'full_name': REPO}}


class MatrixTests(unittest.TestCase):
    def test_all_version_tags_and_master_are_selected(self):
        with patch.object(image_matrix, 'api', return_value=[[{'name': 'v10.3'}, {'name': 'v10.2'}, {'name': 'v10.1'}, {'name': 'not-version'}]]), \
                patch.object(image_matrix, 'release', side_effect=lambda repo, tag: {'ref': tag}) as release, \
                patch.object(image_matrix, 'master', return_value={'ref': 'master'}):
            entries = image_matrix.select(REPO, {}, 'all')
        self.assertEqual([item['ref'] for item in entries], ['v10.3', 'v10.2', 'v10.1', 'master'])
        self.assertEqual(release.call_count, 3)

    def test_pull_request_or_fork_cannot_publish(self):
        for run in [{**RUN, 'event': 'pull_request'}, {**RUN, 'head_repository': {'full_name': 'attacker/fork'}}]:
            with self.subTest(run=run), patch.object(image_matrix, 'api') as api, self.assertRaises(ValueError):
                image_matrix.select(REPO, {'workflow_run': run}, 'all')
            api.assert_not_called()

    def test_failed_or_wrong_workflow_cannot_publish_master(self):
        for run in [{**RUN, 'conclusion': 'failure'}, {**RUN, 'path': 'untrusted.yml'}]:
            with self.subTest(run=run), patch.object(image_matrix, 'api', return_value=run), self.assertRaises(ValueError):
                image_matrix.master(REPO, '123')

    def test_expired_master_binary_is_rejected(self):
        with patch.object(image_matrix, 'api', side_effect=[RUN, {'artifacts': [{'name': 'telegram-bot-api-linux-x86_64', 'expired': True}]}]), self.assertRaises(ValueError):
            image_matrix.master(REPO, '123')

    def test_release_digest_is_required(self):
        with patch.object(image_matrix, 'api', return_value={'assets': [{'name': 'telegram-bot-api', 'digest': None}]}), self.assertRaises(ValueError):
            image_matrix.release(REPO, 'v10.3')

    def test_mismatched_release_version_is_rejected(self):
        asset = {'assets': [{'name': 'telegram-bot-api', 'digest': 'sha256:' + 'b' * 64}]}
        cmake = {'content': base64.b64encode(b'project(TelegramBotApi VERSION 10.2 LANGUAGES CXX)').decode()}
        with patch.object(image_matrix, 'api', side_effect=[asset, {'sha': 'a' * 40}, cmake]), self.assertRaises(ValueError):
            image_matrix.release(REPO, 'v10.3')

    def test_versioned_images_never_overwrite_latest(self):
        asset = {'assets': [{'name': 'telegram-bot-api', 'digest': 'sha256:' + 'b' * 64}]}
        cmake = {'content': base64.b64encode(b'project(TelegramBotApi VERSION 10.3 LANGUAGES CXX)').decode()}
        with patch.object(image_matrix, 'api', side_effect=[asset, {'sha': 'a' * 40}, cmake]):
            image = image_matrix.release(REPO, 'v10.3')
        self.assertEqual(image['tags'], 'ghcr.io/pinchana/telegram-bot-api:v10.3,ghcr.io/pinchana/telegram-bot-api:10.3')
        self.assertNotIn('latest', image['tags'])
