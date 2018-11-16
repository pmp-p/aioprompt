scheduled = None
scheduler = None
wrapper_ref = None
paused = None  # autorun
create_task = None
close = None
loop =None

# ==== display coroutines values ================
# 1:  coroutine()
# 2:  x=coroutine();x
# 3:  x=await coroutine()

# 1/2/3
import sys
import asyncio
import builtins

# 3
import readline
import textwrap

# import ast

sys.stdout.write = sys.__stdout__.write


async def await_displayhook(value):
    try:
        result = await value
        sys.stdout.write(f":async: {result}\n~~> ")
    except RuntimeError as e:
        sys.stdout.write(f"{e.__class__.__name__}: {str(e)}\n~~> ")
    except Exception as e:
        pdb(":", e, e.__name__)
    finally:
        sys.ps1 = sys.__ps1__


# 1 &  2
def displayhook(value):
    if value is None:
        return
    builtins._ = None

    text = repr(value)
    import asyncio

    if asyncio.iscoroutine(value):
        sys.__ps1__ = sys.ps1
        sys.ps1 = ""

        sys.stdout.write(f":async: awaiting {text}")
        asyncio.get_event_loop().create_task(await_displayhook(value))
    else:

        try:
            sys.stdout.write(text)
        except UnicodeEncodeError:
            bytes = text.encode(sys.stdout.encoding, "backslashreplace")
            if hasattr(sys.stdout, "buffer"):
                sys.stdout.buffer.write(bytes)
            else:
                text = bytes.decode(sys.stdout.encoding, "strict")
                sys.stdout.write(text)
    sys.stdout.write("\n")
    builtins._ = value


sys.displayhook = displayhook

# 3

async_skeleton = """
#==========================================
import builtins
async def retry_async_body():
    __snapshot = list( locals().keys() )
{}
    maybe_new = list( locals().keys() )
    while len(__snapshot):
        try:maybe_new.remove( __snapshot.pop() )
        except:pass
    maybe_new.remove('__snapshot')
    print('_'*30)
    while len(maybe_new):
        new_one = maybe_new.pop(0)
        print(new_one , ':=', locals()[new_one])
        setattr(__import__('__main__'), new_one , locals()[new_one] )
#==========================================
"""

async def retry(index):
    try:
        for x in range(10):
            code = readline.get_history_item(index)
            if code and code.count("await"):
                sys.stdout.write(f'{code}"\n')
                code = async_skeleton.format(  textwrap.indent(code, " " * 4) )
                try:
                    bytecode = compile(code, "<asyncify>", "exec")
                except IndentationError:

                    stack = [ readline.get_history_item(index)]

                    #pep8 indents
                    if stack[-1][0]==' ':
                        indent = " " * 4
                    else:
                        indent = '\t'
                    line_index = index -1
                    while line_index>=0:
                        code =  readline.get_history_item(line_index)
                        if code is None:
                            break

                        if code and len(code):

#FIXME: multiline triple quotes and mixing indent styles.
                            if not code[0] in ' #':
                                if code[0] != indent[0]:
                                    line_index = 0

                        stack.append( "{}{}".format(indent,code) )
                        line_index -= 1

                    stack.reverse()
                    for line,code in enumerate(stack):
                        sys.stdout.write(f":async: {line}:{repr(code)}\n")
                    # FIXME: what about non PEP8 tabs indentations ?
                    code = async_skeleton.format( '\n'.join( stack ) )
                    bytecode = compile(code, "<asyncify>", "exec")

                exec(bytecode, globals(), globals())
                await retry_async_body()
                return sys.stdout.write("~~> ")

            await asyncio.sleep(0.001)
        # FIXME: raise old exception
        sys.stdout.write(f":async: code vanished\n~~> ")

    finally:
        sys.ps1 = sys.__ps1__


def excepthook(etype, e, tb):

    if isinstance(e, SyntaxError) and e.filename == "<stdin>":
        index = readline.get_current_history_length()
        sys.__ps1__ = sys.ps1
        sys.ps1 = ""
        sys.stdout.write(f':async:  asyncify "')
        asyncio.get_event_loop().create_task(retry(index))
        # discard trace
        return
    sys.__excepthook__(etype, e, tb)


sys.excepthook = excepthook


# ======== have asyncio loop runs interleaved with repl
import sys
import builtins
import signal

# *no effect :
from signal import pthread_sigmask, SIG_SETMASK, SIG_BLOCK, SIG_UNBLOCK, SIGWINCH, SIGINT


if not sys.flags.inspect:
    print("Error: interpreter must be run with -i or PYTHONINSPECT must be set for using", __name__)
    raise SystemExit


def init():
    global scheduled, scheduler, scheduler_c, wrapper_ref
    #! KEEP IT WOULD BE GC OTHERWISE!
    # wrapper_ref

    scheduled = []
    from ctypes import pythonapi, cast, c_char_p, c_void_p, CFUNCTYPE

    HOOKFUNC = CFUNCTYPE(c_char_p)
    PyOS_InputHookFunctionPointer = c_void_p.in_dll(pythonapi, "PyOS_InputHook")

    def scheduler():
        global scheduled
        # prevent reenter
        lq = len(scheduled)
        while lq:
            fn, a = scheduled.pop(0)
            fn(a)
            lq -= 1

    wrapper_ref = HOOKFUNC(scheduler)
    scheduler_c = cast(wrapper_ref, c_void_p)
    PyOS_InputHookFunctionPointer.value = scheduler_c.value

    # replace with faster function
    def schedule(fn, a):
        scheduled.append((fn, a))

    __import__(__name__).schedule = schedule

    # now the init code is useless
    del __import__(__name__).init


def schedule(fn, a):
    global scheduled
    if scheduled is None:
        init()
    scheduled.append((fn, a))


# ========== asyncio stepping ================


def step(arg):
    global aio, paused
    if aio.is_closed():
        sys.__stdout__.write(f"\n:async: stopped\n{sys.ps1}")
        return
    if not paused:
        aio.call_soon(aio.stop)
        aio.run_forever()
    if arg:
        schedule(step, arg)


def pause(duration=-1):
    global paused
    paused = True


def resume(delay=-1):
    global paused
    paused = False


def run(*entrypoints, start=True):

    global aio, create_task, paused, close, loop

    if loop is None:
        #some aliases to match import * and import as aio
        loop = aio = asyncio.get_event_loop()
        aio.loop = loop
        create_task = aio.create_task
        aio.run =  run
        close = aio.close

    for entrypoint in entrypoints:
        aio.create_task(entrypoint())

    if paused is None:
        schedule(step, 1)

    if start:
        paused = False
    else:
        paused = True


# make step/pause/resume/shedule via "aio" namespace on repl
builtins.aio = __import__(__name__)


__ALL__ = ["loop", "close", "create_task", "pause", "resume", "step", "schedule"]
print("type aio.close() to halt asyncio background operations")
