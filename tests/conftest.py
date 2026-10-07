"""pytest setup (05b): import torch before pandas / pyarrow. pyarrow 15 bundles an old msvcp140.dll; once it is loaded, torch's
c10.dll fails to initialise (WinError 1114). Loading torch first binds the newer system runtime."""
try:
    import torch  # noqa: F401
except ImportError:
    pass
