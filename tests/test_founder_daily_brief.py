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
    assert brief["project_health"] == [{"project": "Daily Brief UI", "status": "🔴"}]
    assert "next_founder_action" in brief


def test_build_founder_daily_brief_does_not_invent_hardcoded_projects() -> None:
    result = {
        "implementation_plan": {"milestones": [{"name": "Warehouse Sync", "risks": "Vendor API timeout"}]},
        "actions": {"items": [{"description": "Fix retries", "priority": "high", "owner": "Agent"}]},
    }

    brief = build_founder_daily_brief(result)
    project_names = [item["project"] for item in brief["project_health"]]

    assert project_names == ["Warehouse Sync"]
    assert "Dear Saigon" not in project_names
    assert "CoachAI" not in project_names
    assert "ZOS Command Center" not in project_names
    assert "Marketing" not in project_names


def test_build_founder_daily_brief_represents_multiple_projects() -> None:
    result = {
        "project_metadata": {"projects": [{"name": "Atlas"}, {"name": "Beacon"}]},
        "actions": {
            "items": [
                {"description": "Finalize Atlas launch plan", "priority": "high", "project": "Atlas"},
                {"description": "Refine Beacon docs", "priority": "medium", "project": "Beacon"},
            ]
        },
        "implementation_plan": {
            "milestones": [
                {"name": "Atlas milestone", "project": "Atlas", "risks": "Pending security sign-off"},
                {"name": "Beacon milestone", "project": "Beacon", "risks": ""},
            ]
        },
        "agent_task_report": {
            "task_slides": [
                {"task_title": "Beacon QA", "status": "waiting", "project": "Beacon"},
            ]
        },
    }

    brief = build_founder_daily_brief(result)
    health_by_project = {item["project"]: item["status"] for item in brief["project_health"]}

    assert set(health_by_project) == {"Atlas", "Beacon"}
    assert health_by_project["Atlas"] == "🔴"
    assert health_by_project["Beacon"] == "🟡"


def test_build_founder_daily_brief_handles_minimal_result() -> None:
    brief = build_founder_daily_brief({})

    assert brief["today_focus"] == "Execution priorities and decision velocity."
    assert brief["project_health"] == []
    assert isinstance(brief["alerts"], dict)
    assert "next_founder_action" in brief
    assert brief["founder_approvals_required"] == []
    assert brief["work_completed_since_previous_brief"] == []
    assert brief["agent_status_requiring_attention"] == []
    assert brief["today_top_three_priorities"] == []
