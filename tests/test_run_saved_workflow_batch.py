import importlib.util
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).parents[1] / "scripts" / "run_saved_workflow_batch.py"
SPEC = importlib.util.spec_from_file_location("run_saved_workflow_batch", SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class OutputDownloadSafetyTests(unittest.TestCase):
    def test_server_filename_is_flattened_inside_output_directory(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir)
            path = MODULE.local_output_path(
                output_dir,
                prompt_id="12345678-dead-beef",
                node_id="9",
                filename="../../outside.png",
            )

            self.assertEqual(path.parent, output_dir.resolve())
            self.assertEqual(path.name, "12345678_node9_outside.png")

    def test_windows_style_server_filename_is_flattened(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir)
            path = MODULE.local_output_path(
                output_dir,
                prompt_id="abcdefgh-dead-beef",
                node_id="12",
                filename=r"..\..\outside.png",
            )

            self.assertEqual(path.parent, output_dir.resolve())
            self.assertEqual(path.name, "abcdefgh_node12_outside.png")

    def test_view_url_percent_encodes_server_metadata(self):
        url = MODULE.build_view_url(
            "http://127.0.0.1:8188",
            filename="image & draft.png",
            subfolder="batch/one",
            image_type="output",
        )

        self.assertEqual(
            url,
            "http://127.0.0.1:8188/view?"
            "filename=image+%26+draft.png&subfolder=batch%2Fone&type=output",
        )


if __name__ == "__main__":
    unittest.main()
