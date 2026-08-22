# Architecture Proposal v0.1 — Paperclip × Agents-OS Core × Hermes

**Status:** Draft for multi-agent review. Not approved architecture.

## Objective

Use the `aavendano/paperclip` fork as the experimental organization layer for a hierarchy of agents governed by Agents-OS Core. A non-technical Shopify operator interacts with a persistent principal/CEO agent implemented with Hermes. When required capabilities do not exist, the system must communicate the limitation, create a governed engineering escalation in Linear, and maintain traceability back to the originating user need.

## Initial evidence

Paperclip already provides an operational control plane with org charts, tasks, heartbeats, budgets, approvals, audit trails, persistent agent state and provider adapters. The fork also contains adapter packages, MCP infrastructure and Hermes gateway smoke scripts. The initial design should therefore exploit those boundaries rather than replace Paperclip's orchestration kernel.

## Responsibility split

### Paperclip
Own organization topology, reporting lines, task lifecycle, heartbeats, budgets, operator approvals, operational coordination and the management UI.

### Agents-OS Core
Own normative governance semantics, identity/authority/capability evaluation, grants, human-direction gates, escalation semantics, evidence requirements and the governed execution/tool boundary.

### Hermes
Implement the cognitive/runtime behavior of the principal CEO agent. Hermes is not the source of authority.

### OpenWebUI
Act as an alternate conversational channel to the same principal-agent identity. It must not create a logically separate CEO.

### Linear
Operational SSoT for engineering escalations and implementation work arising from missing capabilities.

### GitHub
Versioned source, technical proposals, PRs and implementation evidence.

### Notion
Historical bitácora and knowledge only; not the operational task SSoT.

## Hypotheses

### H1 — Governed adapter boundary

Material agent execution invoked by Paperclip should pass through a Core-governed boundary. Core evaluates identity, requested capability, authority/grant, policy/gates and evidence requirements before routing allowed execution to a provider/runtime.

This preserves the invariant `Governance != Execution` and keeps Paperclip, Hermes and downstream providers replaceable.

### H2 — Core distribution

Do not make a Git submodule the primary runtime integration. Prefer a versioned immutable Core package/service contract. Construction mode may use source repositories; operation mode should consume released Core interfaces only.

### H3 — One principal identity, multiple channels

The Paperclip CEO and OpenWebUI chat endpoint resolve to one durable principal `AgentIdentity` and one governed memory namespace. Channel sessions contribute transient context but cannot create separate authority or divergent long-term identity.

### H4 — Missing capability becomes governed escalation

When the user requests an unavailable capability, the principal agent responds with a bounded unavailable/escalation state, records the requested outcome and evidence, and opens a Linear technical request. This is a request for engineering evaluation, not a promise that implementation will be approved.

## First business vertical

A Shopify operator asks the CEO to create or manage content without programming knowledge:

`content request → capability discovery → governed execution OR technical escalation → user-visible status`

The first implementation should be deliberately small enough to falsify the architecture quickly.

## Shared-memory requirements

1. Stable agent identity independent of channel.
2. Durable facts/decisions separated from transient conversation context.
3. Memory writes governed and auditable.
4. Paperclip task context may be injected into Hermes without automatically becoming unrestricted long-term memory.
5. Paperclip and OpenWebUI share only the memory scopes allowed for the principal identity.

## Approval invariant

Direction decisions must not exist as two independent approval authorities. Paperclip may be the human-facing approval surface, but Core must remain the semantic authority that determines when a Human Gate is required and records the authorization basis/evidence.

## Architecture forum protocol

Each reviewer must:

- classify major claims as `SUPPORTED`, `WEAK`, `REJECT`, or `UNKNOWN`;
- identify concrete repository extension points;
- challenge stack and coupling assumptions;
- propose alternatives;
- identify double-governance risks;
- propose the smallest experiment that could falsify the current thesis;
- preserve dissent rather than force consensus.

## Cycle 1 acceptance criteria

- Identify concrete Paperclip extension points for governed execution and the principal agent.
- Decide package vs sidecar/service vs plugin vs hybrid for Core, with evidence.
- Define principal identity/shared-memory boundary across Paperclip and OpenWebUI.
- Define `missing capability → Linear escalation` contract.
- Select the minimal Shopify content-management experiment.
- Obtain Cursor adversarial review followed by Codex independent review.

## Open questions

1. Does Paperclip's existing Hermes gateway already satisfy enough integration to avoid a new principal-agent adapter?
2. Which Paperclip operations must Core intercept for governance to be real rather than cosmetic?
3. Where should durable memory physically live, and what authority does Core hold over writes?
4. Should Core run in-process for policy evaluation while execution remains out-of-process?
5. Which technology should implement Shopify content actions in the first vertical?
6. How should Paperclip approvals project a single Core Human Gate without creating a second source of authority?

## Operational references

- Linear project: `Paperclip × Agents-OS Core × Hermes Experiment`
- Research cycle: `AAD-51`
- Cursor review: `AAD-52`
- Codex second-pass review: `AAD-53`
