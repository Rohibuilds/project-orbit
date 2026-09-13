import concurrent.futures
import json
import tempfile
import unittest
from pathlib import Path

from modules.projects import ProjectManager, safe_name
from modules.resistor_codes import decode_bands


class ResistorTests(unittest.TestCase):
    def test_standard_four_band(self):
        self.assertEqual(decode_bands(['yellow','violet','red','gold']), (4700,5))

    def test_gold_multiplier(self):
        self.assertEqual(decode_bands(['brown','black','gold','gold']), (1.0,5))

    def test_silver_multiplier(self):
        self.assertEqual(decode_bands(['brown','black','silver','silver']), (0.1,10))

    def test_invalid_band_positions(self):
        for bands in [[], ['red']*3, ['red']*5,
                      ['black','red','red','gold'],
                      ['gold','red','red','gold'],
                      ['brown','black','red','orange']]:
            with self.subTest(bands=bands):
                self.assertIsNone(decode_bands(bands))


class ProjectTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.manager = ProjectManager(self.temp.name)

    def test_same_name_never_overwrites(self):
        first = self.manager.start('demo')
        self.manager.log('keep this')
        second = self.manager.start('demo')
        self.assertNotEqual(first, second)
        old = json.loads((first/'project.json').read_text())
        self.assertIsNotNone(old['ended'])
        self.assertEqual(old['events'][-1]['message'], 'keep this')

    def test_parallel_events_are_not_lost(self):
        folder = self.manager.start('parallel')
        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
            list(pool.map(lambda n: self.manager.log(str(n)), range(80)))
        data = self.manager.metadata()
        self.assertEqual(len(data['events']), 81)
        self.assertEqual({e['message'] for e in data['events'][1:]}, {str(n) for n in range(80)})
        self.assertFalse(list(folder.glob('*.tmp')))

    def test_names_stay_inside_root(self):
        folder = self.manager.start('../../outside/file')
        self.assertEqual(folder.parent, Path(self.temp.name))
        self.assertNotIn('/', safe_name('../../outside/file'))

    def test_end_then_log_creates_new_session(self):
        first = self.manager.start('first')
        self.assertEqual(self.manager.end(), first)
        self.assertIsNone(self.manager.end())
        self.manager.log('new session')
        self.assertNotEqual(first, self.manager.current)


if __name__ == '__main__':
    unittest.main()
