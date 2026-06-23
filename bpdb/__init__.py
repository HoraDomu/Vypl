import os
import sys
import traceback
from optparse import OptionParser
from pdb import Restart

import vypl
from vypl.args import version_banner

from .debugger import BPdb

__version__ = vypl.__version__


def set_trace():
    debugger = BPdb()
    debugger.set_trace(sys._getframe().f_back)


def post_mortem(t=None):
    if t is None:
        t = sys.exc_info()[2]
        if t is None:
            raise ValueError(
                "A valid traceback must be passed if no exception is being handled."
            )

    p = BPdb()
    p.reset()
    p.interaction(None, t)


def pm():
    post_mortem(getattr(sys, "last_traceback", None))


def main():
    parser = OptionParser(usage="Usage: %prog [options] [file [args]]")
    parser.add_option(
        "--version", "-V", action="store_true", help="Print version and exit."
    )
    options, args = parser.parse_args(sys.argv)
    if options.version:
        print(version_banner(base="bpdb"))
        return 0

    if len(args) < 2:
        print("usage: bpdb scriptfile [arg] ...")
        return 2

    mainpyfile = args[1]
    if not os.path.exists(mainpyfile):
        print(f"Error: {mainpyfile} does not exist.")
        return 1

    del sys.argv[0]

    sys.path[0] = os.path.dirname(mainpyfile)

    pdb = BPdb()
    while True:
        try:
            pdb._runscript(mainpyfile)
            if pdb._user_requested_quit:
                break
            print("The program finished and will be restarted.")
        except Restart:
            print(f"Restarting {mainpyfile} with arguments:")
            print("\t" + " ".join(sys.argv[1:]))
        except SystemExit:
            print(
                "The program exited via sys.exit(). Exit status: ",
            )
            print(sys.exc_info()[1])
        except Exception:
            traceback.print_exc()
            print("Uncaught exception. Entering post mortem debugging.")
            print("Running 'cont' or 'step' will restart the program.")
            t = sys.exc_info()[2]
            pdb.interaction(None, t)
            print(
                f"Post mortem debugger finished. The {mainpyfile} will be restarted."
            )
