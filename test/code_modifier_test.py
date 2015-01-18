from unittest import TestCase
from codevo import CodeModifier, JavaPrinter


class CodeModifierTest(TestCase):
    def test_create_statement(self):
        code_modifier = CodeModifier()
        stmt = code_modifier.create_statement()
        printer = JavaPrinter()
        stmt.accept(printer)
        self.assertEqual('int var0 = 0;\n', printer.result)

    def test_delete_reference(self):
        code_modifier = CodeModifier()
        klass = code_modifier.create_class(None)
        method1 = code_modifier.create_method(klass)
        method2 = code_modifier.create_method(klass)
        code_modifier.create_reference(method1, method2, klass)
        self.assertEqual(1, len(method1.body))
        code_modifier.delete_reference(method1, method2, klass)
        self.assertEqual(0, len(method1.body))