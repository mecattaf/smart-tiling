try:
    from importlib import metadata
except ImportError:
    import importlib_metadata as metadata

try:
    __version__ = metadata.version("smart-tiling")
except Exception:
    __version__ = "0.0.0"
