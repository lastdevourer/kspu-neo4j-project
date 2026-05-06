from __future__ import annotations

try:
    from pyvis.network import Network
except Exception:  # pragma: no cover - handled by UI fallback
    Network = None


def _palette(theme: str) -> dict[str, str]:
    if theme == "light":
        return {
            "bg": "#f7fbff",
            "font": "#10233d",
            "teacher": "#0ea5e9",
            "teacher_alt": "#14b8a6",
            "teacher_focus": "#f59e0b",
            "publication": "#2563eb",
            "department": "#0f766e",
            "department_alt": "#0369a1",
            "edge": "#7a8ea8",
            "edge_accent": "#d97706",
            "shadow": "rgba(148, 163, 184, 0.28)",
        }
    return {
        "bg": "#081526",
        "font": "#e5eefb",
        "teacher": "#2dd4bf",
        "teacher_alt": "#7dd3fc",
        "teacher_focus": "#f59e0b",
        "publication": "#38bdf8",
        "department": "#2dd4bf",
        "department_alt": "#38bdf8",
        "edge": "#5b728f",
        "edge_accent": "#f59e0b",
        "shadow": "rgba(15, 23, 42, 0.55)",
    }


def _base_network(height: str = "720px", theme: str = "dark") -> Network | None:
    if Network is None:
        return None
    colors = _palette(theme)
    net = Network(
        height=height,
        width="100%",
        bgcolor=colors["bg"],
        font_color=colors["font"],
        directed=False,
    )
    net.barnes_hut(gravity=-22000, central_gravity=0.22, spring_length=160, spring_strength=0.035, damping=0.88)
    net.set_options(
        f"""
        const options = {{
          "nodes": {{
            "font": {{ "size": 14, "face": "Manrope", "color": "{colors['font']}" }},
            "borderWidth": 2,
            "shadow": {{ "enabled": true, "color": "{colors['shadow']}", "size": 16, "x": 0, "y": 8 }}
          }},
          "edges": {{
            "smooth": false,
            "color": {{ "inherit": false }},
            "selectionWidth": 2.6,
            "hoverWidth": 2.2
          }},
          "layout": {{ "improvedLayout": true }},
          "configure": {{ "enabled": false }},
          "interaction": {{
            "hover": true,
            "tooltipDelay": 120,
            "navigationButtons": true,
            "keyboard": true
          }},
          "physics": {{
            "enabled": true,
            "barnesHut": {{
              "gravitationalConstant": -22000,
              "centralGravity": 0.22,
              "springLength": 160,
              "springConstant": 0.035,
              "damping": 0.88
            }},
            "minVelocity": 0.75
          }}
        }}
        """
    )
    return net


def build_bipartite_graph_html(edges: list[dict], focus_teacher_id: str = "", theme: str = "dark") -> str | None:
    net = _base_network(theme=theme)
    if net is None or not edges:
        return None

    colors = _palette(theme)
    teacher_nodes: set[str] = set()
    publication_nodes: set[str] = set()
    normalized_focus_teacher_id = focus_teacher_id.strip()

    for edge in edges:
        teacher_node = f"teacher::{edge['teacher_id']}"
        publication_node = f"publication::{edge['publication_id']}"

        if teacher_node not in teacher_nodes:
            teacher_nodes.add(teacher_node)
            is_focus_teacher = normalized_focus_teacher_id and str(edge.get("teacher_id") or "").strip() == normalized_focus_teacher_id
            net.add_node(
                teacher_node,
                label=edge["teacher_name"],
                title=f"Викладач: {edge['teacher_name']}<br>Кафедра: {edge['department_name']}",
                group="teacher",
                color=colors["teacher_focus"] if is_focus_teacher else colors["teacher"],
                shape="dot",
                size=26 if is_focus_teacher else 20,
            )

        if publication_node not in publication_nodes:
            publication_nodes.add(publication_node)
            year_value = edge["year"] if edge["year"] is not None else "н/д"
            net.add_node(
                publication_node,
                label=edge["publication_title"][:48],
                title=f"Публікація: {edge['publication_title']}<br>Рік: {year_value}",
                group="publication",
                color=colors["publication"],
                shape="square",
                size=17,
            )

        net.add_edge(teacher_node, publication_node, color=colors["edge"], width=1.2)

    return net.generate_html()


def build_coauthor_graph_html(edges: list[dict], theme: str = "dark") -> str | None:
    net = _base_network(theme=theme)
    if net is None or not edges:
        return None

    colors = _palette(theme)
    seen_nodes: set[str] = set()
    for edge in edges:
        source_id = f"teacher::{edge['source_id']}"
        target_id = f"teacher::{edge['target_id']}"
        if source_id not in seen_nodes:
            seen_nodes.add(source_id)
            net.add_node(
                source_id,
                label=edge["source_name"],
                title=f"Викладач: {edge['source_name']}<br>Кафедра: {edge['source_department']}",
                color=colors["teacher"],
                shape="dot",
                size=18 + min(int(edge.get("weight", 1)), 8),
            )
        if target_id not in seen_nodes:
            seen_nodes.add(target_id)
            net.add_node(
                target_id,
                label=edge["target_name"],
                title=f"Викладач: {edge['target_name']}<br>Кафедра: {edge['target_department']}",
                color=colors["teacher_alt"],
                shape="dot",
                size=18 + min(int(edge.get("weight", 1)), 8),
            )

        titles = "<br>".join(str(item) for item in edge.get("sample_titles", []) if item)
        net.add_edge(
            source_id,
            target_id,
            color=colors["edge_accent"],
            width=max(1.6, min(float(edge.get("weight", 1)) * 1.4, 8.0)),
            title=f"Спільні публікації: {edge.get('weight', 1)}<br>{titles}",
        )

    return net.generate_html()


def build_department_graph_html(edges: list[dict], theme: str = "dark") -> str | None:
    net = _base_network(theme=theme)
    if net is None or not edges:
        return None

    colors = _palette(theme)
    seen_nodes: set[str] = set()
    for edge in edges:
        source_id = f"department::{edge['source_id']}"
        target_id = f"department::{edge['target_id']}"
        if source_id not in seen_nodes:
            seen_nodes.add(source_id)
            net.add_node(
                source_id,
                label=edge["source_name"],
                title=f"Кафедра: {edge['source_name']}<br>Факультет: {edge['source_faculty']}",
                color=colors["department"],
                shape="box",
                size=24,
            )
        if target_id not in seen_nodes:
            seen_nodes.add(target_id)
            net.add_node(
                target_id,
                label=edge["target_name"],
                title=f"Кафедра: {edge['target_name']}<br>Факультет: {edge['target_faculty']}",
                color=colors["department_alt"],
                shape="box",
                size=24,
            )

        titles = "<br>".join(str(item) for item in edge.get("sample_titles", []) if item)
        net.add_edge(
            source_id,
            target_id,
            color=colors["edge_accent"],
            width=max(2.0, min(float(edge.get("weight", 1)) * 1.5, 9.0)),
            title=f"Спільні публікації: {edge.get('weight', 1)}<br>{titles}",
        )

    return net.generate_html()
