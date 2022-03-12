import _ast as ast
print(ast.__file__)
import re


class TelethonMigrator(ast.NodeTransformer):
    def visit_ImportFrom(self, node: ast.ImportFrom) -> ast.ImportFrom:
        if not isinstance(node.module, str):
            return node

        if node.module == "telethon.tl":
            # Fix renamed `tl` package
            node.module = "telethon._tl"
        elif node.module.startswith("telethon.tl.functions"):
            # Fix renamed `tl.functions` package
            node.module = node.module.replace(
                "telethon.tl.functions", "telethon._tl.fn"
            )
            node.names = [
                ast.alias(
                    name=re.sub(r"([a-zA-Z]+)Request", r"\g<1>", name.name),
                    asname=name.asname,
                )
                for name in node.names
            ]
        elif node.module == "telethon.tl.types":
            # Fix `types` migrated to `_tl`
            node.module = "telethon._tl"

        return node

    def visit_Call(self, node: ast.Call) -> ast.Call:
        if not isinstance(node.func, ast.Name) or not isinstance(node.func.id, str):
            return node

        node.func.id = re.sub(r"([a-zA-Z]+)Request", r"\g<1>", node.func.id)
        return node

    def dive(self, node):
        # Recursive wrapper
        for child in ast.iter_child_nodes(node):
            child = self.dive(child)

        if isinstance(node, ast.Call):
            node = self.visit_Call(node)

        # print(node)

        return node

    def visit_AsyncFunctionDef(
        self, node: ast.AsyncFunctionDef
    ) -> ast.AsyncFunctionDef:
        # Visit all async functions to replace telethon
        # functions to a new ones w\o -`Request`
        node = self.dive(node)
        return node


def process(code):
    tree = ast.parse(code)

    optimizer = TelethonMigrator()
    tree = optimizer.visit(tree)

    return ast.unparse(tree)
