import os
import unittest
from pipeline.launch import launch_command


class TestNamespaceLaunch(unittest.TestCase):
    def test_launch_command_configures_demo_environment(self):
        command, env = launch_command('demo', 8510, '127.0.0.1')
        self.assertIn('pipeline', command[4])
        self.assertEqual(env['PIPELINE_MODE'], 'demo')
        self.assertEqual(env['DEMO_MODE'], 'true')
        self.assertIn('--client.toolbarMode', command)
        self.assertIn('minimal', command)
