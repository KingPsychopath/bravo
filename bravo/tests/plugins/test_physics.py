import shutil
import tempfile

from twisted.trial import unittest

import bravo.blocks
import bravo.config
import bravo.ibravo
import bravo.plugin
import bravo.world

class WaterMockFactory(object):

    def flush_chunk(self, chunk):
        pass

class TestWater(unittest.TestCase):

    def setUp(self):
        # Using build hook to grab the plugin, but dig hook should work as
        # well.
        self.p = bravo.plugin.retrieve_plugins(bravo.ibravo.IBuildHook)

        if "water" not in self.p:
            raise unittest.SkipTest("Plugin not present")

        self.hook = self.p["water"]

        # Set up world.
        self.name = "unittest"
        self.d = tempfile.mkdtemp()

        bravo.config.configuration.add_section("world unittest")
        bravo.config.configuration.set("world unittest", "url",
            "file://%s" % self.d)
        bravo.config.configuration.set("world unittest", "serializer",
            "alpha")

        self.w = bravo.world.World(self.name)
        self.w.pipeline = []

        # And finally the mock factory.
        self.f = WaterMockFactory()
        self.f.world = self.w

    def tearDown(self):
        if self.w.chunk_management_loop.running:
            self.w.chunk_management_loop.stop()
        del self.w

        shutil.rmtree(self.d)
        bravo.config.configuration.remove_section("world unittest")

    def test_trivial(self):
        pass

    def test_zero_y(self):
        """
        Double-check that water placed on the very bottom of the world doesn't
        cause internal errors.
        """

        self.w.set_block((0, 0, 0), bravo.blocks.blocks["spring"].slot)
        self.hook.pending[self.f].add((0, 0, 0))

        # Tight-loop run the hook to equilibrium; if any exceptions happen,
        # they will bubble up.
        while self.hook.pending:
            self.hook.process()

    def test_spring_spread(self):
        self.w.set_block((0, 0, 0), bravo.blocks.blocks["spring"].slot)
        self.hook.pending[self.f].add((0, 0, 0))

        # Tight-loop run the hook to equilibrium.
        while self.hook.pending:
            self.hook.process()

        for coords in ((1, 0, 0), (-1, 0, 0), (0, 0, 1), (0, 0, -1)):
            self.assertEqual(self.w.get_block(coords),
                bravo.blocks.blocks["water"].slot)
            self.assertEqual(self.w.get_metadata(coords), 0x0)

    def test_obstacle(self):
        """
        Test that obstacles are flowed around correctly.
        """

        raise unittest.SkipTest("Currently goes into an infinite loop.")

        self.w.set_block((0, 0, 0), bravo.blocks.blocks["spring"].slot)
        self.w.set_block((1, 0, 0), bravo.blocks.blocks["stone"].slot)
        self.hook.pending[self.f].add((0, 0, 0))

        # Tight-loop run the hook to equilibrium.
        while self.hook.pending:
            self.hook.process()

        # Make sure that the water level behind the stone is 0x3, not 0x0.
        self.assertEqual(self.w.get_metadata((2, 0, 0)), 0x3)

    def test_sponge(self):
        """
        Test that sponges prevent water from spreading near them.
        """

        raise unittest.SkipTest("Currently goes into an infinite loop.")

        self.w.set_block((0, 0, 0), bravo.blocks.blocks["spring"].slot)
        self.w.set_block((3, 0, 0), bravo.blocks.blocks["sponge"].slot)
        self.hook.pending[self.f].add((0, 0, 0))

        # Tight-loop run the hook to equilibrium.
        while self.hook.pending:
            self.hook.process()

        # Make sure that water did not spread near the sponge.
        self.assertNotEqual(self.w.get_block((1, 0, 0)),
            bravo.blocks.blocks["water"].slot)

    def test_spring_remove(self):
        """
        Test that water dries up if no spring is providing it.
        """

        self.w.set_block((0, 0, 0), bravo.blocks.blocks["spring"].slot)
        self.hook.pending[self.f].add((0, 0, 0))

        # Tight-loop run the hook to equilibrium.
        while self.hook.pending:
            self.hook.process()

        # Remove the spring.
        self.w.destroy((0, 0, 0))

        # Tight-loop run the hook to equilibrium.
        while self.hook.pending:
            self.hook.process()

        for coords in ((1, 0, 0), (-1, 0, 0), (0, 0, 1), (0, 0, -1)):
            self.assertEqual(self.w.get_block(coords),
                bravo.blocks.blocks["air"].slot)