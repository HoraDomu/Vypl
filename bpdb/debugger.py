import pdb
import vypl

class BPdb(pdb.Pdb):
    """PDB with BPython support."""

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.prompt = "(BPdb) "
        self.intro = 'Use "B" to enter vypl, Ctrl-d to exit it.'

    def postloop(self) -> None:
        self.intro = None
        super().postloop()

    def do_Bpython(self, arg: str) -> None:
        locals_ = self.curframe.f_globals.copy()
        locals_.update(self.curframe.f_locals)
        vypl.embed(locals_, ["-i"])

    def help_Bpython(self) -> None:
        print("B(python)")
        print("")
        print(
            "Invoke the vypl interpreter for this stack frame. To exit "
            "vypl and return to a standard pdb press Ctrl-d"
        )

    do_B = do_Bpython
    help_B = help_Bpython
