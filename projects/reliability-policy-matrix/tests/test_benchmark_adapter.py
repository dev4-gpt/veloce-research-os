from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from rpmatrix.benchmark_adapter import OSWorldAdapter, adapter_for_benchmark


class BenchmarkAdapterTest(unittest.TestCase):
    def test_osworld_stub_loads_manifest_tasks(self) -> None:
        tasks = OSWorldAdapter("manifests/osworld_subset.jsonl").load_tasks()
        self.assertGreaterEqual(len(tasks), 1)
        self.assertEqual(tasks[0].source, "osworld_subset")
        self.assertTrue(tasks[0].task_id)

    def test_adapter_factory_uses_osworld_adapter(self) -> None:
        adapter = adapter_for_benchmark("osworld_subset")
        self.assertEqual(adapter.name, "osworld")


if __name__ == "__main__":
    unittest.main()
