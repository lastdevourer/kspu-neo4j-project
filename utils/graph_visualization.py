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
        bgcolor="#fffaf0",
        font_color="#102a43",
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
                title=f"????????: {edge['teacher_name']}<br>???????: {edge['department_name']}",
                color="#0f766e",
                shape="dot",
                size=18,
            )

        if publication_node not in publication_nodes:
            publication_nodes.add(publication_node)
            year_value = edge["year"] if edge["year"] is not None else "?/?"
            net.add_node(
                publication_node,
                label=edge["publication_title"][:48],
                title=f"??????????: {edge['publication_title']}<br>???: {year_value}",
                color="#c2410c",
                shape="square",
                size=16,
            )

        net.add_edge(teacher_node, publication_node, color="#94a3b8")

    net.set_options(
        """
        const options = {
          "nodes": {
            "font": {
              "size": 14,
              "face": "Trebuchet MS"
            }
          },
          "edges": {
            "smooth": false,
            "color": {
              "inherit": false
            }
          },
          "interaction": {
            "hover": true,
            "tooltipDelay": 120
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
