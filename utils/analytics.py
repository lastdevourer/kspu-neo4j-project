from __future__ import annotations

from collections import Counter
from itertools import combinations

try:
    import networkx as nx
except Exception:  # pragma: no cover - handled in UI fallback
    nx = None


OFFICIAL_STATUSES = {"Офіційно підтверджено"}
CONFIRMED_STATUSES = {"Офіційно підтверджено", "Підтверджено"}


def filter_publications_by_scope(rows: list[dict], scope: str) -> list[dict]:
    if scope == "Підтверджені":
        return [row for row in rows if str(row.get("status") or "") in CONFIRMED_STATUSES]
    if scope == "Офіційні":
        return [row for row in rows if str(row.get("status") or "") in OFFICIAL_STATUSES]
    return rows


def build_teacher_publication_rankings(
    publications: list[dict],
    teachers: list[dict],
    limit: int,
) -> list[dict]:
    teacher_meta = {
        str(row.get("full_name") or "").strip(): {
            "department": str(row.get("department_name") or "").strip(),
        }
        for row in teachers
        if str(row.get("full_name") or "").strip()
    }
    counts: Counter[str] = Counter()
    for publication in publications:
        authors = {str(author).strip() for author in (publication.get("authors") or []) if str(author).strip()}
        for author in authors:
            if author in teacher_meta:
                counts[author] += 1

    rows = [
        {
            "teacher": teacher,
            "department": teacher_meta.get(teacher, {}).get("department", ""),
            "publications": total,
        }
        for teacher, total in counts.items()
    ]
    rows.sort(key=lambda item: (-item["publications"], item["teacher"]))
    return rows[:limit]


def build_coauthor_pair_rankings(publications: list[dict], teachers: list[dict], limit: int) -> list[dict]:
    teacher_names = {str(row.get("full_name") or "").strip() for row in teachers if str(row.get("full_name") or "").strip()}
    pair_data: dict[tuple[str, str], dict[str, object]] = {}
    for publication in publications:
        title = str(publication.get("title") or "").strip()
        authors = sorted({str(author).strip() for author in (publication.get("authors") or []) if str(author).strip() in teacher_names})
        for teacher_a, teacher_b in combinations(authors, 2):
            key = (teacher_a, teacher_b)
            if key not in pair_data:
                pair_data[key] = {
                    "teacher_a": teacher_a,
                    "teacher_b": teacher_b,
                    "shared_publications": 0,
                    "sample_publications": [],
                }
            pair_data[key]["shared_publications"] = int(pair_data[key]["shared_publications"]) + 1
            if title and title not in pair_data[key]["sample_publications"]:
                pair_data[key]["sample_publications"].append(title)

    rows = list(pair_data.values())
    rows.sort(key=lambda item: (-int(item["shared_publications"]), str(item["teacher_a"]), str(item["teacher_b"])))
    return rows[:limit]


def build_centrality_edges(publications: list[dict], teachers: list[dict]) -> list[dict]:
    teacher_meta = {
        str(row.get("full_name") or "").strip(): str(row.get("id") or "").strip()
        for row in teachers
        if str(row.get("full_name") or "").strip()
    }
    pair_weights: Counter[tuple[str, str]] = Counter()
    for publication in publications:
        authors = sorted({str(author).strip() for author in (publication.get("authors") or []) if str(author).strip() in teacher_meta})
        for teacher_a, teacher_b in combinations(authors, 2):
            pair_weights[(teacher_a, teacher_b)] += 1

    rows = []
    for (teacher_a, teacher_b), weight in pair_weights.items():
        rows.append(
            {
                "source_id": teacher_meta.get(teacher_a) or teacher_a,
                "source_name": teacher_a,
                "target_id": teacher_meta.get(teacher_b) or teacher_b,
                "target_name": teacher_b,
                "weight": int(weight),
            }
        )
    rows.sort(key=lambda item: (-int(item["weight"]), str(item["source_name"]), str(item["target_name"])))
    return rows


def build_publication_source_rows(publications: list[dict]) -> list[dict]:
    counts: Counter[str] = Counter()
    for row in publications:
        source_value = str(row.get("source") or "").strip()
        sources = [item.strip() for item in source_value.split(";") if item.strip()] or ["Невідомо"]
        for source in sources:
            counts[source] += 1
    rows = [{"source": source, "publications": total} for source, total in counts.items()]
    rows.sort(key=lambda item: (-int(item["publications"]), str(item["source"])))
    return rows


def calculate_centrality_rows(edges: list[dict]) -> list[dict]:
    if nx is None:
        return []

    graph = nx.Graph()
    for edge in edges:
        source_id = edge["source_id"]
        target_id = edge["target_id"]
        graph.add_node(source_id, label=edge["source_name"])
        graph.add_node(target_id, label=edge["target_name"])
        graph.add_edge(source_id, target_id, weight=edge.get("weight", 1))

    if graph.number_of_nodes() == 0:
        return []

    degree = nx.degree_centrality(graph)
    betweenness = nx.betweenness_centrality(graph) if graph.number_of_edges() else {node: 0.0 for node in graph.nodes}

    rows = []
    for node in graph.nodes:
        weighted_connections = sum(graph[node][neighbor].get("weight", 1) for neighbor in graph.neighbors(node))
        rows.append(
            {
                "teacher": graph.nodes[node]["label"],
                "connections": graph.degree[node],
                "weighted_connections": weighted_connections,
                "degree_centrality": round(degree[node], 4),
                "betweenness_centrality": round(betweenness[node], 4),
            }
        )

    rows.sort(
        key=lambda item: (
            item["degree_centrality"],
            item["betweenness_centrality"],
            item["weighted_connections"],
            item["teacher"],
        ),
        reverse=True,
    )
    return rows


def build_diploma_summary(
    top_teachers: list[dict],
    top_pairs: list[dict],
    centrality_rows: list[dict],
) -> str:
    insights: list[str] = []

    if top_teachers:
        leader = top_teachers[0]
        insights.append(
            f"Найвищу публікаційну активність демонструє {leader['teacher']}, "
            f"що може свідчити про роль локального лідера наукової продуктивності."
        )

    if top_pairs:
        pair = top_pairs[0]
        insights.append(
            f"Найсильніша пара співавторів — {pair['teacher_a']} та {pair['teacher_b']}; "
            f"це показує стабільну дослідницьку взаємодію між викладачами."
        )

    if centrality_rows:
        hub = centrality_rows[0]
        insights.append(
            f"За degree centrality найбільш центральним вузлом є {hub['teacher']}, "
            f"тобто саме цей викладач має найбільшу кількість зв'язків у мережі співавторства."
        )

    if len(centrality_rows) > 1 and centrality_rows[0]["betweenness_centrality"] > 0:
        bridge = max(centrality_rows, key=lambda row: row["betweenness_centrality"])
        insights.append(
            f"Показник betweenness centrality виділяє {bridge['teacher']} як можливий місток між "
            f"окремими науковими групами або кафедральними підмережами."
        )

    if not insights:
        return (
            "Після появи даних сервіс зможе показати продуктивних авторів, сталі пари співавторів "
            "та центральні вузли академічної мережі, що важливо для аналітичної частини дипломної роботи."
        )

    return " ".join(insights)
