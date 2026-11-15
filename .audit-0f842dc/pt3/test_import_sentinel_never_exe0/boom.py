from pathlib import Path
Path(r'D:\breakdown\.audit-0f842dc\pt3\test_import_sentinel_never_exe0\marker.txt').write_text('imported')
raise RuntimeError('scanned code was imported')
