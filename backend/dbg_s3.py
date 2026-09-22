import os
import time

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.dev")
django.setup()

from django.core.files.base import ContentFile
from django.core.files.storage import default_storage

name = default_storage.save("dbg/perf5.bin", ContentFile(b"y" * 10000))
t0 = time.time()
u1 = default_storage.url(name)
t1 = time.time()
print("url1:", round(t1 - t0, 2), "s")
t2 = time.time()
u2 = default_storage.url(name)
t3 = time.time()
print("url2:", round(t3 - t2, 2), "s")
t4 = time.time()
name2 = default_storage.save("dbg/perf6.bin", ContentFile(b"y" * 10000))
t5 = time.time()
print("save2:", round(t5 - t4, 2), "s")