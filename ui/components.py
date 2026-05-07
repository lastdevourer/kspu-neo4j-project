from __future__ import annotations

import re
from textwrap import dedent
from html import escape, unescape
from typing import TYPE_CHECKING, Any

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

from config import get_connection_help_text, get_neo4j_config
from data.loaders import load_teachers_seed
from data.seed_data import DEPARTMENTS, FACULTIES

if TYPE_CHECKING:
    from services.neo4j_service import Neo4jService


def setup_page(title: str) -> None:
    st.set_page_config(
        page_title=title,
        layout="wide",
        page_icon="🎓",
        initial_sidebar_state="expanded",
    )
    apply_theme()


def apply_theme() -> None:
    dark_theme_css = """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Manrope:wght@400;500;600;700;800&family=Space+Grotesk:wght@500;700&display=swap');

        :root {
            --bg-main: #07111f;
            --bg-shell: rgba(7, 17, 31, 0.86);
            --bg-card: rgba(10, 25, 47, 0.78);
            --bg-card-strong: rgba(14, 34, 61, 0.92);
            --bg-card-soft: rgba(11, 29, 53, 0.62);
            --line-soft: rgba(148, 163, 184, 0.16);
            --line-strong: rgba(96, 165, 250, 0.20);
            --text-main: #e5eefb;
            --text-soft: #9fb3c9;
            --text-muted: #6f88a5;
            --teal: #2dd4bf;
            --cyan: #38bdf8;
            --amber: #f59e0b;
            --shadow: 0 22px 60px rgba(2, 8, 23, 0.38);
        }

        html, body, [class*="css"] {
            font-family: "Manrope", sans-serif;
        }

        .stApp {
            background:
                radial-gradient(circle at 12% 18%, rgba(45, 212, 191, 0.16), transparent 28%),
                radial-gradient(circle at 86% 14%, rgba(56, 189, 248, 0.14), transparent 26%),
                radial-gradient(circle at 52% 88%, rgba(245, 158, 11, 0.10), transparent 24%),
                linear-gradient(180deg, #07111f 0%, #081526 42%, #091827 100%);
            color: var(--text-main);
        }

        .stApp::before {
            content: "";
            position: fixed;
            inset: 0;
            pointer-events: none;
            background-image:
                linear-gradient(rgba(148, 163, 184, 0.05) 1px, transparent 1px),
                linear-gradient(90deg, rgba(148, 163, 184, 0.05) 1px, transparent 1px);
            background-size: 72px 72px;
            mask-image: radial-gradient(circle at center, black 38%, transparent 88%);
            opacity: 0.24;
        }

        [data-testid="stAppViewContainer"] {
            background: transparent;
        }

        [data-testid="stHeader"] {
            background: rgba(7, 17, 31, 0.82);
            backdrop-filter: blur(10px);
            border-bottom: 1px solid rgba(96, 165, 250, 0.08);
        }

        .block-container {
            max-width: 1320px;
            padding-top: 4.8rem;
            padding-bottom: 2.7rem;
        }

        div[data-testid="stVerticalBlock"] > div:has(> .section-heading),
        div[data-testid="stVerticalBlock"] > div:has(> .hero-card),
        div[data-testid="stVerticalBlock"] > div:has(> .info-card),
        div[data-testid="stVerticalBlock"] > div:has(> .summary-strip),
        div[data-testid="stVerticalBlock"] > div:has(> .kv-card),
        div[data-testid="stVerticalBlock"] > div:has(> .empty-state) {
            margin-bottom: 0.55rem;
        }

        h1, h2, h3 {
            font-family: "Space Grotesk", "Manrope", sans-serif;
            color: var(--text-main);
            letter-spacing: -0.04em;
        }

        h3 {
            font-size: 1.55rem;
            margin-bottom: 0.7rem;
        }

        p, li, label, span, div {
            color: inherit;
        }

        .hero-card {
            position: relative;
            overflow: hidden;
            border: 1px solid var(--line-strong);
            background:
                linear-gradient(135deg, rgba(18, 38, 63, 0.94), rgba(8, 24, 43, 0.96)),
                radial-gradient(circle at top right, rgba(56, 189, 248, 0.22), transparent 32%);
            border-radius: 30px;
            padding: 1.7rem 1.9rem;
            box-shadow: var(--shadow);
            margin-bottom: 1rem;
            isolation: isolate;
            text-align: center;
        }

        .hero-card::before {
            content: "";
            position: absolute;
            width: 360px;
            height: 360px;
            right: -120px;
            top: -120px;
            border-radius: 999px;
            background: radial-gradient(circle, rgba(45, 212, 191, 0.20) 0%, rgba(45, 212, 191, 0.02) 58%, transparent 70%);
            filter: blur(6px);
            animation: drift 16s ease-in-out infinite;
            z-index: -1;
        }

        .hero-kicker {
            display: inline-block;
            border-radius: 999px;
            padding: 0.45rem 0.85rem;
            background: rgba(45, 212, 191, 0.10);
            color: #8cf0df;
            font-size: 0.8rem;
            font-weight: 800;
            text-transform: uppercase;
            letter-spacing: 0.12em;
            margin-bottom: 0.9rem;
            border: 1px solid rgba(45, 212, 191, 0.16);
        }

        .hero-title {
            max-width: 980px;
            font-size: clamp(1.75rem, 2.35vw, 2.8rem);
            font-weight: 800;
            line-height: 1.02;
            margin-bottom: 0.22rem;
        }

        .hero-subtitle {
            font-size: 1.02rem;
            line-height: 1.72;
            color: var(--text-soft);
            max-width: 920px;
            margin: 0 auto;
        }

        .info-card {
            border: 1px solid var(--line-soft);
            border-radius: 24px;
            background:
                linear-gradient(180deg, rgba(10, 25, 47, 0.88), rgba(8, 22, 41, 0.92));
            padding: 1.18rem 1.22rem;
            box-shadow: var(--shadow);
            backdrop-filter: blur(16px);
            margin-bottom: 0.82rem;
            text-align: center;
        }

        .info-card h3 {
            margin-top: 0.1rem;
            margin-bottom: 0.7rem;
        }

        .info-card div {
            color: var(--text-soft);
            line-height: 1.72;
        }

        .section-heading {
            margin: 0.12rem 0 0.9rem;
            text-align: center;
        }

        .section-heading-title {
            font-family: "Space Grotesk", "Manrope", sans-serif;
            font-size: 1.25rem;
            font-weight: 700;
            letter-spacing: -0.04em;
            color: var(--text-main);
        }

        .section-heading-subtitle {
            margin-top: 0.28rem;
            color: var(--text-soft);
            font-size: 0.95rem;
            line-height: 1.65;
            max-width: 860px;
            margin-left: auto;
            margin-right: auto;
        }

        .empty-state {
            border: 1px dashed rgba(148, 163, 184, 0.18);
            border-radius: 24px;
            background: rgba(8, 22, 41, 0.72);
            padding: 1.2rem 1.25rem;
            box-shadow: var(--shadow);
            text-align: center;
        }

        .empty-state-title {
            font-family: "Space Grotesk", "Manrope", sans-serif;
            font-size: 1.1rem;
            font-weight: 700;
            color: var(--text-main);
            margin-bottom: 0.4rem;
        }

        .empty-state-body {
            color: var(--text-soft);
            line-height: 1.7;
        }

        .summary-strip {
            border: 1px solid var(--line-soft);
            border-radius: 24px;
            background: linear-gradient(180deg, rgba(10, 25, 47, 0.78), rgba(8, 22, 41, 0.92));
            padding: 1rem 1.05rem;
            box-shadow: var(--shadow);
            margin-bottom: 0.82rem;
            text-align: center;
        }

        .summary-strip-title {
            color: var(--text-soft);
            text-transform: uppercase;
            letter-spacing: 0.08em;
            font-size: 0.75rem;
            font-weight: 800;
            margin-bottom: 0.4rem;
        }

        .summary-strip-value {
            font-family: "Space Grotesk", "Manrope", sans-serif;
            font-size: clamp(1.1rem, 1.55vw, 1.55rem);
            font-weight: 700;
            letter-spacing: -0.04em;
            color: var(--text-main);
            word-break: break-word;
            line-height: 1.15;
        }

        .summary-strip-caption {
            margin-top: 0.35rem;
            color: var(--text-muted);
            font-size: 0.88rem;
            line-height: 1.55;
        }

        .kv-card {
            border: 1px solid var(--line-soft);
            border-radius: 24px;
            background:
                linear-gradient(180deg, rgba(10, 25, 47, 0.88), rgba(8, 22, 41, 0.94));
            padding: 1.1rem 1.2rem;
            box-shadow: var(--shadow);
            backdrop-filter: blur(16px);
            margin-bottom: 0.82rem;
        }

        .kv-title {
            font-family: "Space Grotesk", "Manrope", sans-serif;
            font-size: 1.15rem;
            font-weight: 700;
            margin-bottom: 0.75rem;
            color: var(--text-main);
        }

        .kv-row {
            display: flex;
            justify-content: space-between;
            gap: 1rem;
            border-top: 1px dashed rgba(148, 163, 184, 0.14);
            padding: 0.72rem 0;
            font-size: 0.96rem;
        }

        .kv-row:first-of-type {
            border-top: none;
            padding-top: 0;
        }

        .kv-label {
            color: var(--text-soft);
        }

        .kv-value {
            font-weight: 700;
            color: var(--text-main);
            text-align: right;
            word-break: break-word;
            max-width: 64%;
        }

        div[data-testid="stMetric"] {
            position: relative;
            overflow: hidden;
            background:
                linear-gradient(180deg, rgba(10, 25, 47, 0.84), rgba(8, 22, 41, 0.96));
            border: 1px solid var(--line-soft);
            border-radius: 24px;
            padding: 1.05rem 1.1rem;
            min-height: 7.4rem;
            box-shadow: var(--shadow);
            text-align: center;
        }

        div[data-testid="stMetric"] > div {
            align-items: center;
            text-align: center;
        }

        div[data-testid="stMetric"]::after {
            content: "";
            position: absolute;
            inset: auto 0 0 0;
            height: 3px;
            background: linear-gradient(90deg, var(--teal), var(--cyan), var(--amber));
            opacity: 0.92;
        }

        div[data-testid="stMetricLabel"] {
            font-size: 0.84rem;
            color: var(--text-soft);
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.06em;
            line-height: 1.35;
            justify-content: center;
            text-align: center;
        }

        div[data-testid="stMetricLabel"] p {
            line-height: 1.35;
            margin-bottom: 0;
            text-align: center;
            width: 100%;
        }

        div[data-testid="stMetricValue"] {
            font-size: 2rem;
            color: var(--text-main);
            font-family: "Space Grotesk", "Manrope", sans-serif;
            letter-spacing: -0.04em;
            justify-content: center;
            text-align: center;
            width: 100%;
        }

        div[data-testid="stMetricValue"] > div,
        div[data-testid="stMetricValue"] p {
            width: 100%;
            text-align: center;
        }

        div.stButton > button {
            min-height: 3rem;
            border-radius: 18px;
            border: 1px solid rgba(56, 189, 248, 0.24);
            background: linear-gradient(180deg, rgba(17, 39, 66, 0.95), rgba(10, 25, 47, 0.98));
            color: var(--text-main);
            font-weight: 700;
            box-shadow: 0 18px 32px rgba(2, 8, 23, 0.28);
            transition: transform 0.2s ease, border-color 0.2s ease, box-shadow 0.2s ease;
        }

        div.stButton > button:hover {
            border-color: rgba(45, 212, 191, 0.5);
            box-shadow: 0 18px 42px rgba(45, 212, 191, 0.10);
            transform: translateY(-1px);
        }

        div.stButton > button[kind="tertiary"] {
            min-height: auto;
            min-width: auto;
            padding: 0;
            border: none;
            background: transparent;
            color: var(--text-main);
            box-shadow: none;
            font-size: 1.25rem;
            font-weight: 700;
            line-height: 1.2;
            justify-content: flex-start;
        }

        div.stButton > button[kind="tertiary"]:hover {
            background: transparent;
            box-shadow: none;
            color: #8cf0df;
            text-decoration: underline;
            transform: none;
        }

        .download-link-button {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            width: 100%;
            min-height: 3rem;
            padding: 0.8rem 1rem;
            border-radius: 18px;
            border: 1px solid rgba(56, 189, 248, 0.24);
            background: linear-gradient(180deg, rgba(17, 39, 66, 0.95), rgba(10, 25, 47, 0.98));
            color: var(--text-main) !important;
            text-decoration: none !important;
            font-weight: 700;
            box-shadow: 0 18px 32px rgba(2, 8, 23, 0.28);
            transition: transform 0.2s ease, border-color 0.2s ease, box-shadow 0.2s ease;
            box-sizing: border-box;
        }

        .download-link-button:hover {
            border-color: rgba(45, 212, 191, 0.5);
            box-shadow: 0 18px 42px rgba(45, 212, 191, 0.10);
            transform: translateY(-1px);
        }

        div[data-baseweb="select"] > div,
        div[data-baseweb="base-input"] > div,
        .stTextInput > div > div,
        .stNumberInput > div > div {
            border-radius: 18px;
            background: rgba(9, 24, 43, 0.88);
            border: 1px solid rgba(96, 165, 250, 0.15);
            color: var(--text-main);
            box-shadow: 0 14px 26px rgba(2, 8, 23, 0.18);
        }

        label[data-testid="stWidgetLabel"] p {
            color: var(--text-soft);
            font-weight: 700;
        }

        [data-testid="stSidebar"] {
            background:
                linear-gradient(180deg, rgba(4, 13, 26, 0.96), rgba(8, 22, 41, 0.98));
            border-right: 1px solid rgba(96, 165, 250, 0.10);
        }

        [data-testid="stSidebar"] > div:first-child {
            background: transparent;
        }

        [data-testid="stSidebarNav"] {
            background: transparent;
            padding-top: 0.4rem;
        }

        [data-testid="stSidebarNav"] ul {
            gap: 0.38rem;
        }

        [data-testid="stSidebarNavLink"] {
            border-radius: 16px;
            background: rgba(255, 255, 255, 0.01);
            border: 1px solid transparent;
            transition: background 0.18s ease, border-color 0.18s ease, transform 0.18s ease;
        }

        [data-testid="stSidebarNavLink"]:hover {
            background: rgba(45, 212, 191, 0.08);
            border-color: rgba(45, 212, 191, 0.16);
            transform: translateX(2px);
        }

        [data-testid="stSidebarNavLink"] span {
            color: var(--text-soft);
            font-weight: 700;
        }

        [data-testid="stSidebarNavLink"][aria-current="page"] {
            background: linear-gradient(90deg, rgba(45, 212, 191, 0.14), rgba(56, 189, 248, 0.08));
            border-color: rgba(45, 212, 191, 0.22);
            box-shadow: inset 0 0 0 1px rgba(45, 212, 191, 0.06);
        }

        [data-testid="stSidebarNavLink"][aria-current="page"] span {
            color: #f3fbff;
        }

        [data-testid="stDataFrame"] {
            border: 1px solid var(--line-soft);
            border-radius: 24px;
            overflow: hidden;
            box-shadow: var(--shadow);
            background: rgba(8, 22, 41, 0.84);
        }

        [data-testid="stDataFrame"] [role="columnheader"] {
            justify-content: center;
            text-align: center;
            font-weight: 800;
        }

        [data-testid="stDataFrame"] [role="gridcell"] {
            align-items: center;
            line-height: 1.45;
        }

        [data-testid="stDataFrame"] [role="row"] {
            min-height: 2.7rem;
        }

        [data-testid="stDataFrame"] [role="row"]:hover {
            background: rgba(56, 189, 248, 0.05);
        }

        [data-testid="stTable"] {
            border-radius: 24px;
            overflow: hidden;
        }

        [data-testid="stTable"] th {
            text-align: center;
            font-weight: 800;
        }

        [data-testid="stTable"] td {
            vertical-align: middle;
        }

        [data-testid="stAlert"] {
            background: rgba(14, 34, 61, 0.92);
            color: var(--text-main);
            border: 1px solid rgba(96, 165, 250, 0.16);
            border-radius: 20px;
            box-shadow: var(--shadow);
        }

        .stAlert p {
            color: var(--text-soft);
        }

        [data-testid="stExpander"] {
            border: 1px solid var(--line-soft);
            border-radius: 20px;
            background: rgba(9, 24, 43, 0.74);
            margin-bottom: 0.9rem;
        }

        [data-testid="stExpander"] details summary p {
            color: var(--text-main);
            font-weight: 700;
        }

        div[role="dialog"] {
            width: min(96vw, 1520px) !important;
            max-width: 96vw !important;
            border-radius: 28px !important;
            border: 1px solid rgba(96, 165, 250, 0.18) !important;
            background:
                linear-gradient(180deg, rgba(8, 22, 41, 0.97), rgba(7, 19, 35, 0.98)) !important;
            box-shadow: 0 28px 100px rgba(2, 8, 23, 0.52) !important;
            backdrop-filter: blur(18px);
        }

        div[data-baseweb="tab-list"] {
            margin-bottom: 0.55rem;
        }

        div[role="dialog"] [data-testid="stVerticalBlock"] {
            gap: 0.8rem;
        }

        div[role="dialog"] h1,
        div[role="dialog"] h2,
        div[role="dialog"] h3,
        div[role="dialog"] label,
        div[role="dialog"] p,
        div[role="dialog"] span {
            color: var(--text-main);
        }

        div[role="dialog"]::before {
            content: "";
            position: absolute;
            inset: 0;
            border-radius: 28px;
            pointer-events: none;
            background:
                radial-gradient(circle at top right, rgba(45, 212, 191, 0.12), transparent 24%),
                radial-gradient(circle at bottom left, rgba(56, 189, 248, 0.10), transparent 28%);
        }

        [data-testid="stMarkdownContainer"] p code,
        code {
            background: rgba(45, 212, 191, 0.10);
            color: #94f5e7;
            border-radius: 10px;
            padding: 0.16rem 0.42rem;
            border: 1px solid rgba(45, 212, 191, 0.12);
        }

        .sidebar-brand {
            margin-bottom: 1.1rem;
            padding: 0.1rem 0 0.95rem;
            border-bottom: 1px solid rgba(148, 163, 184, 0.12);
        }

        .sidebar-brand-kicker {
            color: var(--text-muted);
            text-transform: uppercase;
            font-size: 0.7rem;
            letter-spacing: 0.16em;
            font-weight: 800;
            margin-bottom: 0.24rem;
        }

        .sidebar-brand-title {
            font-family: "Space Grotesk", "Manrope", sans-serif;
            font-size: 1.02rem;
            font-weight: 700;
            color: var(--text-main);
            line-height: 1.28;
        }

        .sidebar-section-label {
            margin: 1rem 0 0.48rem;
            color: var(--text-soft);
            text-transform: uppercase;
            letter-spacing: 0.08em;
            font-size: 0.76rem;
            font-weight: 800;
        }

        .sidebar-model {
            margin-top: 1.25rem;
            padding-top: 1rem;
            border-top: 1px solid rgba(148, 163, 184, 0.10);
            color: var(--text-muted);
            font-size: 0.82rem;
            line-height: 1.7;
        }

        @keyframes drift {
            0% { transform: translate3d(0, 0, 0) scale(1); }
            50% { transform: translate3d(-24px, 18px, 0) scale(1.05); }
            100% { transform: translate3d(0, 0, 0) scale(1); }
        }

        @media (max-width: 960px) {
            .block-container {
                padding-top: 3.05rem;
                padding-bottom: 1.4rem;
            }

            .hero-card {
                padding: 1.3rem 1.1rem;
                border-radius: 24px;
            }

            div[data-testid="stMetricValue"] {
                font-size: 1.65rem;
            }
        }
        </style>
        """

    light_theme_css = """
        <style>
        :root {
            --bg-main: #f4f8fc;
            --bg-shell: rgba(255, 255, 255, 0.88);
            --bg-card: rgba(255, 255, 255, 0.95);
            --bg-card-strong: rgba(255, 255, 255, 0.98);
            --bg-card-soft: rgba(247, 250, 253, 0.92);
            --line-soft: rgba(37, 99, 235, 0.12);
            --line-strong: rgba(14, 165, 233, 0.18);
            --text-main: #10233d;
            --text-soft: #17324d;
            --text-muted: #274867;
            --shadow: 0 18px 42px rgba(15, 23, 42, 0.08);
        }

        .stApp {
            background:
                radial-gradient(circle at 10% 15%, rgba(14, 165, 233, 0.08), transparent 26%),
                radial-gradient(circle at 88% 12%, rgba(45, 212, 191, 0.08), transparent 24%),
                linear-gradient(180deg, #f7fbff 0%, #eef4fb 48%, #eaf1f8 100%);
            color: var(--text-main);
        }

        .stApp::before {
            opacity: 0.08;
        }

        [data-testid="stHeader"] {
            background: rgba(244, 248, 252, 0.88);
            border-bottom: 1px solid rgba(37, 99, 235, 0.08);
        }

        .hero-card {
            background:
                linear-gradient(135deg, rgba(255, 255, 255, 0.98), rgba(240, 248, 255, 0.98)),
                radial-gradient(circle at top right, rgba(14, 165, 233, 0.08), transparent 34%);
            box-shadow: 0 18px 42px rgba(15, 23, 42, 0.08);
        }

        .hero-kicker {
            background: rgba(14, 165, 233, 0.08);
            color: #0f6e92;
            border-color: rgba(14, 165, 233, 0.14);
        }

        .info-card,
        .summary-strip,
        .kv-card,
        div[data-testid="stMetric"],
        [data-testid="stDataFrame"],
        [data-testid="stAlert"],
        .empty-state,
        [data-testid="stExpander"] {
            background: rgba(255, 255, 255, 0.94) !important;
        }

        div.stButton > button,
        div.stDownloadButton > button {
            background: linear-gradient(180deg, rgba(255, 255, 255, 0.98), rgba(245, 249, 254, 0.98));
            color: var(--text-main);
            border-color: rgba(37, 99, 235, 0.16);
            box-shadow: 0 12px 24px rgba(15, 23, 42, 0.06);
        }

        div.stButton > button:hover,
        div.stDownloadButton > button:hover {
            border-color: rgba(14, 165, 233, 0.28);
            box-shadow: 0 14px 28px rgba(15, 23, 42, 0.08);
        }

        div.stButton > button[kind="primary"] {
            background: linear-gradient(180deg, rgba(15, 118, 110, 0.96), rgba(14, 165, 233, 0.92));
            color: #f8feff;
        }

        div.stButton > button[kind="secondary"],
        div.stDownloadButton > button[kind="secondary"] {
            background: linear-gradient(180deg, rgba(255, 255, 255, 0.98), rgba(247, 250, 254, 0.98));
            color: var(--text-main);
        }

        div[data-baseweb="select"] > div,
        div[data-baseweb="base-input"] > div,
        div[data-baseweb="textarea"] > div,
        .stTextInput > div > div,
        .stNumberInput > div > div,
        .stTextArea > div > div {
            background: rgba(255, 255, 255, 0.98);
            border-color: rgba(37, 99, 235, 0.12);
            box-shadow: 0 10px 20px rgba(15, 23, 42, 0.04);
        }

        .stTextInput input,
        .stTextArea textarea,
        .stNumberInput input,
        div[data-baseweb="select"] input {
            color: var(--text-main) !important;
        }

        .stTextInput input::placeholder,
        .stTextArea textarea::placeholder {
            color: #64748b !important;
            opacity: 1 !important;
        }

        label[data-testid="stWidgetLabel"] p,
        .sidebar-brand-kicker,
        .sidebar-brand-title,
        .sidebar-section-label,
        [data-testid="stSidebar"] .stMarkdown p,
        [data-testid="stSidebar"] label p {
            color: var(--text-main) !important;
        }

        .hero-subtitle,
        .section-heading-subtitle,
        .summary-strip-caption,
        .kv-label,
        .empty-state-body,
        [data-testid="stMetricLabel"] p,
        [data-testid="stMetricLabel"] label,
        .stCaption,
        .stCaption p,
        small {
            color: #10233d !important;
        }

        .summary-strip-caption,
        .empty-state-body,
        .kv-label,
        .stCaption p {
            font-weight: 600;
        }

        .summary-strip-title,
        .kv-title,
        .sidebar-section-label,
        .sidebar-brand-title,
        .sidebar-brand-kicker,
        label[data-testid="stWidgetLabel"] p,
        [data-testid="stMetricLabel"] {
            color: #10233d !important;
        }

        .empty-state-title {
            color: var(--text-main) !important;
        }

        .stMarkdown p,
        .stMarkdown li,
        .stMarkdown span,
        .stMarkdown div,
        [data-testid="stAlert"] p,
        [data-testid="stAlert"] span,
        [data-testid="stAlert"] div {
            color: #132c49 !important;
        }

        .empty-state {
            border: 1px dashed rgba(37, 99, 235, 0.14) !important;
            background: rgba(255, 255, 255, 0.92) !important;
            box-shadow: 0 14px 28px rgba(15, 23, 42, 0.05) !important;
        }

        [data-testid="stSidebar"] .stTextInput input,
        [data-testid="stSidebar"] .stSelectbox div[data-baseweb="select"] * {
            color: var(--text-main) !important;
        }

        [data-testid="stSidebar"] button[title*="password"],
        [data-testid="stSidebar"] button[aria-label*="password"],
        [data-testid="stSidebar"] button[aria-label*="Password"] {
            background: transparent !important;
            border: none !important;
            box-shadow: none !important;
            color: #35516f !important;
            min-height: auto !important;
            padding: 0.2rem 0.35rem !important;
        }

        [data-testid="stSidebar"] .stButton > button {
            border-radius: 16px !important;
        }

        [data-testid="stSidebar"] .stTextInput > div > div,
        [data-testid="stSidebar"] div[data-baseweb="select"] > div,
        [data-testid="stSidebar"] div[data-baseweb="textarea"] > div,
        [data-testid="stSidebar"] div[data-baseweb="base-input"] > div {
            background: rgba(255, 255, 255, 0.96) !important;
            border: 1px solid rgba(37, 99, 235, 0.14) !important;
            box-shadow: 0 10px 20px rgba(15, 23, 42, 0.05) !important;
        }

        [data-testid="stSidebar"] div[data-baseweb="input"],
        [data-testid="stSidebar"] div[data-baseweb="base-input"],
        [data-testid="stSidebar"] [data-testid="stTextInputRootElement"] {
            background: rgba(255, 255, 255, 0.96) !important;
            border-color: rgba(37, 99, 235, 0.14) !important;
            box-shadow: none !important;
        }

        [data-testid="stSidebar"] div[data-baseweb="input"] button,
        [data-testid="stSidebar"] div[data-baseweb="base-input"] button {
            background: transparent !important;
            border: none !important;
            box-shadow: none !important;
            color: #35516f !important;
        }

        div[data-baseweb="tab-list"] {
            gap: 0.45rem;
            margin-bottom: 0.35rem;
        }

        div[role="tablist"] button,
        button[role="tab"] {
            border-radius: 14px !important;
            padding: 0.55rem 0.9rem !important;
            border: 1px solid rgba(37, 99, 235, 0.08) !important;
            background: rgba(255, 255, 255, 0.58) !important;
            color: #17324d !important;
            transition: all 0.18s ease;
        }

        div[role="tablist"] button *,
        button[role="tab"] * {
            color: #17324d !important;
            opacity: 1 !important;
        }

        div[role="tablist"] button[aria-selected="true"],
        button[role="tab"][aria-selected="true"] {
            background: rgba(255, 255, 255, 0.96) !important;
            color: var(--text-main) !important;
            border-color: rgba(14, 165, 233, 0.18) !important;
            box-shadow: 0 10px 22px rgba(15, 23, 42, 0.06);
        }

        div[role="tablist"] button[aria-selected="true"] *,
        button[role="tab"][aria-selected="true"] * {
            color: var(--text-main) !important;
        }

        [data-baseweb="radio"] > div {
            background: rgba(255, 255, 255, 0.88);
            border-radius: 14px;
            padding: 0.2rem 0.24rem;
            border: 1px solid rgba(37, 99, 235, 0.10);
            box-shadow: 0 8px 18px rgba(15, 23, 42, 0.05);
        }

        [data-baseweb="radio"] label {
            background: rgba(255, 255, 255, 0.98);
            border: 1px solid rgba(37, 99, 235, 0.16);
            border-radius: 999px;
            padding: 0.38rem 0.8rem;
            color: var(--text-main) !important;
        }

        [data-baseweb="radio"] label p,
        [data-baseweb="radio"] label span {
            color: var(--text-main) !important;
            font-weight: 700;
        }

        [role="radiogroup"] label {
            color: var(--text-main) !important;
        }

        [role="radiogroup"] label p,
        [role="radiogroup"] label span,
        [role="radiogroup"] div {
            color: var(--text-main) !important;
            opacity: 1 !important;
        }

        [data-baseweb="radio"] input:checked + div,
        [data-baseweb="radio"] label:has(input:checked) {
            background: rgba(14, 165, 233, 0.10) !important;
            border-color: rgba(14, 165, 233, 0.22) !important;
            box-shadow: 0 8px 18px rgba(14, 165, 233, 0.10);
        }

        [data-testid="stProgressBar"] > div > div {
            background: rgba(14, 165, 233, 0.14) !important;
        }

        [data-testid="stProgressBar"] div[role="progressbar"] {
            background: linear-gradient(90deg, rgba(14, 165, 233, 0.92), rgba(45, 212, 191, 0.88)) !important;
        }

        [data-baseweb="slider"] [role="slider"] {
            box-shadow: 0 0 0 6px rgba(14, 165, 233, 0.12);
        }

        [data-testid="stSidebar"] {
            background: linear-gradient(180deg, rgba(245, 249, 254, 0.98), rgba(237, 244, 251, 0.98));
            border-right: 1px solid rgba(37, 99, 235, 0.08);
        }

        .sidebar-brand {
            margin-bottom: 0.95rem;
            padding-bottom: 0.82rem;
        }

        [data-testid="stSidebarNavLink"] {
            background: rgba(255, 255, 255, 0.4);
        }

        [data-testid="stSidebarNavLink"][aria-current="page"] {
            background: linear-gradient(90deg, rgba(14, 165, 233, 0.12), rgba(45, 212, 191, 0.10));
            border-color: rgba(14, 165, 233, 0.14);
        }

        [data-testid="stSidebarNavLink"][aria-current="page"] span {
            color: var(--text-main);
        }

        [data-testid="stDataFrame"] table,
        [data-testid="stDataFrameResizable"] table {
            background: rgba(255, 255, 255, 0.96);
        }

        [data-testid="stDataFrame"] th,
        [data-testid="stDataFrameResizable"] th {
            background: rgba(243, 248, 253, 0.96) !important;
            color: var(--text-main) !important;
        }

        [data-testid="stDataFrame"] td,
        [data-testid="stDataFrameResizable"] td {
            color: var(--text-main) !important;
        }

        [data-testid="stDataFrame"] [role="row"]:hover {
            background: rgba(14, 165, 233, 0.04);
        }


        [data-testid="stDataFrame"] [data-testid="stElementToolbar"],
        [data-testid="stDataFrameResizable"] [data-testid="stElementToolbar"] {
            background: transparent !important;
        }

        iframe {
            border-radius: 22px;
            background: rgba(255, 255, 255, 0.98);
            border: 1px solid rgba(37, 99, 235, 0.10);
            box-shadow: 0 12px 24px rgba(15, 23, 42, 0.06);
        }

        [data-testid="stTable"] table {
            background: rgba(255, 255, 255, 0.98);
            border-collapse: separate;
            border-spacing: 0;
        }

        [data-testid="stTable"] th {
            background: rgba(243, 248, 253, 0.96);
            color: var(--text-main);
        }

        [data-testid="stTable"] td {
            color: var(--text-main);
            background: rgba(255, 255, 255, 0.98);
        }

        .adaptive-light-table-shell {
            width: 100%;
            max-width: 100%;
            overflow-x: auto;
            overflow-y: auto;
            display: block;
            box-sizing: border-box;
            border-radius: 24px;
            border: 1px solid rgba(37, 99, 235, 0.12);
            background: rgba(255, 255, 255, 0.98);
            box-shadow: 0 14px 28px rgba(15, 23, 42, 0.06);
            scrollbar-color: rgba(37, 99, 235, 0.28) rgba(226, 236, 248, 0.9);
            scrollbar-width: thin;
            padding-bottom: 0.15rem;
        }

        .adaptive-light-table-shell table {
            width: max-content;
            min-width: 100%;
            max-width: none;
            border-collapse: separate;
            border-spacing: 0;
            background: rgba(255, 255, 255, 0.98);
            color: var(--text-main);
            font-size: 0.95rem;
            table-layout: auto;
        }

        .adaptive-light-table-shell thead th {
            position: sticky;
            top: 0;
            z-index: 1;
            background: rgba(243, 248, 253, 0.98);
            color: var(--text-main);
            font-weight: 800;
            text-align: left;
            border-bottom: 1px solid rgba(37, 99, 235, 0.10);
        }

        .adaptive-light-table-shell th,
        .adaptive-light-table-shell td {
            padding: 0.78rem 0.88rem;
            border-bottom: 1px solid rgba(37, 99, 235, 0.08);
            vertical-align: top;
            white-space: normal;
            word-break: break-word;
            min-width: 96px;
            max-width: 320px;
        }

        .adaptive-light-table-shell th {
            white-space: nowrap;
        }

        .adaptive-light-table-shell td {
            line-height: 1.45;
            color: var(--text-main);
        }

        .adaptive-light-table-shell td *,
        .adaptive-light-table-shell th *,
        .adaptive-light-table-shell a,
        .adaptive-light-table-shell span,
        .adaptive-light-table-shell div {
            color: var(--text-main) !important;
        }

        .adaptive-light-table-shell tbody tr:hover td {
            background: rgba(14, 165, 233, 0.04);
        }

        .adaptive-light-table-shell tbody tr:last-child td {
            border-bottom: none;
        }

        .adaptive-light-table-shell::-webkit-scrollbar {
            width: 10px;
            height: 10px;
        }

        .adaptive-light-table-shell::-webkit-scrollbar-thumb {
            background: rgba(37, 99, 235, 0.25);
            border-radius: 999px;
        }

        .adaptive-light-table-shell-compact th,
        .adaptive-light-table-shell-compact td {
            padding: 0.62rem 0.72rem;
            max-width: 260px;
        }

        .empty-state {
            border: 1px dashed rgba(37, 99, 235, 0.12);
            background: rgba(255, 255, 255, 0.98);
            box-shadow: 0 12px 24px rgba(15, 23, 42, 0.06);
        }

        .empty-state-title,
        .empty-state-body {
            color: var(--text-main) !important;
        }

        .summary-strip-caption,
        .section-heading-subtitle,
        .sidebar-section-label,
        .sidebar-theme-caption,
        .sidebar-admin-hint,
        .kv-label,
        [data-testid="stCaptionContainer"],
        .stCaption,
        small {
            color: #17324d !important;
        }

        div[data-testid="stMetricLabel"],
        div[data-testid="stMetricLabel"] *,
        label[data-testid="stWidgetLabel"],
        label[data-testid="stWidgetLabel"] *,
        .stMarkdown p,
        .stMarkdown li,
        .stMarkdown span,
        .stMarkdown div {
            color: #10233d !important;
        }

        .stMarkdown strong,
        .stMarkdown b,
        .kv-value,
        .summary-strip-title,
        .section-heading-title {
            color: #0f2747 !important;
        }

        [data-testid="stSidebar"] .stTextInput input,
        [data-testid="stSidebar"] .stTextInput input::placeholder,
        [data-testid="stSidebar"] div[data-baseweb="select"] *,
        [data-testid="stSidebar"] div[data-baseweb="base-input"] *,
        [data-testid="stSidebar"] svg {
            color: var(--text-main) !important;
            fill: var(--text-main) !important;
        }

        [data-testid="stSidebar"] .stTextInput > div > div,
        [data-testid="stSidebar"] div[data-baseweb="select"] > div,
        [data-testid="stSidebar"] div[data-baseweb="base-input"] > div {
            background: rgba(255, 255, 255, 0.98) !important;
            border: 1px solid rgba(37, 99, 235, 0.14) !important;
            box-shadow: 0 8px 18px rgba(15, 23, 42, 0.06) !important;
        }

        .stSlider [data-baseweb="slider"] {
            background: transparent !important;
        }

        .stSlider [role="slider"] {
            box-shadow: none !important;
        }

        .stSlider [data-testid="stTickBarMin"],
        .stSlider [data-testid="stTickBarMax"] {
            background: #cfe0f4 !important;
        }

        div[role="tablist"],
        div[data-baseweb="tab-list"],
        div[role="radiogroup"],
        div[data-baseweb="radio"] > div {
            background: #edf4fa !important;
            border: 1px solid rgba(37, 99, 235, 0.12) !important;
            border-radius: 14px !important;
            padding: 4px !important;
            box-shadow: none !important;
        }

        button[role="tab"],
        div[data-baseweb="tab-list"] button,
        div[role="tablist"] button,
        div[role="radiogroup"] > label,
        div[data-baseweb="radio"] label {
            background: transparent !important;
            color: #17324d !important;
            border-radius: 10px !important;
            border: none !important;
            box-shadow: none !important;
            font-weight: 700 !important;
            opacity: 1 !important;
        }

        button[role="tab"] *,
        div[data-baseweb="tab-list"] button *,
        div[role="tablist"] button *,
        div[role="radiogroup"] > label *,
        div[data-baseweb="radio"] label * {
            color: #17324d !important;
            opacity: 1 !important;
        }

        button[role="tab"][aria-selected="true"],
        div[data-baseweb="tab-list"] button[aria-selected="true"],
        div[role="tablist"] button[aria-selected="true"],
        div[role="radiogroup"] > label:has(input:checked),
        div[data-baseweb="radio"] label:has(input:checked) {
            background: rgba(255, 255, 255, 0.98) !important;
            color: #0f2747 !important;
            border: 1px solid rgba(37, 99, 235, 0.12) !important;
            box-shadow: 0 1px 2px rgba(15, 39, 71, 0.06) !important;
        }

        [data-testid="stSidebar"] div.stButton > button {
            background: rgba(255, 255, 255, 0.98);
            color: var(--text-main);
            border: 1px solid rgba(37, 99, 235, 0.14);
            box-shadow: 0 10px 22px rgba(15, 23, 42, 0.06);
        }

        [data-testid="stSidebar"] div.stButton > button[kind="primary"] {
            background: linear-gradient(135deg, #12b8d6, #1d9bf0);
            color: white;
            border-color: rgba(8, 145, 178, 0.24);
        }

        [data-testid="stSidebar"] div.stButton > button:hover {
            border-color: rgba(14, 165, 233, 0.24);
            box-shadow: 0 12px 24px rgba(14, 165, 233, 0.10);
        }

        .stSelectbox label,
        .stTextInput label,
        .stSlider label,
        .stMultiSelect label,
        .stCheckbox label,
        .stRadio label {
            color: var(--text-main) !important;
        }

        [data-testid="stMetricLabel"],
        [data-testid="stMetricLabel"] p {
            color: #0f2747 !important;
        }

        /* ===== Light theme widget fixes for Streamlit/BaseWeb widgets ===== */
        div[role="tablist"] {
            background: #edf4fa !important;
            border: 1px solid rgba(37, 99, 235, 0.12) !important;
            border-radius: 14px !important;
            padding: 4px !important;
            gap: 4px !important;
        }

        button[role="tab"] {
            background: transparent !important;
            color: #17324d !important;
            border-radius: 10px !important;
            border: none !important;
            box-shadow: none !important;
            font-weight: 700 !important;
        }

        button[role="tab"][aria-selected="true"] {
            background: rgba(255, 255, 255, 0.98) !important;
            color: var(--text-main) !important;
            border: 1px solid rgba(37, 99, 235, 0.12) !important;
            box-shadow: 0 1px 2px rgba(15, 39, 71, 0.06) !important;
        }

        div[role="radiogroup"] {
            background: #edf4fa !important;
            border: 1px solid rgba(37, 99, 235, 0.12) !important;
            border-radius: 14px !important;
            padding: 4px !important;
        }

        div[role="radiogroup"] > label {
            background: transparent !important;
            color: #17324d !important;
            border-radius: 10px !important;
            border: none !important;
            box-shadow: none !important;
            font-weight: 700 !important;
        }

        div[role="radiogroup"] > label:has(input:checked) {
            background: rgba(255, 255, 255, 0.98) !important;
            color: var(--text-main) !important;
            border: 1px solid rgba(37, 99, 235, 0.12) !important;
            box-shadow: 0 1px 2px rgba(15, 39, 71, 0.06) !important;
        }

        .stTextInput > div > div,
        .stNumberInput > div > div,
        div[data-baseweb="input"],
        div[data-baseweb="base-input"] {
            background: rgba(255, 255, 255, 0.98) !important;
            border: 1px solid rgba(37, 99, 235, 0.14) !important;
            border-radius: 14px !important;
            box-shadow: none !important;
        }

        .stTextInput input,
        .stNumberInput input,
        div[data-baseweb="input"] input,
        div[data-baseweb="base-input"] input {
            background: transparent !important;
            color: var(--text-main) !important;
            -webkit-text-fill-color: var(--text-main) !important;
        }

        .stTextInput input::placeholder,
        .stNumberInput input::placeholder {
            color: #7b90aa !important;
        }

        div[data-baseweb="input"]:focus-within,
        div[data-baseweb="base-input"]:focus-within,
        .stTextInput > div > div:focus-within,
        .stNumberInput > div > div:focus-within {
            border-color: #8fded1 !important;
            box-shadow: 0 0 0 3px rgba(45, 212, 191, 0.14) !important;
        }

        div[data-baseweb="select"] > div,
        div[data-baseweb="select"] {
            background: rgba(255, 255, 255, 0.98) !important;
            color: var(--text-main) !important;
            border: 1px solid rgba(37, 99, 235, 0.14) !important;
            border-radius: 14px !important;
            box-shadow: none !important;
        }

        div[data-baseweb="select"] * {
            color: var(--text-main) !important;
        }

        /* Dropdown popovers / listboxes */
        div[data-baseweb="popover"],
        div[data-baseweb="menu"] {
            background: rgba(255, 255, 255, 0.98) !important;
            border: 1px solid rgba(37, 99, 235, 0.14) !important;
            border-radius: 18px !important;
            box-shadow: 0 18px 38px rgba(15, 23, 42, 0.12) !important;
        }

        div[data-baseweb="popover"] *,
        div[data-baseweb="menu"] * {
            color: var(--text-main) !important;
        }

        div[role="listbox"],
        ul[role="listbox"] {
            background: rgba(255, 255, 255, 0.98) !important;
            color: var(--text-main) !important;
            border-radius: 16px !important;
        }

        div[role="option"],
        li[role="option"] {
            background: transparent !important;
            color: var(--text-main) !important;
            border-radius: 12px !important;
        }

        div[role="option"]:hover,
        li[role="option"]:hover {
            background: rgba(14, 165, 233, 0.08) !important;
            color: var(--text-main) !important;
        }

        div[role="option"][aria-selected="true"],
        li[role="option"][aria-selected="true"] {
            background: rgba(14, 165, 233, 0.14) !important;
            color: var(--text-main) !important;
            font-weight: 600 !important;
        }

        div[role="listbox"]::-webkit-scrollbar,
        ul[role="listbox"]::-webkit-scrollbar {
            width: 10px;
        }

        div[role="listbox"]::-webkit-scrollbar-thumb,
        ul[role="listbox"]::-webkit-scrollbar-thumb {
            background: rgba(37, 99, 235, 0.18);
            border-radius: 999px;
        }

        div[role="listbox"]::-webkit-scrollbar-track,
        ul[role="listbox"]::-webkit-scrollbar-track {
            background: rgba(15, 23, 42, 0.04);
        }

        [data-baseweb="slider"] > div {
            background: transparent !important;
        }

        [data-baseweb="slider"] [role="slider"] {
            background: #22c7b7 !important;
            border: 2px solid #ffffff !important;
            box-shadow: 0 0 0 3px rgba(45, 212, 191, 0.18) !important;
        }

        .stSlider [data-baseweb="slider"] {
            background: transparent !important;
        }

        .stSlider [role="slider"] {
            box-shadow: none !important;
        }

        /* Checkboxes */
        [data-testid="stCheckbox"] label,
        [data-testid="stCheckbox"] p,
        [data-testid="stCheckbox"] span {
            color: var(--text-main) !important;
            opacity: 1 !important;
        }

        [data-testid="stCheckbox"] label {
            display: flex !important;
            align-items: center !important;
            gap: 0.55rem !important;
        }

        [data-testid="stCheckbox"] [data-baseweb="checkbox"] {
            background: transparent !important;
            display: inline-flex !important;
            align-items: center !important;
            justify-content: center !important;
        }

        [data-testid="stCheckbox"] [data-baseweb="checkbox"] > div {
            background: rgba(255, 255, 255, 0.98) !important;
            border: 1px solid rgba(37, 99, 235, 0.20) !important;
            border-radius: 8px !important;
            box-shadow: 0 4px 10px rgba(15, 23, 42, 0.04) !important;
        }

        [data-testid="stCheckbox"] [data-baseweb="checkbox"] svg {
            fill: #0f6e92 !important;
            color: #0f6e92 !important;
        }

        [data-testid="stCheckbox"][aria-disabled="true"] label,
        [data-testid="stCheckbox"][aria-disabled="true"] p,
        [data-testid="stCheckbox"][aria-disabled="true"] span {
            color: var(--text-soft) !important;
            opacity: 0.88 !important;
        }

        details,
        summary,
        [data-testid="stExpander"] {
            background: rgba(255, 255, 255, 0.98) !important;
            color: var(--text-main) !important;
            border-color: rgba(37, 99, 235, 0.12) !important;
        }

        .stButton > button {
            border-radius: 14px !important;
        }

        .stButton > button[kind="secondary"],
        .stButton > button[data-testid="baseButton-secondary"] {
            background: rgba(255, 255, 255, 0.98) !important;
            color: var(--text-main) !important;
            border: 1px solid rgba(37, 99, 235, 0.12) !important;
        }

        .stButton > button[kind="secondary"]:hover,
        .stButton > button[data-testid="baseButton-secondary"]:hover {
            border-color: rgba(37, 99, 235, 0.20) !important;
            background: #f8fbfe !important;
        }

        .download-link-button {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            width: 100%;
            min-height: 3rem;
            padding: 0.8rem 1rem;
            border-radius: 16px;
            border: 1px solid rgba(37, 99, 235, 0.12);
            background: rgba(255, 255, 255, 0.98);
            color: var(--text-main) !important;
            text-decoration: none !important;
            font-weight: 700;
            box-shadow: 0 10px 22px rgba(15, 23, 42, 0.06);
            box-sizing: border-box;
        }

        .download-link-button:hover {
            border-color: rgba(37, 99, 235, 0.20);
            background: #f8fbfe;
            box-shadow: 0 12px 24px rgba(14, 165, 233, 0.10);
        }

        .light-chart-shell {
            border-radius: 24px;
            border: 1px solid rgba(37, 99, 235, 0.12);
            background: rgba(255, 255, 255, 0.98);
            box-shadow: 0 14px 28px rgba(15, 23, 42, 0.06);
            padding: 0.6rem 0.8rem 0.2rem;
        }

        .light-chart-shell [data-testid="stVegaLiteChart"] {
            background: transparent !important;
        }

        [data-testid="stMarkdownContainer"] p code,
        code {
            background: rgba(14, 165, 233, 0.08);
            color: #0f6e92;
            border-color: rgba(14, 165, 233, 0.12);
        }

        div[role="dialog"] {
            background: linear-gradient(180deg, rgba(255, 255, 255, 0.98), rgba(243, 248, 253, 0.98)) !important;
            box-shadow: 0 24px 80px rgba(15, 23, 42, 0.12) !important;
        }

        div[role="dialog"] iframe {
            background: rgba(255, 255, 255, 0.99);
            border: 1px solid rgba(37, 99, 235, 0.10);
        }

        [data-testid="stException"] {
            background: rgba(254, 242, 242, 0.98) !important;
            border: 1px solid rgba(239, 68, 68, 0.18) !important;
            border-radius: 24px !important;
        }

        [data-testid="stException"] * {
            color: #7f1d1d !important;
        }

        [data-testid="stAlert"],
        [data-testid="stAlert"] *,
        small,
        .stCaption,
        [data-testid="stCaptionContainer"],
        .stMarkdown p,
        .stMarkdown li,
        .stMarkdown span,
        .stMarkdown div {
            color: #10233d !important;
        }

        .stMarkdown a,
        a {
            color: #0f5fa8 !important;
        }

        .stMarkdown strong,
        .stMarkdown b {
            color: #0f2747 !important;
        }

        [data-testid="stAlert"] p,
        [data-testid="stInfo"] p,
        [data-testid="stSuccess"] p,
        [data-testid="stWarning"] p,
        [data-testid="stError"] p {
            color: #17324d !important;
        }

        [data-baseweb="radio"] label,
        [data-baseweb="radio"] span,
        [data-baseweb="radio"] div {
            color: var(--text-main) !important;
        }

        [data-baseweb="tag"] {
            background: rgba(14, 165, 233, 0.10) !important;
            border: 1px solid rgba(14, 165, 233, 0.14) !important;
            color: var(--text-main) !important;
            border-radius: 999px !important;
        }

        [data-testid="stSidebar"] input,
        [data-testid="stSidebar"] textarea,
        [data-testid="stSidebar"] svg,
        [data-testid="stSidebar"] button[title*="password"],
        [data-testid="stSidebar"] button[aria-label*="password"],
        [data-testid="stSidebar"] button[aria-label*="Password"] {
            color: var(--text-main) !important;
            fill: var(--text-main) !important;
        }

        [data-testid="stSidebar"] .stTextInput button,
        [data-testid="stSidebar"] div[data-baseweb="input"] button,
        [data-testid="stSidebar"] div[data-baseweb="base-input"] button {
            background: transparent !important;
            border: none !important;
            box-shadow: none !important;
            color: #17324d !important;
            fill: #17324d !important;
        }

        /* Final light-theme widget overrides */
        div[role="tablist"],
        div[data-baseweb="tab-list"],
        div[role="radiogroup"],
        div[data-baseweb="radio"] > div {
            background: #edf4fa !important;
            border: 1px solid rgba(37, 99, 235, 0.12) !important;
            border-radius: 14px !important;
            padding: 4px !important;
            gap: 4px !important;
        }

        button[role="tab"],
        div[data-baseweb="tab-list"] button,
        div[role="tablist"] button,
        div[role="radiogroup"] > label,
        div[data-baseweb="radio"] label {
            background: transparent !important;
            color: #0f2747 !important;
            border-radius: 10px !important;
            border: none !important;
            box-shadow: none !important;
            font-weight: 700 !important;
            opacity: 1 !important;
            min-height: 2.5rem !important;
        }

        button[role="tab"] *,
        div[data-baseweb="tab-list"] button *,
        div[role="tablist"] button *,
        div[role="radiogroup"] > label *,
        div[data-baseweb="radio"] label * {
            color: #0f2747 !important;
            opacity: 1 !important;
        }

        button[role="tab"][aria-selected="true"],
        div[data-baseweb="tab-list"] button[aria-selected="true"],
        div[role="tablist"] button[aria-selected="true"],
        div[role="radiogroup"] > label:has(input:checked),
        div[data-baseweb="radio"] label:has(input:checked) {
            background: rgba(255, 255, 255, 0.98) !important;
            color: #0f2747 !important;
            border: 1px solid rgba(37, 99, 235, 0.12) !important;
            box-shadow: 0 1px 2px rgba(15, 39, 71, 0.06) !important;
        }

        button[role="tab"][aria-selected="true"] *,
        div[data-baseweb="tab-list"] button[aria-selected="true"] *,
        div[role="tablist"] button[aria-selected="true"] *,
        div[role="radiogroup"] > label:has(input:checked) *,
        div[data-baseweb="radio"] label:has(input:checked) * {
            color: #0f2747 !important;
        }

        div[role="tablist"]::before,
        div[data-baseweb="tab-list"]::before,
        div[role="radiogroup"]::before,
        div[data-baseweb="radio"] > div::before {
            display: none !important;
            content: none !important;
        }
        </style>
        """

    st.markdown(dark_theme_css, unsafe_allow_html=True)


def render_header(title: str, subtitle: str = "", kicker: str = "") -> None:
    normalized_title = str(title or "").strip()
    normalized_subtitle = str(subtitle or "").strip()
    combined = "\n".join(part for part in [normalized_title, normalized_subtitle] if part)
    if "hero-title" in combined or "hero-subtitle" in combined:
        title_match = re.search(r'hero-title[^>]*>(.*?)</div>', combined, re.IGNORECASE | re.DOTALL)
        subtitle_match = re.search(r'hero-subtitle[^>]*>(.*?)</div>', combined, re.IGNORECASE | re.DOTALL)
        if title_match:
            normalized_title = title_match.group(1)
        if subtitle_match:
            normalized_subtitle = subtitle_match.group(1)

    normalized_title = re.sub(r"<[^>]+>", "", normalized_title)
    normalized_subtitle = re.sub(r"<[^>]+>", "", normalized_subtitle)
    normalized_kicker = re.sub(r"<[^>]+>", "", str(kicker or "").strip())

    content_lines = ['<div class="hero-card">']
    if normalized_kicker:
        content_lines.append(f'<div class="hero-kicker">{escape(unescape(normalized_kicker))}</div>')
    content_lines.append(f'<div class="hero-title">{escape(unescape(normalized_title))}</div>')
    if normalized_subtitle:
        content_lines.append(f'<div class="hero-subtitle">{escape(unescape(normalized_subtitle))}</div>')
    content_lines.append("</div>")
    st.markdown("\n".join(content_lines), unsafe_allow_html=True)


def render_info_card(title: str, body: str) -> None:
    st.markdown(
        dedent(
            f"""
            <div class="info-card">
                <h3>{escape(title)}</h3>
                <div>{escape(body)}</div>
            </div>
            """
        ).strip(),
        unsafe_allow_html=True,
    )


def render_section_heading(title: str, subtitle: str = "") -> None:
    subtitle_markup = f'<div class="section-heading-subtitle">{escape(subtitle)}</div>' if subtitle else ""
    st.markdown(
        dedent(
            f"""
            <div class="section-heading">
                <div class="section-heading-title">{escape(title)}</div>
                {subtitle_markup}
            </div>
            """
        ).strip(),
        unsafe_allow_html=True,
    )


def render_fullscreen_dataframe_heading(
    title: str,
    frame: pd.DataFrame,
    *,
    key: str,
    subtitle: str = "",
    caption: str = "",
) -> None:
    if frame.empty:
        render_section_heading(title, subtitle)
        return
    if st.button(title, key=key, type="tertiary", help="Відкрити на весь екран"):
        _fullscreen_dataframe_dialog(title, frame, caption)
    if subtitle:
        st.markdown(
            f'<div class="section-heading-subtitle">{escape(subtitle)}</div>',
            unsafe_allow_html=True,
        )


def render_fullscreen_bar_chart_heading(
    title: str,
    data: pd.DataFrame,
    *,
    key: str,
    subtitle: str = "",
    caption: str = "",
) -> None:
    if data.empty:
        render_section_heading(title, subtitle)
        return
    if st.button(title, key=key, type="tertiary", help="Відкрити на весь екран"):
        _fullscreen_bar_chart_dialog(title, data, caption)
    if subtitle:
        st.markdown(
            f'<div class="section-heading-subtitle">{escape(subtitle)}</div>',
            unsafe_allow_html=True,
        )


def render_fullscreen_html_heading(
    title: str,
    html: str,
    *,
    key: str,
    subtitle: str = "",
    caption: str = "",
    height: int = 980,
) -> None:
    if not html.strip():
        render_section_heading(title, subtitle)
        return
    if st.button(title, key=key, type="tertiary", help="Відкрити на весь екран"):
        _fullscreen_html_dialog(title, html, height, caption)
    if subtitle:
        st.markdown(
            f'<div class="section-heading-subtitle">{escape(subtitle)}</div>',
            unsafe_allow_html=True,
        )


def render_empty_state(title: str, body: str) -> None:
    st.markdown(
        dedent(
            f"""
            <div class="empty-state">
                <div class="empty-state-title">{escape(title)}</div>
                <div class="empty-state-body">{escape(body)}</div>
            </div>
            """
        ).strip(),
        unsafe_allow_html=True,
    )


def render_summary_strip(title: str, value: str, caption: str = "") -> None:
    caption_markup = f'<div class="summary-strip-caption">{escape(caption)}</div>' if caption else ""
    st.markdown(
        dedent(
            f"""
            <div class="summary-strip">
                <div class="summary-strip-title">{escape(title)}</div>
                <div class="summary-strip-value">{escape(value)}</div>
                {caption_markup}
            </div>
            """
        ).strip(),
        unsafe_allow_html=True,
    )


def render_key_value_card(title: str, items: list[tuple[str, str]]) -> None:
    rows = "".join(
        [
            f'<div class="kv-row"><div class="kv-label">{escape(label)}</div><div class="kv-value">{escape(value or "—")}</div></div>'
            for label, value in items
        ]
    )
    st.markdown(
        dedent(
            f"""
            <div class="kv-card">
                <div class="kv-title">{escape(title)}</div>
                {rows}
            </div>
            """
        ).strip(),
        unsafe_allow_html=True,
    )


def render_adaptive_dataframe(
    frame: pd.DataFrame,
    *,
    use_container_width: bool = True,
    hide_index: bool = True,
    height: int | None = None,
    compact: bool = False,
) -> None:
    del compact
    st.dataframe(
        frame,
        use_container_width=use_container_width,
        hide_index=hide_index,
        height=height,
    )


def render_adaptive_bar_chart(
    data: pd.DataFrame,
    *,
    use_container_width: bool = True,
    height: int = 280,
) -> None:
    st.bar_chart(data, use_container_width=use_container_width, height=height)


def render_download_link(
    label: str,
    data: bytes,
    *,
    file_name: str,
    mime: str,
) -> None:
    st.download_button(
        label,
        data,
        file_name=file_name,
        mime=mime,
        use_container_width=True,
    )


if hasattr(st, "dialog"):
    @st.dialog("Перегляд на весь екран", width="large")
    def _fullscreen_dataframe_dialog(title: str, frame: pd.DataFrame, caption: str = "") -> None:
        render_section_heading(title, caption)
        render_adaptive_dataframe(frame, use_container_width=True, hide_index=True, height=760)


    @st.dialog("Перегляд на весь екран", width="large")
    def _fullscreen_bar_chart_dialog(title: str, data: pd.DataFrame, caption: str = "") -> None:
        render_section_heading(title, caption)
        render_adaptive_bar_chart(data, use_container_width=True, height=760)


    @st.dialog("Перегляд на весь екран", width="large")
    def _fullscreen_html_dialog(title: str, html: str, height: int, caption: str = "") -> None:
        render_section_heading(title, caption)
        components.html(html, height=height, scrolling=False)
else:
    def _fullscreen_dataframe_dialog(title: str, frame: pd.DataFrame, caption: str = "") -> None:
        st.info("Повноекранний перегляд недоступний у цьому середовищі.")
        render_adaptive_dataframe(frame, use_container_width=True, hide_index=True, height=760)


    def _fullscreen_bar_chart_dialog(title: str, data: pd.DataFrame, caption: str = "") -> None:
        st.info("Повноекранний перегляд недоступний у цьому середовищі.")
        render_adaptive_bar_chart(data, use_container_width=True, height=760)


    def _fullscreen_html_dialog(title: str, html: str, height: int, caption: str = "") -> None:
        st.info("Повноекранний перегляд недоступний у цьому середовищі.")
        components.html(html, height=height, scrolling=False)


@st.cache_resource(show_spinner=False)
def _build_service(uri: str, user: str, password: str, database: str) -> Neo4jService:
    from services.neo4j_service import Neo4jService

    service = Neo4jService(uri=uri, user=user, password=password, database=database)
    service.verify_connection()
    return service


def require_service() -> Neo4jService:
    config = get_neo4j_config()
    if not config:
        st.error("Не знайдено налаштування підключення до Neo4j Aura.")
        st.code(get_connection_help_text())
        st.stop()

    try:
        return _build_service(config.uri, config.user, config.password, config.database)
    except ModuleNotFoundError as exc:
        st.error("Не вдалося запустити клієнт Neo4j у середовищі Streamlit Cloud.")
        st.caption(
            "Найімовірніше, залежність `neo4j` ще не встановилася або збірка середовища завершилася з помилкою. "
            "Перевірте `Logs` і виконайте `Redeploy` після завершення встановлення залежностей."
        )
        st.code(str(exc))
        st.stop()
    except Exception as exc:
        st.error(f"Не вдалося підключитися до Neo4j Aura: {exc}")
        if config.database:
            st.caption(
                "Порада: якщо в `Secrets` вказано `NEO4J_DATABASE`, перевірте назву бази або тимчасово приберіть "
                "цей параметр, щоб Aura використала домашню базу автоматично."
            )
        else:
            st.caption("Перевірте `NEO4J_URI`, `NEO4J_USER`, `NEO4J_PASSWORD` і права доступу до Neo4j Aura.")
        st.stop()
