"""
backend/utils/native_libs.py
Helper to configure native library paths for WeasyPrint on macOS.
"""
import os
import sys


def prepare_macos_weasyprint_runtime():
    """
    On macOS, WeasyPrint relies on Pango / GLib / GDK-Pixbuf shared libraries
    that are typically installed via Homebrew.  This function ensures the
    correct DYLD_FALLBACK_LIBRARY_PATH is set so that WeasyPrint can locate
    them at runtime.  It is safe to call on non-macOS systems (no-op).
    """
    if sys.platform != 'darwin':
        return

    # Common Homebrew lib paths (Apple Silicon + Intel)
    brew_paths = [
        '/opt/homebrew/lib',          # Apple Silicon
        '/usr/local/lib',             # Intel Mac
    ]

    existing = os.environ.get('DYLD_FALLBACK_LIBRARY_PATH', '')
    parts = [p for p in existing.split(':') if p]

    changed = False
    for bp in brew_paths:
        if os.path.isdir(bp) and bp not in parts:
            parts.append(bp)
            changed = True

    if changed:
        os.environ['DYLD_FALLBACK_LIBRARY_PATH'] = ':'.join(parts)
