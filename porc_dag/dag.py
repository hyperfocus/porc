class DAG:
    def __init__(self):
        self.graph = {}
        self.resolved = []
        self.visited = set()
        self.temp_mark = set()

    def add_node(self, node):
        if node not in self.graph:
            self.graph[node] = []

    def add_dependency(self, node, depends_on):
        self.add_node(node)
        self.add_node(depends_on)
        self.graph[node].append(depends_on)

    def _visit(self, node):
        if node in self.temp_mark:
            raise ValueError(f"Cycle detected: {node} is part of a circular dependency")
        if node not in self.visited:
            self.temp_mark.add(node)
            for dep in self.graph[node]:
                self._visit(dep)
            self.temp_mark.remove(node)
            self.visited.add(node)
            self.resolved.append(node)

    def resolve(self):
        self.resolved.clear()
        self.visited.clear()
        self.temp_mark.clear()
        for node in self.graph:
            if node not in self.visited:
                self._visit(node)
        return list(reversed(self.resolved))