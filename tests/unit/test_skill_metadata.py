"""Tests for skill SKILL.md metadata and structure.

Verifies that all skills have correct frontmatter, consistent versions,
valid structure, and no fragile cross-skill references.
"""

import re
from pathlib import Path

import pytest
import yaml


SKILLS_DIR = Path(__file__).resolve().parent.parent.parent / "skills"
AGENTS_DIR = Path(__file__).resolve().parent.parent.parent / "agents"

RECOGNIZED_FRONTMATTER_FIELDS = {
    "name", "description", "argument-hint", "disable-model-invocation",
    "user-invocable", "allowed-tools", "model", "effort", "context",
    "agent", "hooks", "paths", "shell", "version",
}

SKILLS_REQUIRING_DISABLE_MODEL_INVOCATION = {
    "implement-roadmap",
    "implement-roadmap-interactively",
    "generate-test-roadmap",
    "import-shared-project",
    "progress-dashboard",
}

ALL_SKILLS = sorted(SKILLS_DIR.iterdir()) if SKILLS_DIR.exists() else []


def _parse_skill_frontmatter(skill_path: Path) -> dict:
    """Parse YAML frontmatter from a SKILL.md file."""
    text = skill_path.read_text()
    match = re.match(r"^---\n(.*?)\n---", text, re.DOTALL)
    assert match, f"No frontmatter in {skill_path}"
    return yaml.safe_load(match.group(1))


def _skill_ids():
    return [d.name for d in ALL_SKILLS if d.is_dir()]


# ---------------------------------------------------------------------------
# Frontmatter field validation
# ---------------------------------------------------------------------------

class TestFrontmatterFields:
    """Every skill must have required frontmatter fields."""

    @pytest.mark.parametrize("skill_name", _skill_ids())
    def test_has_name_field(self, skill_name):
        meta = _parse_skill_frontmatter(SKILLS_DIR / skill_name / "SKILL.md")
        assert "name" in meta

    @pytest.mark.parametrize("skill_name", _skill_ids())
    def test_name_matches_directory(self, skill_name):
        meta = _parse_skill_frontmatter(SKILLS_DIR / skill_name / "SKILL.md")
        assert meta["name"] == skill_name

    @pytest.mark.parametrize("skill_name", _skill_ids())
    def test_name_is_kebab_case(self, skill_name):
        meta = _parse_skill_frontmatter(SKILLS_DIR / skill_name / "SKILL.md")
        assert re.match(r"^[a-z][a-z0-9-]*$", meta["name"]), \
            f"Name '{meta['name']}' is not kebab-case"

    @pytest.mark.parametrize("skill_name", _skill_ids())
    def test_has_description(self, skill_name):
        meta = _parse_skill_frontmatter(SKILLS_DIR / skill_name / "SKILL.md")
        assert "description" in meta
        assert len(meta["description"]) > 0

    @pytest.mark.parametrize("skill_name", _skill_ids())
    def test_description_under_200_chars(self, skill_name):
        meta = _parse_skill_frontmatter(SKILLS_DIR / skill_name / "SKILL.md")
        assert len(meta["description"]) <= 200, \
            f"Description is {len(meta['description'])} chars (max 200)"

    @pytest.mark.parametrize("skill_name", _skill_ids())
    def test_has_version(self, skill_name):
        meta = _parse_skill_frontmatter(SKILLS_DIR / skill_name / "SKILL.md")
        assert "version" in meta

    @pytest.mark.parametrize("skill_name", _skill_ids())
    def test_disable_model_invocation_policy(self, skill_name):
        meta = _parse_skill_frontmatter(SKILLS_DIR / skill_name / "SKILL.md")
        if skill_name in SKILLS_REQUIRING_DISABLE_MODEL_INVOCATION:
            assert meta.get("disable-model-invocation") is True, \
                f"Skill '{skill_name}' must have disable-model-invocation: true"
        else:
            assert "disable-model-invocation" not in meta or \
                meta.get("disable-model-invocation") is not True, \
                f"Skill '{skill_name}' should NOT have disable-model-invocation: true"


# ---------------------------------------------------------------------------
# Version consistency
# ---------------------------------------------------------------------------

class TestVersionConsistency:
    """Version in frontmatter must match the version check output string."""

    @pytest.mark.parametrize("skill_name", _skill_ids())
    def test_version_string_matches_frontmatter(self, skill_name):
        skill_path = SKILLS_DIR / skill_name / "SKILL.md"
        meta = _parse_skill_frontmatter(skill_path)
        version = str(meta["version"])
        text = skill_path.read_text()

        expected_pattern = f"{skill_name} v{version}"
        assert expected_pattern in text, \
            f"Version check should print '{expected_pattern}' but frontmatter version is '{version}'"


# ---------------------------------------------------------------------------
# argument-hint when $ARGUMENTS is used
# ---------------------------------------------------------------------------

class TestArgumentHint:
    """Skills that use $ARGUMENTS should have an argument-hint."""

    @pytest.mark.parametrize("skill_name", _skill_ids())
    def test_argument_hint_present_when_arguments_used(self, skill_name):
        skill_path = SKILLS_DIR / skill_name / "SKILL.md"
        text = skill_path.read_text()
        meta = _parse_skill_frontmatter(skill_path)

        uses_arguments = "$ARGUMENTS" in text
        # Skills that only use $ARGUMENTS for --version check don't need argument-hint
        # But having one is still fine — we only fail if $ARGUMENTS is used in the
        # main skill body (not just the version check block) without an argument-hint
        if uses_arguments and "argument-hint" not in meta:
            # Count non-version-check uses of $ARGUMENTS
            # Version check is always the first use, in a block ending with "stop"
            lines = text.split("\n")
            version_block = True
            non_version_uses = 0
            for line in lines:
                if "---" in line and not version_block:
                    version_block = False
                if version_block and ("stop" in line.lower() or "---" == line.strip()):
                    if "---" == line.strip():
                        continue
                    version_block = False
                    continue
                if not version_block and "$ARGUMENTS" in line:
                    non_version_uses += 1

            if non_version_uses > 0:
                pytest.fail(
                    f"Skill '{skill_name}' uses $ARGUMENTS in main body "
                    f"but has no argument-hint in frontmatter"
                )


# ---------------------------------------------------------------------------
# File structure
# ---------------------------------------------------------------------------

class TestFileStructure:
    """Skills must have proper file structure."""

    @pytest.mark.parametrize("skill_name", _skill_ids())
    def test_skill_md_exists(self, skill_name):
        assert (SKILLS_DIR / skill_name / "SKILL.md").exists()

    @pytest.mark.parametrize("skill_name", _skill_ids())
    def test_under_500_lines(self, skill_name):
        skill_path = SKILLS_DIR / skill_name / "SKILL.md"
        line_count = len(skill_path.read_text().splitlines())
        assert line_count <= 500, \
            f"SKILL.md is {line_count} lines (max 500)"

    @pytest.mark.parametrize("skill_name", _skill_ids())
    def test_no_loose_files_at_root(self, skill_name):
        """Only SKILL.md should be at the skill root; other files go in references/."""
        skill_dir = SKILLS_DIR / skill_name
        root_files = [f.name for f in skill_dir.iterdir() if f.is_file()]
        unexpected = [f for f in root_files if f != "SKILL.md"]
        assert not unexpected, \
            f"Unexpected files at skill root (should be in references/): {unexpected}"

    @pytest.mark.parametrize("skill_name", _skill_ids())
    def test_no_fragile_parent_references(self, skill_name):
        """Skills must not use ../ to reference sibling skill directories."""
        skill_path = SKILLS_DIR / skill_name / "SKILL.md"
        text = skill_path.read_text()
        parent_refs = re.findall(r'\$\{CLAUDE_SKILL_DIR\}/\.\./', text)
        assert not parent_refs, \
            f"Fragile parent references found: {parent_refs}. " \
            f"Copy files into this skill's references/ instead."

    @pytest.mark.parametrize("skill_name", _skill_ids())
    def test_referenced_files_exist(self, skill_name):
        """Files referenced via ${CLAUDE_SKILL_DIR} must exist."""
        skill_path = SKILLS_DIR / skill_name / "SKILL.md"
        text = skill_path.read_text()
        refs = re.findall(r'\$\{CLAUDE_SKILL_DIR\}/(\S+)', text)
        for ref in refs:
            # Clean up trailing punctuation/quotes
            ref = ref.rstrip('"`\')`.,')
            ref_path = SKILLS_DIR / skill_name / ref
            assert ref_path.exists(), \
                f"Referenced file does not exist: {ref}"


# ---------------------------------------------------------------------------
# Step numbering (skills that contain step definitions)
# ---------------------------------------------------------------------------

class TestStepNumbering:
    """Skills with numbered steps must have sequential numbering."""

    @pytest.mark.parametrize("skill_name", _skill_ids())
    def test_no_step_numbering_gaps(self, skill_name):
        """Step N headers must be sequential with no gaps."""
        skill_path = SKILLS_DIR / skill_name / "SKILL.md"
        text = skill_path.read_text()

        # Find all "## Step N:" or "## Step N " patterns
        step_numbers = [int(m) for m in re.findall(r'^## Step (\d+)[:\s]', text, re.MULTILINE)]

        if len(step_numbers) < 2:
            return  # Not enough steps to check sequencing

        for i in range(1, len(step_numbers)):
            assert step_numbers[i] == step_numbers[i - 1] + 1, \
                f"Step numbering gap: Step {step_numbers[i - 1]} followed by " \
                f"Step {step_numbers[i]} (expected Step {step_numbers[i - 1] + 1})"


# ---------------------------------------------------------------------------
# Repair-roadmap specific: own copies of shared files
# ---------------------------------------------------------------------------

class TestRepairRoadmapReferences:
    """repair-roadmap must have its own copies of coordinator and template."""

    def test_has_coordinator(self):
        assert (SKILLS_DIR / "repair-roadmap" / "references" / "coordinator").exists()

    def test_has_template(self):
        assert (SKILLS_DIR / "repair-roadmap" / "references" / "feature-roadmap-template.md").exists()

    def test_coordinator_matches_source(self):
        """repair-roadmap's coordinator should match implement-roadmap's."""
        repair = (SKILLS_DIR / "repair-roadmap" / "references" / "coordinator").read_text()
        source = (SKILLS_DIR / "implement-roadmap" / "references" / "coordinator").read_text()
        assert repair == source, "coordinator copy is out of sync with source"

    def test_template_matches_source(self):
        """repair-roadmap's template should match plan-roadmap's."""
        repair = (SKILLS_DIR / "repair-roadmap" / "references" / "feature-roadmap-template.md").read_text()
        source = (SKILLS_DIR / "plan-roadmap" / "references" / "feature-roadmap-template.md").read_text()
        assert repair == source, "template copy is out of sync with source"


# ---------------------------------------------------------------------------
# Lint verification: template and agent must support lint
# ---------------------------------------------------------------------------

class TestLintVerification:
    """Templates must include Lint row and agent must have lint phase."""

    def test_template_has_lint_row(self):
        """Feature roadmap template must have a Lint row in Verification Strategy."""
        template = (SKILLS_DIR / "plan-roadmap" / "references" / "feature-roadmap-template.md").read_text()
        assert "| Lint |" in template, "Template missing Lint row in Verification Strategy"

    def test_agent_has_lint_section(self):
        """implement-step-agent must have a lint verification section."""
        agent = (Path(__file__).resolve().parent.parent.parent / "agents" / "implement-step-agent.md").read_text()
        assert "### 4.3. Lint" in agent, "Agent missing lint verification section (4.3)"

    def test_agent_gate_includes_lint(self):
        """implement-step-agent's mandatory gate must include lint."""
        agent = (Path(__file__).resolve().parent.parent.parent / "agents" / "implement-step-agent.md").read_text()
        assert "LINT_GATE_FAILED" in agent, "Agent gate missing LINT_GATE_FAILED log entry"


# ---------------------------------------------------------------------------
# Guideline applicability checklist: template and skill must support concerns
# ---------------------------------------------------------------------------

class TestGuidelineConcerns:
    """Templates must have concerns field and skill must have concern selection step."""

    def test_template_has_concerns_field(self):
        """Feature roadmap template must have a concerns field in frontmatter."""
        template = (SKILLS_DIR / "plan-roadmap" / "references" / "feature-roadmap-template.md").read_text()
        assert "concerns:" in template, "Template missing concerns field in frontmatter"

    def test_template_concerns_has_always_list(self):
        """Concerns field must include an always list with core engineering concerns."""
        template = (SKILLS_DIR / "plan-roadmap" / "references" / "feature-roadmap-template.md").read_text()
        assert "always:" in template, "Template missing always list in concerns"
        assert "fail-fast" in template, "Template missing fail-fast in always concerns"
        assert "separation-of-concerns" in template, "Template missing separation-of-concerns in always concerns"

    def test_template_concerns_has_opt_lists(self):
        """Concerns field must include opted-in and opted-out lists."""
        template = (SKILLS_DIR / "plan-roadmap" / "references" / "feature-roadmap-template.md").read_text()
        assert "opted-in:" in template, "Template missing opted-in list in concerns"
        assert "opted-out:" in template, "Template missing opted-out list in concerns"

    def test_skill_has_concern_selection_step(self):
        """plan-roadmap must have Step 3c for concern selection."""
        skill = (SKILLS_DIR / "plan-roadmap" / "SKILL.md").read_text()
        assert "## Step 3c: Concern Selection" in skill, "Skill missing Step 3c"

    def test_skill_references_pipeline_concerns(self):
        """plan-roadmap must reference the cookbook's pipeline-concerns.json."""
        skill = (SKILLS_DIR / "plan-roadmap" / "SKILL.md").read_text()
        assert "pipeline-concerns.json" in skill, "Skill doesn't reference pipeline-concerns.json"


# ---------------------------------------------------------------------------
# Three-phase discipline: agent must have Phase 1 and Phase 2
# ---------------------------------------------------------------------------

class TestThreePhaseDiscipline:
    """implement-step-agent must structure implementation as Phase 1 (Work) + Phase 2 (Right)."""

    def test_agent_has_phase_1(self):
        """Agent must have Phase 1 — Make It Work."""
        agent = (Path(__file__).resolve().parent.parent.parent / "agents" / "implement-step-agent.md").read_text()
        assert "Phase 1" in agent and "Make It Work" in agent, "Agent missing Phase 1 — Make It Work"

    def test_agent_has_phase_2(self):
        """Agent must have Phase 2 — Make It Right."""
        agent = (Path(__file__).resolve().parent.parent.parent / "agents" / "implement-step-agent.md").read_text()
        assert "Phase 2" in agent and "Make It Right" in agent, "Agent missing Phase 2 — Make It Right"

    def test_agent_logs_phase_transitions(self):
        """Agent must log phase start/complete events."""
        agent = (Path(__file__).resolve().parent.parent.parent / "agents" / "implement-step-agent.md").read_text()
        assert "PHASE_1_START" in agent, "Agent missing PHASE_1_START log"
        assert "PHASE_1_COMPLETE" in agent, "Agent missing PHASE_1_COMPLETE log"
        assert "PHASE_2_START" in agent, "Agent missing PHASE_2_START log"
        assert "PHASE_2_COMPLETE" in agent, "Agent missing PHASE_2_COMPLETE log"


# ---------------------------------------------------------------------------
# Plan deviation handling: agent and coordinator support deviations
# ---------------------------------------------------------------------------

class TestPlanDeviationHandling:
    """Agent must detect deviations and coordinator must handle blocked status."""

    def test_agent_has_deviation_check(self):
        """Agent must have plan deviation check section."""
        agent = (Path(__file__).resolve().parent.parent.parent / "agents" / "implement-step-agent.md").read_text()
        assert "Plan Deviation Check" in agent, "Agent missing Plan Deviation Check section"

    def test_agent_logs_minor_deviation(self):
        """Agent must log minor deviations."""
        agent = (Path(__file__).resolve().parent.parent.parent / "agents" / "implement-step-agent.md").read_text()
        assert "PLAN_DEVIATION_MINOR" in agent, "Agent missing PLAN_DEVIATION_MINOR log"

    def test_agent_logs_major_deviation(self):
        """Agent must log major deviations."""
        agent = (Path(__file__).resolve().parent.parent.parent / "agents" / "implement-step-agent.md").read_text()
        assert "PLAN_DEVIATION_MAJOR" in agent, "Agent missing PLAN_DEVIATION_MAJOR log"

    def test_coordinator_handles_blocked(self):
        """Coordinator must handle blocked status and output blocked action."""
        coordinator = (SKILLS_DIR / "implement-roadmap" / "references" / "coordinator").read_text()
        assert '"blocked"' in coordinator, "Coordinator missing blocked action"
        assert "blocked_steps" in coordinator, "Coordinator missing blocked_steps output"


# ---------------------------------------------------------------------------
# Verification summary: agent posts consolidated results to PR
# ---------------------------------------------------------------------------

class TestVerificationSummary:
    """Agent must post a verification summary comment to the PR."""

    def test_agent_has_verification_summary(self):
        """Agent must have verification summary section in Finalize step."""
        agent = (Path(__file__).resolve().parent.parent.parent / "agents" / "implement-step-agent.md").read_text()
        assert "Verification Summary" in agent, "Agent missing Verification Summary section"
        assert "VERIFICATION_SUMMARY" in agent, "Agent missing VERIFICATION_SUMMARY log entry"


# ---------------------------------------------------------------------------
# Design decision audit trail
# ---------------------------------------------------------------------------

class TestDesignDecisionAuditTrail:
    """Agent must log design decisions and include them in PR comments."""

    def test_agent_has_design_decision_log_type(self):
        """Agent must define DESIGN_DECISION log entry type."""
        agent = (Path(__file__).resolve().parent.parent.parent / "agents" / "implement-step-agent.md").read_text()
        assert "DESIGN_DECISION:" in agent, "Agent missing DESIGN_DECISION log entry type"

    def test_agent_includes_decisions_in_pr_comment(self):
        """Agent must include design decisions in per-step PR comments."""
        agent = (Path(__file__).resolve().parent.parent.parent / "agents" / "implement-step-agent.md").read_text()
        assert "Design decisions:" in agent, "Agent missing design decisions in PR comment template"


# ---------------------------------------------------------------------------
# Guideline compliance in final review
# ---------------------------------------------------------------------------

class TestGuidelineComplianceReview:
    """Final review must verify opted-in concerns from planning."""

    def test_agent_has_guideline_compliance_step(self):
        """Agent must have guideline compliance check in Finalize."""
        agent = (Path(__file__).resolve().parent.parent.parent / "agents" / "implement-step-agent.md").read_text()
        assert "GUIDELINE_COMPLIANCE_START" in agent, "Agent missing GUIDELINE_COMPLIANCE_START"
        assert "GUIDELINE_COMPLIANCE:" in agent, "Agent missing GUIDELINE_COMPLIANCE log entries"

    def test_agent_reads_concerns_from_frontmatter(self):
        """Agent must read concerns field from Roadmap frontmatter."""
        agent = (Path(__file__).resolve().parent.parent.parent / "agents" / "implement-step-agent.md").read_text()
        assert "opted-in" in agent, "Agent doesn't reference opted-in concerns"


# ---------------------------------------------------------------------------
# Idempotent resume: coordinator resume command
# ---------------------------------------------------------------------------

class TestIdempotentResume:
    """Coordinator must have a resume command for interrupted implementations."""

    def test_coordinator_has_resume_command(self):
        """Coordinator must have a resume command registered."""
        coordinator = (SKILLS_DIR / "implement-roadmap" / "references" / "coordinator").read_text()
        assert '"resume"' in coordinator, "Coordinator missing resume command registration"

    def test_coordinator_resume_outputs_state(self):
        """Resume command must output worktree state classification."""
        coordinator = (SKILLS_DIR / "implement-roadmap" / "references" / "coordinator").read_text()
        assert "uncommitted" in coordinator, "Resume missing uncommitted state"
        assert "committed-not-marked" in coordinator, "Resume missing committed-not-marked state"
        assert "no-worktree" in coordinator, "Resume missing no-worktree state"


# ---------------------------------------------------------------------------
# Auto-merge feature: coordinator skill + worker agent consistency
# ---------------------------------------------------------------------------

class TestAutoMergeFeature:
    """implement-roadmap must offer auto-merge and pass it to the worker agent."""

    @pytest.fixture(autouse=True)
    def load_files(self):
        self.skill_text = (SKILLS_DIR / "implement-roadmap" / "SKILL.md").read_text()
        self.agent_text = (AGENTS_DIR / "implement-step-agent.md").read_text()

    def test_skill_has_auto_merge_question(self):
        """Coordinator must ask the user about auto-merge preference."""
        assert "Auto-Merge Preference" in self.skill_text

    def test_skill_auto_merge_default_is_yes(self):
        """Auto-merge should default to on (yes checked by default)."""
        assert "[x] yes" in self.skill_text

    def test_skill_passes_auto_merge_in_worker_prompt(self):
        """Coordinator must include Auto-merge in the worker agent prompt."""
        assert "Auto-merge: <$AUTO_MERGE>" in self.skill_text

    def test_agent_parses_auto_merge(self):
        """Worker agent must list Auto-merge in its PARSE YOUR TASK section."""
        assert "**Auto-merge**" in self.agent_text

    def test_agent_has_conditional_merge_for_true(self):
        """Worker agent must merge when Auto-merge is true."""
        assert "Auto-merge is `true`" in self.agent_text

    def test_agent_has_conditional_skip_for_false(self):
        """Worker agent must skip merge when Auto-merge is false."""
        assert "Auto-merge is `false`" in self.agent_text

    def test_agent_preserves_worktree_when_no_auto_merge(self):
        """Worker agent must preserve the worktree when auto-merge is off."""
        assert "Do NOT proceed to steps 8-10" in self.agent_text

    def test_agent_prints_manual_merge_command(self):
        """Worker agent must print the manual merge command for the user."""
        assert "gh pr merge <PR_NUMBER> --merge" in self.agent_text
