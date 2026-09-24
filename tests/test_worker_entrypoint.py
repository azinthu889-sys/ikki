"""Worker entrypoint must load render helpers before starting the job loop."""
import ast
import os


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, "worker", "run.py")


_R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


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

    # ⚠️ **API retry က လုံလောက်ရမည်** — ၂၀၂၆-၀၉-၂၄: Mac ရဲ့ DNS ယာယီ
    #    ပြတ်သွား၍ (`Errno 8: nodename nor servname`) retry ၅ ကြိမ်
    #    (၈၉s) ကုန်ပြီး stage 4 မှာ render တစ်ခုလုံး ကျကာ **~၄၀ မိနစ်စာ
    #    အလုပ် ဆုံးရှုံး**ခဲ့သည်。 render တစ်ခု ၄၀ မိနစ် ကြာသဖြင့်
    #    အနည်းဆုံး **၁၅ မိနစ်** စောင့်တာက သက်သာသည်。
    import re as _re
    _src = open(os.path.join(_R, "worker", "run.py"), encoding="utf-8").read()
    _m = _re.search(r"RETRY_WAIT\s*=\s*\(([^)]*)\)", _src)
    assert _m, "RETRY_WAIT မတွေ့"
    _w = [float(x) for x in _m.group(1).replace(",", " ").split()]
    assert sum(_w) >= 900, (
        f"API retry စုစုပေါင်း {sum(_w):.0f}s — ၉၀၀s (၁၅ မိနစ်) အနည်းဆုံး လိုသည်; "
        "ကွန်ရက် ခဏ ပြတ်ရုံနဲ့ render တစ်ခုလုံး ကျမည်")
    print(f"  ✓ API retry {len(_w)} ကြိမ် · {sum(_w)/60:.0f} မိနစ်")


if __name__ == "__main__":
    main()
