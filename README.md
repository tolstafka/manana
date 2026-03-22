# Mañana

Mañana (Spanish for "tomorrow") is a lightweight Python package for deferring most module imports until they are actually used.

It reduces program startup overhead by installing an import hook to defer most imports. Some imports are exempted if they have a low enough overhead.

Example profile
```py
[manana] total=18 loaded=16 ignored=2
loaded  _bisect in 0.001ms (trigger=main.py:18)
loaded  _decimal in 0.001ms (trigger=main.py:18)
loaded  _json in 0.010ms (trigger=main.py:14)
loaded  _random in 0.004ms (trigger=main.py:18)
loaded  _sha2 in 0.008ms (trigger=main.py:18)
loaded  _statistics in 0.001ms (trigger=main.py:18)
loaded  bisect in 0.334ms (trigger=main.py:18)
loaded  decimal in 0.968ms (trigger=main.py:18)
loaded  fractions in 1.666ms (trigger=main.py:18)
ignored h5py
loaded  json in 1.125ms (trigger=main.py:14)
loaded  json.decoder in 0.552ms (trigger=main.py:14)
loaded  json.encoder in 0.201ms (trigger=main.py:14)
loaded  json.scanner in 0.146ms (trigger=main.py:14)
loaded  numbers in 0.207ms (trigger=main.py:18)
loaded  random in 1.243ms (trigger=main.py:18)
ignored scipy
loaded  statistics in 3.580ms (trigger=main.py:18)
```

It is an "add-it-and-forget-about-it" package: use it when you want faster import-time performance without affecting runtime behavior after modules are accessed.
