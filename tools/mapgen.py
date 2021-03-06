#!/usr/bin/env python

from __future__ import division

from itertools import product
import sys
import time

from bravo.config import BravoConfigParser
from bravo.ibravo import ITerrainGenerator
from bravo.plugin import retrieve_plugins
from bravo.world import World

if len(sys.argv) <= 3:
    print "Not enough arguments."
    sys.exit()

d = retrieve_plugins(ITerrainGenerator)

size = int(sys.argv[1])
pipeline = [d[name] for name in sys.argv[2].split(",")]
target = sys.argv[3]

print "Making map of %dx%d chunks in %s" % (size, size, target)
print "Using pipeline: %s" % ", ".join(plugin.name for plugin in pipeline)

config = BravoConfigParser()
config.add_section("world mapgen")
config.set("world mapgen", "url", target)
config.set("world mapgen", "serializer", "beta")

world = World(config, "mapgen")
world.connect()
world.pipeline = pipeline
world.season = None
world.saving = True

counts = [1, 2, 4, 5, 8]
count = 0
total = size ** 2

cpu = 0
before = time.time()
for i, j in product(xrange(size), repeat=2):
    start = time.time()
    d = world.request_chunk(i, j)
    cpu += (time.time() - start)
    d.addCallback(lambda chunk: world.save_chunk(chunk))
    count += 1
    if count >= counts[0]:
        print "Status: %d/%d (%.2f%%)" % (count, total, count * 100 / total)
        counts.append(counts.pop(0) * 10)

taken = time.time() - before
print "Finished!"
print "Took %.2f seconds to generate (%dms/chunk)" % (taken,
    taken * 1000 / size)
print "Spent %.2f seconds on CPU (%dms/chunk)" % (cpu, cpu * 1000 / size)
