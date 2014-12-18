from unittest import TestCase
from unittest.mock import patch, Mock
import codevo
from plyj.model import *


class EvolverTest(TestCase):
    def test_step(self):
        evolver = codevo.Evolver()
        evolver.create_method = Mock()
        with patch.object(codevo, 'random', return_value=0):
            evolver.step()
            evolver.create_method.assert_called_once_with()

    def test_create_method(self):
        evolver = codevo.Evolver()
        with patch.object(codevo, 'random', return_value=1):
            method = evolver.create_method()
            self.assertIsInstance(method, MethodDeclaration)
            self.assertIsNotNone(evolver.methods[method.name])
            self.assertEqual(evolver.callers[method.name], [])
