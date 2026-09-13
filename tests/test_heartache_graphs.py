import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1] / 'workflows/h3/heartache-native'


class HeartacheGraphs(unittest.TestCase):
    def test_recovered_and_parameterized_graphs_have_complete_sources(self):
        self.assertTrue((ROOT / 'manifest.json').is_file(), 'Missing recovered native graphs')
        manifest = json.loads((ROOT / 'manifest.json').read_text())
        self.assertEqual(len(manifest['graphs']), 6)
        classes = set()
        import hashlib
        for entry in manifest['graphs']:
            raw = (ROOT / entry['file']).read_bytes()
            self.assertEqual(hashlib.sha256(raw).hexdigest(), entry['sha256'])
            graph = json.loads(raw)
            self.assertEqual(len(graph), entry['node_count'])
            self.assertNotIn('/data5/', raw.decode())
            for node in graph.values():
                classes.add(node['class_type'])
                for value in node['inputs'].values():
                    if isinstance(value, list) and len(value) == 2:
                        self.assertIn(value[0], graph)
                        self.assertIsInstance(value[1], int)
        self.assertEqual(classes, set(manifest['node_sources']))
        self.assertEqual(len([x for x in manifest['node_sources'].values() if x['kind'] == 'custom']), 4)
        self.assertFalse(manifest['inference_verified'])
        for name in ['first.api.template.json', 'continue.api.template.json']:
            graph = json.loads((ROOT / name).read_text())
            self.assertEqual(graph['5']['inputs']['length'], '{{sample_frames}}')
            self.assertEqual(graph['6']['inputs']['noise_seed'], '{{seed}}')
            self.assertEqual(graph['20']['inputs']['visible_frames'], '{{visible_frames}}')
        cont = json.loads((ROOT / 'continue.api.template.json').read_text())
        self.assertEqual(cont['53']['class_type'], 'MiniMaxH3MotionContext')
        self.assertEqual(cont['53']['inputs']['context_latent'], ['50', 0])
        self.assertEqual(cont['54']['inputs']['visible_frames'], '{{visible_frames}}')


if __name__ == '__main__':
    unittest.main()
