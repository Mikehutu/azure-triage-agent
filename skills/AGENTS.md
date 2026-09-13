# skills

## Purpose

Product/domain agent skills that stay inside the project (not global methodology skills).

## Ownership

- Owns: in-repo skill packs for this product
- Parent owns: when skills must be loaded; methodology skills live in the agent install, not here

## Local Contracts

- Each skill: directory + `SKILL.md` with name/description frontmatter
- Domain skills must not silently overwrite global SDD methodology skill names
- Cite `kb/` / official sources when encoding product behavior

## Work Guidance

- Keep procedures operational and current
- Prefer linking to DESIGN/BUILD docs over duplicating long prose

## Verification

- Skill loads with clear trigger description
- No invented vendor behavior

## Child DOX Index

- None unless a skill grows a multi-folder subsystem
