from unittest import TestCase
from plyj.parser import Parser
from codevo.java_printer import JavaPrinter


class JavaPrinterTest(TestCase):
    def test_print_empty_class(self):
        parser = Parser()
        tree = parser.parse_string('public class Foo {}')
        printer = JavaPrinter()
        tree.accept(printer)
        self.assertEqual('''
public class Foo {
}
        '''.strip(), printer.result)


    def test_print_method(self):
        parser = Parser()
        tree = parser.parse_string('''public class Foo{
                                        static void bar() { int i = 1; }
                                    }''')
        printer = JavaPrinter()
        tree.accept(printer)
        self.assertEqual('''
public class Foo {
    static void bar() {
        int i = 1;
    }
}
        '''.strip(), printer.result)