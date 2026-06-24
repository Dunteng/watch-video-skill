# Technical / Interview Video Summary Example

> This is a sanitized example. It demonstrates the document-grade summary shape that `watchvideo` expects an agent to produce from transcript, keyframes, and OCR evidence.

## One-Sentence Summary

The video argues that an agent memory system is not about storing everything; it is about **saving, retrieving, and forgetting high-value context at the right time**. This is most relevant when designing long-running coding agents, project assistants, and knowledge workflows.

## Video Throughline

1. `[00:00:08 - 00:00:42]` The interview framing: when asked how to design agent memory, do not answer only with "use a database" or "use vector search."
2. `[00:00:43 - 00:01:28]` The speaker introduces three layers: short-term context, working memory, and long-term memory.
3. `[00:01:29 - 00:02:12]` The write policy matters: long-term memory should keep stable preferences, project rules, decisions, and failure lessons, not every interaction.
4. `[00:02:13 - 00:02:58]` Compression and forgetting are part of the design: keep conclusions and evidence, drop low-value intermediate steps.
5. `[00:02:59 - 00:03:24]` The interview answer should distinguish memory from context engineering and explain when to store, retrieve, and forget.

## Core Concepts

### Short-Term Memory

- **Definition**: Information currently visible in the model context window.
- **Boundary**: Fast and immediate, but capacity-limited.
- **Example**: Recent turns, current tool outputs, and current task state.
- **Why it matters**: It keeps the current answer coherent.
- **Video evidence**: The transcript around `[00:00:55]` mentions the current context window and recent conversation.

### Working Memory

- **Definition**: Temporary structured notes or task state for a long-running task.
- **Boundary**: Usually tied to the current task and not always worth storing across sessions.
- **Example**: Files changed during a coding task, next verification step, unresolved bugs.
- **Why it matters**: It prevents losing intermediate decisions during long work.
- **Video evidence**: The transcript around `[00:01:16]` describes a temporary draft area for task state.

### Long-Term Memory

- **Definition**: Stable information that can be reused across sessions.
- **Boundary**: It should be filtered, compressed, updated, and deleted; it is not a dump of all chat history.
- **Example**: User preferences, project conventions, historical decisions, recurring mistakes.
- **Why it matters**: It helps an agent recall stable context in future sessions.
- **Video evidence**: The transcript around `[00:01:48]` mentions high-value memory such as user preferences and verified decisions.

## Common Misconceptions

### Misconception: Memory is just a vector database

- **Why it is wrong**: Vector search is only one retrieval mechanism. It does not solve write policy, memory quality, forgetting, or context budget.
- **Better answer**: Cover writing, retrieval, compression, expiry, and permission boundaries.
- **Evidence**: Around `[00:00:31]`, the transcript says not to answer only with database/vector database.

### Misconception: More long-term memory is always better

- **Why it is wrong**: Low-quality memory pollutes retrieval and consumes context.
- **Better answer**: Keep stable, high-value, confirmed information.
- **Evidence**: Around `[00:02:02]`, the transcript focuses on high-value memory.

## Actionable Method

- **Prerequisite**: The task needs context across turns or sessions.
- **Steps**:
  1. Split information into short-term, working, and long-term memory.
  2. Set a write threshold for long-term memory: stable, reusable, confirmed.
  3. Retrieve by current task goal instead of injecting all history.
  4. When context is full, compress intermediate steps and preserve conclusions, evidence, and next actions.
  5. Periodically prune outdated preferences, wrong decisions, and one-off task details.
- **Checklist**:
  - Does the design explain when memory is written?
  - Does it explain when memory is retrieved?
  - Does it include forgetting or updating?
  - Does it separate memory from context engineering?
- **Good fit**: Coding assistants, research assistants, long-term project agents, support agents.
- **Poor fit**: One-off Q&A and short tasks with no cross-turn continuity.

## Interview Answer Template

### 30-Second Version

I would split agent memory into short-term context, task-level working memory, and long-term memory. Short-term context supports current reasoning, working memory supports long tasks, and long-term memory stores stable high-value information like user preferences, project rules, and historical decisions. The point is not to store more; the point is to decide when to write, retrieve, compress, and forget.

### 2-Minute Version

I would not equate memory with a vector database. A vector database may help retrieval, but a full memory system also needs write policy, retrieval policy, context injection, compression, and expiry. User preferences and project rules can become long-term memory; the current bug investigation state is better treated as working memory; recent conversation stays in short-term context. Retrieval should be scoped to the current task, otherwise irrelevant history pollutes the prompt. When context gets full, the agent should compress tool calls and intermediate reasoning, keeping conclusions, evidence, failure lessons, and next actions.

### Follow-Up Answers

- If asked how to prevent memory pollution: use write thresholds, source labels, update time, confidence, and deletion.
- If asked whether to use a vector database: use it when useful, but treat it as retrieval infrastructure, not the memory system itself.
- If asked how to evaluate it: measure task success, repeated-error rate, stale memory hits, and user corrections.

### Weak Answer

"Connect a vector database and store every chat message, then retrieve relevant messages when needed."

This misses write policy, forgetting, context budget, and evidence boundaries.

## Transcription Correction Notes

| Suspicious ASR | Suggested Correction | Confidence | Evidence |
| --- | --- | --- | --- |
| context compression | Context Compression | High | Keyframe OCR shows the English title |
| connect database/vector DB | connect a database or vector database | Medium | The transcript context is consistent, but ASR punctuation is noisy |
| working memory draft area | temporary draft area in working memory | Medium | Surrounding transcript discusses task state |

## Evidence Limits

- This sample does not include real keyframe images; it demonstrates the final report structure.
- If a real report lacks transcript, OCR, or keyframe support for a section, keep the heading and write "not explicitly stated in the video."
