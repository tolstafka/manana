# Mañana

Mañana (Spanish for "tomorrow") is a lightweight Python package for deferring most module imports until they are actually used.

It reduces program startup overhead by installing an import hook to defer most imports. Some imports are exempted if they have a low enough overhead.



It is an "add-it-and-forget-about-it" package: use it when you want faster import-time performance without affecting runtime behavior after modules are accessed.