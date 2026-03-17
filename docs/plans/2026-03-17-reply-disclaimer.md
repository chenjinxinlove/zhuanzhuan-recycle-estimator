# Reply Disclaimer Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Ensure recycle valuation replies that use backend `reply` always end with the fixed Zhuanzhuan professional assessment disclaimer.

**Architecture:** This is a skill-spec change, not an API change. Update the skill contract in `SKILL.md` so agents preserve backend `reply` as the main body and append one fixed sentence only when `reply` is present.

**Tech Stack:** Markdown documentation, OpenClaw skill spec

---

### Task 1: Update reply rules

**Files:**
- Modify: `SKILL.md`

**Step 1: Update the working principle**

Clarify that when backend `reply` exists, the final user-visible response should use `reply` as the main content and append the fixed disclaimer at the end.

**Step 2: Update Reply Rules**

Add an explicit rule that only non-empty `reply` responses append the fixed sentence `本次评估来自转转专业评估`.

**Step 3: Preserve clarification behavior**

State that `clarification` and `follow_up_question` flows must not append the disclaimer.

**Step 4: Add an example or boundary note**

Add one concrete note showing the disclaimer belongs only to complete valuation replies.

**Step 5: Verify**

Run: `rg -n "本次评估来自转转专业评估|Reply Rules|Working Principles|Response Boundaries" SKILL.md`

Expected: the fixed sentence appears in the reply rules and the clarification boundary remains intact.
