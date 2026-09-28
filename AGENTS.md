# Contributor and agent guide

Read `README.md` before changing the build. Sindri executable truth is always
consumed from `vardirhq/sindri-engine`; never hand-maintain API signatures here
or refer to a retired engine repository.

Run `python scripts/build.py --engine-dir ../sindri-engine`, then
`python scripts/check_site.py _site`. Authored Decay fences must state an
expectation (`decay compile` or `decay fail`) and are checked with
`scripts/validate_examples.py`.

Generated output belongs in `_site/` and is not committed. Preserve static
hosting, `CNAME`, stable routes, and the **teach here, define there** boundary.
