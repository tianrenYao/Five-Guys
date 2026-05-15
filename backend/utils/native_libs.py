import ctypes.util
import os


def prepare_macos_weasyprint_runtime():
    """Prepare dynamic library resolution for WeasyPrint on macOS/Homebrew."""
    if os.name != "posix":
        return

    homebrew_prefixes = ["/opt/homebrew", "/usr/local"]
    lib_dirs = []
    for prefix in homebrew_prefixes:
        candidates = [
            f"{prefix}/lib",
            f"{prefix}/opt/glib/lib",
            f"{prefix}/opt/pango/lib",
            f"{prefix}/opt/cairo/lib",
            f"{prefix}/opt/gdk-pixbuf/lib",
        ]
        for path in candidates:
            if os.path.isdir(path):
                lib_dirs.append(path)

    if lib_dirs:
        existing = os.environ.get("DYLD_FALLBACK_LIBRARY_PATH", "")
        merged = ":".join(lib_dirs + ([existing] if existing else []))
        os.environ["DYLD_FALLBACK_LIBRARY_PATH"] = merged

        existing_pkg = os.environ.get("PKG_CONFIG_PATH", "")
        pkg_dirs = [d + "/pkgconfig" for d in lib_dirs if os.path.isdir(d + "/pkgconfig")]
        if pkg_dirs:
            merged_pkg = ":".join(pkg_dirs + ([existing_pkg] if existing_pkg else []))
            os.environ["PKG_CONFIG_PATH"] = merged_pkg

    # Some upstream loaders ask for Linux-style names like "gobject-2.0-0".
    # On macOS/Homebrew the real file is usually libgobject-2.0.dylib.
    original_find = ctypes.util.find_library

    def patched_find_library(name):
        alias_map = {
            "gobject-2.0-0": "gobject-2.0",
            "glib-2.0-0": "glib-2.0",
            "gio-2.0-0": "gio-2.0",
        }
        mapped = alias_map.get(name, name)
        result = original_find(mapped)
        if result:
            return result

        # Fallback to common Homebrew absolute paths
        hardcoded = {
            "gobject-2.0-0": "libgobject-2.0.dylib",
            "gobject-2.0": "libgobject-2.0.dylib",
            "glib-2.0-0": "libglib-2.0.dylib",
            "glib-2.0": "libglib-2.0.dylib",
            "gio-2.0-0": "libgio-2.0.dylib",
            "gio-2.0": "libgio-2.0.dylib",
        }
        filename = hardcoded.get(name) or hardcoded.get(mapped)
        if filename:
            for prefix in homebrew_prefixes:
                candidate = f"{prefix}/lib/{filename}"
                if os.path.exists(candidate):
                    return candidate
                candidate = f"{prefix}/opt/glib/lib/{filename}"
                if os.path.exists(candidate):
                    return candidate
        return None

    ctypes.util.find_library = patched_find_library
