# Contributing

Bug reports, corrections and new analysis ideas are welcome.

- **A wrong number or unclear claim on the site:** open an issue with the "Wrong number" template. We correct errors publicly and log them at https://tidywells.com/corrections.html.
- **A bug in the package or tools:** open an issue with the "Bug" template.
- **Code changes:** keep tests on synthetic data only (never commit regulator files), run `pytest -q`, then `python posts/build_feed.py && python posts/verify_site.py`. CI runs the same steps and fails if a published figure does not match the data.
- **Rules for analysis posts:** state the data, the method and the limits; say what the numbers do not show; no investment, legal or engineering advice.
