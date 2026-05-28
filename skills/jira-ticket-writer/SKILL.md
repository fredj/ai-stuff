---
name: jira-ticket-writer
description: >
  Use when the user wants to write, draft, or create a Jira ticket or Jira
  comment — bugs, stories, tasks, status updates, or replies. Activate on
  action verbs like "make a ticket", "write up this bug", "post a comment",
  "reply to that comment", even when "Jira" is never mentioned. The signal is
  creation intent: the user has something to communicate and needs it turned
  into a structured Jira artifact. Skip when the user wants to read, analyze,
  summarize, or estimate an existing ticket, or when the output is a PR
  description, email, or Slack message.
---

# Jira Ticket & Comment Writer

## Your job

Turn a rough description into polished Jira content — a ticket, a new comment,
or a reply to an existing comment — always in Jira wiki markup.

---

## Writing a ticket

### Step 1 — Infer the ticket type

From the user's prompt, decide:

- **Story / Feature** — new capability or user-facing improvement
- **Bug** — something broken or behaving incorrectly
- **Chore / Task** — internal work, refactoring, dependency update, CI/infra

If the type is ambiguous, lean toward Story.

### Step 2 — Identify missing information

Before writing, check whether you have enough to fill the key sections.
Ask up to 3 targeted questions **only** if critical information is absent:

| Ticket type | You must know |
|-------------|--------------|
| Story | What the user/system can do after this is done (the goal) |
| Bug | How to reproduce it, and what the expected vs actual behavior is |
| Chore | What concretely needs to be done and how to verify it's complete |

If the prompt already implies these answers, skip questions and write directly.
One focused clarification round is fine; don't ask more than once.

### Step 3 — Write the ticket

Output the title first, then the description body in Jira wiki markup.

#### Title format

```
*Title:* <concise imperative phrase, max ~80 chars>
```

Examples:
- `*Title:* Add search filter to hiking list page`
- `*Title:* Fix map not loading on mobile Safari`
- `*Title:* Upgrade Node.js to v22 in CI pipeline`

#### Description templates

Use the appropriate template. Always write in English.

---

**Story / Feature**

```
h2. Context

<Why this matters. What problem it solves or opportunity it addresses.>

h2. Goal

<What the system or user can do after this ticket is done. One or two sentences.>

h2. Acceptance Criteria

(x) <criterion 1>
(x) <criterion 2>
(x) <criterion 3>

h2. Out of Scope

<Optional. List what is explicitly not included, if clarifying this avoids ambiguity.>
```

---

**Bug**

```
h2. Summary

<One sentence describing what is broken and where.>

h2. Steps to Reproduce

# <step 1>
# <step 2>
# <step 3>

h2. Expected Behavior

<What should happen.>

h2. Actual Behavior

<What actually happens.>

h2. Impact / Severity

<Who is affected, how often, and how badly. Include environment/browser/device if known.>
```

---

**Chore / Task**

```
h2. Context

<Why this work needs to happen. Link to a problem, tech debt, or requirement.>

h2. What to Do

<Concrete steps or description of the work. Be specific enough that any team member can pick this up.>

h2. Definition of Done

(x) <criterion 1>
(x) <criterion 2>
```

---

## Writing a comment or reply

Use this when the user wants to post a new comment or reply to an existing one
on a Jira ticket.

### When to ask questions

Ask only if the intent is unclear:

- What is the message trying to communicate? (status update, question, decision, blocker, etc.)
- Who is the audience? (team member, PO, external stakeholder)

If the user provides enough context, write directly without asking.

### Comment format

Keep comments focused and readable. Use markup only when it genuinely helps
clarity (e.g., a list of findings, a code snippet). Avoid over-formatting short
conversational replies.

**Status update**

```
*Status update*

<One or two sentences on current state, what was done, what's next.>
```

**Question or request for input**

```
<Clear, direct question.>

<Optional: brief context explaining why you need this.>
```

**Decision or outcome**

```
*Decision:* <what was decided>

<Optional: rationale in one or two sentences.>
```

**Reply to a comment**

Mirror the tone and register of the thread. If the original comment is informal,
reply informally. If it's formal (e.g., a stakeholder or PO), reply formally.
Quote the relevant part only if needed for clarity:

```
{quote}<excerpt from comment being replied to>{quote}

<Your reply.>
```

---

## Jira wiki markup reference

Jira uses its own wiki markup — **not Markdown**. Always use Jira syntax in
ticket descriptions and comments:

| Effect | Syntax |
|--------|--------|
| Bold | `*text*` |
| Italic | `_text_` |
| Bullet list | `* item` |
| Numbered list | `# item` |
| Heading | `h2. Title` |
| Monospace | `{{code}}` |
| Code block | `{code}...{code}` |
| Quote | `{quote}...{quote}` |

Always present the raw markup in a fenced code block so the user can copy-paste
it directly into Jira.

---

## Tone and style

- Be direct and specific. Avoid filler phrases like "This ticket aims to...".
- Acceptance criteria and DoD items should be independently verifiable.
- If the user's prompt mentions a specific project, feature, or area of the
  codebase, preserve that context — don't genericize it.
- Keep ticket titles short enough to scan in a backlog list.
- **Audience**: Adapt the tone to the intended reader. If the content is directed
  at a non-technical stakeholder (PO, customer), keep language simple and avoid
  internal terms. If unclear, ask the user who the audience is.
