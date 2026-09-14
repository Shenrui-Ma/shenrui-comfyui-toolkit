"""Contract tests for the RMBG-2.0 alpha package. Offline, metadata only."""
import json
import re
import unittest
from pathlib import Path

P = Path(__file__).resolve().parents[1]
TOKEN = re.compile(r'\{\{([A-Za-z_][A-Za-z0-9_]*)\}\}')
PRIVATE = re.compile(r'(?:/Users/|/home/[a-z]|/data\d+/|[A-Za-z]:\\\\|[0-9]{1,3}(?:\.[0-9]{1,3}){3})')
FORBIDDEN = ['__CHARACTER_IMAGE__', '__OUTPUT_PREFIX__', 'heartache', 'yaoguang', 'seg0', 'seg1']


def load(name):
    return json.loads((P / name).read_text(encoding='utf-8'))


class GraphContractTests(unittest.TestCase):
    def test_graph_is_parseable_and_parameterized(self):
        graph = load('api.template.json')
        self.assertEqual(len(graph), 4)
        for node in graph.values():
            self.assertIn('class_type', node)
        text = (P / 'api.template.json').read_text(encoding='utf-8')
        for bad in FORBIDDEN:
            self.assertNotIn(bad, text, bad)

    def test_every_placeholder_is_declared(self):
        graph = load('api.template.json')
        callers = set(load('interface.json')['caller_inputs'])
        used = set(TOKEN.findall(json.dumps(graph)))
        self.assertEqual(used, callers, used ^ callers)

    def test_nodes_match_the_interface(self):
        graph = load('api.template.json')
        declared = {n['class_type'] for n in load('interface.json')['nodes']}
        found = {n['class_type'] for n in graph.values()}
        self.assertEqual(declared, found)

    def test_alpha_and_mask_slots_are_documented(self):
        graph = load('api.template.json')
        slots = {n['inputs']['images'][1] for n in graph.values() if n['class_type'] == 'SaveImage'}
        self.assertEqual(slots, {0, 2})
        notes = ' '.join(load('interface.json')['notes']) + (P/'README.md').read_text(encoding='utf-8')
        self.assertIn('slot 2', notes)

    def test_fixed_bindings_are_the_graph_values(self):
        graph = load('api.template.json')
        rmbg = next(n for n in graph.values() if n['class_type'] == 'RMBG')
        fixed = load('interface.json')['fixed_bindings']
        for key, value in fixed.items():
            self.assertEqual(rmbg['inputs'][key], value, key)


class DependencyTests(unittest.TestCase):
    def test_dependency_lock_pins_node_and_model(self):
        deps = load('dependencies.lock.json')
        self.assertEqual(len(deps['node_packs']), 1)
        node = deps['node_packs'][0]
        self.assertRegex(node['revision'], r'^[0-9a-f]{40}$')
        self.assertEqual(node['class_type'], 'RMBG')
        model = deps['models'][0]
        self.assertRegex(model['revision'], r'^[0-9a-f]{40}$')
        for f in model['files']:
            self.assertRegex(f['sha256'], r'^[0-9a-f]{64}$')
            self.assertGreater(f['bytes'], 0)

    def test_workflow_ids_agree(self):
        ids = {load('interface.json')['workflow_id'], load('dependencies.lock.json')['workflow_id']}
        self.assertEqual(len(ids), 1)

    def test_licences_are_separated(self):
        deps = load('dependencies.lock.json')
        self.assertIn('GPL-3.0', deps['node_packs'][0]['license'])
        self.assertIn('NC', deps['license_notice'])


class HygieneTests(unittest.TestCase):
    def test_no_private_paths_or_credentials(self):
        # 跳过测试自身：它必须写出这些模式才能检查
        for f in P.rglob('*'):
            if f.is_file() and f.suffix in ('.json', '.md', '.py') and 'tests' not in f.parts:
                text = f.read_text(encoding='utf-8', errors='replace')
                self.assertIsNone(PRIVATE.search(text), f)

    def test_no_python_outside_tests(self):
        self.assertEqual([str(f.relative_to(P)) for f in P.rglob('*.py') if 'tests' not in f.parts], [])

    def test_status_does_not_claim_a_clean_run(self):
        text = (P / 'README.md').read_text(encoding='utf-8')
        self.assertIn('不是', text)
        self.assertIn('没有在干净环境跑过', text)


if __name__ == '__main__':
    unittest.main()
