"""The browser fit (docs/decline.js) must match the Python fit (src/tidywells/decline.py)."""
import json
import shutil
import subprocess
from pathlib import Path

import numpy as np
import pytest

from tidywells import arps_rate, fit_arps

JS = Path(__file__).resolve().parents[1] / "docs" / "decline.js"
pytestmark = pytest.mark.skipif(shutil.which("node") is None, reason="node not installed")


def run_js(t, q):
    code = ("const d=require(%r);const i=JSON.parse(require('fs').readFileSync(0,'utf8'));"
            "const f=d.fitArps(i.t,i.q);console.log(JSON.stringify({qi:f.qi,di:f.di,b:f.b,n:f.n,w:f.warnings}))" % str(JS))
    out = subprocess.run(["node", "-e", code], input=json.dumps({"t": list(t), "q": list(q)}),
                         capture_output=True, text=True, check=True).stdout
    return json.loads(out)


@pytest.mark.parametrize("seed,qi,di,b", [(1, 200, 1.2, 1.0), (2, 80, 0.4, 0.0), (3, 500, 2.0, 1.5)])
def test_js_matches_python(seed, qi, di, b):
    rng = np.random.default_rng(seed)
    t = np.arange(48) / 12
    q = arps_rate(t, qi, di, b) * np.exp(rng.normal(0, 0.08, 48))
    py = fit_arps(t, q)
    js = run_js(t, q)
    assert js["n"] == py["n"]
    assert js["b"] == pytest.approx(py["b"], abs=1e-9)
    assert js["qi"] == pytest.approx(py["qi"], rel=1e-4)
    assert js["di"] == pytest.approx(py["di"], rel=1e-4)
    assert sorted(js["w"]) == sorted(py["warnings"])
