from . import *

#============  test program ===================
sys.stderr.flush()
sys.stderr.flush()


class tui:
    #use direct access, it is absolute addressing on raw terminal.
    out = sys.__stdout__.write

    #save cursor
    def __enter__(self):
        self.out('\x1b7\x1b[?25l')
        return self

    #restore cursor
    def __exit__(self,*tb):
        self.out('\x1b8\x1b[?25h')


    def __call__(self,*a,**kw):
        self.out( '\x1b[{};{}H{}'.format( kw.get('y',12), kw.get('x',40) , ' '.join(a) ) )


tui.instance = tui()

async def render_ui():
    import time

    while True:
        with tui.instance as print:
            #draw a clock
            print('%2d:%2d:%2d' % time.localtime()[3:6] , x=70, y=1 )

        await asyncio.sleep(1)
        sys.stdout.flush()


async def __main__(*a,**k):

    while True:
        await asyncio.sleep(1)

async def test():
    await asyncio.sleep(1)
    print('wait me !')
    await asyncio.sleep(1)
    return 666

run(__main__, render_ui)
