from graphviz import Digraph

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

def process_blueprint(blueprint_json, output_prefix="blueprint_dag"):
    dag = DAG()
    for module in blueprint_json["modules"]:
        name = module["name"]
        for dep in module.get("depends_on", []):
            dag.add_dependency(name, dep)

    execution_order = dag.resolve()

    dot = Digraph()
    for module in blueprint_json["modules"]:
        name = module["name"]
        dot.node(name)
        for dep in module.get("depends_on", []):
            dot.edge(dep, name)

    image_path = f"{output_prefix}.png"
    dot.render(output_prefix, format="png", cleanup=True)
    return execution_order, image_path