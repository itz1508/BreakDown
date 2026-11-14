"""Boundary tests ??? B01: contracts have no runtime imports."""

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
        "agent.skills.shared.storage.artifact_store",
        "agent.skills.shared.storage.receipt_store",
        "agent.skills.shared.storage.checkpoint_store",
        "agent.skills.shared.host.sys_policy_enforcer",
        "agent.skills.shared.host.sys_controller",
        "agent.skills.builder.effect_executor",
        "agent.skills.planner.specification_freezer",
        "agent.skills.builder.package_lock",
        "agent.skills.builder.build_admission",
        "agent.skills.planner.scanner_gateway",
        "agent.skills.shared.host.recovery",
        "agent.skills.shared.storage.event_store",
        "agent.skills.shared.host.loaders",
    }

    def test_contracts_no_runtime_imports(self):
        """B01: Contract modules do not import runtime modules."""
        contracts_dir = pathlib.Path("agent/skills/shared/contracts")
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
        validation_dir = pathlib.Path("agent/skills/shared/contracts/workflow/validation")
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
        "system/host/sys_controller.py",
        "mvp/service.py",
        ".agents/contracts/workflow.yaml",
        "agent/runtime/controller.py",
        "conftest.py",
        "MVP/api.py",
    )
    assert forbidden_paths(paths) == tuple(sorted(paths))
    assert forbidden_paths(("agent/skills/planner/scanner_gateway.py", "agent/skills/builder/file_operations.py")) == ()


def test_every_e2e_module_is_marked_and_uses_no_mock() -> None:
    """A module without the marker would silently escape CI's `-m e2e` step."""
    modules = sorted(pathlib.Path("tests/e2e").glob("test_*.py"))
    assert modules, "e2e marker guard cannot pass without scanning modules"
    for module in modules:
        source = module.read_text(encoding="utf-8")
        assert "pytestmark = pytest.mark.e2e" in source, f"{module} is not selected by -m e2e"
        assert "unittest.mock" not in source, f"{module} stubs a collaborator instead of driving the host"
