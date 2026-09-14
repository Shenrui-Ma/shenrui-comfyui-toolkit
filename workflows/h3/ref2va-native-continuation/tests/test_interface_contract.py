"""Contract checks for the H3 native continuation execution package.

These only read the package's own metadata. They do not start ComfyUI, load
weights or reach the network, so passing them says the interface and the
dependency pins are self-consistent, not that the chain runs.
"""

import json
import re
import unittest
from pathlib import Path

PACKAGE = Path(__file__).parents[1]
INTERFACE = json.loads((PACKAGE / "interface.json").read_text(encoding="utf-8"))
DEPENDENCIES = json.loads((PACKAGE / "dependencies.lock.json").read_text(encoding="utf-8"))
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
COMMIT_RE = re.compile(r"^[0-9a-f]{40}$")
UPSTREAM_REPO = "https://github.com/NikoDemon80/ComfyUI-H3-Motion-Context"
# Anything that looks like a machine-local absolute path or a private host.
PRIVATE_RE = re.compile(r"(/Users/|/home/[a-z]|C:\\\\|192\.168\.|10\.\d+\.\d+\.\d+)")


class InterfacePinTests(unittest.TestCase):
    def test_package_files_agree_on_workflow_id(self):
        workflow_id = f"h3-{PACKAGE.name}"
        self.assertEqual(INTERFACE["workflow_id"], workflow_id)
        self.assertEqual(DEPENDENCIES["workflow_id"], workflow_id)

    def test_graph_is_pinned_upstream_not_vendored(self):
        graph = INTERFACE["graph"]
        self.assertEqual(graph["location"], "upstream")
        self.assertEqual(graph["repository"], UPSTREAM_REPO)
        self.assertRegex(graph["commit"], COMMIT_RE)
        self.assertRegex(graph["sha256"], SHA256_RE)
        self.assertEqual(graph["license"], "GPL-3.0")

    def test_dependency_pin_matches_interface_pin(self):
        pack = DEPENDENCIES["node_packs"][0]
        self.assertEqual(pack["repository"], UPSTREAM_REPO)
        self.assertEqual(pack["commit"], INTERFACE["graph"]["commit"])
        self.assertEqual(pack["tag"], INTERFACE["graph"]["tag"])
        self.assertFalse(pack["vendored"])

    def test_node_classes_match_the_dependency_lock(self):
        listed = sorted(node["class"] for node in INTERFACE["nodes"])
        pinned = sorted(DEPENDENCIES["node_packs"][0]["required_node_classes"])
        self.assertEqual(listed, pinned)

    def test_every_node_declares_a_role(self):
        for node in INTERFACE["nodes"]:
            self.assertTrue(node.get("role"), node.get("class"))

    def test_recovery_covers_a_missing_node_and_a_seam_problem(self):
        symptoms = " ".join(entry["symptom"] for entry in INTERFACE["recovery"])
        self.assertIn("节点", symptoms)
        self.assertIn("接缝", symptoms)


class HonestyTests(unittest.TestCase):
    def test_package_states_it_was_not_run_here(self):
        scope = INTERFACE["verified"]["by_this_repository"]
        self.assertIn("未执行", scope)

    def test_no_python_outside_tests(self):
        self.assertEqual([p for p in PACKAGE.rglob("*.py") if "tests" not in p.parts], [])

    def test_no_private_paths_or_hosts_in_package_text(self):
        for path in sorted(PACKAGE.rglob("*")):
            if not path.is_file() or path.suffix not in (".json", ".md"):
                continue
            text = path.read_text(encoding="utf-8", errors="replace")
            self.assertIsNone(PRIVATE_RE.search(text), path.name)

    def test_unknown_model_files_stay_null_rather_than_guessed(self):
        for role, model in DEPENDENCIES["models"].items():
            if model["sha256"] is None:
                self.assertIsNone(model["filename"], role)
            else:
                self.assertRegex(model["sha256"], SHA256_RE)


if __name__ == "__main__":
    unittest.main()
