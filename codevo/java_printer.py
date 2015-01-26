from plyj.model import Visitor


class JavaPrinter(Visitor):
    """
    Reason for traversing substree in "visit" method:
    * subnodes may be mixed with other strings during printing

    Reason for not implementing it in __str__ method of AST nodes:
    * indents are context-dependent
    """
    def __init__(self):
        super(JavaPrinter, self).__init__()
        self.result = ''
        self.indent = 0

    def visit_ClassDeclaration(self, class_declaration):
        self.result += '    ' * self.indent
        for m in class_declaration.modifiers:
            self.result += m + ' '

        self.result += 'class ' + class_declaration.name + ' '
        if class_declaration.extends:
            self.result += 'extends '
            class_declaration.extends.accept(self)
            self.result += ' '
        self.result += '{\n'
        self.indent += 1
        for elem in class_declaration.body:
            elem.accept(self)
        self.indent -= 1
        self.result += '    ' * self.indent + '}'
        return False

    def visit_MethodDeclaration(self, method_declaration):
        self.result += '    ' * self.indent
        for m in method_declaration.modifiers:
            self.result += m + ' '
        self.result += method_declaration.return_type
        self.result += ' '
        self.result += method_declaration.name
        self.result += '('
        self.result += ') {\n'
        self.indent += 1
        for stmt in method_declaration.body:
            stmt.accept(self)
        self.indent -= 1
        self.result += '    ' * self.indent + '}\n'
        return False

    def visit_VariableDeclaration(self, variable_declaration):
        self.result += '    ' * self.indent
        self.result += variable_declaration.type
        self.result += ' '
        for declarator in variable_declaration.variable_declarators:
            declarator.accept(self)
        self.result += ';\n'
        return False

    def visit_VariableDeclarator(self, variable_declarator):
        variable_declarator.variable.accept(self)
        self.result += ' = '
        variable_declarator.initializer.accept(self)
        return False

    def visit_Literal(self, literal):
        self.result += str(literal.value)
        return False

    def visit_Variable(self, variable):
        self.result += variable.name
        return False

    def visit_Name(self, name):
        self.result += name.value
        return False

    def visit_MethodInvocation(self, method):
        method.target.accept(self)
        self.result += '.' + method.name + '()'
        return False

    def visit_Type(self, type):
        type.name.accept(self)
        return False

    def visit_ExpressionStatement(self, stmt):
        self.result += '    ' * self.indent
        stmt.expression.accept(self)
        self.result += ';\n'
        return False