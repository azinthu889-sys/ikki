"""Worker entrypoint must load render helpers before starting the job loop."""
import ast
import os


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, "worker", "run.py")


def main():
    tree = ast.parse(open(PATH, encoding="utf-8").read(), filename=PATH)
    helpers = {n.name: n.lineno for n in tree.body if isinstance(n, ast.FunctionDef)}
    guards = []
    for n in tree.body:
        if not isinstance(n, ast.If):
            continue
        test = n.test
        if (isinstance(test, ast.Compare) and isinstance(test.left, ast.Name)
                and test.left.id == "__name__"):
            guards.append(n.lineno)

    assert "subject_box" in helpers, "safe-zone helper is missing"
    assert guards, "worker entrypoint is missing"
    assert min(guards) > helpers["subject_box"], (
        "main() starts before subject_box is defined; safe-zone rendering fails "
        "with NameError in direct worker mode")
    print("  ✓ worker helpers load before main loop")


if __name__ == "__main__":
    main()
