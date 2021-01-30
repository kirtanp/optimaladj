import networkx as nx

#TODO: check types of inputs and raise errors accordingly
#TODO: unit and integration tests using pytest; use the examples in the paper


class CausalGraph(nx.DiGraph):
    """
    A class for Causal Graphs. Inherits from nx.Digraph.

    Implements a number of methods for finding optimal adjustment sets.
    """
    def __init__(self):
        super().__init__(self)

    def ancestors_all(self, nodes):
        """Returns a set with all ancestors of nodes

        Parameters
        ----------
        nodes : list
           A list of nodes in the graph

        Returns
        ----------
        ancestors: set

        Notes
        -----
        A node is always an ancestor of itself.
        """
        ancestors = set()

        for node in nodes:
            ancestors_node = nx.ancestors(self, node)
            ancestors = ancestors.union(ancestors_node)

        ancestors = ancestors.union(set(nodes))

        return ancestors

    def backdoor_graph(self, treatment, outcome):
        """Returns the back-door graph associated with treatment and outcome

        Parameters
        ----------
        treatment : string
           A node in the graph
        outcome : string
           A node in the graph

        Returns
        ----------
        Gbd: nx.DiGraph()
        """
        Gbd = self.copy()

        for path in nx.all_simple_edge_paths(self, treatment, outcome):
            first_edge = path[0]
            Gbd.remove_edge(first_edge[0], first_edge[1])

        return Gbd

    def causal_vertices(self, treatment, outcome):
        """Returns the set of all vertices that lie in a causal path between treatment and outcome.

        Parameters
        ----------
        treatment : string
           A node in the graph
        outcome : string
           A node in the graph

        Returns
        ----------
        causal_vertices: set
        """
        causal_vertices = set()
        causal_paths = list(nx.all_simple_paths(self, source=treatment, target=outcome))

        for path in causal_paths:
            causal_vertices = causal_vertices.union(set(path))

        causal_vertices.remove(treatment)

        return causal_vertices

    def forbidden(self, treatment, outcome):
        """Returns the forbidden set with respect to treatment and outcome

        Parameters
        ----------
        treatment : string
           A node in the graph
        outcome : string
           A node in the graph

        Returns
        ----------
        forbidden: set
        """
        forbidden = set()

        for node in self.causal_vertices(treatment, outcome):
            forbidden = forbidden.union(nx.descendants(self, node).union(node))

        return forbidden.union(treatment)

    def ignore(self, treatment, outcome, L, N):
        """Returns the set of ignorable vertices with respect to treatment, outcome,
        L and N. Used in the construction of the H0 and H1 graphs.

        Parameters
        ----------
        treatment : string
            A node in the graph
        outcome : string
            A node in the graph
        L : list of strings
            Nodes in the graph
        N : list of strings
            Nodes in the graph

        Returns
        ----------
        ignore: set
        """
        set1 = set(self.ancestors_all(L + [treatment, outcome]))
        set1.remove(treatment)
        set1.remove(outcome)

        set2 = set(self.nodes()) - set(N)
        set2 = set2.union(self.forbidden(treatment, outcome))

        ignore = set1.intersection(set2)

        return ignore

    @staticmethod
    def unblocked(H, treatment, Z):
        """Returns the unblocked set of Z with respect to treatment

        Parameters
        ----------
        H : nx.Graph()
            Undirected graph
        treatment : string
            A node in the graph
        Z : list of strings
            Nodes in the graph

        Returns
        ----------
        unblocked: set
        """

        G2 = H.subgraph(H.nodes() - set(Z))

        B = nx.node_connected_component(G2, treatment)

        unblocked = set(nx.node_boundary(H, B))
        return unblocked

    def build_H0(self, treatment, outcome, L):
        """Returns the H0 graph associated with treatment, outcome and L

        Parameters
        ----------
        treatment : string
            A node in the graph
        outcome : string
            A node in the graph
        L : list of strings
            Nodes in the graph

        Returns
        ----------
        H0: nx.Graph()
        """
        # restriction to ancestors
        anc = self.ancestors_all(L + [treatment, outcome])
        G2 = self.subgraph(anc)

        # back-door graph
        G3 = G2.backdoor_graph(treatment, outcome)

        # moralization
        H0 = nx.moral_graph(G3)

        return H0

    def build_H1(self, treatment, outcome, L, N):
        """Returns the H0 graph associated with treatment, outcome, L and N

        Parameters
        ----------
        treatment : string
            A node in the graph
        outcome : string
            A node in the graph
        L : list of strings
            Nodes in the graph
        N : list of strings
            Nodes in the graph

        Returns
        ----------
        H1: nx.Graph()
        """
        H0 = self.build_H0(treatment, outcome, L)

        ignore_nodes = self.ignore(treatment, outcome, L, N)

        H1 = H0.copy().subgraph(H0.nodes() - ignore_nodes)
        H1 = nx.Graph(H1)
        vertices_list = list(H1.nodes())

        for i, node1 in enumerate(vertices_list):
            for node2 in vertices_list[(i + 1):]:
                for path in nx.all_simple_paths(H0, source=node1, target=node2):
                    if set(path).issubset(ignore_nodes.union(set([node1, node2]))):
                        H1.add_edge(node1, node2)
                        break
        for node in L:
            H1.add_edge(treatment, node)
            H1.add_edge(node, outcome)

        return H1

    def optimal_adj_set(self, treatment, outcome, L, N):
        """Returns the optimal adjustment set with respect to treatment, outcome, L and N

        Parameters
        ----------
        treatment : string
            A node in the graph
        outcome : string
            A node in the graph
        L : list of strings
            Nodes in the graph
        N : list of strings
            Nodes in the graph

        Returns
        ----------
        optimal: set
        """
        H1 = self.build_H1(treatment, outcome, L, N)
        if N == self.nodes() or set(N).issubset(self.ancestors_all(L + [treatment, outcome])):
            optimal = nx.node_boundary(H1, outcome)
            return optimal
        else:
            return "Conditions to guarantee the existence of an optimal adjustment set are not satisfied"

    def optimal_minimal_adj_set(self, treatment, outcome, L, N):
        """Returns the optimal minimal adjustment set with respect to treatment, outcome, L and N

        Parameters
        ----------
        treatment : string
            A node in the graph
        outcome : string
            A node in the graph
        L : list of strings
            Nodes in the graph
        N : list of strings
            Nodes in the graph

        Returns
        ----------
        optimal_minimal: set
        """

        H1 = self.build_H1(treatment, outcome, L, N)
        optimal_minimal = self.unblocked(H1, treatment, nx.node_boundary(H1, set([outcome])))
        return optimal_minimal

    @staticmethod
    def isInMinimum(H, treatment, outcome, node):
        """Returns true if and only if node is a member of a minimum size vertex
        cut between treatment and outcome in H

        Parameters
        ----------
        H : nx.Graph()
            Undirected graph
        treatment : string
            A node in the graph
        outcome : string
            A node in the graph
        node : string
            A node in the graph

        Returns
        ----------
        is_in_minimum: bool
        """
        m1 = len(nx.minimum_node_cut(H, treatment, outcome))

        H_mod = H.copy()
        H_mod.add_edge(treatment, node)
        H_mod.add_edge(outcome, node)

        m2 = len(nx.minimum_node_cut(H_mod, treatment, outcome))

        is_in_minimum = m1 == m2

        return is_in_minimum

    def optimal_minimum_adj_set(self, treatment, outcome, L, N):
        """Returns the optimal minimum adjustment set with respect to treatment, outcome, L and N

        Parameters
        ----------
        treatment : string
            A node in the graph
        outcome : string
            A node in the graph
        L : list of strings
            Nodes in the graph
        N : list of strings
            Nodes in the graph

        Returns
        ----------
        optimal_minimum: set
        """

        H1 = self.build_H1(treatment, outcome, L, N)

        optimal_minimum = set()

        if outcome not in nx.node_connected_component(H1, treatment):
            return optimal_minimum

        for path in nx.node_disjoint_paths(H1, s=outcome, t=treatment):
            for node in path:
                if node == outcome:
                    continue
                if self.isInMinimum(H1, treatment, outcome, node):
                    optimal_minimum.add(node)
                    break
        return optimal_minimum
