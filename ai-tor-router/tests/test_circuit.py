from src.tor.circuit_manager import CircuitManager


class MockTor:
    def new_circuit(self):
        return True

    def get_exit_ip(self):
        return "185.220.101.1"


def test_circuit_rotation():
    tor = MockTor()

    manager = CircuitManager(tor)

    event = manager.rotate(reason="test")

    assert event.new_ip == "185.220.101.1"
    assert manager.rotation_count == 1