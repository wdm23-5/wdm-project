_wdm_debug = True


def wdm_debug():
    return _wdm_debug


def wdm_debug_mask(obj) -> str:
    return str(obj) if wdm_debug() else ''


def wdm_assert(cond, msg=None):
    if wdm_debug():
        assert cond, msg


def wdm_assert_type(obj, ty: type, msg=None):
    if wdm_debug():
        assert isinstance(obj, ty), msg


def wdm_print(*args):
    print(*args, flush=True)
