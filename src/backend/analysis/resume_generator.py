"""
Resume Item Generator - Generates professional resume bullet points from project analysis
"""

from typing import Any, Dict, List


def generate_resume_items(report: Dict[str, Any]) -> List[str]:
    """
    Generate resume bullet points from project analysis report.
    """
    resume_items = []

    for project in report.get("projects", []):
        items = _generate_project_items(project)
        resume_items.extend(items)

    return resume_items


def _generate_project_items(project: Dict[str, Any]) -> List[str]:
    """Generate resume items for a single project."""
    items = []
    project_name = project.get("project_name", "Project")
    primary_language = project.get("primary_language", "")

    # Technical stack item
    tech_item = _generate_tech_stack_item(project, project_name)
    if tech_item:
        items.append(tech_item)

    # OOP/Architecture item for Python projects
    if "oop_analysis" in project and "error" not in project.get("oop_analysis", {}):
        oop = project["oop_analysis"]
        if oop.get("total_classes", 0) > 0:
            if oop.get("inheritance_depth", 0) > 1:
                items.append(f"Implemented advanced OOP with {oop['total_classes']} classes and inheritance up to {oop['inheritance_depth']} levels.")
            elif oop.get("abstract_classes"):
                items.append(f"Used abstraction and encapsulation in {oop['total_classes']} classes, including {len(oop['abstract_classes'])} abstract base classes.")
            elif oop.get("properties_count", 0) > 0:
                items.append(f"Leveraged Python properties and encapsulation in {oop['total_classes']} classes.")
            else:
                items.append(f"Designed object-oriented modules with {oop['total_classes']} classes.")

    if "java_oop_analysis" in project and "error" not in project.get("java_oop_analysis", {}):
        java = project["java_oop_analysis"]
        if java.get("total_classes", 0) > 0 or java.get("interface_count", 0) > 0:
            if java.get("design_patterns"):
                items.append(f"Applied design patterns ({', '.join(java['design_patterns'][:2])}) in {java['total_classes'] + java['interface_count']} Java types.")
            elif java.get("generic_classes", 0) > 0:
                items.append(f"Developed generic and interface-based Java modules with {java['total_classes']} classes and {java['interface_count']} interfaces.")
            else:
                items.append(f"Built Java OOP modules with {java['total_classes']} classes and {java['interface_count']} interfaces.")

    if project.get('has_tests', False):
        if project.get('test_files', 0) > 0:
            items.append(f"Implemented {project['test_files']} automated tests ({project.get('test_coverage_estimate', 'unknown')} coverage) to ensure code reliability.")
        else:
            items.append("Established a test suite for code validation.")
    if project.get('has_ci_cd', False):
        items.append("Integrated CI/CD pipelines for continuous integration and deployment.")

    if project.get('has_docker', False):
        items.append("Containerized the application for reproducible deployment.")
    if project.get('directory_depth', 0) >= 4:
        items.append(f"Organized codebase with a modular {project['directory_depth']}-level directory structure.")
    if project.get('contributors') and len(project.get('contributors', [])) > 1:
        items.append(f"Collaborated with {len(project['contributors'])} contributors using version control workflows.")
    if project.get('total_commits', 0) > 50:
        items.append(f"Drove project development with {project['total_commits']}+ commits.")

    return items


def _generate_tech_stack_item(project: Dict[str, Any], project_name: str) -> str:
    """Generate technical stack resume item."""
    languages = list(project.get("languages", {}).keys())
    frameworks = project.get("frameworks", [])

    if not languages and not frameworks:
        return ""

    parts = []

    # Language part
    if languages:
        lang_str = ", ".join(languages[:3])  # Top 3 languages
        if len(languages) > 3:
            lang_str += f", and {len(languages) - 3} more"
        parts.append(lang_str)

    # Framework part
    if frameworks:
        fw_str = ", ".join(frameworks[:3])
        if len(frameworks) > 3:
            fw_str += f", and {len(frameworks) - 3} more"
        parts.append(fw_str)

    tech_list = " with ".join(parts) if parts else "multiple technologies"

    # Count files for impact
    total_files = project.get("total_files", 0)
    code_files = project.get("code_files", 0)

    if code_files > 0:
        return f"Developed {project_name} ({project.get('primary_language','')}) using {tech_list}, implementing {code_files} source files with {total_files} total project files"
    else:
        return f"Built {project_name} ({project.get('primary_language','')}) using {tech_list}"


def _generate_python_oop_item(project: Dict[str, Any], project_name: str) -> str:
    """Generate OOP-focused resume item for Python projects."""
    oop = project.get("oop_analysis", {})

    total_classes = oop.get("total_classes", 0)
    abstract_classes = len(oop.get("abstract_classes", []))
    inheritance_depth = oop.get("inheritance_depth", 0)
    private_methods = oop.get("private_methods", 0)
    protected_methods = oop.get("protected_methods", 0)
    properties = oop.get("properties_count", 0)

    if total_classes == 0:
        return ""

    # Build description based on OOP sophistication
    oop_features = []

    if abstract_classes > 0:
        oop_features.append(f"abstraction with {abstract_classes} abstract base classes")

    if inheritance_depth > 0:
        oop_features.append(f"inheritance hierarchies up to {inheritance_depth} levels deep")

    if private_methods > 0 or protected_methods > 0:
        encap_count = private_methods + protected_methods
        oop_features.append(f"encapsulation across {encap_count} private/protected methods")

    if properties > 0:
        oop_features.append(f"{properties} property decorators")

    if oop_features:
        features_str = ", ".join(oop_features[:2])
        return f"Architected {project_name} ({project.get('primary_language','')}) with {total_classes} classes demonstrating {features_str} and unique OOP structure."
    else:
        return f"Designed {project_name} ({project.get('primary_language','')}) using object-oriented programming with {total_classes} classes and custom class relationships."


def _generate_java_oop_item(project: Dict[str, Any], project_name: str) -> str:
    """Generate OOP-focused resume item for Java projects."""
    java_oop = project.get("java_oop_analysis", {})

    total_classes = java_oop.get("total_classes", 0)
    interfaces = java_oop.get("interface_count", 0)
    abstract_classes = len(java_oop.get("abstract_classes", []))
    design_patterns = java_oop.get("design_patterns", [])
    generics = java_oop.get("generic_classes", 0)
    lambdas = java_oop.get("lambda_count", 0)

    if total_classes == 0 and interfaces == 0:
        return ""

    oop_features = []

    if design_patterns:
        patterns_str = ", ".join(design_patterns[:2])
        oop_features.append(f"{patterns_str} design patterns")

    if interfaces > 0:
        oop_features.append(f"{interfaces} interfaces")

    if abstract_classes > 0:
        oop_features.append(f"{abstract_classes} abstract classes")

    if generics > 0:
        oop_features.append(f"generics in {generics} classes")

    if lambdas > 0:
        oop_features.append(f"{lambdas} lambda expressions")

    total_types = total_classes + interfaces

    if oop_features:
        features_str = ", ".join(oop_features[:3])
        return f"Engineered {project_name} ({project.get('primary_language','')}) with {total_types} classes/interfaces implementing {features_str} and project-specific patterns."
    else:
        return f"Developed {project_name} ({project.get('primary_language','')}) with object-oriented design using {total_types} classes and interfaces tailored to project needs."


def _generate_quality_item(project: Dict[str, Any], project_name: str) -> str:
    """Generate testing and code quality resume item."""
    has_tests = project.get("has_tests", False)
    test_files = project.get("test_files", 0)
    has_ci_cd = project.get("has_ci_cd", False)
    test_coverage = project.get("test_coverage_estimate", "")

    if not has_tests and not has_ci_cd:
        return ""

    quality_features = []

    if has_tests and test_files > 0:
        quality_features.append(f"{test_files} test files with {test_coverage} coverage")
    elif has_tests:
        quality_features.append("comprehensive test suite")

    if has_ci_cd:
        quality_features.append("CI/CD pipeline")

    if quality_features:
        features_str = " and ".join(quality_features)
        return f"Ensured code quality for {project_name} ({project.get('primary_language','')}) through {features_str} and project-specific testing strategies."

    return ""


def _generate_scale_item(project: Dict[str, Any], project_name: str) -> str:
    """Generate project scale and complexity resume item."""
    total_files = project.get("total_files", 0)
    total_commits = project.get("total_commits", 0)
    contributors_count = len(project.get("contributors", []))
    has_docker = project.get("has_docker", False)
    depth = project.get("directory_depth", 0)
    if total_files < 10 and total_commits < 20:
        return ""

    scale_features = []

    if total_commits > 50:
        scale_features.append(f"{total_commits} commits")

    if contributors_count > 1:
        scale_features.append(f"{contributors_count} contributors")

    if has_docker:
        scale_features.append("containerized deployment")

    if depth > 3:
        scale_features.append(f"modular architecture with {depth}-level directory structure")

    if scale_features:
        features_str = ", ".join(scale_features[:2])
        return f"Managed {project_name} ({project.get('primary_language','')}) development lifecycle with {features_str} and unique team/project structure."

    return ""


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
    project_name = project.get("project_name", "Project")
    role = project.get("role", "Software Developer")
    timeline = project.get("timeline", "")  # optional if you ever add it

    bullets = _generate_project_items(project)
    languages = list(project.get("languages", {}).keys())
    frameworks = project.get("frameworks", [])
    deps = project.get("dependencies", {})
    databases = deps.get("pip", []) if deps else []
    docker = ["Docker"] if project.get("has_docker") else []
    tech_stack = languages + frameworks + databases + docker
    tech_stack = [t for t in tech_stack if t]
    tech_line = ""
    if tech_stack:
        tech_line = "Technologies: " + ", ".join(sorted(set(tech_stack)))

    # Bullet formatting
    bullet_str = ""
    for b in bullets:
        bullet_str += f"  • {b}\n"

    # Final formatted block
    block = f"""
{project_name} – {role}    {timeline}
{tech_line}
{bullet_str}
""".rstrip()

    return block

def generate_full_resume(report: Dict[str, Any]) -> str:
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
