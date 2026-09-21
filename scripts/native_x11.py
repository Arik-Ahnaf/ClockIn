"""Small native XWayland probe for ClockIn desktop verification; no extra packages.

Import NativeX11 in the Qt test harness. Calls move/button inject real pointer input.
Keep QT_QPA_PLATFORM=xcb for Qt windows, and run desktop probes with display access.
"""
import ctypes as C
import ctypes.util
import re
import subprocess


class NativeX11:
    def __init__(self):
        self.x = C.CDLL(ctypes.util.find_library('X11'))
        self.t = C.CDLL(ctypes.util.find_library('Xtst'))
        self.x.XOpenDisplay.argtypes = [C.c_char_p]
        self.x.XOpenDisplay.restype = C.c_void_p
        self.x.XDefaultRootWindow.argtypes = [C.c_void_p]
        self.x.XDefaultRootWindow.restype = C.c_ulong
        self.x.XFlush.argtypes = [C.c_void_p]
        self.x.XCloseDisplay.argtypes = [C.c_void_p]
        self.x.XQueryPointer.argtypes = [C.c_void_p, C.c_ulong] + [C.POINTER(C.c_ulong)] * 2 + [C.POINTER(C.c_int)] * 4 + [C.POINTER(C.c_uint)]
        self.x.XTranslateCoordinates.argtypes = [C.c_void_p, C.c_ulong, C.c_ulong, C.c_int, C.c_int, C.POINTER(C.c_int), C.POINTER(C.c_int), C.POINTER(C.c_ulong)]
        self.x.XGetGeometry.argtypes = [C.c_void_p, C.c_ulong, C.POINTER(C.c_ulong), C.POINTER(C.c_int), C.POINTER(C.c_int)] + [C.POINTER(C.c_uint)] * 4
        self.t.XTestFakeMotionEvent.argtypes = [C.c_void_p, C.c_int, C.c_int, C.c_int, C.c_ulong]
        self.t.XTestFakeButtonEvent.argtypes = [C.c_void_p, C.c_uint, C.c_int, C.c_ulong]
        self.t.XTestQueryExtension.argtypes = [C.c_void_p] + [C.POINTER(C.c_int)] * 4
        self.d = self.x.XOpenDisplay(None)
        if not self.d:
            raise RuntimeError('Cannot connect to XWayland; run with desktop display access.')
        self.root = self.x.XDefaultRootWindow(self.d)
        event, error, major, minor = [C.c_int() for _ in range(4)]
        if not self.t.XTestQueryExtension(self.d, C.byref(event), C.byref(error), C.byref(major), C.byref(minor)):
            raise RuntimeError('XTest extension unavailable')
        self.xtest_version = (major.value, minor.value)

    def move(self, x, y):
        self.t.XTestFakeMotionEvent(self.d, -1, x, y, 0)
        self.x.XFlush(self.d)

    def button(self, down, button=1):
        self.t.XTestFakeButtonEvent(self.d, button, bool(down), 0)
        self.x.XFlush(self.d)

    def pointer(self):
        root, child = C.c_ulong(), C.c_ulong()
        rx, ry, wx, wy = [C.c_int() for _ in range(4)]
        mask = C.c_uint()
        self.x.XQueryPointer(self.d, self.root, C.byref(root), C.byref(child), C.byref(rx), C.byref(ry), C.byref(wx), C.byref(wy), C.byref(mask))
        return rx.value, ry.value, child.value, mask.value

    def geometry(self, window):
        root, child = C.c_ulong(), C.c_ulong()
        x, y = C.c_int(), C.c_int()
        width, height, border, depth = [C.c_uint() for _ in range(4)]
        self.x.XGetGeometry(self.d, window, C.byref(root), C.byref(x), C.byref(y), C.byref(width), C.byref(height), C.byref(border), C.byref(depth))
        self.x.XTranslateCoordinates(self.d, window, self.root, 0, 0, C.byref(x), C.byref(y), C.byref(child))
        return x.value, y.value, width.value, height.value

    def properties(self, window):
        return subprocess.check_output(['xprop', '-id', hex(window), '_NET_WM_STATE', '_NET_WM_WINDOW_TYPE', '_MOTIF_WM_HINTS'], text=True)

    def stacking(self):
        output = subprocess.check_output(['xprop', '-root', '_NET_CLIENT_LIST_STACKING'], text=True)
        return [int(x, 16) for x in re.findall(r'0x[0-9a-fA-F]+', output)]

    def close(self):
        self.x.XCloseDisplay(self.d)
        self.d = None


if __name__ == '__main__':
    probe = NativeX11()
    print('XTest version:', probe.xtest_version)
    print('Pointer:', probe.pointer())
    print('Stacking (bottom to top):', [hex(window) for window in probe.stacking()])
    probe.close()
