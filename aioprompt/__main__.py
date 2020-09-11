from . import *
import time

# ============  test program ===================
sys.stderr.flush()
sys.stderr.flush()


class tui:
    # use direct access, it is absolute addressing on raw terminal.
    out = sys.__stdout__.write

    # save cursor
    def __enter__(self):
        self.out("\x1b7\x1b[?25l")
        return self

    # restore cursor
    def __exit__(self, *tb):
        self.out("\x1b8\x1b[?25h")

    def __call__(self, *a, **kw):
        self.out("\x1b[{};{}H{}".format(kw.get("z", 12), kw.get("x", 40), " ".join(a)))


tui.instance = tui()


async def render_ui():
    import time

    def box(t,x,y,z):
        lines = t.split('\n')
        fill = "─"*(1+len(t))
        if z>1:
            print( '┌%s┐' % fill, x=70, z=z-1)
        for t in lines:
            print( '│%s│' % t, x=70, z=2)
            z+=1
        print( '└%s┘' % fill, x=70, z=z)

    while True:
        with tui.instance as print:
            # draw a clock
            t =  "%2d:%2d:%2d 📻 ☢  99%%" % time.localtime()[3:6]
            box(t,x=70,y=0,z=2)

#            fill = "─"*(1+len(t))
#            print( '┌%s┐' % fill, x=70, z=1)
#            print( '│%s│' % t, x=70, z=2)
#            print( '└%s┘' % fill, x=70, z=3)
#
        await asyncio.sleep(1)
        sys.stdout.flush()


async def __main__(*a, **k):

    while not aio.loop.is_closed():
        await asyncio.sleep(1)


async def test():
    await asyncio.sleep(1)
    print("wait me !")
    await asyncio.sleep(1)
    return 666


def hog():
    while True:
        print("blocking")
        time.sleep(1)

def autostart():
    run(__main__, render_ui)
    aio.test = test

#sys.__interactivehook__=autostart # droid: not worky
run(__main__, render_ui)


