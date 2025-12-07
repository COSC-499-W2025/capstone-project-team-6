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
    cpp_oop = analysis.get("cpp_oop_analysis", {})
    c_oop = analysis.get("c_oop_analysis", {})
    complexity = analysis.get("complexity_analysis", {})

    # C++ OOP Analysis
    cpp_classes = cpp_oop.get("total_classes", 0)
    cpp_inheritance = cpp_oop.get("classes_with_inheritance", 0)
    cpp_abstract = len(cpp_oop.get("abstract_classes", []))
    cpp_virtual = cpp_oop.get("virtual_methods", 0)
    cpp_overloads = cpp_oop.get("operator_overloads", 0)
    cpp_templates = cpp_oop.get("template_classes", 0)
    cpp_namespaces = cpp_oop.get("namespaces_used", 0)

    # C OOP Analysis
    c_patterns = c_oop.get("design_patterns", [])

    # complexity Anlysis
    optimization_score = complexity.get("optimization_score", 0)

    # Core OOP quantities (python/java)
    py_classes = python_oop.get("total_classes", 0)
    java_classes = java_oop.get("total_classes", 0)
    py_inheritance = python_oop.get("classes_with_inheritance", 0)
    java_inheritance = java_oop.get("classes_with_inheritance", 0)
    py_abstract = len(python_oop.get("abstract_classes", []))
    java_abstract = len(java_oop.get("abstract_classes", []))

    # Advanced feature metrics
    java_patterns = java_oop.get("design_patterns", [])
    cpp_patterns = cpp_oop.get("design_patterns", [])
    design_patterns = list(set(java_patterns + cpp_patterns + c_patterns))
    java_lambdas = java_oop.get("lambda_count", 0)
    py_properties = python_oop.get("properties_count", 0)
    py_overloads = python_oop.get("operator_overloads", 0)
    py_overloads += cpp_overloads

    # Engineering practices
    has_tests = analysis.get("has_tests", False)
    has_readme = analysis.get("has_readme", False)
    has_ci_cd = analysis.get("has_ci_cd", False)
    has_docker = analysis.get("has_docker", False)

    test_coverage = analysis.get("test_coverage_estimate", "none")
    coverage_score = {"high": 3, "medium": 2, "low": 1, "none": 0}.get(test_coverage, 0)

    # --------------------------
    # Quality score calculation
    # ----------------------
    total_classes = py_classes + java_classes + cpp_classes
    total_abstract = py_abstract + java_abstract + cpp_abstract

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
    # C
    advanced_points += min(c_oop.get("vtable_structs", 0) * 2, 6)
    advanced_points += min(c_oop.get("function_pointer_fields", 0) * 1, 4)
    advanced_points += min(c_oop.get("opaque_pointer_structs", 0) * 2, 4)
    if c_oop.get("constructor_destructor_pairs", 0) > 0:
        advanced_points += 2
    # C++
    advanced_points += min(cpp_virtual * 1.5, 6)
    advanced_points += min(cpp_templates * 2, 6)
    advanced_points += min(cpp_namespaces * 1, 4)

    advanced_points += min(len(design_patterns) * 5, 10)
    advanced_points += min(total_abstract * 2, 5)
    if java_lambdas > 0:
        advanced_points += 3
    if py_overloads > 0:
        advanced_points += 2
    quality_score += min(advanced_points, 15)

    is_git = analysis.get("is_git_repo", False)
    total_commits = analysis.get("total_commits", 0)
    branch_count = analysis.get("branch_count", 0)
    commit_authors = analysis.get("commit_authors", [])

    git_points = 0
    if is_git:
        git_points += 1
    if total_commits >= 10:
        git_points += 1
    if branch_count >= 2:
        git_points += 1
    if isinstance(commit_authors, list) and len(commit_authors) >= 2:
        git_points += 1
    
    # Engineering points
    eng_points = (
        coverage_score * 2
        + (1 if has_tests else 0)
        + (1 if has_readme else 0)
        + (1 if has_ci_cd else 0)
        + (1 if has_docker else 0)
    )
    eng_points += min(git_points, 4)
    quality_score += min(eng_points, 10)

    # Algorithmic Complexity / Optimization scoring
    algo_points = 0
    if optimization_score >= 75:
        algo_points = 6
    elif optimization_score >= 50:
        algo_points = 4
    elif optimization_score >= 25:
        algo_points = 2
    elif optimization_score > 0:
        algo_points = 1

    quality_score += algo_points

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
        "uses_inheritance": (py_inheritance + java_inheritance + cpp_inheritance) > 0,
        "uses_abstraction": total_abstract > 0,
        "total_abstract": total_abstract,
        "design_patterns": design_patterns,
        "java_lambdas": java_lambdas,
        "py_properties": py_properties,
        "py_overloads": py_overloads,
        "optimization_score": optimization_score,
        "uses_optimization": optimization_score > 0,
    }


# ---------------------------------------------------------------
# 2. ARCHITECTURE DESCRIPTION
# ---------------------------------------------------------------


def _generate_architecture_description(analysis: dict, quality: dict) -> str:
    python_oop = analysis.get("oop_analysis", {})
    java_oop = analysis.get("java_oop_analysis", {})
    cpp_oop = analysis.get("cpp_oop_analysis", {})
    c_oop = analysis.get("c_oop_analysis", {})

    py_classes = python_oop.get("total_classes", 0)
    java_classes = java_oop.get("total_classes", 0)
    cpp_classes = cpp_oop.get("total_classes", 0)
    c_structs = c_oop.get("total_structs", 0)

    arch_parts = []
    if py_classes > 0:
        arch_parts.append(f"{py_classes} Python classes")
    if java_classes > 0:
        arch_parts.append(f"{java_classes} Java classes")
    if cpp_classes > 0:
        arch_parts.append(f"{cpp_classes} C++ classes")
    if c_structs > 0:
        arch_parts.append(f"{c_structs} C structs")

    if not arch_parts:
        return "The project follows a modular structure with organized code files."

    base = f"The project architecture includes {', '.join(arch_parts)}"

    py_depth = python_oop.get("inheritance_depth", 0)
    java_depth = java_oop.get("inheritance_depth", 0)
    cpp_depth = cpp_oop.get("inheritance_depth", 0)
    cpp_virtual = cpp_oop.get("virtual_methods", 0)
    cpp_templates = cpp_oop.get("template_classes", 0)
    cpp_namespaces = cpp_oop.get("namespaces_used", 0)
    cpp_overloads = cpp_oop.get("operator_overloads", 0)
    c_vtables = c_oop.get("vtable_structs", 0)
    c_fp_fields = c_oop.get("function_pointer_fields", 0)
    c_opaque = c_oop.get("opaque_pointer_structs", 0)
    c_memory_pairs = c_oop.get("constructor_destructor_pairs", 0)
    optimization_score = quality.get("optimization_score", 0)

    # Advanced tier
    if quality["sophistication_level"] == "advanced":
        details = []

        # C++ advanced features
        if cpp_templates > 0:
            details.append(f"{cpp_templates} template-based components")
        if cpp_virtual > 0:
            details.append(f"{cpp_virtual} virtual-method implementations")
        if cpp_namespaces > 0:
            details.append(f"{cpp_namespaces} namespaces")
        if cpp_overloads > 0:
            details.append(f"{cpp_overloads} operator overloads")
        if cpp_depth > 0:
            details.append(f"inheritance depth {cpp_depth} in C++ hierarchy")

        # C advanced features
        if c_opaque > 0:
            details.append(f"{c_opaque} opaque-pointer modules")
        if c_vtables > 0:
            details.append(f"{c_vtables} C vtable-style structs")
        if c_fp_fields > 0:
            details.append(f"{c_fp_fields} function-pointer fields")
        if c_memory_pairs > 0:
            details.append(f"{c_memory_pairs} constructor/destructor pairs")

        # Complexity / Optomization features
        if optimization_score >= 75:
            details.append("high-performance algorithmic optimizations")
        elif optimization_score >= 50:
            details.append("algorithmic improvements for efficiency")
        elif optimization_score >= 25:
            details.append("basic performance-oriented refactoring")
        elif optimization_score > 0:
            details.append("some optimization considerations")

        if quality["uses_abstraction"]:
            details.append(f"{quality['total_abstract']} abstract classes")
        if quality["uses_inheritance"]:
            depth = max(py_depth, java_depth, cpp_depth)
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
            tier_text = f"{base}, demonstrating advanced OOP with {', '.join(details)}."
        else:
            tier_text = f"{base}, demonstrating advanced object-oriented architecture."

    # Intermediate tier
    elif quality["sophistication_level"] == "intermediate":
        tags = []
        if quality["uses_inheritance"]:
            tags.append("inheritance")
        if quality["uses_abstraction"]:
            tags.append("abstraction")
        if quality["design_patterns"]:
            tags.append(f"{', '.join(quality['design_patterns'])} patterns")
        if cpp_templates > 0:
            tags.append("templates")
        if cpp_virtual > 0:
            tags.append("virtual methods")
        if cpp_namespaces > 0:
            tags.append("namespaces")
        if cpp_overloads > 0:
            tags.append("operator overloading")
        if c_opaque > 0:
            tags.append("opaque pointers")
        if c_vtables > 0:
            tags.append("vtable-style structs")
        if c_fp_fields > 0:
            tags.append("function-pointer polymorphism")
        if optimization_score >= 50:
            tags.append("algorithmic optimizations")
        elif optimization_score >= 25:
            tags.append("performance considerations")

        if tags:
            tier_text = f"{base}, demonstrating object-oriented principles including {', '.join(tags)}."
        else:
            tier_text = f"{base}, demonstrating solid object-oriented design."

    # Basic tier
    else: 
        tier_text = f"{base}, demonstrating foundational object-oriented design principles."

    # Git metadata 
    is_git = analysis.get("is_git_repo", False)
    total_commits = analysis.get("total_commits", 0)
    branch_count = analysis.get("branch_count", 0)
    authors = analysis.get("commit_authors", [])

    git_sentence = ""
    if is_git and (total_commits > 3 or branch_count > 1 or len(authors) > 1):
        git_sentence = (
            f" The project uses Git with {total_commits} commits "
            f"across {branch_count} branches by {len(authors)} contributor(s)."
        )

    return tier_text + git_sentence


# ---------------------------------------------------------------
# 3. CONTRIBUTIONS
# ---------------------------------------------------------------


def _generate_contributions_summary(analysis: dict, quality: dict) -> str:
    contrib = []

    python_oop = analysis.get("oop_analysis", {})
    java_oop = analysis.get("java_oop_analysis", {})
    cpp_oop = analysis.get("cpp_oop_analysis", {})
    c_oop = analysis.get("c_oop_analysis", {})
    # C++ contributions
    cpp_virtual = cpp_oop.get("virtual_methods", 0)
    cpp_templates = cpp_oop.get("template_classes", 0)
    cpp_namespaces = cpp_oop.get("namespaces_used", 0)
    cpp_overloads = cpp_oop.get("operator_overloads", 0)
    cpp_depth = cpp_oop.get("inheritance_depth", 0)
    cpp_abstract = len(cpp_oop.get("abstract_classes", []))
    # C contributions
    c_structs = c_oop.get("total_structs", 0)
    c_vtables = c_oop.get("vtable_structs", 0)
    c_fp_fields = c_oop.get("function_pointer_fields", 0)
    c_opaque = c_oop.get("opaque_pointer_structs", 0)
    c_memory_pairs = c_oop.get("constructor_destructor_pairs", 0)
    c_patterns = c_oop.get("design_patterns", [])
    # Git contributions
    is_git = analysis.get("is_git_repo", False)
    total_commits = analysis.get("total_commits", 0)
    branch_count = analysis.get("branch_count", 0)
    authors = analysis.get("commit_authors", [])
    # Algorithmic complexity / optimization
    optimization_score = quality.get("optimization_score", 0)

    # Python & Java contributions
    if quality["uses_abstraction"]:
        contrib.append("implementing abstract classes")

    if quality["design_patterns"]:
        patterns = quality["design_patterns"]
        name = ", ".join(patterns)
        plural = "pattern" if len(patterns) == 1 else "patterns"
        contrib.append(f"applying {name} {plural}")

    if quality["java_lambdas"] > 0:
        contrib.append(f"using {quality['java_lambdas']} lambda expressions")

    if quality["py_overloads"] > 0:
        contrib.append("implementing operator overloading")

    if cpp_virtual > 0:
        contrib.append(f"building {cpp_virtual} virtual-method hierarchies")

    if cpp_templates > 0:
        contrib.append(f"designing {cpp_templates} template-based components")

    if cpp_namespaces > 0:
        contrib.append(f"organizing code across {cpp_namespaces} namespaces")

    if cpp_overloads > 0:
        contrib.append(f"using {cpp_overloads} C++ operator overloads")

    if cpp_depth > 0:
        contrib.append(f"working with C++ inheritance depth {cpp_depth}")

    if cpp_abstract > 0:
        contrib.append(f"defining {cpp_abstract} abstract C++ classes")

    if c_structs > 0:
        contrib.append(f"designing {c_structs} C data structures")
    if c_opaque > 0:
        contrib.append(f"using {c_opaque} opaque-pointer modules for encapsulation")
    if c_vtables > 0:
        contrib.append(f"implementing {c_vtables} vtable-style polymorphic structs")
    if c_fp_fields > 0:
        contrib.append(f"building {c_fp_fields} function-pointer based components")
    if c_memory_pairs > 0:
        contrib.append(f"maintaining {c_memory_pairs} constructor/destructor memory-safety pairs")
    if c_patterns:
        name = ", ".join(c_patterns)
        plural = "pattern" if len(c_patterns) == 1 else "patterns"
        contrib.append(f"applying C-style {name} {plural}")
    
    # Algorithmic Optimization Contributions
    if optimization_score >= 75:
        contrib.append("implementing high-performance algorithmic optimizations")
    elif optimization_score >= 50:
        contrib.append("improving runtime efficiency through algorithmic refinements")
    elif optimization_score >= 25:
        contrib.append("refactoring code with performance considerations in mind")
    elif optimization_score > 0:
        contrib.append("introducing basic optimization techniques")

    # Engineering contributions
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

    if is_git and (total_commits > 3 or len(authors) > 1 or branch_count > 1):
        contrib.append(
            f"maintaining a Git-based workflow with {total_commits} commits "
            f"across {branch_count} branches by {len(authors)} contributor(s)"
        )

    if contrib:
        return f"Key contributions include {', '.join(contrib)}."

    return "Key contributions include implementing core logic and maintaining project structure."


# ---------------------------------------------------------------
# 4. SKILLS LIST
# ---------------------------------------------------------------


def _generate_skills_list(analysis: dict, quality: dict) -> list[str]:
    python_oop = analysis.get("oop_analysis", {})
    java_oop = analysis.get("java_oop_analysis", {})
    cpp_oop = analysis.get("cpp_oop_analysis", {})
    c_oop = analysis.get("c_oop_analysis", {})
    optimization_score = quality.get("optimization_score", 0)
    languages = analysis.get("languages", {})
    frameworks = analysis.get("frameworks", [])
    skills = []

    # Language OOP skills
    if "python" in languages and python_oop.get("total_classes", 0) > 0:
        skills.append("Python OOP")
    if "java" in languages and java_oop.get("total_classes", 0) > 0:
        skills.append("Java OOP")
    if "cpp" in languages and cpp_oop.get("total_classes", 0) > 0:
        skills.append("C++ OOP")
    if "c" in languages and c_oop.get("total_structs", 0) > 0:
        skills.append("C (OOP-style design)")

    # Frameworks
    for fw in frameworks[:2]:
        skills.append(f"{fw} framework")

    # Design Patterns (Java and C++)
    for pattern in quality["design_patterns"]:
        skills.append(f"{pattern} design pattern")

    # Python specifics
    if quality["py_overloads"] > 0:
        skills.append("Operator overloading (Python)")
    if quality["py_properties"] > 0:
        skills.append("Python properties")

    # Abstract classes
    if quality["uses_abstraction"]:
        skills.append("Abstract class design")

    # Java specifics
    if quality["java_lambdas"] > 0:
        skills.append("Functional programming (Java lambdas)")

    # C++ specifics
    cpp_virtual = cpp_oop.get("virtual_methods", 0)
    cpp_templates = cpp_oop.get("template_classes", 0)
    cpp_overloads = cpp_oop.get("operator_overloads", 0)
    cpp_namespaces = cpp_oop.get("namespaces_used", 0)
    cpp_abstract = len(cpp_oop.get("abstract_classes", []))

    if cpp_virtual > 0:
        skills.append("Virtual methods (C++)")
    if cpp_templates > 0:
        skills.append("Templates (C++)")
    if cpp_overloads > 0:
        skills.append("Operator overloading (C++)")
    if cpp_namespaces > 0:
        skills.append("Namespaces (C++)")
    if cpp_abstract > 0:
        skills.append("Abstract classes (C++)")

    # C specifics
    c_vtables = c_oop.get("vtable_structs", 0)
    c_fp_fields = c_oop.get("function_pointer_fields", 0)
    c_opaque = c_oop.get("opaque_pointer_structs", 0)
    c_memory_pairs = c_oop.get("constructor_destructor_pairs", 0)

    if c_opaque > 0:
        skills.append("Encapsulation using opaque pointers (C)")
    if c_vtables > 0:
        skills.append("VTable-style polymorphism (C)")
    if c_fp_fields > 0:
        skills.append("Function pointer–based modularity (C)")
    if c_memory_pairs > 0:
        skills.append("Manual memory management discipline (C)")

    # Algorithmic Optimization Skills
    if optimization_score >= 75:
        skills.append("Advanced algorithmic optimization")
        skills.append("Performance engineering")
    elif optimization_score >= 50:
        skills.append("Algorithmic optimization techniques")
    elif optimization_score >= 25:
        skills.append("Performance-aware development")
    elif optimization_score > 0:
        skills.append("Basic optimization practices")

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
    
    # Git specifics
    is_git = analysis.get("is_git_repo", False)
    branch_count = analysis.get("branch_count", 0)
    authors = analysis.get("commit_authors", [])

    if is_git:
        skills.append("Git workflow")
        if branch_count >= 2:
            skills.append("Branch-based version control")
        if isinstance(authors, list) and len(authors) > 1:
            skills.append("Collaborative development")
    
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
    optimization_score = quality.get("optimization_score", 0)

    # Summary build
    langs_str = ", ".join(tech_stack[:3]) if tech_stack else "multiple languages"

    if quality["sophistication_level"] == "advanced":
        opening = f"{project_name} is an advanced software project developed using {langs_str}."
    elif quality["sophistication_level"] == "intermediate":
        opening = f"{project_name} is a well-structured software project developed using {langs_str}."
    else:
        opening = f"{project_name} is a software project developed using {langs_str}."

    if optimization_score >= 50:
        opening += " It features algorithmic optimization to improve runtime performance."
    elif optimization_score >= 25:
        opening += " It incorporates performance-aware development practices."

    summary = [
        opening,
        f"It contains {file_stats['total_files']} total files, including "
        f"{file_stats['code_files']} source files and {file_stats['test_files']} test files.",
        architecture,
        contributions_summary,
    ]

    # Algorithmic optimization narrative
    if optimization_score >= 75:
        summary.append("The project demonstrates strong algorithmic optimization with a focus on high-performance execution.")
    elif optimization_score >= 50:
        summary.append("The codebase includes meaningful algorithmic refinements that improve computational efficiency.")
    elif optimization_score >= 25:
        summary.append("The implementation reflects basic performance-oriented improvements guided by algorithmic considerations.")
    elif optimization_score > 0:
        summary.append("Some sections of the project incorporate minor optimization techniques.")

    if analysis.get("has_tests") and analysis.get("test_coverage_estimate") != "none":
        summary.append(f"Test coverage is estimated as {analysis.get('test_coverage_estimate')}.")

    if skills:
        summary.append(f"This project demonstrates {', '.join(skills[:5])}, among other skills.")

    text_summary = " ".join(summary)

    # Append Git metadata to summary
    commits = analysis.get("total_commits", 0)
    branches = analysis.get("branch_count", 0)
    authors = analysis.get("commit_authors", [])
    if analysis.get("is_git_repo", False) and (commits > 0 or branches > 1 or len(authors) > 1):
        text_summary += (
            f" The repository includes {commits} commits across {branches} branches "
            f"from {len(authors)} contributor(s), demonstrating active version-controlled development."
        )

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
        "quality_metrics": quality,
    }
