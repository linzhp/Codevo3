from plyj.model import *

class CodeModifier:
    def __init__(self):
        self.counter = 0

    def create_method(self, class_node):
        """
        The created methods are static methods for now
        """
        method = MethodDeclaration(
            'method' + str(self.counter),
            body=[], modifiers=['static'])
        self.counter += 1
        class_node.body.append(method)
        return method

    def delete_method(self, class_node, method):
        class_node.body.remove(method)

    def create_class(self, superclass_name):
        klass = ClassDeclaration('Class' + str(self.counter), [])
        if superclass_name:
            klass.extends = Type(Name(superclass_name))
        self.counter += 1
        return klass

    def create_reference(self, from_method, to_method, target):
        ref = MethodInvocation(to_method.name, target=Name(target.name))
        from_method.body.append(ref)
        return ref

    def delete_reference(self, from_method, to_method, target):
        to_delete = []
        for stmt in from_method.body:
            if isinstance(stmt, MethodInvocation) and \
                    stmt.name == to_method.name:
                to_delete.append(stmt)

        for stmt in to_delete:
            from_method.body.remove(stmt)

    def create_statement(self):
        """
        Generate a statement. May use a fuzzer to generate a variety of statements
        :return:
        """
        var = VariableDeclaration(
            type='int',
            variable_declarators=[VariableDeclarator(
                variable=Variable(
                    name='var' + str(self.counter)
                ),
                initializer=Literal(self.counter)
            )]
        )
        self.counter += 1
        return var