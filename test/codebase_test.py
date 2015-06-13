from unittest import TestCase
from codevo import Codebase, JavaPrinter


class CodebaseTest(TestCase):
    def test_create_statement(self):
        code_modifier = Codebase()
        stmt = code_modifier.create_statement()
        printer = JavaPrinter()
        stmt.accept(printer)
        self.assertEqual('int var0 = 0;\n', printer.result)

    def test_delete_reference(self):
        code_modifier = Codebase()
        klass = code_modifier.create_class(None)
        method1 = code_modifier.create_method(klass.name)
        method2 = code_modifier.create_method(klass.name)
        code_modifier.add_method_call(method1.name, method2.name)
        self.assertEqual(1, len(method1.body))
        code_modifier.delete_method_call(method1, method2, klass)
        self.assertEqual(0, len(method1.body))