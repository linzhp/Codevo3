from unittest import TestCase
from plyj.parser import Parser
from codevo import JavaPrinter


class JavaPrinterTest(TestCase):
    def test_print_empty_class(self):
        parser = Parser()
        tree = parser.parse_string('public class Foo extends Bar {}')
        printer = JavaPrinter()
        tree.accept(printer)
        self.assertEqual('''
public class Foo extends Bar {
}
        '''.strip(), printer.result)

    def test_print_method(self):
        parser = Parser()
        tree = parser.parse_string('''public class Foo{
                                        static void bar() { double d = Math.random(); }
                                    }''')
        printer = JavaPrinter()
        tree.accept(printer)
        self.assertEqual('''
public class Foo {
    static void bar() {
        double d = Math.random();
    }
}
        '''.strip(), printer.result)

    def test_print_statement(self):
        parser = Parser()
        tree = parser.parse_string('''public class Foo{
                                        static void bar() { Math.random(); }
                                    }''')
        printer = JavaPrinter()
        tree.accept(printer)
        self.assertEqual('''
public class Foo {
    static void bar() {
        Math.random();
    }
}
        '''.strip(), printer.result)