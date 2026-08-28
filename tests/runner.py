# -*- coding: utf-8 -*-
"""总控：依次以独立进程运行各测试模块，汇总结果。"""
import subprocess, sys, os
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

HERE = os.path.dirname(os.path.abspath(__file__))
MODULES = ["t_core.py", "t_edit.py", "t_fold_drag.py", "t_reparent.py", "t_zibei.py", "t_bookfmt.py", "t_autosave.py", "t_export.py", "t_perf.py", "t_view.py"]

results = []
for m in MODULES:
    r = subprocess.run([sys.executable, os.path.join(HERE, m)],
                       capture_output=True, text=True, encoding="utf-8", errors="replace",
                       timeout=240)
    out = (r.stdout or "") + (("\n[stderr]\n" + r.stderr) if r.returncode != 0 and r.stderr else "")
    print(out.rstrip())
    ok = r.returncode == 0
    results.append((m, ok))

print("\n========== 汇总 ==========")
fails = 0
for m, ok in results:
    print(("  PASS " if ok else "  FAIL ") + m)
    fails += 0 if ok else 1
print(f"{len(results)-fails}/{len(results)} 模块通过")
sys.exit(1 if fails else 0)
