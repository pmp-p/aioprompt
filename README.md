# aioprompt

minimal py3.7+ asyncio repl using	**readline module** tricks. That module if often available on GNU/Linux platform.

testing:

```
python3.7 -i -maioprompt
```

the main test will launch a clock on your repl ( use a VT100 compatible terminal ).


Note that for running panda3D with that repl you may require to compile both python and panda3D with gcc 7+, as gcc/4 and clang 3/5 may lead to strange behaviour.


# LATER:
  maybe use linenoise-ng ( MIT ) as a C readline replacement and mimic window.requestAnimationFrame() from javascript.
