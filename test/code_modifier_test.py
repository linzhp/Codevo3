from unittest import TestCase
from codevo import CodeModifier, JavaPrinter


class CodeModifierTest(TestCase):
    def test_create_statement(self):
        code_modifier = CodeModifier()
        stmt = code_modifier.create_statement()
        printer = JavaPrinter()
        stmt.accept(printer)
        self.assertEqual('int var0 = 0;\n', printer.result)