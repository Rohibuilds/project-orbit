import importlib.util
import os
import tempfile
import unittest
from unittest.mock import patch

HAS_DEPS = all(importlib.util.find_spec(x) for x in ['flask','cv2','requests'])

@unittest.skipUnless(HAS_DEPS, 'Install application dependencies to run Flask/camera boundary tests')
class ApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.storage = tempfile.TemporaryDirectory()
        os.environ['ORBIT_HEADLESS'] = '1'
        os.environ['ORBIT_PROJECTS_DIR'] = cls.storage.name
        import orbit
        cls.orbit = orbit
        cls.client = orbit.app.test_client()

    @classmethod
    def tearDownClass(cls):
        cls.orbit.vision.close()
        cls.storage.cleanup()

    def test_dashboard(self):
        self.assertEqual(self.client.get('/').status_code, 200)

    def test_rejects_bad_command_types(self):
        for data in [[], {'text': []}, {'text': 42}, {}, {'text': ''}, {'text': 'x'*2001}]:
            with self.subTest(data=data):
                self.assertEqual(self.client.post('/command',json=data).status_code, 400)

    def test_missing_camera_returns_503(self):
        self.assertEqual(self.client.get('/video').status_code, 503)

    def test_project_commands(self):
        response=self.client.post('/command',json={'text':'start project Demo'})
        self.assertTrue(response.json['ok'])
        self.assertIsNotNone(self.client.get('/state').json['project'])
        response=self.client.post('/command',json={'text':'end project'})
        self.assertEqual(response.status_code,200)
        self.assertIsNone(self.client.get('/state').json['project'])

    def test_end_closes_video_writer(self):
        with patch.object(self.orbit.vision,'stop_recording') as stop:
            self.client.post('/command',json={'text':'end project'})
            stop.assert_called_once()

    def test_camera_encoder_failure_not_reported_as_recording(self):
        import numpy as np
        with patch.object(self.orbit,'current_frame',return_value=np.zeros((20,20,3),dtype=np.uint8)), patch.object(self.orbit.vision,'start_recording',return_value=None):
            response=self.client.post('/command',json={'text':'start recording'})
            self.assertIn('could not start',response.json['response'])
            self.assertFalse(self.orbit.state['recording'])

    def test_ai_answer_is_visible(self):
        with patch.object(self.orbit.ai,'ask',return_value='A resistor limits current.'):
            response=self.client.post('/command',json={'text':'What is a resistor?'})
            self.assertEqual(response.json['response'],'A resistor limits current.')

    def test_failed_photo_write(self):
        import numpy as np
        from pathlib import Path
        with patch('modules.vision.cv2.imwrite',return_value=False):
            self.assertIsNone(self.orbit.vision.snapshot(Path(self.storage.name),np.zeros((10,10,3),dtype=np.uint8)))
