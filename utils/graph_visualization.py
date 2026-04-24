from __future__ import annotations

try:
    from pyvis.network import Network
except Exception:  # pragma: no cover - handled by UI fallback
    Network = None


def build_graph_html(edges: list[dict]) -> str | None:
    if Network is None or not edges:
        return None

    net = Network(
        height="720px",
        width="100%",
        bgcolor="#081526",
        font_color="#e5eefb",
        directed=False,
    )
    net.barnes_hut(gravity=-22000, central_gravity=0.22, spring_length=160, spring_strength=0.035, damping=0.88)

    teacher_nodes: set[str] = set()
    publication_nodes: set[str] = set()

    for edge in edges:
        teacher_node = f"teacher::{edge['teacher_id']}"
        publication_node = f"publication::{edge['publication_id']}"

        if teacher_node not in teacher_nodes:
            teacher_nodes.add(teacher_node)
            net.add_node(
                teacher_node,
                label=edge["teacher_name"],
                title=f"Викладач: {edge['teacher_name']}<br>Кафедра: {edge['department_name']}",
                group="teacher",
                color="#2dd4bf",
                shape="dot",
                size=20,
                borderWidth=2,
            )

        if publication_node not in publication_nodes:
            publication_nodes.add(publication_node)
            year_value = edge["year"] if edge["year"] is not None else "н/д"
            net.add_node(
                publication_node,
                label=edge["publication_title"][:48],
                title=f"Публікація: {edge['publication_title']}<br>Рік: {year_value}",
                group="publication",
                color="#38bdf8",
                shape="square",
                size=17,
                borderWidth=2,
            )

        net.add_edge(teacher_node, publication_node, color="#5b728f")

    net.set_options(
        """
        const options = {
          "nodes": {
            "font": {
              "size": 14,
              "face": "Manrope",
              "color": "#e5eefb"
            },
            "borderWidth": 2,
            "shadow": {
              "enabled": true,
              "color": "rgba(15, 23, 42, 0.55)",
              "size": 16,
              "x": 0,
              "y": 8
            }
          },
          "edges": {
            "smooth": false,
            "color": {
              "inherit": false
            },
            "width": 1.2,
            "selectionWidth": 2.6,
            "hoverWidth": 2.2
          },
          "layout": {
            "improvedLayout": true
          },
          "configure": {
            "enabled": false
          },
          "interaction": {
            "hover": true,
            "tooltipDelay": 120,
            "navigationButtons": true,
            "keyboard": true
          },
          "manipulation": {
            "enabled": false
          },
          "groups": {
            "teacher": {
              "color": "#2dd4bf"
            },
            "publication": {
              "color": "#38bdf8"
            }
          },
          "physics": {
            "enabled": true,
            "barnesHut": {
              "gravitationalConstant": -22000,
              "centralGravity": 0.22,
              "springLength": 160,
              "springConstant": 0.035,
              "damping": 0.88
            },
            "minVelocity": 0.75
          }
        }
        """
    )
    return net.generate_html()
