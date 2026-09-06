from collections import defaultdict, deque

from sqlalchemy import Engine, inspect

from jjuza_db.schema import TableInfo


def build_dependency_graph(
    engine: Engine,
    tables: list[TableInfo],
):
    """
    Build a graph where:

        child -> parent

    Example:

        orders -> users
    """

    inspector = inspect(engine)

    graph = defaultdict(set)

    for table in tables:
        foreign_keys = inspector.get_foreign_keys(
            table
        )
        for fk in foreign_keys:

            parent_table = fk["referred_table"]

            # Ignore self-referencing relationships.
            if parent_table == table:
                continue

            graph[table].add(
                fk['referred_table']
            )

    return graph


def get_generation_order(
    graph,
    target_table: str,
):
    """
    Return tables in dependency-first order.
    """

    required = set()

    queue = deque([target_table])

    while queue:

        current = queue.popleft()

        if current in required:
            continue

        required.add(current)

        for parent in graph.get(current, []):
            queue.append(parent)

    # --- Step 2: order them parents-before-children (Kahn's algorithm) ---
 
    # in_degree[table] = number of NOT-YET-PLACED dependencies (parents)
    # this table still has. A table is only safe to generate once this
    # count reaches 0.
    in_degree = {
        table: len(graph.get(table, set()) & required)
        for table in required
    }

    # children[parent] = tables that list `parent` as a dependency.
    # This is the reverse of `graph`, and lets us go directly from
    # "this table just got placed" to "these are the tables that were
    # waiting on it" -- no scanning the whole remaining set.
    children = defaultdict(list)
 
    for table in required:
        for parent in graph.get(table, set()):
            if parent in required:
                children[parent].append(table)
 
    # Seed the queue with every table that has no unmet dependencies --
    # these can be generated immediately.
    queue = deque(
        table for table in required
        if in_degree[table] == 0
    )

    ordered = []
 
    while queue:
 
        current = queue.popleft()
        ordered.append(current)
 
        # This table is done -- tell everyone waiting on it directly.
        for dependent in children[current]:
            in_degree[dependent] -= 1
            if in_degree[dependent] == 0:
                queue.append(dependent)
 
    if len(ordered) != len(required):
        # Some tables never hit in_degree == 0 -- they're stuck waiting
        # on each other in a cycle.
        raise ValueError(
            "Circular table dependency detected."
        )
 
    return ordered