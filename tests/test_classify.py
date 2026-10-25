from catalog import classify as C


def r(name, desc="", readme="", topics=()):
    return {"name": name, "description": desc, "readme": readme, "topics": list(topics)}


def test_industry_from_name_first():
    assert C.industries(r("x-insurance-claims-agents", "fraud signals"))[0] == "insurance"


def test_industry_fallback_cross():
    assert C.industries(r("x-context-engineering", "token budgets")) == ["cross"]


def test_hr_detected():
    assert "hr" in C.industries(r("x-recruiting-fairness-agents"))


def test_skills_ranked():
    s = C.skills(r("x-agentic-rag", "retrieval with rerank", "rag rag retrieval"))
    assert s[0] == "retrieval"


def test_framework_rules():
    assert C.framework(r("x-langchain-langgraph-langsmith")) == "LangGraph"
    assert C.framework(r("x-agentic-playwright")) == "Playwright"
    assert C.framework(r("x-a", readme="agent framework ... agent framework")) == "Agent Framework"
    assert C.framework(r("x-azure-finops")) == "Azure"
    assert C.framework(r("x-plain")) == "Python"


def test_test_count_readme_then_profile():
    assert C.test_count(r("a", readme="**1,234 automated tests** pass"), {}) == 1234
    assert C.test_count(r("a", readme="none"), {"a": 7}) == 7
    assert C.test_count(r("a"), {}) is None


def test_profile_counts():
    md = "| [**Repo-a**](u) | x | 29 |\n| [**Repo-b**](u) | y | Python |\n"
    assert C.profile_test_counts(md) == {"Repo-a": 29}


def test_levels():
    assert C.level(300, "") == "Advanced"
    assert C.level(150, "a multi-agent build") == "Advanced"
    assert C.level(150, "") == "Intermediate"
    assert C.level(79, "") == "Beginner"
    assert C.level(None, "") == "Beginner"


def test_featured_counts_skip_inner_parentheses():
    md = "featured repositories (10 agent labs + 283 agentic-playwright (148 a + 135 b), counted) and more"
    got = C.featured_test_counts(md, ["J-azure-agent-labs", "J-agentic-playwright", "J-agentic-playwright-extra"])
    assert got == {"J-azure-agent-labs": 10, "J-agentic-playwright": 283}


def test_profile_counts_cell_with_breakdown():
    assert C.profile_test_counts("| [**R**](u) | x | 708 (687 a + 21 b) |") == {"R": 708}
