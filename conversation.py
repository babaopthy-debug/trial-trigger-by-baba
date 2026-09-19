import os, sys, marshal

_root = os.path.dirname(os.path.abspath(__file__))
if _root not in sys.path:
    sys.path.insert(0, _root)

_pyc = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'runtime\\_conversation.pyc')
with open(_pyc, 'rb') as _f:
    _f.seek(16)
    _code = marshal.load(_f)

exec(_code, globals())
