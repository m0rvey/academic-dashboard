import ast
from pathlib import Path

db_path = Path("src/core/database.py")
code = db_path.read_text()
tree = ast.parse(code)

imports = [
    "from abc import ABC, abstractmethod",
    "from typing import List, Optional, Tuple, Dict, Any",
    "from pathlib import Path",
    "from .models import Task, TaskStatus",
]

methods = []
for node in tree.body:
    if isinstance(node, ast.ClassDef) and node.name == "DatabaseManager":
        for item in node.body:
            if isinstance(item, ast.FunctionDef) and not item.name.startswith("_"):
                if item.name == "init_db":
                    continue  # Optional, but keep it

                # Extract signature
                args = []
                for arg in item.args.args:
                    arg_str = arg.arg
                    if arg.annotation:
                        arg_str += ": " + ast.unparse(arg.annotation)
                    args.append(arg_str)

                # Defaults
                if item.args.defaults:
                    for i, default in enumerate(reversed(item.args.defaults)):
                        args[-(i + 1)] += " = " + ast.unparse(default)

                ret_ann = " -> " + ast.unparse(item.returns) if item.returns else ""

                docstring = ast.get_docstring(item)
                doc = f'        """{docstring}"""\n' if docstring else ""

                methods.append(
                    f"    @abstractmethod\n    def {item.name}({', '.join(args)}){ret_ann}:\n{doc}        pass\n"
                )

interface_code = "\n".join(imports) + "\n\nclass IDatabaseManager(ABC):\n" + "\n".join(methods)
Path("src/core/interfaces.py").write_text(interface_code)
print("Done")
