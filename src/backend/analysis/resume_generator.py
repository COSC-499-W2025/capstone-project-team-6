from typing import Any, Dict, List, Optional, Set


def generate_resume_items(report: Dict[str, Any]) -> List[str]:
    """
    Generate resume bullet points from project analysis report.
    """
    resume_items = []

    for project in report.get("projects", []):
        items = _generate_project_items(project)
        resume_items.extend(items)

    return resume_items


def _detect_project_type(project: Dict[str, Any]) -> str:
    frameworks = project.get("frameworks", [])
    dependencies = project.get("dependencies", {})
    all_deps = []
    for deps_list in dependencies.values():
        all_deps.extend([d.lower() for d in deps_list])

    web_frameworks = {"flask", "django", "fastapi", "express", "react", "vue", "angular", "next.js", "spring", "rails"}
    if any(fw.lower() in web_frameworks for fw in frameworks):
        if any("api" in dep or "rest" in dep or "graphql" in dep for dep in all_deps):
            return "api"
        return "web_app"

    if "click" in all_deps or "argparse" in all_deps or "typer" in all_deps:
        return "cli_tool"
   
    ml_deps = {"numpy", "pandas", "scikit-learn", "tensorflow", "pytorch", "keras", "matplotlib", "seaborn"}
    if any(dep in ml_deps for dep in all_deps):
        return "data_science"
   
    db_deps = {"sqlalchemy", "django-orm", "sequelize", "typeorm", "prisma", "mongodb", "redis"}
    if any(dep in db_deps for dep in all_deps):
        return "backend"
    
    if project.get("test_files", 0) > project.get("code_files", 0) * 0.5:
        return "test_suite"
    
    if project.get("code_files", 0) > 0 and project.get("test_files", 0) > 0:
        return "library"
    
    return "application"



def _generate_project_items(project: Dict[str, Any]) -> List[str]:
    items = []
    project_name = project.get("project_name", "Project")
    project_type = _detect_project_type(project)
    
    opening_item = _generate_opening_item(project, project_name, project_type)
    if opening_item:
        items.append(opening_item)
    
    arch_items = _generate_architecture_items(project, project_name, project_type)
    items.extend(arch_items)
    
    optimization_items = _generate_optimization_items(project, project_name)
    items.extend(optimization_items)
    
    tech_items = _generate_tech_items(project, project_name, project_type)
    items.extend(tech_items)
    
    quality_items = _generate_quality_items(project, project_name)
    items.extend(quality_items)
    
    scale_items = _generate_scale_items(project, project_name)
    items.extend(scale_items)
    
    unique_items = _generate_unique_items(project, project_name, project_type)
    items.extend(unique_items)
    
    return items


def _generate_opening_item(project: Dict[str, Any], project_name: str, project_type: str) -> Optional[str]:
    primary_lang = project.get("primary_language", "")
    code_files = project.get("code_files", 0)
    frameworks = project.get("frameworks", [])
    
    project_type_names = {
        "web_app": "web application",
        "api": "RESTful API",
        "cli_tool": "command-line interface tool",
        "data_science": "data analysis/ML project",
        "backend": "backend service",
        "library": "reusable library/package",
        "test_suite": "comprehensive test suite",
        "application": "software application"
    }
    
    type_name = project_type_names.get(project_type, "application")
    
    framework_context = ""
    if frameworks:
        fw_str = ", ".join(frameworks[:2])
        framework_context = f" using {fw_str}"
    
    if code_files > 50:
        return f"Architected and developed {project_name}, a {type_name} in {primary_lang}{framework_context}, comprising {code_files} source files with scalable, maintainable design."
    elif code_files > 20:
        return f"Built {project_name}, a {type_name} in {primary_lang}{framework_context}, implementing {code_files} source files with clean architecture."
    else:
        return f"Developed {project_name}, a {type_name} in {primary_lang}{framework_context}, delivering focused functionality through modular design."


def _generate_architecture_items(project: Dict[str, Any], project_name: str, project_type: str) -> List[str]:
    """Generate architecture and design pattern items."""
    items = []
    
    # oop
    if "oop_analysis" in project and "error" not in project.get("oop_analysis", {}):
        oop = project["oop_analysis"]
        total_classes = oop.get("total_classes", 0)
        
        if total_classes > 0:
            features = []
            if oop.get("inheritance_depth", 0) >= 3:
                features.append(f"multi-level inheritance hierarchies ({oop['inheritance_depth']} levels)")
            elif oop.get("inheritance_depth", 0) > 0:
                features.append("inheritance-based design")

            abstract_count = len(oop.get("abstract_classes", []))
            if abstract_count > 0:
                if abstract_count >= 3:
                    features.append(f"{abstract_count} abstract base classes")
                else:
                    features.append("abstract base classes")
            private = oop.get("private_methods", 0)
            protected = oop.get("protected_methods", 0)
            if private + protected > 10:
                features.append(f"strong encapsulation ({private + protected} private/protected methods)")
            elif private + protected > 0:
                features.append("encapsulation patterns")
            if oop.get("properties_count", 0) > 5:
                features.append(f"{oop['properties_count']} property decorators")
            if oop.get("operator_overloads", 0) > 0:
                features.append("operator overloading")
            
            if features:
                features_str = ", ".join(features[:3])
                items.append(f"Designed {project_name} with {total_classes} classes implementing {features_str}, demonstrating advanced OOP principles and maintainable code structure.")
            else:
                items.append(f"Structured {project_name} using object-oriented design with {total_classes} classes and modular architecture for scalability.")
    if "java_oop_analysis" in project and "error" not in project.get("java_oop_analysis", {}):
        java = project["java_oop_analysis"]
        total_types = java.get("total_classes", 0) + java.get("interface_count", 0)
        
        if total_types > 0:
            features = []
            
            patterns = java.get("design_patterns", [])
            if patterns:
                patterns_str = ", ".join(patterns[:3])
                features.append(f"{patterns_str} design patterns")
            
            if java.get("interface_count", 0) >= 5:
                features.append(f"{java['interface_count']} interfaces for contract-based design")
            elif java.get("interface_count", 0) > 0:
                features.append("interface-based architecture")

            if java.get("generic_classes", 0) > 0:
                features.append(f"generic programming ({java['generic_classes']} generic classes)")

            if java.get("lambda_count", 0) > 10:
                features.append(f"functional programming ({java['lambda_count']} lambda expressions)")
            if java.get("private_fields", 0) > java.get("public_fields", 0) * 2:
                features.append("SOLID principles")
            
            if features:
                features_str = ", ".join(features[:3])
                items.append(f"Engineered {project_name} with {total_types} Java types ({java.get('total_classes', 0)} classes, {java.get('interface_count', 0)} interfaces) implementing {features_str} for robust enterprise architecture.")
            else:
                items.append(f"Developed {project_name} using Java OOP with {total_types} types and enterprise-grade architecture following industry best practices.")
    
    depth = project.get("directory_depth", 0)
    if depth >= 5:
        items.append(f"Organized {project_name} with a {depth}-level hierarchical structure, enabling scalability and maintainability through clear module boundaries.")
    elif depth >= 3:
        items.append(f"Structured {project_name} with modular {depth}-level architecture for clear separation of concerns and improved code organization.")
    
    return items


def _generate_optimization_items(project: Dict[str, Any], project_name: str) -> List[str]:
    """Generate items based on complexity and optimization analysis."""
    items = []
    
    # Complexity analysis
    if "complexity_analysis" in project and "error" not in project.get("complexity_analysis", {}):
        complexity = project["complexity_analysis"]
        score = complexity.get("optimization_score", 0)
        insights_count = complexity.get("insights_count", 0)
        summary = complexity.get("summary", {})
        
        if score >= 75 and insights_count > 0:
            # High optimization awareness
            good_practices = []
            
            if summary.get("efficient_data_structure", 0) > 5:
                good_practices.append("efficient data structures (sets/dicts)")
            if summary.get("list_comprehension", 0) > 10:
                good_practices.append("list comprehensions")
            if summary.get("generator_expression", 0) > 0:
                good_practices.append("generator expressions for memory efficiency")
            if summary.get("memoization", 0) > 0:
                good_practices.append("memoization/caching")
            if summary.get("binary_search", 0) > 0:
                good_practices.append("binary search algorithms")
            
            if good_practices:
                practices_str = ", ".join(good_practices[:3])
                items.append(f"Optimized {project_name} for performance using {practices_str}, achieving {score:.0f}/100 optimization score and improved runtime efficiency.")
            else:
                items.append(f"Implemented performance-optimized algorithms in {project_name}, demonstrating strong algorithmic awareness ({score:.0f}/100 score) and efficient resource utilization.")
        
        elif score >= 50:
            # Moderate optimization
            items.append(f"Applied algorithmic optimization techniques in {project_name}, balancing performance and readability ({score:.0f}/100 score) for maintainable code.")
    
    return items


def _generate_tech_items(project: Dict[str, Any], project_name: str, project_type: str) -> List[str]:
    items = []
    
    languages = list(project.get("languages", {}).keys())
    frameworks = project.get("frameworks", [])
    dependencies = project.get("dependencies", {})
    
    # Multi-language projects
    if len(languages) >= 3:
        lang_str = ", ".join(languages[:3])
        items.append(f"Implemented {project_name} as a polyglot system using {lang_str}, leveraging each language's strengths for optimal performance across different components.")
    elif len(languages) == 2:
        lang_str = " and ".join(languages)
        items.append(f"Developed {project_name} using {lang_str}, integrating multiple technologies to create a cohesive solution.")
    
    # Framework-specific items
    if frameworks:
        fw_str = ", ".join(frameworks[:2])
        if project_type == "web_app":
            items.append(f"Built the frontend/backend using {fw_str}, implementing responsive UI and RESTful services for seamless user experience.")
        elif project_type == "api":
            items.append(f"Designed the API using {fw_str}, following REST principles and industry best practices for reliable service integration.")
    
    # Dependency analysis
    all_deps = []
    for deps_list in dependencies.values():
        all_deps.extend(deps_list)
    
    if len(all_deps) > 20:
        items.append(f"Integrated {len(all_deps)}+ dependencies managing complex dependency relationships and ensuring compatibility across versions.")
    elif len(all_deps) > 10:
        items.append(f"Leveraged {len(all_deps)} external libraries extending functionality efficiently while maintaining code quality.")
    
    # Database integration
    db_keywords = {"sqlalchemy", "django-orm", "sequelize", "typeorm", "prisma", "mongodb", "redis", "postgresql", "mysql"}
    db_deps = [d for d in all_deps if any(kw in d.lower() for kw in db_keywords)]
    if db_deps:
        items.append(f"Integrated database layer in {project_name} using {db_deps[0]}, implementing data persistence and query optimization for efficient data management.")
    
    return items


def _generate_quality_items(project: Dict[str, Any], project_name: str) -> List[str]:
    items = []
    
    test_files = project.get("test_files", 0)
    code_files = project.get("code_files", 0)
    has_tests = project.get("has_tests", False)
    test_coverage = project.get("test_coverage_estimate", "")
    has_ci_cd = project.get("has_ci_cd", False)
    
    # Test coverage metrics
    if test_files > 0 and code_files > 0:
        test_ratio = test_files / code_files
        if test_ratio >= 0.5:
            items.append(f"Established comprehensive test coverage with {test_files} test files ({test_ratio:.0%} test-to-code ratio), ensuring reliability and reducing production bugs.")
        elif test_ratio >= 0.3:
            items.append(f"Implemented {test_files} automated tests, achieving {test_coverage} coverage and reducing regression risk through systematic validation.")
        elif test_files >= 5:
            items.append(f"Developed {test_files} test suites, validating core functionality and edge cases to ensure system stability.")
    
    # CI/CD
    if has_ci_cd:
        if has_tests:
            items.append(f"Configured CI/CD pipeline through which automated testing is enabled, enabling continuous integration and deployment with quality gates.")
        else:
            items.append(f"Set up CI/CD infrastructure, automating build and deployment processes for efficient release cycles.")
    
    # Code quality tools
    dependencies = project.get("dependencies", {})
    all_deps = []
    for deps_list in dependencies.values():
        all_deps.extend([d.lower() for d in deps_list])
    
    quality_tools = []
    if any("pytest" in d or "unittest" in d for d in all_deps):
        quality_tools.append("pytest")
    if any("black" in d or "autopep8" in d for d in all_deps):
        quality_tools.append("code formatting")
    if any("flake8" in d or "pylint" in d or "mypy" in d for d in all_deps):
        quality_tools.append("static analysis")
    
    if quality_tools:
        tools_str = ", ".join(quality_tools)
        items.append(f"Enforced code quality standards using {tools_str}, maintaining consistent codebase quality and adherence to best practices.")
    
    return items


def _generate_scale_items(project: Dict[str, Any], project_name: str) -> List[str]:
    """Generate scale and collaboration items."""
    items = []
    
    total_files = project.get("total_files", 0)
    code_files = project.get("code_files", 0)
    total_commits = project.get("total_commits", 0)
    contributors = project.get("contributors", [])
    contributors_count = len(contributors) if contributors else 0
    has_docker = project.get("has_docker", False)
    
    if total_files > 100:
        items.append(f"Managed large-scale {project_name} with {total_files} files and {code_files} source files, demonstrating ability to handle complex codebases and maintain system architecture.")
    elif total_files > 50:
        items.append(f"Developed {project_name} comprising {total_files} files, maintaining organization and structure throughout the development lifecycle.")
    

    
    # Collaboration to be integrated after gitanalysis is done 
    if contributors_count >= 5:
        items.append(f"Led collaborative development of with {contributors_count} team members, coordinating through version control and code reviews to ensure code quality.")
    elif contributors_count > 1:
        items.append(f"Collaborated on with {contributors_count} contributors, using Git workflows and collaborative practices for effective team coordination.")
    
    # Deployment
    if has_docker:
        if project.get("has_ci_cd", False):
            items.append(f"Containerized and deployed using Docker with CI/CD, enabling reproducible deployments across environments and streamlined release processes.")
        else:
            items.append(f"Containerized using Docker, ensuring consistent runtime environments and simplified deployment across different platforms.")
    
    return items


def _generate_unique_items(project: Dict[str, Any], project_name: str, project_type: str) -> List[str]:
    """Generate items highlighting unique project characteristics."""
    items = []
    
    languages = project.get("languages", {})
    if len(languages) >= 3:
        items.append(f"Architected the project as a multi-language system, integrating diverse technology stacks for optimal performance across different components and use cases.")
    
    doc_files = project.get("doc_files", 0)
    if doc_files >= 5:
        items.append(f"Documented the project extensively with {doc_files} documentation files, ensuring maintainability and knowledge transfer for future developers.")
    
    config_files = project.get("config_files", 0)
    if config_files >= 5:
        items.append(f"Configured with {config_files} configuration files, supporting flexible deployment and environment management for various operational contexts.")
    
    if project_type == "cli_tool":
        items.append(f"Designed {project_name} as a user-friendly CLI tool, providing intuitive command-line interface and comprehensive help documentation for efficient task automation.")
    elif project_type == "data_science":
        items.append(f"Implemented {project_name} for data analysis and machine learning, processing datasets and generating insights through statistical modeling and visualization.")
    elif project_type == "library":
        items.append(f"Developed {project_name} as a reusable library, providing clean APIs and comprehensive functionality for other projects to integrate and extend.")
    
    return items


def format_resume_items(items: List[str]) -> str:
    """
    Format resume items for display.
    """
    if not items:
        return "No resume items generated."

    formatted = "\n"
    for i, item in enumerate(items, 1):
        formatted += f"  • {item}\n"

    return formatted


def generate_formatted_resume_entry(project: Dict[str, Any]) -> str:
    """Generate a formatted resume entry for a single project."""
    project_name = project.get("project_name", "Project")
    timeline = project.get("timeline", "")

    bullets = _generate_project_items(project)
    languages = list(project.get("languages", {}).keys())
    frameworks = project.get("frameworks", [])
    deps = project.get("dependencies", {})
    
    # Collect all dependencies
    all_deps = []
    for deps_list in deps.values():
        all_deps.extend(deps_list)
    
    # Build tech stack
    tech_stack = languages + frameworks
    notable_deps = [d for d in all_deps if any(kw in d.lower() for kw in ["fastapi", "django", "flask", "react", "vue", "express", "spring"])]
    tech_stack.extend(notable_deps[:3])
    
    if project.get("has_docker"):
        tech_stack.append("Docker")
    
    tech_stack = [t for t in tech_stack if t]
    tech_line = ""
    if tech_stack:
        tech_line = "Technologies: " + ", ".join(sorted(set(tech_stack))[:10])  # Limit to top 10

    # Bullet formatting
    bullet_str = ""
    for b in bullets:
        bullet_str += f"  • {b}\n"

    # Final formatted block
    block = f"""
{project_name}
{tech_line}
{bullet_str}
""".rstrip()

    return block


def generate_full_resume(report: Dict[str, Any]) -> str:
    """Generate a complete formatted resume from the analysis report."""
    entries = []
    for project in report.get("projects", []):
        entry = generate_formatted_resume_entry(project)
        entries.append(entry)

    return "\n\n".join(entries)


def print_resume_items(report: Dict[str, Any]) -> None:
    """
    Generate and print resume items from analysis report.

    Args:
        report: Complete analysis report
    """
    items = generate_resume_items(report)

    print("\n" + "=" * 70)
    print("  GENERATED RESUME ITEMS")
    print("=" * 70)

    if items:
        print(format_resume_items(items))
        print(f"Total items generated: {len(items)}")
    else:
        print("\nNo resume items could be generated from this analysis.")

    print("=" * 70 + "\n")
