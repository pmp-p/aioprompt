# aioprompt

minimal py3.7+ repl for asyncio using **readline module** tricks. That module is often available on GNU/Linux platform.

testing:

```
python3.7 -i -maioprompt
```

the main test will launch a clock on your repl ( use a VT100 compatible terminal ).

![Preview1](./aioprompt.png)

Note that for running Panda3D with that repl you may require to compile both python and panda3D with gcc 7+, as gcc/4 and clang 3/5 may lead to strange behaviour.

also terminal is not resizeable unless you apply a fix to readline module.

https://github.com/python/cpython/compare/master...pmp-p:master.diff



## LATER:
  maybe use linenoise-ng ( MIT ) as a C readline replacement and mimic window.requestAnimationFrame() from javascript.
  add a C function to set refresh rate in a timely fashion ( Microcontroller style ).
