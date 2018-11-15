# aioprompt

minimal py3.7+ repl for asyncio using **readline module** tricks. That module is often available on GNU/Linux platform.

testing:

```
python3.7 -i -maioprompt
```

the main test will launch a clock on your repl ( use a VT100 compatible terminal ).

![Preview1](./aioprompt.png)

aio ( which actually is the asyncio loop)  namespace provides pause/resume/step/run function to control async loop
 and add coroutines.

you can also import them in repl with from aioprompt import * and use them directly

to add a task just use : aio.create_task( the_task() )
or run(the_task)



## LATER:
  maybe use linenoise-ng ( MIT ) as a C readline replacement and mimic window.requestAnimationFrame() from javascript.

  add a C function to set refresh rate in a timely manner ( microcontroller style ).
