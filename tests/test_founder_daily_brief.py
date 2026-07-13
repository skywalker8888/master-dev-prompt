from app import build_founder_daily_brief


def test_build_founder_daily_brief_includes_expected_sections() -> None:
    result = {
        "design_doc": {
            "requirements_constraints": "Ship Founder Daily Brief v0.1.",
            "open_questions_risks": "Founder approval needed for release date.\nSecurity review pending.",
            "decisions": "Choose launch sequence for Dear Saigon and Command Center.",
        },
        "actions": {
            "items": [
                {"description": "Approve launch scope", "priority": "high", "owner": "Founder"},
                {"description": "Implement brief UI", "priority": "high", "owner": "Agent"},
                {"description": "Add metrics wiring", "priority": "medium", "owner": "Agent"},
            ]
        },
        "implementation_plan": {
            "milestones": [
                {"name": "Daily Brief UI", "risks": "Blocked by final founder wording"},
            ]
        },
        "agent_task_report": {
            "master_checklist": [
                {"task_title": "Wire summary cards", "checked": True},
                {"task_title": "Connect API", "checked": False},
            ],
            "task_slides": [
                {"task_title": "Implement endpoint", "status": "running"},
                {"task_title": "Review copy", "status": "needs review"},
            ],
        },
    }

    brief = build_founder_daily_brief(result)

    assert "date" in brief
    assert brief["decisions_requiring_approval"]
    assert brief["founder_approvals_required"] == brief["decisions_requiring_approval"]
    assert brief["current_blockers"]
    assert brief["completed_since_last_brief"] == ["Wire summary cards"]
    assert brief["work_completed_since_previous_brief"] == ["Wire summary cards"]
    assert brief["agent_status"]["Running"] == 1
    assert brief["agent_status"]["Needs Review"] == 1
    assert brief["agent_status_requiring_attention"] == ["Review copy (Unassigned) needs review"]
    assert len(brief["today_top_3"]) >= 2
    assert brief["today_top_three_priorities"] == brief["today_top_3"]
    assert "next_founder_action" in brief


def test_build_founder_daily_brief_handles_minimal_result() -> None:
    brief = build_founder_daily_brief({})

    assert brief["today_focus"] == "Execution priorities and decision velocity."
    assert isinstance(brief["project_health"], list)
    assert isinstance(brief["alerts"], dict)
    assert "next_founder_action" in brief
    assert brief["founder_approvals_required"] == []
    assert brief["work_completed_since_previous_brief"] == []
    assert brief["agent_status_requiring_attention"] == []
    assert brief["today_top_three_priorities"] == []
