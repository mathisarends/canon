# Repository guidance

## Python module layout

In new or edited Python source modules, put the public API (public classes and
functions) first, immediately after imports and module constants. Define private
implementation helpers below the public API. Keep the executable `__main__`
entrypoint at the end of the module.

Generated client files are owned by the generators; update their templates rather
than editing generated output by hand.
