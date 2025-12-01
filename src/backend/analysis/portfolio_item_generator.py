"""
portfolio_item_generator.py

Generates a detailed portfolio item from a single project's
analysis dictionary. Adapts output quality and detail based on
actual project sophistication detected in the analysis.
"""

# ---------------------------------------------------------------
# 1. QUALITY SCORE (NO artificial OOP score, only real metrics)
# ---------------------------------------------------------------

def _calculate_project_quality_score(analysis: dict) -> dict:
    """
    Calculate overall project sophistication based on real metrics:
    - total classes
    - inheritance
    - abstraction
    - design patterns
    - lambdas
    - operator overloads
    - engineering practices (tests, readme, docker, cicd)
    """

    python_oop = analysis.get("oop_analysis", {})
    java_oop = analysis.get("java_oop_analysis", {})

    # Core OOP quantities
    py_classes = python_oop.get("total_classes", 0)
    java_classes = java_oop.get("total_classes", 0)
    total_classes = py_classes + java_classes

    py_inheritance = python_oop.get("classes_with_inheritance", 0)
    java_inheritance = java_oop.get("classes_with_inheritance", 0)

    py_abstract = len(python_oop.get("abstract_classes", []))
    java_abstract = len(java_oop.get("abstract_classes", []))
    total_abstract = py_abstract + java_abstract

    # Advanced feature metrics
    java_patterns = java_oop.get("design_patterns", [])
    java_lambdas = java_oop.get("lambda_count", 0)
    py_properties = python_oop.get("properties_count", 0)
    py_overloads = python_oop.get("operator_overloads", 0)

    # Engineering practices
    has_tests = analysis.get("has_tests", False)
    has_readme = analysis.get("has_readme", False)
    has_ci_cd = analysis.get("has_ci_cd", False)
    has_docker = analysis.get("has_docker", False)

    test_coverage = analysis.get("test_coverage_estimate", "none")
    coverage_score = {"high": 3, "medium": 2, "low": 1, "none": 0}.get(test_coverage, 0)

    # --------------------------
    # Quality score calculation
    # --------------------------

    quality_score = 0

    # Class count
    if total_classes > 10:
        quality_score += 25
    elif total_classes > 5:
        quality_score += 18
    elif total_classes > 2:
        quality_score += 10
    elif total_classes > 0:
        quality_score += 5

    # Advanced OOP 
    advanced_points = 0
    advanced_points += min(len(java_patterns) * 5, 10)
    advanced_points += min(total_abstract * 2, 5)
    if java_lambdas > 0:
        advanced_points += 3
    if py_overloads > 0:
        advanced_points += 2
    quality_score += min(advanced_points, 15)

    # Engineering points
    eng_points = (
        coverage_score * 2
        + (1 if has_tests else 0)
        + (1 if has_readme else 0)
        + (1 if has_ci_cd else 0)
        + (1 if has_docker else 0)
    )
    quality_score += min(eng_points, 10)

    # --------------------------
    # Sophistication tier
    # --------------------------
    if quality_score >= 50:
        sophistication = "advanced"
    elif quality_score >= 30:
        sophistication = "intermediate"
    else:
        sophistication = "basic"

    return {
        "quality_score": quality_score,
        "sophistication_level": sophistication,
        "total_classes": total_classes,
        "uses_inheritance": (py_inheritance + java_inheritance) > 0,
        "uses_abstraction": total_abstract > 0,
        "total_abstract": total_abstract,
        "design_patterns": java_patterns,
        "java_lambdas": java_lambdas,
        "py_properties": py_properties,
        "py_overloads": py_overloads,
    }


# ---------------------------------------------------------------
# 2. ARCHITECTURE DESCRIPTION
# ---------------------------------------------------------------

def _generate_architecture_description(analysis: dict, quality: dict) -> str:
    python_oop = analysis.get("oop_analysis", {})
    java_oop = analysis.get("java_oop_analysis", {})

    py_classes = python_oop.get("total_classes", 0)
    java_classes = java_oop.get("total_classes", 0)

    arch_parts = []
    if py_classes > 0:
        arch_parts.append(f"{py_classes} Python classes")
    if java_classes > 0:
        arch_parts.append(f"{java_classes} Java classes")

    if not arch_parts:
        return "The project follows a modular structure with organized code files."

    base = f"The project architecture includes {' and '.join(arch_parts)}"

    py_depth = python_oop.get("inheritance_depth", 0)
    java_depth = java_oop.get("inheritance_depth", 0)

    # Advanced tier
    if quality["sophistication_level"] == "advanced":
        details = []

        if quality["uses_abstraction"]:
            details.append(f"{quality['total_abstract']} abstract classes")
        if quality["uses_inheritance"]:
            depth = max(py_depth, java_depth)
            if depth > 0:
                details.append(f"inheritance up to depth {depth}")
        if quality["design_patterns"]:
            patterns = quality["design_patterns"]
            if patterns:
                name = ", ".join(patterns)
                plural = "design pattern" if len(patterns) == 1 else "design patterns"
                details.append(f"{name} {plural}")

        if quality["py_properties"] > 0:
            details.append(f"{quality['py_properties']} properties")

        if details:
            return f"{base}, demonstrating advanced OOP with {', '.join(details)}."

        return f"{base}, demonstrating advanced object-oriented architecture."

    # Intermediate tier
    if quality["sophistication_level"] == "intermediate":
        tags = []
        if quality["uses_inheritance"]:
            tags.append("inheritance")
        if quality["uses_abstraction"]:
            tags.append("abstraction")
        if quality["design_patterns"]:
            tags.append(f"{', '.join(quality['design_patterns'])} patterns")

        if tags:
            return f"{base}, demonstrating object-oriented principles including {', '.join(tags)}."

        return f"{base}, demonstrating solid object-oriented design."

    # Basic tier
    return f"{base}, demonstrating foundational object-oriented design principles."


# ---------------------------------------------------------------
# 3. CONTRIBUTIONS
# ---------------------------------------------------------------

def _generate_contributions_summary(analysis: dict, quality: dict) -> str:
    contrib = []

    if quality["uses_abstraction"]:
        contrib.append("implementing abstract classes")
    if quality["design_patterns"]:
        patterns = quality["design_patterns"]
        if patterns:
            name = ", ".join(patterns)
            plural = "pattern" if len(patterns) == 1 else "patterns"
            contrib.append(f"applying {name} {plural}")
    if quality["java_lambdas"] > 0:
        contrib.append(f"using {quality['java_lambdas']} lambda expressions")
    if quality["py_overloads"] > 0:
        contrib.append("implementing operator overloading")

    # Engineering
    if analysis.get("has_tests"):
        test_files = analysis.get("test_files", 0)
        cov = analysis.get("test_coverage_estimate", "unknown")
        contrib.append(f"creating {test_files} tests ({cov} coverage)")

    if analysis.get("has_ci_cd"):
        contrib.append("configuring CI/CD pipelines")
    if analysis.get("has_docker"):
        contrib.append("adding Docker containerization")
    if analysis.get("has_readme"):
        contrib.append("writing documentation")

    if contrib:
        return f"Key contributions include {', '.join(contrib)}."

    return "Key contributions include implementing core logic and maintaining project structure."


# ---------------------------------------------------------------
# 4. SKILLS LIST
# ---------------------------------------------------------------

def _generate_skills_list(analysis: dict, quality: dict) -> list[str]:
    python_oop = analysis.get("oop_analysis", {})
    java_oop = analysis.get("java_oop_analysis", {})
    languages = analysis.get("languages", {})
    frameworks = analysis.get("frameworks", [])

    skills = []

    # OOP skills only if classes exist
    if "python" in languages and python_oop.get("total_classes", 0) > 0:
        skills.append("Python OOP")
    if "java" in languages and java_oop.get("total_classes", 0) > 0:
        skills.append("Java OOP")

    # Framework skills
    for fw in frameworks[:2]:
        skills.append(f"{fw} framework")

    # Advanced OOP
    for pattern in quality["design_patterns"]:
        skills.append(f"{pattern} design pattern")
    if quality["java_lambdas"] > 0:
        skills.append("Functional programming")
    if quality["py_overloads"] > 0:
        skills.append("Operator overloading")
    if quality["uses_abstraction"]:
        skills.append("Abstract design")

    # Engineering skills
    if analysis.get("test_coverage_estimate") in ["high", "medium"]:
        skills.append("Test-driven development")
    elif analysis.get("has_tests"):
        skills.append("Unit testing")

    if analysis.get("has_ci_cd"):
        skills.append("CI/CD pipelines")
    if analysis.get("has_docker"):
        skills.append("Docker")
    if analysis.get("has_readme"):
        skills.append("Technical documentation")

    return skills


# ---------------------------------------------------------------
# 5. MAIN PORTFOLIO ITEM BUILDER
# ---------------------------------------------------------------

def generate_portfolio_item(analysis: dict) -> dict:
    quality = _calculate_project_quality_score(analysis)

    project_name = analysis.get("project_name", "Unnamed Project")
    languages = analysis.get("languages", {})
    frameworks = analysis.get("frameworks", [])

    file_stats = {
        "total_files": analysis.get("total_files", 0),
        "code_files": analysis.get("code_files", 0),
        "test_files": analysis.get("test_files", 0),
        "documentation_files": analysis.get("doc_files", 0),
    }

    tech_stack = []
    if isinstance(languages, dict):
        for lang, _ in sorted(languages.items(), key=lambda x: x[1], reverse=True):
            tech_stack.append(lang)
    elif isinstance(languages, list):
        tech_stack.extend(languages)

    tech_stack.extend(frameworks)

    architecture = _generate_architecture_description(analysis, quality)
    contributions_summary = _generate_contributions_summary(analysis, quality)
    skills = _generate_skills_list(analysis, quality)

    # Summary build
    langs_str = ", ".join(tech_stack[:3]) if tech_stack else "multiple languages"

    if quality["sophistication_level"] == "advanced":
        opening = f"{project_name} is an advanced software project developed using {langs_str}."
    elif quality["sophistication_level"] == "intermediate":
        opening = f"{project_name} is a well-structured software project developed using {langs_str}."
    else:
        opening = f"{project_name} is a software project developed using {langs_str}."

    summary = [
        opening,
        f"It contains {file_stats['total_files']} total files, including "
        f"{file_stats['code_files']} source files and {file_stats['test_files']} test files.",
        architecture,
        contributions_summary
    ]

    if analysis.get("has_tests") and analysis.get("test_coverage_estimate") != "none":
        summary.append(f"Test coverage is estimated as {analysis.get('test_coverage_estimate')}.")

    if skills:
        summary.append(f"This project demonstrates {', '.join(skills[:5])}, among other skills.")

    text_summary = " ".join(summary)
    overview = text_summary[:300] + ("..." if len(text_summary) > 300 else "")

    return {
        "project_name": project_name,
        "overview": overview,
        "tech_stack": tech_stack,
        "architecture": architecture,
        "contributions_summary": contributions_summary,
        "project_statistics": {
            **file_stats,
            "sophistication_level": quality["sophistication_level"],
            "quality_score": quality["quality_score"],
        },
        "skills_exercised": skills,
        "text_summary": text_summary,
        "quality_metrics": quality
    }
