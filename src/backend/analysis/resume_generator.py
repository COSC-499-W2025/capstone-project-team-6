import json
import os
import re
import subprocess
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Union

# --- LaTeX Template ---
LATEX_HEADER = r"""
\documentclass[letterpaper,11pt]{article}
\usepackage{latexsym}
\usepackage[empty]{fullpage}
\usepackage{titlesec}
\usepackage{marvosym}
\usepackage[usenames,dvipsnames]{color}
\usepackage{verbatim}
\usepackage{enumitem}
\usepackage[hidelinks]{hyperref}
\usepackage{fancyhdr}
\usepackage[english]{babel}
\usepackage{tabularx}
\input{glyphtounicode}

\pagestyle{fancy}
\fancyhf{} 
\fancyfoot{}
\renewcommand{\headrulewidth}{0pt}
\renewcommand{\footrulewidth}{0pt}

\addtolength{\oddsidemargin}{-0.5in}
\addtolength{\evensidemargin}{-0.5in}
\addtolength{\textwidth}{1in}
\addtolength{\topmargin}{-.5in}
\addtolength{\textheight}{1.0in}

\urlstyle{same}
\raggedbottom
\raggedright
\setlength{\tabcolsep}{0in}

\titleformat{\section}{
  \vspace{-4pt}\scshape\raggedright\large
}{}{0em}{}[\color{black}\titlerule \vspace{-5pt}]

\pdfgentounicode=1

\newcommand{\resumeItem}[1]{
  \item\small{{#1 \vspace{-2pt}}}
}

\newcommand{\resumeSubheading}[4]{
  \vspace{-2pt}\item
    \begin{tabular*}{0.97\textwidth}[t]{l@{\extracolsep{\fill}}r}
      \textbf{#1} & #2 \\
      \textit{\small#3} & \textit{\small #4} \\
    \end{tabular*}\vspace{-7pt}
}

\newcommand{\resumeProjectHeading}[2]{
    \item
    \begin{tabular*}{0.97\textwidth}{l@{\extracolsep{\fill}}r}
      \small#1 & #2 \\
    \end{tabular*}\vspace{-7pt}
}

\newcommand{\resumeSubHeadingListStart}{\begin{itemize}[leftmargin=0.15in, label={}]}
\newcommand{\resumeSubHeadingListEnd}{\end{itemize}}
\newcommand{\resumeItemListStart}{\begin{itemize}}
\newcommand{\resumeItemListEnd}{\end{itemize}\vspace{-5pt}}

\begin{document}
"""


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

    web_frameworks = {
        "flask",
        "django",
        "fastapi",
        "express",
        "react",
        "vue",
        "angular",
        "next.js",
        "spring",
        "rails",
    }
    if any(fw.lower() in web_frameworks for fw in frameworks):
        if any("api" in dep or "rest" in dep or "graphql" in dep for dep in all_deps):
            return "api"
        return "web_app"

    if "click" in all_deps or "argparse" in all_deps or "typer" in all_deps:
        return "cli_tool"

    ml_deps = {
        "numpy",
        "pandas",
        "scikit-learn",
        "tensorflow",
        "pytorch",
        "keras",
        "matplotlib",
        "seaborn",
    }
    if any(dep in ml_deps for dep in all_deps):
        return "data_science"

    db_deps = {
        "sqlalchemy",
        "django-orm",
        "sequelize",
        "typeorm",
        "prisma",
        "mongodb",
        "redis",
    }
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
        "application": "software application",
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
                items.append(
                    f"Designed {project_name} with {total_classes} classes implementing {features_str}, demonstrating advanced OOP principles and maintainable code structure."
                )
            else:
                items.append(
                    f"Structured {project_name} using object-oriented design with {total_classes} classes and modular architecture for scalability."
                )
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
                items.append(
                    f"Engineered {project_name} with {total_types} Java types ({java.get('total_classes', 0)} classes, {java.get('interface_count', 0)} interfaces) implementing {features_str} for robust enterprise architecture."
                )
            else:
                items.append(
                    f"Developed {project_name} using Java OOP with {total_types} types and enterprise-grade architecture following industry best practices."
                )

    depth = project.get("directory_depth", 0)
    if depth >= 5:
        items.append(
            f"Organized {project_name} with a {depth}-level hierarchical structure, enabling scalability and maintainability through clear module boundaries."
        )
    elif depth >= 3:
        items.append(
            f"Structured {project_name} with modular {depth}-level architecture for clear separation of concerns and improved code organization."
        )

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
                items.append(
                    f"Optimized {project_name} for performance using {practices_str}, achieving {score:.0f}/100 optimization score and improved runtime efficiency."
                )
            else:
                items.append(
                    f"Implemented performance-optimized algorithms in {project_name}, demonstrating strong algorithmic awareness ({score:.0f}/100 score) and efficient resource utilization."
                )

        elif score >= 50:
            # Moderate optimization
            items.append(
                f"Applied algorithmic optimization techniques in {project_name}, balancing performance and readability ({score:.0f}/100 score) for maintainable code."
            )

    return items


def _generate_tech_items(project: Dict[str, Any], project_name: str, project_type: str) -> List[str]:
    items = []

    languages = list(project.get("languages", {}).keys())
    frameworks = project.get("frameworks", [])
    dependencies = project.get("dependencies", {})

    # Multi-language projects
    if len(languages) >= 3:
        lang_str = ", ".join(languages[:3])
        items.append(
            f"Implemented {project_name} as a polyglot system using {lang_str}, leveraging each language's strengths for optimal performance across different components."
        )
    elif len(languages) == 2:
        lang_str = " and ".join(languages)
        items.append(
            f"Developed {project_name} using {lang_str}, integrating multiple technologies to create a cohesive solution."
        )

    # Framework-specific items
    if frameworks:
        fw_str = ", ".join(frameworks[:2])
        if project_type == "web_app":
            items.append(
                f"Built the frontend/backend using {fw_str}, implementing responsive UI and RESTful services for seamless user experience."
            )
        elif project_type == "api":
            items.append(
                f"Designed the API using {fw_str}, following REST principles and industry best practices for reliable service integration."
            )

    # Dependency analysis
    all_deps = []
    for deps_list in dependencies.values():
        all_deps.extend(deps_list)

    if len(all_deps) > 20:
        items.append(
            f"Integrated {len(all_deps)}+ dependencies managing complex dependency relationships and ensuring compatibility across versions."
        )
    elif len(all_deps) > 10:
        items.append(
            f"Leveraged {len(all_deps)} external libraries extending functionality efficiently while maintaining code quality."
        )

    # Database integration
    db_keywords = {
        "sqlalchemy",
        "django-orm",
        "sequelize",
        "typeorm",
        "prisma",
        "mongodb",
        "redis",
        "postgresql",
        "mysql",
    }
    db_deps = [d for d in all_deps if any(kw in d.lower() for kw in db_keywords)]
    if db_deps:
        items.append(
            f"Integrated database layer in {project_name} using {db_deps[0]}, implementing data persistence and query optimization for efficient data management."
        )

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
            items.append(
                f"Established comprehensive test coverage with {test_files} test files ({test_ratio:.0%} test-to-code ratio), ensuring reliability and reducing production bugs."
            )
        elif test_ratio >= 0.3:
            items.append(
                f"Implemented {test_files} automated tests, achieving {test_coverage} coverage and reducing regression risk through systematic validation."
            )
        elif test_files >= 5:
            items.append(
                f"Developed {test_files} test suites, validating core functionality and edge cases to ensure system stability."
            )

    # CI/CD
    if has_ci_cd:
        if has_tests:
            items.append(
                f"Configured CI/CD pipeline through which automated testing is enabled, enabling continuous integration and deployment with quality gates."
            )
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
        items.append(
            f"Enforced code quality standards using {tools_str}, maintaining consistent codebase quality and adherence to best practices."
        )

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
        items.append(
            f"Managed large-scale {project_name} with {total_files} files and {code_files} source files, demonstrating ability to handle complex codebases and maintain system architecture."
        )
    elif total_files > 50:
        items.append(
            f"Developed {project_name} comprising {total_files} files, maintaining organization and structure throughout the development lifecycle."
        )

    # Collaboration to be integrated after gitanalysis is done
    if contributors_count >= 5:
        items.append(
            f"Led collaborative development of with {contributors_count} team members, coordinating through version control and code reviews to ensure code quality."
        )
    elif contributors_count > 1:
        items.append(
            f"Collaborated on with {contributors_count} contributors, using Git workflows and collaborative practices for effective team coordination."
        )

    # Deployment
    if has_docker:
        if project.get("has_ci_cd", False):
            items.append(
                f"Containerized and deployed using Docker with CI/CD, enabling reproducible deployments across environments and streamlined release processes."
            )
        else:
            items.append(
                f"Containerized using Docker, ensuring consistent runtime environments and simplified deployment across different platforms."
            )

    return items


def _generate_unique_items(project: Dict[str, Any], project_name: str, project_type: str) -> List[str]:
    """Generate items highlighting unique project characteristics."""
    items = []

    languages = project.get("languages", {})
    if len(languages) >= 3:
        items.append(
            f"Architected the project as a multi-language system, integrating diverse technology stacks for optimal performance across different components and use cases."
        )

    doc_files = project.get("doc_files", 0)
    if doc_files >= 5:
        items.append(
            f"Documented the project extensively with {doc_files} documentation files, ensuring maintainability and knowledge transfer for future developers."
        )

    config_files = project.get("config_files", 0)
    if config_files >= 5:
        items.append(
            f"Configured with {config_files} configuration files, supporting flexible deployment and environment management for various operational contexts."
        )

    if project_type == "cli_tool":
        items.append(
            f"Designed {project_name} as a user-friendly CLI tool, providing intuitive command-line interface and comprehensive help documentation for efficient task automation."
        )
    elif project_type == "data_science":
        items.append(
            f"Implemented {project_name} for data analysis and machine learning, processing datasets and generating insights through statistical modeling and visualization."
        )
    elif project_type == "library":
        items.append(
            f"Developed {project_name} as a reusable library, providing clean APIs and comprehensive functionality for other projects to integrate and extend."
        )

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
    notable_deps = [
        d
        for d in all_deps
        if any(
            kw in d.lower()
            for kw in [
                "fastapi",
                "django",
                "flask",
                "react",
                "vue",
                "express",
                "spring",
                "postgres",
                "postgresql",
                "mysql",
                "mongodb",
                "redis",
                "docker",
            ]
        )
    ]
    tech_stack.extend(notable_deps[:4])

    if project.get("has_docker") and "docker" not in [t.lower() for t in tech_stack]:
        tech_stack.append("Docker")

    # Format tech stack
    tech_stack = sorted(set([t for t in tech_stack if t]))[:8]
    tech_str = ", ".join(tech_stack)

    header_line = f"**{project_name}** | *{tech_str}*"

    # Bullet points (limit to 4 like Jake's resume for conciseness)
    bullet_lines = []
    for b in bullets[:4]:
        bullet_lines.append(f"  - {b}")

    # Combine into final entry
    entry = f"\n{header_line}\n" + "\n".join(bullet_lines) + "\n"

    return entry


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


def generate_latex_resume(
    portfolios: List[Dict[str, Any]],
    personal_info: Optional[Dict[str, str]] = None,
    include_skills: bool = True,
    include_projects: bool = True,
    max_projects: Optional[int] = None,
) -> str:
    """Generates a full LaTeX document based on Resume template."""

    # Collect all projects and skills
    all_projects = []
    all_skills = set()

    for portfolio in portfolios:
        projects = portfolio.get("projects", [])
        all_projects.extend(projects)

        # Collect skills from portfolio level
        portfolio_skills = portfolio.get("skills", [])
        if isinstance(portfolio_skills, list):
            all_skills.update(portfolio_skills)
        elif isinstance(portfolio_skills, dict):
            for skill_list in portfolio_skills.values():
                if isinstance(skill_list, list):
                    all_skills.update(skill_list)

        # Collect skills from projects
        for project in projects:
            skills_data = project.get("skills", {})
            if isinstance(skills_data, dict):
                for skill_list in skills_data.values():
                    if isinstance(skill_list, list):
                        all_skills.update(skill_list)
            elif isinstance(skills_data, list):
                all_skills.update(skills_data)

    if max_projects and len(all_projects) > max_projects:
        all_projects = all_projects[:max_projects]

    # 1. Personal Header
    info = personal_info or {}
    name = info.get("name", "Your Name").upper()
    phone = info.get("phone", "123-456-7890")
    email = info.get("email", "email@address.com")
    location = info.get("location", "")
    linkedin = info.get("linkedIn", "linkedin.com/in/username")
    github = info.get("github", "github.com/username")
    website = info.get("website", "")

    # Clean URLs for display
    linkedin_display = linkedin.replace("https://", "").replace("http://", "")
    github_display = github.replace("https://", "").replace("http://", "")
    website_display = website.replace("https://", "").replace("http://", "") if website else ""

    def _safe(s: str) -> str:
        # Normalize common unicode punctuation into ASCII so pdflatex can compile reliably.
        s = (s or "").replace("•", "-")
        s = s.replace("–", "-").replace("—", "-").replace("−", "-")
        s = s.replace("’", "'").replace("‘", "'")
        s = s.replace("“", '"').replace("”", '"')
        s = s.replace("…", "...")
        s = s.replace("\n", " ").replace("\r", " ")

        # Ensure ASCII compatibility for this pdflatex toolchain.
        s = s.encode("ascii", errors="replace").decode("ascii")

        # Escape LaTeX special characters used in our template.
        return (
            s.replace("\\", "\\textbackslash ")
            .replace("&", "\\&")
            .replace("%", "\\%")
            .replace("_", "\\_")
            .replace("#", "\\#")
            .replace("$", "\\$")
            .replace("{", "\\{")
            .replace("}", "\\}")
            .replace("~", "\\textasciitilde ")
            .replace("^", "\\textasciicircum ")
        )

    def _format_month_year(value: Any) -> str:
        """
        Convert stored month values (from <input type="month"> => "YYYY-MM")
        into a readable "Mon YYYY" string.
        """
        if value is None:
            return ""
        s = str(value).strip()
        m = re.match(r"^(\d{4})-(\d{2})$", s)
        if not m:
            return s
        year = int(m.group(1))
        month = int(m.group(2))
        if month < 1 or month > 12:
            return s
        month_names = [
            "Jan",
            "Feb",
            "Mar",
            "Apr",
            "May",
            "Jun",
            "Jul",
            "Aug",
            "Sep",
            "Oct",
            "Nov",
            "Dec",
        ]
        return f"{month_names[month - 1]} {year}"

    safe_phone = _safe(phone)
    safe_email = _safe(email)
    safe_location = _safe(location)
    safe_linkedin = _safe(linkedin)
    safe_github = _safe(github)
    safe_website = _safe(website)
    safe_linkedin_display = _safe(linkedin_display)
    safe_github_display = _safe(github_display)
    safe_website_display = _safe(website_display)

    contact_parts = [safe_phone]
    contact_parts.append(rf"\href{{mailto:{safe_email}}}{{\underline{{{safe_email}}}}}")
    if location:
        contact_parts.append(safe_location)
    contact_parts.append(rf"\href{{{safe_linkedin}}}{{\underline{{{safe_linkedin_display}}}}}")
    contact_parts.append(rf"\href{{{safe_github}}}{{\underline{{{safe_github_display}}}}}")
    if website:
        contact_parts.append(rf"\href{{{safe_website}}}{{\underline{{{safe_website_display}}}}}")

    contact_line = " $|$ ".join(contact_parts)

    latex = LATEX_HEADER
    latex += rf"""
\begin{{center}}
    \textbf{{\Huge \scshape {name}}} \\ \vspace{{1pt}}
    \small {contact_line}
\end{{center}}
"""

    # 2. Education Section (Jake's format: subheading + date + awards list)
    education_entries = info.get("education_entries")
    if isinstance(education_entries, list) and len(education_entries) > 0:
        education_blocks: List[str] = []
        for entry in education_entries:
            if not isinstance(entry, dict):
                continue

            university = (entry.get("education_university") or entry.get("university") or "").strip()
            location = (entry.get("education_location") or entry.get("location") or "").strip()
            degree = (entry.get("education_degree") or entry.get("degree") or "").strip()
            start_date = (
                entry.get("education_start_date") or entry.get("start_date") or ""
            ).strip()
            end_date = (entry.get("education_end_date") or entry.get("end_date") or entry.get("grad_date") or "").strip()
            start_date_fmt = _format_month_year(start_date)
            end_date_fmt = _format_month_year(end_date)
            if start_date_fmt and end_date_fmt:
                date_range = f"{start_date_fmt} -- {end_date_fmt}"
            elif start_date_fmt and not end_date_fmt:
                date_range = f"{start_date_fmt} -- Present"
            else:
                date_range = end_date_fmt or start_date_fmt or " "
            awards = (entry.get("education_awards") or entry.get("awards") or "").strip()
            education_text = (entry.get("education_text") or entry.get("education") or "").strip()
            # Keep education text on one line for LaTeX safety.
            education_text_single_line = education_text.replace(chr(10), ' ').replace(chr(13), ' ')

            if university or degree:
                block = "  \\resumeSubheading{"
                block += _safe(university or " ") + "}{" + _safe(location) + "}{"
                block += _safe(degree) + "}{\\textnormal{" + _safe(date_range) + "}}\n"
                if awards:
                    block += "  \\resumeItemListStart\n"
                    block += "    \\resumeItem{\\textbf{Awards}: " + _safe(awards) + "}\n"
                    block += "  \\resumeItemListEnd\n"
                education_blocks.append(block)
            elif education_text:
                education_blocks.append(f"  \\item \\small{{{_safe(education_text_single_line)}}}\n")
            elif date_range.strip():
                # Keep list non-empty even when user only saved date fields.
                education_blocks.append(f"  \\item \\small{{{_safe(date_range)}}}\n")

        if education_blocks:
            latex += r"\section{Education}" + "\n\\resumeSubHeadingListStart\n"
            for block in education_blocks:
                latex += block
            latex += "\\resumeSubHeadingListEnd\n\n"

    else:
        university = (info.get("education_university") or info.get("university") or "").strip()
        location = (info.get("education_location") or info.get("location") or "").strip()
        degree = (info.get("education_degree") or info.get("degree") or "").strip()
        start_date = (info.get("education_start_date") or "").strip()
        end_date = (info.get("education_end_date") or info.get("grad_date") or "").strip()
        start_date_fmt = _format_month_year(start_date)
        end_date_fmt = _format_month_year(end_date)
        if start_date_fmt and end_date_fmt:
            date_range = f"{start_date_fmt} -- {end_date_fmt}"
        elif start_date_fmt and not end_date_fmt:
            date_range = f"{start_date_fmt} -- Present"
        else:
            date_range = end_date_fmt or start_date_fmt or " "
        awards = (info.get("education_awards") or "").strip()

        if university or degree or (info.get("education") or "").strip():
            latex += r"\section{Education}" + "\n\\resumeSubHeadingListStart\n"
            if university or degree:
                latex += "  \\resumeSubheading{"
                latex += _safe(university or " ") + "}{" + _safe(location) + "}{"
                latex += _safe(degree) + "}{\\textnormal{" + _safe(date_range) + "}}\n"
                if awards:
                    latex += "  \\resumeItemListStart\n"
                    latex += "    \\resumeItem{\\textbf{Awards}: " + _safe(awards) + "}\n"
                    latex += "  \\resumeItemListEnd\n"
            else:
                education_text = (info.get("education") or "").strip().replace("\n", " ")
                latex += f"  \\item \\small{{{_safe(education_text)}}}\n"
            latex += "\\resumeSubHeadingListEnd\n\n"

    # 3. Work Experience Section
    # Supports multiple entries via `work_experience_entries`.
    def _parse_responsibility_bullets(raw_text: Any) -> List[str]:
        """Normalize responsibility text into clean bullet items."""
        if raw_text is None:
            return []
        text = str(raw_text).replace("\r", "\n")
        bullets: List[str] = []
        for line in text.split("\n"):
            # Allow users to type with '-' bullets or plain lines.
            cleaned = line.strip().lstrip("-*•").strip()
            if cleaned:
                bullets.append(cleaned)
        return bullets

    work_entries = info.get("work_experience_entries")
    if isinstance(work_entries, list) and len(work_entries) > 0:
        latex += r"\section{Work Experience}" + "\n\\resumeSubHeadingListStart\n"
        for entry in work_entries:
            if not isinstance(entry, dict):
                continue

            job_title = (entry.get("job_title") or entry.get("work_job_title") or "").strip()
            company = (entry.get("company") or entry.get("work_company") or "").strip()
            location = (entry.get("location") or entry.get("work_location") or "").strip()
            start_date = (entry.get("start_date") or entry.get("work_start_date") or "").strip()
            end_date = (entry.get("end_date") or entry.get("work_end_date") or entry.get("work_grad_date") or "").strip()
            start_date_fmt = _format_month_year(start_date)
            end_date_fmt = _format_month_year(end_date)
            if start_date_fmt and end_date_fmt:
                date_range = f"{start_date_fmt} -- {end_date_fmt}"
            elif start_date_fmt and not end_date_fmt:
                date_range = f"{start_date_fmt} -- Present"
            else:
                date_range = end_date_fmt or start_date_fmt or " "

            responsibilities_text = (
                entry.get("responsibilities_text")
                or entry.get("work_responsibilities_text")
                or entry.get("responsibilities")
                or ""
            )
            responsibilities = _parse_responsibility_bullets(responsibilities_text)

            latex += "  \\resumeSubheading{"
            latex += _safe(job_title or " ") + "}{" + _safe(company or " ") + "}{" + _safe(location or " ") + "}{" + _safe(date_range) + "}\n"

            if responsibilities:
                latex += "  \\resumeItemListStart\n"
                for bullet in responsibilities[:4]:
                    latex += f"    \\resumeItem{{{_safe(bullet)}}}\n"
                latex += "  \\resumeItemListEnd\n"

        latex += "\\resumeSubHeadingListEnd\n\n"

    # 3. Projects Section
    if include_projects and all_projects:
        latex += r"\section{Projects}" + "\n\\resumeSubHeadingListStart\n"
        for project in all_projects:
            project_name = project.get("project_name", "Project")
            timeline = ""  # Timestamp not shown on resume projects

            # Extract Tech Stack
            langs = list(project.get("languages", {}).keys())
            fws = project.get("frameworks", [])
            deps = project.get("dependencies", {})

            # Collect notable dependencies
            all_deps = []
            for deps_list in deps.values():
                all_deps.extend(deps_list)

            notable_deps = [
                d
                for d in all_deps
                if any(
                    kw in d.lower()
                    for kw in [
                        "fastapi",
                        "django",
                        "flask",
                        "react",
                        "vue",
                        "express",
                        "spring",
                        "postgres",
                        "mysql",
                        "mongodb",
                        "redis",
                        "docker",
                    ]
                )
            ]

            tech_stack = (langs + fws + notable_deps[:3])[:6]  # Limit to 6 items
            tech_str = ", ".join(tech_stack)

            safe_name = _safe(project_name)
            safe_tech = _safe(tech_str)

            latex += f"    \\resumeProjectHeading{{\\textbf{{{safe_name}}} $|$ \\emph{{{safe_tech}}}}}{{{timeline}}}\n"
            latex += "      \\resumeItemListStart\n"
            # Use stored resume bullets if provided (from DB), else generate from project dict
            resume_bullets = project.get("resume_bullets")
            if resume_bullets and isinstance(resume_bullets, list):
                bullets = [b for b in resume_bullets if isinstance(b, str) and b.strip()]
            else:
                bullets = _generate_project_items(project)
            for bullet in bullets[:4]:
                safe_bullet = _safe(bullet)
                latex += f"        \\resumeItem{{{safe_bullet}}}\n"

            latex += "      \\resumeItemListEnd\n"
        latex += "\\resumeSubHeadingListEnd\n\n"

    # 4. Technical Skills
    if include_skills and all_skills:
        skills_list = sorted(list(all_skills))

        # Categorize skills
        lang_keywords = {"python", "java", "javascript", "typescript", "c++", "c#", "c", "sql", "html", "css", "r"}
        framework_keywords = {"react", "vue", "angular", "django", "flask", "fastapi", "spring", "express", "node.js", "nextjs"}
        tool_keywords = {
            "git",
            "docker",
            "kubernetes",
            "aws",
            "azure",
            "jenkins",
            "postgres",
            "mysql",
            "mongodb",
            "redis",
            "vscode",
            "intellij",
        }

        langs = [s for s in skills_list if any(kw in s.lower() for kw in lang_keywords)]
        fws = [s for s in skills_list if any(kw in s.lower() for kw in framework_keywords) and s not in langs]
        tools = [s for s in skills_list if s not in langs and s not in fws]

        latex += r"\section{Technical Skills}" + "\n\\begin{itemize}[leftmargin=0.15in, label={}]\n  \\small{\\item{\n"
        if langs:
            safe_langs = _safe(", ".join(langs))
            latex += f"    \\textbf{{Languages}}{{: {safe_langs}}} \\\\\n"
        if fws:
            safe_fws = _safe(", ".join(fws))
            latex += f"    \\textbf{{Frameworks}}{{: {safe_fws}}} \\\\\n"
        if tools:
            safe_tools = _safe(", ".join(tools[:10]))
            latex += f"    \\textbf{{Developer Tools}}{{: {safe_tools}}}\n"
        latex += "  }}\n\\end{itemize}\n\n"

    latex += r"\end{document}"
    return latex


def _compile_latex_to_pdf(latex_content: str) -> bytes:
    """Compile LaTeX content to PDF using pdflatex with intelligent path detection."""
    import shutil
    import subprocess
    import tempfile
    from pathlib import Path

    # 1. Define possible paths for pdflatex
    # Prioritize the specific macOS path we verified
    potential_paths = [
        "/Library/TeX/texbin/pdflatex",
        "/usr/local/texlive/2025basic/bin/universal-darwin/pdflatex",
        "/usr/bin/pdflatex",
    ]

    pdflatex_cmd = None
    for path in potential_paths:
        if Path(path).exists():
            pdflatex_cmd = path
            break

    # Fallback to system PATH (useful for Linux/Windows teammates)
    if not pdflatex_cmd:
        pdflatex_cmd = shutil.which("pdflatex")

    if not pdflatex_cmd:
        raise FileNotFoundError(
            "pdflatex is required to generate the resume as PDF (Jake's format). "
            "Install BasicTeX or MacTeX (e.g. brew install --cask basictex), then run: "
            "export PATH='/Library/TeX/texbin:$PATH'"
        )

    # 2. Run compilation in a temporary directory
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        tex_file = tmpdir_path / "resume.tex"
        tex_file.write_text(latex_content, encoding="utf-8")

        try:
            # Run twice to resolve references and layout
            for _ in range(2):
                result = subprocess.run(
                    [pdflatex_cmd, "-interaction=nonstopmode", "-output-directory", str(tmpdir_path), str(tex_file)],
                    capture_output=True,
                    text=True,
                    timeout=30,
                )

                if result.returncode != 0:
                    raise RuntimeError(f"LaTeX compilation failed: {result.stdout}")

            pdf_file = tmpdir_path / "resume.pdf"
            if pdf_file.exists():
                return pdf_file.read_bytes()
            raise FileNotFoundError("PDF file was not generated.")

        except subprocess.TimeoutExpired:
            raise RuntimeError("LaTeX compilation timed out.")


def _bundles_to_portfolios(
    bundles: List[Dict[str, Any]],
    skills_set: Set[str],
    include_skills: bool,
) -> List[Dict[str, Any]]:
    """Convert API project bundles to the portfolio shape expected by generate_latex_resume."""
    all_projects: List[Dict[str, Any]] = []
    all_skills: Set[str] = set(skills_set) if skills_set else set()
    for bundle in bundles:
        proj_row = bundle.get("project") or {}
        port = bundle.get("portfolio") or {}
        items = bundle.get("resume_items") or []
        name = proj_row.get("project_name") or proj_row.get("name") or "Project"
        timeline = proj_row.get("last_modified_date") or "Present"
        primary = proj_row.get("primary_language") or ""
        languages = {primary: 1} if primary else {}
        tech_stack = port.get("tech_stack")
        if isinstance(tech_stack, str):
            try:
                tech_stack = json.loads(tech_stack) if tech_stack else []
            except Exception:
                tech_stack = []
        frameworks = [t for t in (tech_stack if isinstance(tech_stack, list) else []) if isinstance(t, str)][:10]
        for s in port.get("skills") or port.get("skills_exercised") or []:
            if isinstance(s, str) and s.strip():
                all_skills.add(s.strip())
        resume_bullets = []
        for r in items:
            text = r.get("resume_text") or r.get("content") or r.get("bullet_text") or ""
            if isinstance(text, str) and text.strip():
                resume_bullets.append(text.strip())
        all_projects.append(
            {
                "project_name": name,
                "timeline": timeline,
                "languages": languages,
                "frameworks": frameworks,
                "dependencies": {},
                "resume_bullets": resume_bullets,
            }
        )
    return [{"projects": all_projects, "skills": list(all_skills)}]


def generate_resume(
    projects: List[Dict[str, Any]],
    format: str = "markdown",
    include_skills: bool = True,
    include_projects: bool = True,
    max_projects: Optional[int] = None,
    personal_info: Optional[Dict[str, str]] = None,
    highlighted_skills: Optional[List[str]] = None,
) -> Union[str, bytes]:
    """
    Generate a resume from database project bundles.

    Args:
        projects: List of project bundles, each containing:
            - "project": DB row with project metadata
            - "resume_items": List of resume bullet rows from DB
            - "portfolio": Portfolio summary with skills
        format: Output format ("markdown", "latex", "pdf")
        include_skills: Include skills section
        include_projects: Include projects section
        max_projects: Maximum number of projects to include
        personal_info: Personal contact information
        highlighted_skills: Curated highlighted skills from curation settings.
            If provided, these are used instead of auto-extracted skills.

    Returns:
        Formatted resume as string (markdown/latex) or bytes (pdf)
    """

    # Apply project limit
    selected = projects
    if max_projects is not None:
        selected = selected[:max_projects]

    # Build Skills section from curated skills or portfolio data
    skills_set = set()
    if include_skills:
        # Prefer curated highlighted skills if provided
        if highlighted_skills and len(highlighted_skills) > 0:
            skills_set = set(highlighted_skills)
        else:
            for bundle in selected:
                portfolio = bundle.get("portfolio") or {}
                skills = portfolio.get("skills") or portfolio.get("skill_summary") or {}

                if isinstance(skills, list):
                    for s in skills:
                        if isinstance(s, str) and s.strip():
                            skills_set.add(s.strip())

                elif isinstance(skills, dict):
                    for _, vals in skills.items():
                        if isinstance(vals, list):
                            for s in vals:
                                if isinstance(s, str) and s.strip():
                                    skills_set.add(s.strip())

    def _format_month_year(value: Any) -> str:
        """
        Convert stored month values (from <input type="month"> => "YYYY-MM")
        into a readable "Mon YYYY" string.
        """
        if value is None:
            return ""
        s = str(value).strip()
        m = re.match(r"^(\d{4})-(\d{2})$", s)
        if not m:
            return s
        year = int(m.group(1))
        month = int(m.group(2))
        if month < 1 or month > 12:
            return s
        month_names = [
            "Jan",
            "Feb",
            "Mar",
            "Apr",
            "May",
            "Jun",
            "Jul",
            "Aug",
            "Sep",
            "Oct",
            "Nov",
            "Dec",
        ]
        return f"{month_names[month - 1]} {year}"

    def _extract_bullet_text(row: Dict[str, Any]) -> Optional[str]:
        """Extract resume bullet text from a resume_items database row."""
        for key in ("resume_text", "content", "bullet", "text", "description"):
            val = row.get(key)
            if isinstance(val, str) and val.strip():
                return val.strip()
        return None

    def _format_bundle(bundle: Dict[str, Any]) -> str:
        """Format a project bundle into markdown with bullets."""
        project = bundle.get("project") or {}
        name = project.get("project_name") or project.get("name") or "Project"
        tech = project.get("primary_language") or project.get("language") or ""
        if not tech:
            langs = project.get("languages")
            if isinstance(langs, dict):
                tech = ", ".join([k for k in langs.keys() if k])

        # Build header
        header = f"**{name}**"
        if tech:
            header += f" | *{tech}*"

        # Extract resume bullets from DB
        resume_rows = bundle.get("resume_items") or []
        bullets: List[str] = []
        for r in resume_rows:
            if isinstance(r, dict):
                t = _extract_bullet_text(r)
                if t:
                    bullets.append(t)

        # Fallback bullet if none exist
        if not bullets:
            if tech:
                bullets = [f"Developed {name}, a software project using {tech}."]
            else:
                bullets = [f"Developed {name}, a software project."]

        bullets = bullets[:6]

        # Format as markdown
        lines = [header]
        for b in bullets:
            lines.append(f"  - {b}")
        return "\n".join(lines)

    # Build resume sections
    md_parts: List[str] = []

    # Personal information header
    if personal_info:
        display_name = (personal_info.get("name") or "").strip()
        if display_name:
            md_parts.append(f"# {display_name}")

        contact_bits = []
        for k in ("email", "phone", "location", "linkedIn", "github", "website"):
            v = (personal_info.get(k) or "").strip()
            if v:
                contact_bits.append(v)
        if contact_bits:
            md_parts.append(" • ".join(contact_bits))

        education_entries = personal_info.get("education_entries")
        if isinstance(education_entries, list) and len(education_entries) > 0:
            md_parts.append("## Education")
            for entry in education_entries:
                if not isinstance(entry, dict):
                    continue

                education_text = (entry.get("education_text") or entry.get("education") or "").strip()
                u = (entry.get("education_university") or entry.get("university") or "").strip()
                d = (entry.get("education_degree") or entry.get("degree") or "").strip()

                if u or d:
                    loc = (entry.get("education_location") or entry.get("location") or "").strip()
                    line = ", ".join(x for x in [d, u, loc] if x)

                    start_d = (entry.get("education_start_date") or entry.get("start_date") or "").strip()
                    end_d = (
                        entry.get("education_end_date")
                        or entry.get("end_date")
                        or entry.get("grad_date")
                        or ""
                    ).strip()
                    start_d_fmt = _format_month_year(start_d)
                    end_d_fmt = _format_month_year(end_d)
                    if start_d_fmt or end_d_fmt:
                        if start_d_fmt and end_d_fmt:
                            line += f" ({start_d_fmt} -- {end_d_fmt})"
                        elif start_d_fmt and not end_d_fmt:
                            line += f" ({start_d_fmt} -- Present)"
                        else:
                            line += f" ({start_d_fmt or end_d_fmt})"

                    awards = (entry.get("education_awards") or entry.get("awards") or "").strip()
                    if awards:
                        line += f"\n- **Awards**: {awards}"

                    md_parts.append(line)
                elif education_text:
                    md_parts.append(education_text)
        else:
            education = (personal_info.get("education") or "").strip()
            u = (personal_info.get("education_university") or personal_info.get("university") or "").strip()
            d = (personal_info.get("education_degree") or personal_info.get("degree") or "").strip()
            if u or d:
                line = ", ".join(x for x in [d, u, (personal_info.get("education_location") or "").strip()] if x)
                start_d = (personal_info.get("education_start_date") or "").strip()
                end_d = (personal_info.get("education_end_date") or personal_info.get("grad_date") or "").strip()
                start_d_fmt = _format_month_year(start_d)
                end_d_fmt = _format_month_year(end_d)
                if start_d_fmt or end_d_fmt:
                    if start_d_fmt and end_d_fmt:
                        line += f" ({start_d_fmt} -- {end_d_fmt})"
                    elif start_d_fmt and not end_d_fmt:
                        line += f" ({start_d_fmt} -- Present)"
                    else:
                        line += f" ({start_d_fmt or end_d_fmt})"
                awards = (personal_info.get("education_awards") or "").strip()
                if awards:
                    line += f"\n- **Awards**: {awards}"
                md_parts.append("## Education")
                md_parts.append(line)
            elif education:
                md_parts.append("## Education")
                md_parts.append(education)

        def _parse_responsibility_bullets(raw_text: Any) -> List[str]:
            """Normalize responsibility text into clean bullet items."""
            if raw_text is None:
                return []
            text = str(raw_text).replace("\r", "\n")
            bullets: List[str] = []
            for line in text.split("\n"):
                cleaned = line.strip().lstrip("-*•").strip()
                if cleaned:
                    bullets.append(cleaned)
            return bullets

        work_entries = personal_info.get("work_experience_entries")
        if isinstance(work_entries, list) and len(work_entries) > 0:
            md_parts.append("## Work Experience")
            for entry in work_entries:
                if not isinstance(entry, dict):
                    continue

                job_title = (entry.get("job_title") or entry.get("work_job_title") or "").strip()
                company = (entry.get("company") or entry.get("work_company") or "").strip()
                location = (entry.get("location") or entry.get("work_location") or "").strip()
                start_d = (entry.get("start_date") or entry.get("work_start_date") or "").strip()
                end_d = (entry.get("end_date") or entry.get("work_end_date") or "").strip()
                start_d_fmt = _format_month_year(start_d)
                end_d_fmt = _format_month_year(end_d)

                if start_d_fmt and end_d_fmt:
                    date_range = f"{start_d_fmt} -- {end_d_fmt}"
                elif start_d_fmt and not end_d_fmt:
                    date_range = f"{start_d_fmt} -- Present"
                else:
                    date_range = end_d_fmt or start_d_fmt or ""
                line_bits = []
                if job_title:
                    line_bits.append(f"**{job_title}**")
                if company:
                    line_bits.append(f"at **{company}**")
                line = " ".join(line_bits) if line_bits else "Work Experience"

                if location:
                    line += f" ({location})"
                if date_range:
                    line += f" ({date_range})"

                responsibilities_text = (
                    entry.get("responsibilities_text")
                    or entry.get("work_responsibilities_text")
                    or entry.get("responsibilities")
                    or ""
                )
                bullets = _parse_responsibility_bullets(responsibilities_text)

                if bullets:
                    block = line + "\n" + "\n".join([f"- {b}" for b in bullets[:4]])
                    md_parts.append(block)
                else:
                    md_parts.append(line)

    # Skills section
    if include_skills and skills_set:
        md_parts.append("## Skills")
        md_parts.append(", ".join(sorted(skills_set)))

    # Projects section
    if include_projects:
        md_parts.append("## Projects")
        for bundle in selected:
            md_parts.append(_format_bundle(bundle))

    markdown_resume = "\n\n".join([p for p in md_parts if p and str(p).strip()])

    if format == "markdown":
        return markdown_resume
    elif format == "latex":
        return markdown_resume
    elif format == "pdf":
        # LaTeX (Jake's format) resume compiled to PDF via pdflatex — requires pdflatex on the system
        portfolios = _bundles_to_portfolios(selected, skills_set, include_skills)
        latex_content = generate_latex_resume(
            portfolios,
            personal_info=personal_info,
            include_skills=include_skills,
            include_projects=include_projects,
            max_projects=max_projects,
        )
        return _compile_latex_to_pdf(latex_content)
    else:
        return markdown_resume


def _convert_markdown_to_html(markdown_content: str) -> str:
    """Convert markdown to styled HTML for PDF generation."""
    html = markdown_content

    # Convert headers
    html = re.sub(r"^# (.+)$", r"<h1>\1</h1>", html, flags=re.MULTILINE)
    html = re.sub(r"^## (.+)$", r"<h2>\1</h2>", html, flags=re.MULTILINE)
    html = re.sub(r"^### (.+)$", r"<h3>\1</h3>", html, flags=re.MULTILINE)

    # Convert bold
    html = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", html)

    # Convert bullet points
    html = re.sub(r"^\* (.+)$", r"<li>\1</li>", html, flags=re.MULTILINE)
    html = re.sub(r"(<li>.*</li>\n?)+", r"<ul>\g<0></ul>", html)

    # Convert line breaks to paragraphs
    paragraphs = html.split("\n\n")
    formatted_paragraphs = []
    for para in paragraphs:
        para = para.strip()
        if para and not para.startswith("<"):
            para = f"<p>{para}</p>"
        formatted_paragraphs.append(para)
    html = "\n".join(formatted_paragraphs)

    # Wrap in full HTML document with styling
    styled_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Professional Resume</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 900px;
            margin: 0 auto;
            padding: 40px 20px;
            background: #f5f5f5;
        }}
        .container {{
            background: white;
            padding: 60px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            border-radius: 8px;
        }}
        h1 {{
            color: #2c3e50;
            border-bottom: 3px solid #3498db;
            padding-bottom: 15px;
            margin-bottom: 30px;
            font-size: 2.5em;
        }}
        h2 {{
            color: #34495e;
            margin-top: 40px;
            margin-bottom: 20px;
            font-size: 1.8em;
            border-left: 4px solid #3498db;
            padding-left: 15px;
        }}
        h3 {{
            color: #555;
            margin-top: 25px;
            margin-bottom: 10px;
            font-size: 1.3em;
        }}
        p {{
            margin: 10px 0;
            color: #555;
        }}
        ul {{
            margin: 15px 0;
            padding-left: 0;
            list-style: none;
        }}
        li {{
            margin: 8px 0;
            padding-left: 25px;
            position: relative;
            color: #666;
        }}
        li:before {{
            content: "▸";
            position: absolute;
            left: 0;
            color: #3498db;
            font-weight: bold;
        }}
        strong {{
            color: #2c3e50;
            font-weight: 600;
        }}
        @media print {{
            body {{
                background: white;
            }}
            .container {{
                box-shadow: none;
                padding: 20px;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        {html}
    </div>
</body>
</html>"""

    return styled_html


def _convert_markdown_to_pdf(markdown_content: str) -> bytes:
    """Convert markdown to PDF bytes using reportlab."""
    from io import BytesIO

    from reportlab.lib.enums import TA_LEFT
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import inch
    from reportlab.platypus import (ListFlowable, ListItem, Paragraph,
                                    SimpleDocTemplate, Spacer)

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=0.75 * inch, bottomMargin=0.75 * inch)

    # Build styles
    styles = getSampleStyleSheet()
    styles.add(
        ParagraphStyle(
            name="CustomTitle",
            parent=styles["Heading1"],
            fontSize=24,
            textColor="#2c3e50",
            spaceAfter=20,
            spaceBefore=10,
        )
    )
    styles.add(
        ParagraphStyle(
            name="CustomHeading",
            parent=styles["Heading2"],
            fontSize=16,
            textColor="#34495e",
            spaceAfter=12,
            spaceBefore=20,
            leftIndent=10,
        )
    )
    styles.add(
        ParagraphStyle(
            name="CustomSubHeading",
            parent=styles["Heading3"],
            fontSize=13,
            textColor="#555555",
            spaceAfter=8,
            spaceBefore=15,
            fontName="Helvetica-Bold",
        )
    )
    styles.add(
        ParagraphStyle(
            name="CustomBody",
            parent=styles["Normal"],
            fontSize=10,
            textColor="#555555",
            spaceAfter=6,
            alignment=TA_LEFT,
        )
    )
    styles.add(
        ParagraphStyle(
            name="BulletText",
            parent=styles["Normal"],
            fontSize=10,
            textColor="#666666",
            leftIndent=20,
            spaceAfter=6,
        )
    )

    # Parse markdown and build PDF elements
    story = []
    lines = markdown_content.split("\n")
    i = 0

    while i < len(lines):
        line = lines[i].strip()

        if line.startswith("# "):
            # Main title
            story.append(Paragraph(line[2:], styles["CustomTitle"]))
        elif line.startswith("## "):
            # Section heading
            story.append(Spacer(1, 0.2 * inch))
            story.append(Paragraph(line[3:], styles["CustomHeading"]))
        elif line.startswith("### "):
            # Subsection heading
            story.append(Paragraph(line[4:], styles["CustomSubHeading"]))
        elif line.startswith("* ") or line.startswith("  • "):
            # Bullet point
            bullet_text = line[2:].strip() if line.startswith("* ") else line[4:].strip()
            story.append(Paragraph(f"• {bullet_text}", styles["BulletText"]))
        elif line.startswith("Technologies:"):
            # Technologies line with special formatting
            story.append(Paragraph(f"<i>{line}</i>", styles["CustomBody"]))
        elif line and not line.startswith("#"):
            # Regular paragraph
            story.append(Paragraph(line, styles["CustomBody"]))
        elif not line:
            # Empty line - add small space
            story.append(Spacer(1, 0.1 * inch))

        i += 1

    # Build PDF
    doc.build(story)
    pdf_bytes = buffer.getvalue()
    buffer.close()

    return pdf_bytes
