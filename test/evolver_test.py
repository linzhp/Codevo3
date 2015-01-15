from unittest import TestCase
from unittest.mock import patch, Mock
import codevo
from plyj.model import *


class EvolverTest(TestCase):
    def test_step(self):
        evolver = codevo.Evolver()
        evolver.create_method = Mock()
        with patch.object(codevo.evolver, 'random', return_value=0):
            evolver.step()
            evolver.create_method.assert_called_once_with()

    def test_create_method(self):
        evolver = codevo.Evolver()
        with patch.object(codevo.evolver, 'random', return_value=1):
            method = evolver.create_method()
            self.assertIsInstance(method, MethodDeclaration)
            self.assertIn(method.name, evolver.reference_graph)
            self.assertEqual(evolver.reference_graph.in_degree(method.name), 0)

    def test_call_method(self):
        evolver = codevo.Evolver()
        method_name = next(evolver.reference_graph.nodes_iter())
        method = evolver.reference_graph.node[method_name]['method']
        body_size = len(method.body)
        evolver.call_method()
        self.assertEqual(len(method.body), body_size + 1)
        self.assertIsInstance(method.body[-1], MethodInvocation)
        self.assertEqual(evolver.reference_graph.in_degree(method_name), 1)

    def test_create_class(self):
        evolver = codevo.Evolver()
        with patch.object(codevo.evolver, 'random', return_value=1):
            klass = evolver.create_class()
            self.assertIsInstance(klass, ClassDeclaration)
            self.assertIs(evolver.inheritance_graph.node[klass.name]['class'], klass)
            self.assertEqual(evolver.inheritance_graph.in_degree(klass.name), 0)
