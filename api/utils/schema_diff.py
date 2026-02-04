"""Utility to compare two database schemas using SQLAlchemy reflection.

This can be used to compare the Alembic-migrated schema against the
Django ORM-generated schema to ensure they are in sync.

To run this script, you need to have SQLAlchemy installed in your
environment. You can install it via poetry dev:
    poetry install --with dev

To run the script, use the following command:

    python api/utils/schema_diff.py \
        --db-a "postgresql+psycopg://myuser:mypassword@localhost:5440/paidiver_st3" \
        --db-b "postgresql+psycopg://myuser:mypassword@localhost:5435/annotationsdb" \
        --schema-a public \
        --schema-b public \
        --out-json diff.json

This will connect to the two specified databases, compare their schemas,
and output the differences to the specified JSON file.
"""

from __future__ import annotations

import json
from collections.abc import Iterable
from dataclasses import asdict, dataclass
from typing import Any

from sqlalchemy import create_engine, inspect
from sqlalchemy.engine.reflection import Inspector


@dataclass
class ColumnSig:
    """Signature of a database column."""

    name: str
    type: str
    nullable: bool
    default: str | None
    autoincrement: bool | None


@dataclass
class IndexSig:
    """Signature of a database index."""

    name: str
    unique: bool
    column_names: tuple[str, ...]


@dataclass
class ConstraintSig:
    """Signature of a database constraint."""

    name: str | None
    kind: str  # "pk" | "fk" | "unique" | "check"
    columns: tuple[str, ...]
    details: dict[str, Any]


def _normalize_type(type_obj: Any) -> str:
    return " ".join(str(type_obj).strip().lower().split())


def _get_schema_snapshot(
    ins: Inspector,
    schema: str | None = None,
    exclude_tables: Iterable[str] | None = None,
) -> dict[str, Any]:
    exclude: set[str] = set(exclude_tables or [])

    tables = sorted(t for t in ins.get_table_names(schema=schema) if t not in exclude)
    snapshot: dict[str, Any] = {}

    for t in tables:
        cols: list[ColumnSig] = []
        for c in ins.get_columns(t, schema=schema):
            cols.append(
                ColumnSig(
                    name=c["name"],
                    type=_normalize_type(c["type"]),
                    nullable=bool(c.get("nullable", True)),
                    default=(str(c["default"]).strip() if c.get("default") is not None else None),
                    autoincrement=c.get("autoincrement"),
                )
            )

        pk = ins.get_pk_constraint(t, schema=schema) or {}
        pk_cols = tuple(pk.get("constrained_columns") or ())
        pk_name = pk.get("name")

        constraints: list[ConstraintSig] = []
        if pk_cols:
            constraints.append(
                ConstraintSig(
                    name=pk_name,
                    kind="pk",
                    columns=pk_cols,
                    details={},
                )
            )

        for fk in ins.get_foreign_keys(t, schema=schema) or []:
            constraints.append(
                ConstraintSig(
                    name=fk.get("name"),
                    kind="fk",
                    columns=tuple(fk.get("constrained_columns") or ()),
                    details={
                        "referred_schema": fk.get("referred_schema"),
                        "referred_table": fk.get("referred_table"),
                        "referred_columns": tuple(fk.get("referred_columns") or ()),
                        "options": fk.get("options") or {},
                    },
                )
            )

        for uq in ins.get_unique_constraints(t, schema=schema) or []:
            constraints.append(
                ConstraintSig(
                    name=uq.get("name"),
                    kind="unique",
                    columns=tuple(uq.get("column_names") or ()),
                    details={},
                )
            )

        for ck in getattr(ins, "get_check_constraints", lambda *_args, **_kw: [])(t, schema=schema) or []:
            constraints.append(
                ConstraintSig(
                    name=ck.get("name"),
                    kind="check",
                    columns=tuple(ck.get("column_names") or ()),
                    details={"sqltext": ck.get("sqltext")},
                )
            )

        idxs: list[IndexSig] = []
        for idx in ins.get_indexes(t, schema=schema) or []:
            idxs.append(
                IndexSig(
                    name=idx.get("name"),
                    unique=bool(idx.get("unique", False)),
                    column_names=tuple(idx.get("column_names") or ()),
                )
            )

        snapshot[t] = {
            "columns": {c.name: c for c in cols},
            "indexes": {i.name: i for i in idxs if i.name},
            "constraints": {(c.kind, c.name, c.columns): c for c in constraints},
        }

    return snapshot


def _diff_snapshots(schema_a: dict[str, Any], schema_b: dict[str, Any]) -> dict[str, Any]:
    """Diff two schema snapshots.

    Args:
        schema_a: First schema snapshot.
        schema_b: Second schema snapshot.

    Returns:
        A dict describing the differences between the two snapshots.
    """
    a_tables = set(schema_a.keys())
    b_tables = set(schema_b.keys())

    out: dict[str, Any] = {
        "tables_only_in_a": sorted(a_tables - b_tables),
        "tables_only_in_b": sorted(b_tables - a_tables),
        "tables_in_both": {},
    }

    for t in sorted(a_tables & b_tables):
        a_t = schema_a[t]
        b_t = schema_b[t]

        a_cols: dict[str, ColumnSig] = a_t["columns"]
        b_cols: dict[str, ColumnSig] = b_t["columns"]

        a_idx: dict[str, IndexSig] = a_t["indexes"]
        b_idx: dict[str, IndexSig] = b_t["indexes"]

        a_cons: dict[tuple[str, str | None, tuple[str, ...]], ConstraintSig] = a_t["constraints"]
        b_cons: dict[tuple[str, str | None, tuple[str, ...]], ConstraintSig] = b_t["constraints"]

        col_only_a = sorted(set(a_cols) - set(b_cols))
        col_only_b = sorted(set(b_cols) - set(a_cols))

        col_changed = {}
        for c in sorted(set(a_cols) & set(b_cols)):
            if asdict(a_cols[c]) != asdict(b_cols[c]):
                col_changed[c] = {"a": asdict(a_cols[c]), "b": asdict(b_cols[c])}

        idx_only_a = sorted(set(a_idx) - set(b_idx))
        idx_only_b = sorted(set(b_idx) - set(a_idx))

        idx_changed = {}
        for i in sorted(set(a_idx) & set(b_idx)):
            if asdict(a_idx[i]) != asdict(b_idx[i]):
                idx_changed[i] = {"a": asdict(a_idx[i]), "b": asdict(b_idx[i])}

        cons_only_a = sorted([str(k) for k in (set(a_cons) - set(b_cons))])
        cons_only_b = sorted([str(k) for k in (set(b_cons) - set(a_cons))])

        cons_changed = {}
        for k in sorted(set(a_cons) & set(b_cons), key=lambda x: str(x)):
            if asdict(a_cons[k]) != asdict(b_cons[k]):
                cons_changed[str(k)] = {"a": asdict(a_cons[k]), "b": asdict(b_cons[k])}

        if any(
            [
                col_only_a,
                col_only_b,
                col_changed,
                idx_only_a,
                idx_only_b,
                idx_changed,
                cons_only_a,
                cons_only_b,
                cons_changed,
            ]
        ):
            out["tables_in_both"][t] = {
                "columns_only_in_a": col_only_a,
                "columns_only_in_b": col_only_b,
                "columns_changed": col_changed,
                "indexes_only_in_a": idx_only_a,
                "indexes_only_in_b": idx_only_b,
                "indexes_changed": idx_changed,
                "constraints_only_in_a": cons_only_a,
                "constraints_only_in_b": cons_only_b,
                "constraints_changed": cons_changed,
            }

    return out


def main(  # noqa: C901, PLR0912
    db_a_url: str, db_b_url: str, schema_a: str | None = None, schema_b: str | None = None, out_json: str | None = None
) -> None:
    """Compare two database schemas via SQLAlchemy reflection.

    Args:
        db_a_url: SQLAlchemy URL for first database.
        db_b_url: SQLAlchemy URL for second database.
        schema_a: Optional schema name for first database.
        schema_b: Optional schema name for second database.
        out_json: Optional path to write diff as JSON.

    Returns:
        None
    """
    eng_a = create_engine(db_a_url)
    eng_b = create_engine(db_b_url)

    ins_a = inspect(eng_a)
    ins_b = inspect(eng_b)

    exclude = {
        "alembic_version",
        "auth_group",
        "auth_group_permissions",
        "auth_permission",
        "auth_user",
        "auth_user_groups",
        "auth_user_user_permissions",
        "django_admin_log",
        "django_content_type",
        "django_migrations",
        "django_session",
    }

    snap_a = _get_schema_snapshot(ins_a, schema=schema_a, exclude_tables=exclude)
    snap_b = _get_schema_snapshot(ins_b, schema=schema_b, exclude_tables=exclude)

    diff = _diff_snapshots(snap_a, snap_b)

    print("=== Schema diff ===")
    if diff["tables_only_in_a"]:
        print("\nTables only in A:")
        for t in diff["tables_only_in_a"]:
            print(f"  - {t}")
    if diff["tables_only_in_b"]:
        print("\nTables only in B:")
        for t in diff["tables_only_in_b"]:
            print(f"  - {t}")

    for t, td in diff["tables_in_both"].items():
        print(f"\n--- Table: {t} ---")
        for k in ["columns_only_in_a", "columns_only_in_b", "indexes_only_in_a", "indexes_only_in_b"]:
            if td[k]:
                print(f"{k}: {td[k]}")
        if td["columns_changed"]:
            print("columns_changed:")
            for c, v in td["columns_changed"].items():
                print(f"  - {c}: {v['a']}  !=  {v['b']}")
        if td["indexes_changed"]:
            print("indexes_changed:")
            for i, v in td["indexes_changed"].items():
                print(f"  - {i}: {v['a']}  !=  {v['b']}")
        if td["constraints_only_in_a"]:
            print(f"constraints_only_in_a: {td['constraints_only_in_a']}")
        if td["constraints_only_in_b"]:
            print(f"constraints_only_in_b: {td['constraints_only_in_b']}")
        if td["constraints_changed"]:
            print("constraints_changed:")
            for ck, v in td["constraints_changed"].items():
                print(f"  - {ck}: {v['a']}  !=  {v['b']}")

    if out_json:
        with open(out_json, "w", encoding="utf-8") as f:
            json.dump(diff, f, indent=2)
        print(f"\nWrote JSON diff to: {out_json}")


if __name__ == "__main__":
    import argparse

    p = argparse.ArgumentParser(description="Compare two DB schemas via SQLAlchemy reflection.")
    p.add_argument("--db-a", required=True, help="SQLAlchemy URL for Alembic DB")
    p.add_argument("--db-b", required=True, help="SQLAlchemy URL for Django DB")
    p.add_argument("--schema-a", default=None, help="Schema name for DB A (e.g. public)")
    p.add_argument("--schema-b", default=None, help="Schema name for DB B (e.g. public)")
    p.add_argument("--out-json", default=None, help="Optional path to write diff as JSON")
    args = p.parse_args()

    main(args.db_a, args.db_b, args.schema_a, args.schema_b, args.out_json)
