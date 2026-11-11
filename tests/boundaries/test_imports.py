"""Boundary tests — B01: contracts have no runtime imports."""

import ast
import pathlib


class TestImportBoundaries:
    def _get_imports(self, filepath):
        """Extract module-level imports from a Python file."""
        with open(filepath) as f:
            tree = ast.parse(f.read())
        imports = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.add(alias.name)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imports.add(node.module)
        return imports

    RUNTIME_MODULES = {
        "system.storage.artifact_store",
        "system.storage.receipt_store",
        "system.storage.checkpoint_store",
        "system.host.policy_enforce",
        "system.host.workflow_control",
        "system.host.effect_executor",
        "system.host.specification_freezer",
        "system.host.package_lock",
        "system.host.build_admission",
        "system.host.scanner_gateway",
        "system.host.recovery",
        "system.storage.event_store",
        "system.host.loaders",
    }

    def test_contracts_no_runtime_imports(self):
        """B01: Contract modules do not import runtime modules."""
        contracts_dir = pathlib.Path("contracts")
        assert contracts_dir.is_dir(), "contract source root missing"
        files = sorted(path for path in contracts_dir.rglob("*.py") if path.name != "__init__.py")
        assert files, "boundary test cannot pass without scanning contract modules"
        for py_file in files:
            if py_file.name == "__init__.py":
                continue
            imports = self._get_imports(py_file)
            for imp in imports:
                for rt_mod in self.RUNTIME_MODULES:
                    if imp == rt_mod or imp.startswith(rt_mod + "."):
                        raise AssertionError(f"contract {py_file} imports runtime module {imp}")

    def test_validation_no_io_imports(self):
        """B01b: Validation modules do not import IO modules."""
        validation_dir = pathlib.Path("contracts/workflow/validation")
        assert validation_dir.is_dir(), "validation source root missing"
        assert any(validation_dir.rglob("*.py")), "validation boundary must scan source files"
        io_modules = {"sqlite3", "os", "pathlib", "shutil", "subprocess", "socket"}
        for py_file in validation_dir.rglob("*.py"):
            if py_file.name == "__init__.py":
                continue
            imports = self._get_imports(py_file)
            for imp in imports:
                root = imp.split(".")[0]
                if root in io_modules:
                    raise AssertionError(f"validation module {py_file} imports IO module {imp}")


def test_non_restoration_policy_blocks_removed_and_competing_sources() -> None:
    from scripts.check_retired_paths import forbidden_paths

    paths = (
        "contracts/workflow/common.py",
        "mvp/service.py",
        ".agents/contracts/workflow.yaml",
        "agent/runtime/controller.py",
        "conftest.py",
        "MVP/api.py",
    )
    assert forbidden_paths(paths) == tuple(sorted(paths[1:]))
    assert forbidden_paths(("system/host/scanner_gateway.py", "agent/skills/builder/file_operations.py")) == ()
