import cProfile
import io
import os
import pstats
import time

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.dev")
django.setup()

from django.core.files.base import ContentFile
from django.core.files.storage import default_storage

# warm up (creates shared connection)
name1 = default_storage.save("dbg/perf3.bin", ContentFile(b"y" * 10000))
print("warm save done")

# profile SECOND save (should be fast if caching works)
pr = cProfile.Profile()
pr.enable()
name2 = default_storage.save("dbg/perf4.bin", ContentFile(b"y" * 10000))
pr.disable()
s = io.StringIO()
ps = pstats.Stats(pr, stream=s).sort_stats("cumulative")
ps.print_stats(10)
print(s.getvalue()[:1800])

# profile SECOND url call
pr2 = cProfile.Profile()
pr2.enable()
url = default_storage.url(name2)
pr2.disable()
s2 = io.StringIO()
ps2 = pstats.Stats(pr2, stream=s2).sort_stats("cumulative")
ps2.print_stats(8)
print(s2.getvalue()[:1400])