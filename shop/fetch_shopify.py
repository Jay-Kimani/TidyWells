"""Download the Shopify/Printify mockup photos (listed in shopify_images.json) into docs/img/shop/sp-*.jpg."""
import json, subprocess, os, sys
base = "https://cdn.shopify.com/s/files/1/0969/3220/0732/files/"
m = json.load(open(os.path.join(os.path.dirname(__file__), "shopify_images.json")))
out = os.path.join(os.path.dirname(__file__), "..", "docs", "img", "shop")
raw = os.path.join(os.path.dirname(__file__), "_sp")
for key, names in m.items():
    for i, n in enumerate(names):
        dst = os.path.join(out, f"sp-{key}-{i+1}.jpg")
        if os.path.exists(dst) and os.environ.get("FORCE_KEY") != key and (os.path.getmtime(dst) > os.path.getmtime(os.path.join(raw, "changed.txt")) or key not in open(os.path.join(raw, "changed.txt")).read().split()): continue
        tmp = os.path.join(raw, f"{key}-{i+1}.jpg")
        r = subprocess.run(["curl", "-sSfL", "-o", tmp, base + n + ".jpg"])
        if r.returncode: print("FAIL", key, n); continue
        from PIL import Image
        im = Image.open(tmp).convert("RGB"); im.thumbnail((1000, 1000)); im.save(dst, quality=82, optimize=True, progressive=True)
        print("ok", dst, os.path.getsize(dst))
