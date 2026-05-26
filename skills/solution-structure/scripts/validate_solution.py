#!/usr/bin/env python3
"""Validate a blade-agent Solution v3 directory.

This script is intentionally lightweight so an AI agent can run it while drafting
Solution packages outside the main repo. It checks local structure only; platform
loading still performs registry and runtime checks.
"""

from __future__ import annotations

import argparse
from pathlib import Path
import sys
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, ValidationError, field_validator
import yaml

LayoutType = Literal["default", "skill-editor", "blade-coa"]
InitialMode = Literal["planning", "executing"]


class SolutionYaml(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    name: str
    manifest_version: Literal[3]
    version: str
    description: str = ""
    layout_type: LayoutType = "default"
    initial_mode: InitialMode | None = None
    initial_message: str | None = None
    skill_tools_enabled: bool = True
    imported_skills: list[str] = []
    roles: list[str]
    data: dict[str, Any] | None = None

    @field_validator("id", "name", "version", "description", mode="after")
    @classmethod
    def _strip_required_strings(cls, value: str) -> str:
        return value.strip()

    @field_validator("id", "name", "version", mode="after")
    @classmethod
    def _non_empty_required_strings(cls, value: str) -> str:
        if not value:
            raise ValueError("must be a non-empty string")
        return value

    @field_validator("roles", mode="after")
    @classmethod
    def _roles_must_be_non_empty_strings(cls, value: list[str]) -> list[str]:
        roles = [item.strip() for item in value]
        if not roles:
            raise ValueError("must contain at least one role id")
        if any(not item for item in roles):
            raise ValueError("must contain only non-empty role id strings")
        if len(set(roles)) != len(roles):
            raise ValueError("must not contain duplicate role ids")
        return roles

    @field_validator("imported_skills", mode="after")
    @classmethod
    def _imported_skills_must_be_non_empty_strings(cls, value: list[str]) -> list[str]:
        return _strip_non_empty_list(value)


class RoleYaml(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    name: str
    version: str
    description: str = ""
    layout_type: LayoutType | None = None
    initial_mode: InitialMode | None = None
    initial_message: str | None = None
    local_skills: list[str] = []
    imported_skills: list[str] = []

    @field_validator("id", "name", "version", "description", mode="after")
    @classmethod
    def _strip_strings(cls, value: str) -> str:
        return value.strip()

    @field_validator("id", "name", "version", mode="after")
    @classmethod
    def _non_empty_required_strings(cls, value: str) -> str:
        if not value:
            raise ValueError("must be a non-empty string")
        return value

    @field_validator("local_skills", "imported_skills", mode="after")
    @classmethod
    def _skill_lists_must_be_non_empty_strings(cls, value: list[str]) -> list[str]:
        return _strip_non_empty_list(value)


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate a blade-agent Solution v3 directory")
    parser.add_argument("solution_dir", type=Path)
    args = parser.parse_args()

    errors = validate_solution(args.solution_dir)
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print(f"OK: {args.solution_dir}")
    return 0


def validate_solution(solution_dir: Path) -> list[str]:
    errors: list[str] = []
    solution_dir = solution_dir.resolve()
    solution_yaml = solution_dir / "solution.yaml"
    solution_data = _load_yaml(solution_yaml, errors)
    if not isinstance(solution_data, dict):
        return errors
    solution = _parse_model(SolutionYaml, solution_data, solution_yaml, errors)
    if solution is None:
        for role_id in _raw_role_ids(solution_data, solution_yaml, errors):
            _validate_role(solution_dir, role_id, errors)
        return errors

    for role_id in solution.roles:
        _validate_role(solution_dir, role_id, errors)

    return errors


def _validate_role(solution_dir: Path, role_id: str, errors: list[str]) -> None:
    role_dir = solution_dir / "roles" / role_id
    role_yaml = role_dir / "role.yaml"
    role_data = _load_yaml(role_yaml, errors)
    if not isinstance(role_data, dict):
        return
    role = _parse_model(RoleYaml, role_data, role_yaml, errors)
    if role is None:
        _validate_raw_role_cross_file(solution_dir, role_dir, role_yaml, role_id, role_data, errors)
        return

    if (role_dir / "skills").exists():
        errors.append(
            f"{role_dir / 'skills'}: v3 does not support role-local skills; "
            "move them to solution/skills and reference them with local_skills"
        )

    if role.id != role_id:
        errors.append(f"{role_yaml}: id must match role directory name {role_id!r}")

    for skill_id in role.local_skills:
        skill_path = Path(skill_id)
        if skill_path.is_absolute() or ".." in skill_path.parts:
            errors.append(f"{role_yaml}: local_skills contains invalid skill id {skill_id!r}")
            continue
        if not (solution_dir / "skills" / skill_id / "SKILL.md").is_file():
            errors.append(f"{role_yaml}: local skill {skill_id!r} is missing solution/skills/{skill_id}/SKILL.md")


def _validate_raw_role_cross_file(
    solution_dir: Path,
    role_dir: Path,
    role_yaml: Path,
    role_id: str,
    role_data: dict[str, Any],
    errors: list[str],
) -> None:
    if (role_dir / "skills").exists():
        errors.append(
            f"{role_dir / 'skills'}: v3 does not support role-local skills; "
            "move them to solution/skills and reference them with local_skills"
        )
    if isinstance(role_data.get("id"), str) and role_data["id"].strip() != role_id:
        errors.append(f"{role_yaml}: id must match role directory name {role_id!r}")
    local_skills = role_data.get("local_skills")
    if not isinstance(local_skills, list):
        return
    for skill_id in local_skills:
        if not isinstance(skill_id, str) or not skill_id.strip():
            continue
        skill_id = skill_id.strip()
        skill_path = Path(skill_id)
        if skill_path.is_absolute() or ".." in skill_path.parts:
            errors.append(f"{role_yaml}: local_skills contains invalid skill id {skill_id!r}")
            continue
        if not (solution_dir / "skills" / skill_id / "SKILL.md").is_file():
            errors.append(f"{role_yaml}: local skill {skill_id!r} is missing solution/skills/{skill_id}/SKILL.md")


def _load_yaml(path: Path, errors: list[str]) -> Any:
    if not path.is_file():
        errors.append(f"{path}: file not found")
        return None
    try:
        value = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        errors.append(f"{path}: failed to parse YAML: {exc}")
        return None
    if not isinstance(value, dict):
        errors.append(f"{path}: must contain a mapping")
    return value


def _raw_role_ids(solution_data: dict[str, Any], solution_yaml: Path, errors: list[str]) -> list[str]:
    roles = solution_data.get("roles")
    if not isinstance(roles, list):
        return []
    role_ids: list[str] = []
    for index, role_id in enumerate(roles):
        if not isinstance(role_id, str) or not role_id.strip():
            errors.append(f"{solution_yaml}: roles.{index}: must be a role id string")
            continue
        role_ids.append(role_id.strip())
    return role_ids


def _parse_model(
    model: type[BaseModel],
    data: dict[str, Any],
    path: Path,
    errors: list[str],
) -> BaseModel | None:
    try:
        return model.model_validate(data)
    except ValidationError as exc:
        errors.extend(_format_validation_errors(path, exc))
        return None


def _format_validation_errors(path: Path, exc: ValidationError) -> list[str]:
    errors: list[str] = []
    for item in exc.errors():
        location = ".".join(str(part) for part in item["loc"]) or "<root>"
        message = str(item["msg"])
        errors.append(f"{path}: {location}: {message}")
    return errors


def _strip_non_empty_list(value: list[str]) -> list[str]:
    items = [item.strip() for item in value]
    if any(not item for item in items):
        raise ValueError("must contain only non-empty strings")
    return items


if __name__ == "__main__":
    raise SystemExit(main())
