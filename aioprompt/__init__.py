scheduled = None
scheduler = None
wrapper_ref = None
paused = None  # autorun
create_task = None
close = None
loop = None
last_fail = []
lives = True
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
import traceback

def pdb(*argv, **kw):
    kw['file']=sys.__stderr__
    print(*argv, **kw)


async def await_displayhook(value):
    try:
        result = await value
        sys.stdout.write(f":async: {result}\n~~> ")
    except RuntimeError as e:
        sys.stdout.write(f"{e.__class__.__name__}: {str(e)}\n~~> ")
    except Exception as e:
        pdb(":", e)
        raise
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

# https://bugs.python.org/issue34616
# https://github.com/ipython/ipython/blob/320d21bf56804541b27deb488871e488eb96929f/IPython/core/interactiveshell.py#L121-L150

async_skeleton = """
#==========================================
async def retry_async_wrap():
    __snapshot = list( locals().keys() )
{}
    maybe_new = list( locals().keys() )
    while len(__snapshot):
        try:maybe_new.remove( __snapshot.pop() )
        except:pass
    maybe_new.remove('__snapshot')
#    print('_'*30)
    while len(maybe_new):
        new_one = maybe_new.pop(0)
        print(new_one , ':=', locals()[new_one])
        setattr(__import__('__main__'), new_one , locals()[new_one] )
#==========================================
"""


def retry_with_indent(stack, indent, line_index):
    import ast

    triple = False

    while line_index >= 0:
        code = readline.get_history_item(line_index)
        if code is None:
            return "#error getting code stack"

        if code and len(code):

            # FIXME: multiline triple quotes and mixing indent styles.
            if code.count('"""') or code.count("'''"):  # <=  FIXME: this may not be bullet proof
                if triple:
                    triple = False
                else:
                    triple = True
            if not triple:
                # not a comment and no more indented, that's the top of the block.
                if (code.strip()[0] != "#") and (code[0] != indent[0]):
                    line_index = 0

                # enforce pep8 indent
                while code[0] == "\t":
                    code = code.replace("\t", " " * 4, 1)
            stack.insert(0, code)

        line_index -= 1

    code = async_skeleton.format(textwrap.indent("\n".join(stack), " " * 4))
#    sys.stdout.write(
#        f'''\n
##_____________________________________________
#{code}
##_____________________________________________
#"'''
#    )
    return code


async def retry(index):
    global last_fail
    may_have_value = False
    try:
        last = readline.get_history_item(index)

        # detect indents
        first = last[0]
        if first in " \t":
            # enforce pep8 indent
            while last[0] == "\t":
                last = last.replace("\t", " " * 4, 1)
            code = retry_with_indent([last], first, index - 1)
        else:
            #one liner
            if last.find('await ')>=0:
                may_have_value = True
                last = 'builtins._ = {}'.format(last)
            code = async_skeleton.format(" " * 4 + last)

        bytecode = compile(code, "<asyncify>", "exec")

#        sys.stdout.write(f':async:  asyncify "{code}"\n')
        sys.stdout.write(f':async:  asyncify "[code stack rewritten]"\n')

        exec(bytecode, __import__('__main__').__dict__, globals())
        await retry_async_wrap()
        # success ? clear all previous failures
        last_fail.clear()
        if may_have_value:
            if builtins._ is not None:
                sys.stdout.write('%r\n' % builtins._)

        return sys.stdout.write("~~> ")

    except Exception as e:
        # FIXME: raise old exception
        sys.__excepthook__(*last_fail.pop(0))
        sys.stdout.write(f":async: can't use code : {e}\n~~> ")
        traceback.print_exc()
    finally:
        sys.ps1 = sys.__ps1__


def excepthook(etype, e, tb):
    global last_fail
    if isinstance(e, SyntaxError) and e.filename == "<stdin>":
        index = readline.get_current_history_length()
        sys.__ps1__ = sys.ps1
        sys.ps1 = ""
        asyncio.get_event_loop().create_task(retry(index))
        # store trace
        last_fail.append([etype, e, tb])
        return
    sys.__excepthook__(etype, e, tb)


sys.excepthook = excepthook


# ======== have asyncio loop runs interleaved with repl
import sys
import builtins

if not sys.flags.inspect:
    print("Error: interpreter must be run with -i or PYTHONINSPECT must be set for using", __name__)
    raise SystemExit


def init():
    global scheduled, scheduler, wrapper_ref
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
    if paused is None:
        aio.close()
        return

    if aio.is_closed():
        sys.__stdout__.write(f"\n:async: stopped\n{sys.ps1}")
        return
    if not paused:
        aio.call_soon(aio.stop)
        aio.run_forever()
    if arg:
        schedule(step, arg)


async def asleep_ms(ms=0):
    await asyncio.sleep(float(ms)/1000)

def run(*entrypoints, start=True):

    global aio, create_task, paused, close, loop

    if loop is None:
        # some aliases to match import * and import as aio
        loop = aio = asyncio.get_event_loop()
        aio.loop = loop
        create_task = aio.create_task
        aio.run = run
        close = aio.close

        aio.asleep_ms = asleep_ms

    for entrypoint in entrypoints:
        aio.create_task(entrypoint())

    if paused is None:
        schedule(step, 1)

    if start:
        paused = False
    else:
        paused = True


#bloat  can do aio.paused = 0/1
def pause(duration=-1):
    global paused
    paused = True


def resume(delay=-1):
    global paused
    paused = False

#

aio = sys.modules.get(__name__)
# make loop reachable from various aio monkey patches
builtins.aio = aio

# make step/pause/resume/shedule via "aio" namespace on repl
__import__('__main__').aio = aio


__ALL__ = ["aio", "loop", "load", "close", "create_task", "paused", "step", "run", "asleep_ms", "schedule", "pause", "resume"]

print("type aio.close() to halt asyncio background operations")
