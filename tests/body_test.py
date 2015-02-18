from eth_tools import address
from nose.tools import assert_equal, assert_not_equal
from pyethereum import tester as t

class TestBody:
    def setup(self):
        self.state = t.state()
        self.contract = self.state.abi_contract("contracts/body.se")

    def test_move_left(self):
        brain = self.state.abi_contract("mocks/brain/mover.se")
        location = self.state.abi_contract("contracts/square.se")
        neighbor = self.state.abi_contract("contracts/square.se")

        location.set_left(neighbor.address)
        location.set_creature(self.contract.address)

        assert_equal(address(location.get_creature()[0]), self.contract.address)

        self.contract.set_location(location.address)
        self.contract.set_brain(brain.address)
        assert_equal(address(self.contract.get_location()[0]), location.address)

        self.contract.notify_of_turn()

        assert_equal(address(self.contract.get_location()[0]), neighbor.address)
        assert_equal(location.get_creature(), [0])
        assert_equal(address(neighbor.get_creature()[0]), self.contract.address)

    def test_harvest(self):
        brain = self.state.abi_contract("mocks/brain/harvester.se")

        location = self.state.abi_contract("contracts/square.se")
        location.set_gas(150)
        location.set_creature(self.contract.address)

        self.contract.set_location(location.address)
        self.contract.set_brain(brain.address)

        assert_equal(location.get_gas(), [150])
        assert_equal(self.contract.get_gas(), [0])

        self.contract.notify_of_turn()
        assert_equal(location.get_gas(), [50])
        assert_equal(self.contract.get_gas(), [100])

        self.contract.notify_of_turn()
        assert_equal(location.get_gas(), [0])
        assert_equal(self.contract.get_gas(), [150])

    def test_attack_left(self):
        brain = self.state.abi_contract("mocks/brain/attacker.se")
        location = self.state.abi_contract("contracts/square.se")
        neighbor = self.state.abi_contract("contracts/square.se")
        enemy = self.state.abi_contract("contracts/body.se")

        location.set_left(neighbor.address)
        location.set_creature(self.contract.address)

        neighbor.set_right(location.address)
        neighbor.set_creature(enemy.address)

        enemy.set_location(neighbor.address)
        enemy.set_hp(3)

        self.contract.set_location(location.address)
        self.contract.set_brain(brain.address)

        assert_equal(enemy.get_hp(), [3])

        self.contract.notify_of_turn()

        assert_equal(enemy.get_hp(), [2])

    def test_death(self):
        location = self.state.abi_contract("contracts/square.se")
        location.set_creature(self.contract.address)

        self.contract.set_location(location.address)
        self.contract.set_gas(100)
        self.contract.set_hp(1)

        self.contract.damage()

        assert_equal(self.contract.get_hp(), [0])
        assert_equal(self.contract.get_dead(), [1])
        assert_equal(self.contract.get_gas(), [0])
        assert_equal(location.get_gas(), [100])
        assert_equal(location.get_creature(), [0])

    def test_reproduce_left(self):
        brain = self.state.abi_contract("mocks/brain/reproducer.se")
        location = self.state.abi_contract("contracts/square.se")
        neighbor = self.state.abi_contract("contracts/square.se")
        creature_builder = self.state.abi_contract("contracts/creature_builder.se")

        location.set_left(neighbor.address)
        location.set_creature(self.contract.address)

        self.contract.set_location(location.address)
        self.contract.set_brain(brain.address)
        self.contract.set_creature_builder(creature_builder.address)

        assert_equal(neighbor.get_creature(), [0])

        self.contract.notify_of_turn()

        assert_not_equal(neighbor.get_creature(), [0])

    def test_reproduction_notifies_gamemaster(self):
        brain = self.state.abi_contract("mocks/brain/reproducer.se")
        location = self.state.abi_contract("contracts/square.se")
        neighbor = self.state.abi_contract("contracts/square.se")
        creature_builder = self.state.abi_contract("contracts/creature_builder.se")

        gamemaster = self.state.abi_contract("mocks/gamemaster/spawn_counter.se")

        location.set_left(neighbor.address)
        location.set_creature(self.contract.address)

        self.contract.set_location(location.address)
        self.contract.set_brain(brain.address)
        self.contract.set_creature_builder(creature_builder.address)
        self.contract.set_gamemaster(gamemaster.address)

        gamemaster.send_turn_notification_to(self.contract.address)

        assert_equal(gamemaster.get_spawn_count(), [1])

    def test_can_only_move_on_turn(self):
        location = self.state.abi_contract("contracts/square.se")
        neighbor = self.state.abi_contract("contracts/square.se")

        location.set_left(neighbor.address)
        location.set_creature(self.contract.address)

        self.contract.set_location(location.address)
        self.contract.set_brain(t.a0)

        self.contract.move_left()

        assert_equal(address(location.get_creature()[0]), self.contract.address)
        assert_equal(address(self.contract.get_location()[0]), location.address)

    def test_gamemaster_can_deduct_gas(self):
        self.contract.set_gas(1000)

        self.contract.deduct_gas(400)
        self.contract.deduct_gas(300, sender=t.k1)

        assert_equal(self.contract.get_gas(), [600])
