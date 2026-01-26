#!/usr/bin/env python3
"""
Role Predictor Module - Predicts developer roles based on analyzed project data

This module analyzes project characteristics, technology stack, contribution patterns,
and code quality metrics to predict the most likely developer role/specialization.

Supported Roles:
- Senior Software Engineer
- Full Stack Developer  
- Backend Developer
- Frontend Developer
- DevOps Engineer
- Data Engineer
- Mobile Developer
- Game Developer
- Systems Engineer
- Junior Developer
- Team Lead/Architect
- Machine Learning Engineer
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
from enum import Enum


class DeveloperRole(Enum):
    """Enumeration of developer roles with display names."""
    
    SENIOR_SOFTWARE_ENGINEER = "Senior Software Engineer"
    FULL_STACK_DEVELOPER = "Full Stack Developer"
    BACKEND_DEVELOPER = "Backend Developer"
    FRONTEND_DEVELOPER = "Frontend Developer"
    DEVOPS_ENGINEER = "DevOps Engineer"
    DATA_ENGINEER = "Data Engineer"
    MOBILE_DEVELOPER = "Mobile Developer"
    GAME_DEVELOPER = "Game Developer"
    SYSTEMS_ENGINEER = "Systems Engineer"
    JUNIOR_DEVELOPER = "Junior Developer"
    TEAM_LEAD_ARCHITECT = "Team Lead/Architect"
    ML_ENGINEER = "Machine Learning Engineer"


@dataclass
class RolePrediction:
    """Result of role prediction analysis."""
    
    predicted_role: DeveloperRole
    confidence_score: float  # 0.0 to 1.0
    alternative_roles: List[Tuple[DeveloperRole, float]]  # List of (role, score)
    reasoning: List[str]  # Human-readable justification
    key_indicators: Dict[str, float]  # Factor scores used in prediction


def get_available_roles() -> List[DeveloperRole]:
    """Get list of all available developer roles for curation."""
    return list(DeveloperRole)


def predict_developer_role(project_data: Dict) -> RolePrediction:
    """
    Predict developer role based on comprehensive project analysis.
    
    Args:
        project_data: Project analysis data from the analyzer pipeline
        
    Returns:
        RolePrediction with predicted role, confidence, and reasoning
    """
    
    # Extract key data for analysis
    languages = project_data.get("languages", {})
    frameworks = project_data.get("frameworks", [])
    total_files = project_data.get("total_files", 0)
    code_files = project_data.get("code_files", 0) 
    test_files = project_data.get("test_files", 0)
    
    # Infrastructure indicators
    has_docker = project_data.get("has_docker", False)
    has_ci_cd = project_data.get("has_ci_cd", False)
    
    # Git analysis
    git_analysis = project_data.get("git_analysis", {})
    total_commits = git_analysis.get("total_commits", 0)
    total_contributors = git_analysis.get("total_contributors", 1)
    
    # OOP/Code quality metrics
    oop_analysis = project_data.get("oop_analysis", {})
    java_oop = project_data.get("java_oop_analysis", {})
    cpp_oop = project_data.get("cpp_oop_analysis", {})
    
    # Composite score data
    score_data = project_data.get("score_data", {})
    composite_score = score_data.get("composite_score", 0) if score_data else 0
    
    # Calculate role-specific indicators
    indicators = _calculate_role_indicators(
        languages, frameworks, total_files, code_files, test_files,
        has_docker, has_ci_cd, total_commits, total_contributors,
        oop_analysis, java_oop, cpp_oop, composite_score
    )
    
    # Score each role
    role_scores = {}
    reasoning_points = []
    
    # Senior Software Engineer - high complexity, strong OOP, multiple languages, good practices
    senior_score = 0.0
    if composite_score >= 65:
        senior_score += 0.3
        reasoning_points.append(f"High composite score ({composite_score:.1f}) indicates strong technical skills")
    if indicators["language_diversity"] >= 0.6:
        senior_score += 0.25
        reasoning_points.append("Demonstrates proficiency across multiple programming languages")
    if indicators["oop_mastery"] >= 0.7:
        senior_score += 0.2
        reasoning_points.append("Strong object-oriented programming practices")
    if indicators["project_maturity"] >= 0.6:
        senior_score += 0.15
        reasoning_points.append("Demonstrates mature development practices (testing, CI/CD, documentation)")
    if total_commits >= 100:
        senior_score += 0.1
        reasoning_points.append(f"Extensive commit history ({total_commits} commits) shows sustained contribution")
    role_scores[DeveloperRole.SENIOR_SOFTWARE_ENGINEER] = senior_score
    
    # Full Stack Developer - frontend + backend technologies
    fullstack_score = 0.0
    if indicators["frontend_tech"] >= 0.4 and indicators["backend_tech"] >= 0.4:
        fullstack_score += 0.5
        reasoning_points.append("Demonstrates both frontend and backend technology experience")
    if indicators["database_usage"] >= 0.3:
        fullstack_score += 0.2
        reasoning_points.append("Shows database integration experience")
    if indicators["web_frameworks"] >= 0.3:
        fullstack_score += 0.2
        reasoning_points.append("Uses web development frameworks")
    if len(languages) >= 3:
        fullstack_score += 0.1
        reasoning_points.append("Multi-language experience typical of full-stack development")
    role_scores[DeveloperRole.FULL_STACK_DEVELOPER] = fullstack_score
    
    # Backend Developer - server-side languages, databases, APIs
    backend_score = 0.0
    if indicators["backend_tech"] >= 0.6:
        backend_score += 0.4
        reasoning_points.append("Strong backend technology focus")
    if indicators["database_usage"] >= 0.4:
        backend_score += 0.25
        reasoning_points.append("Significant database usage indicates backend specialization")
    if indicators["api_frameworks"] >= 0.3:
        backend_score += 0.2
        reasoning_points.append("API framework usage suggests backend development")
    if indicators["systems_languages"] >= 0.3:
        backend_score += 0.15
        reasoning_points.append("Systems programming languages indicate backend focus")
    role_scores[DeveloperRole.BACKEND_DEVELOPER] = backend_score
    
    # Frontend Developer - web technologies, UI frameworks
    frontend_score = 0.0
    if indicators["frontend_tech"] >= 0.7:
        frontend_score += 0.5
        reasoning_points.append("Heavy frontend technology usage")
    if indicators["ui_frameworks"] >= 0.4:
        frontend_score += 0.3
        reasoning_points.append("UI framework expertise indicates frontend specialization")
    if indicators["web_languages"] >= 0.4:
        frontend_score += 0.2
        reasoning_points.append("Web-specific language usage")
    role_scores[DeveloperRole.FRONTEND_DEVELOPER] = frontend_score
    
    # DevOps Engineer - infrastructure, automation, deployment
    devops_score = 0.0
    if has_docker and has_ci_cd:
        devops_score += 0.4
        reasoning_points.append("Docker and CI/CD usage indicates DevOps practices")
    elif has_docker or has_ci_cd:
        devops_score += 0.2
        reasoning_points.append("Infrastructure automation tools present")
    if indicators["devops_tools"] >= 0.4:
        devops_score += 0.3
        reasoning_points.append("Strong DevOps tooling presence")
    if indicators["cloud_tech"] >= 0.3:
        devops_score += 0.2
        reasoning_points.append("Cloud technology usage")
    if indicators["scripting_languages"] >= 0.4:
        devops_score += 0.1
        reasoning_points.append("Scripting language proficiency for automation")
    role_scores[DeveloperRole.DEVOPS_ENGINEER] = devops_score
    
    # Data Engineer - data processing, analytics, big data
    data_score = 0.0
    if indicators["data_tech"] >= 0.6:
        data_score += 0.5
        reasoning_points.append("Strong data processing technology usage")
    if indicators["analytics_tools"] >= 0.4:
        data_score += 0.25
        reasoning_points.append("Analytics and data science tools present")
    if indicators["big_data"] >= 0.3:
        data_score += 0.15
        reasoning_points.append("Big data framework usage")
    if indicators["database_usage"] >= 0.5:
        data_score += 0.1
        reasoning_points.append("Heavy database usage supports data engineering role")
    role_scores[DeveloperRole.DATA_ENGINEER] = data_score
    
    # Mobile Developer - mobile platforms and frameworks
    mobile_score = 0.0
    if indicators["mobile_tech"] >= 0.6:
        mobile_score += 0.6
        reasoning_points.append("Strong mobile development technology focus")
    if indicators["mobile_frameworks"] >= 0.3:
        mobile_score += 0.3
        reasoning_points.append("Mobile framework usage")
    if indicators["mobile_languages"] >= 0.4:
        mobile_score += 0.1
        reasoning_points.append("Mobile-specific programming language usage")
    role_scores[DeveloperRole.MOBILE_DEVELOPER] = mobile_score
    
    # Game Developer - game engines, graphics, real-time systems
    game_score = 0.0
    if indicators["game_tech"] >= 0.5:
        game_score += 0.5
        reasoning_points.append("Game development technology usage")
    if indicators["graphics_tech"] >= 0.3:
        game_score += 0.25
        reasoning_points.append("Graphics programming indicators")
    if indicators["realtime_systems"] >= 0.3:
        game_score += 0.15
        reasoning_points.append("Real-time systems programming")
    if indicators["cpp_heavy"] >= 0.4:
        game_score += 0.1
        reasoning_points.append("C++ usage common in game development")
    role_scores[DeveloperRole.GAME_DEVELOPER] = game_score
    
    # Systems Engineer - low-level, performance-critical, systems programming
    systems_score = 0.0
    if indicators["systems_languages"] >= 0.6:
        systems_score += 0.4
        reasoning_points.append("Strong systems programming language usage")
    if indicators["low_level_tech"] >= 0.4:
        systems_score += 0.3
        reasoning_points.append("Low-level systems technology")
    if indicators["performance_focus"] >= 0.3:
        systems_score += 0.2
        reasoning_points.append("Performance-critical code patterns")
    if indicators["embedded_tech"] >= 0.3:
        systems_score += 0.1
        reasoning_points.append("Embedded systems technology")
    role_scores[DeveloperRole.SYSTEMS_ENGINEER] = systems_score
    
    # Team Lead/Architect - high complexity, multiple projects, mentoring indicators
    lead_score = 0.0
    if composite_score >= 75:
        lead_score += 0.3
        reasoning_points.append(f"Exceptional composite score ({composite_score:.1f}) suggests senior/lead capabilities")
    if total_contributors >= 3:
        lead_score += 0.25
        reasoning_points.append(f"Collaborative projects ({total_contributors} contributors) suggest leadership")
    if indicators["architecture_patterns"] >= 0.5:
        lead_score += 0.2
        reasoning_points.append("Strong architectural patterns usage")
    if indicators["language_diversity"] >= 0.7:
        lead_score += 0.15
        reasoning_points.append("Broad technology expertise typical of technical leads")
    if indicators["project_maturity"] >= 0.7:
        lead_score += 0.1
        reasoning_points.append("Exceptional project organization and practices")
    role_scores[DeveloperRole.TEAM_LEAD_ARCHITECT] = lead_score
    
    # ML Engineer - machine learning, data science, AI
    ml_score = 0.0
    if indicators["ml_tech"] >= 0.6:
        ml_score += 0.6
        reasoning_points.append("Strong machine learning technology usage")
    if indicators["data_science"] >= 0.4:
        ml_score += 0.25
        reasoning_points.append("Data science tools and libraries present")
    if indicators["python_heavy"] >= 0.5:
        ml_score += 0.1
        reasoning_points.append("Python dominance typical of ML engineering")
    if indicators["research_patterns"] >= 0.3:
        ml_score += 0.05
        reasoning_points.append("Research-oriented code patterns")
    role_scores[DeveloperRole.ML_ENGINEER] = ml_score
    
    # Junior Developer - lower complexity, basic practices, learning patterns
    junior_score = 0.0
    if composite_score <= 35:
        junior_score += 0.3
        reasoning_points.append(f"Lower composite score ({composite_score:.1f}) suggests early career")
    if total_files <= 20:
        junior_score += 0.2
        reasoning_points.append("Smaller project scale typical of junior developers")
    if test_files == 0:
        junior_score += 0.2
        reasoning_points.append("Limited testing practices common in early career")
    if indicators["basic_patterns"] >= 0.4:
        junior_score += 0.15
        reasoning_points.append("Basic programming patterns without advanced concepts")
    if total_commits <= 50:
        junior_score += 0.15
        reasoning_points.append(f"Limited commit history ({total_commits} commits)")
    role_scores[DeveloperRole.JUNIOR_DEVELOPER] = junior_score
    
    # Determine top prediction
    if not role_scores:
        # Fallback if no scores
        predicted_role = DeveloperRole.JUNIOR_DEVELOPER
        confidence = 0.1
        alternatives = []
    else:
        # Sort by score
        sorted_roles = sorted(role_scores.items(), key=lambda x: x[1], reverse=True)
        predicted_role = sorted_roles[0][0]
        confidence = min(sorted_roles[0][1], 1.0)  # Cap at 1.0
        
        # Get alternatives (top 3, excluding the top prediction)
        alternatives = [(role, score) for role, score in sorted_roles[1:4] if score > 0.1]
    
    return RolePrediction(
        predicted_role=predicted_role,
        confidence_score=confidence,
        alternative_roles=alternatives,
        reasoning=reasoning_points[:5],  # Top 5 reasoning points
        key_indicators=indicators
    )


def _calculate_role_indicators(
    languages: Dict[str, int],
    frameworks: List[str],
    total_files: int,
    code_files: int,
    test_files: int,
    has_docker: bool,
    has_ci_cd: bool,
    total_commits: int,
    total_contributors: int,
    oop_analysis: Dict,
    java_oop: Dict,
    cpp_oop: Dict,
    composite_score: float
) -> Dict[str, float]:
    """
    Calculate role-specific indicators from project data.
    
    Returns a dictionary of normalized indicators (0.0 to 1.0) for different
    aspects relevant to role prediction.
    """
    
    indicators = {}
    
    # Language diversity
    num_languages = len(languages)
    indicators["language_diversity"] = min(num_languages / 5.0, 1.0)  # 5+ languages = max
    
    # Technology categories
    lang_lower = {lang.lower(): count for lang, count in languages.items()}
    framework_lower = [fw.lower() for fw in frameworks]
    
    # Frontend technologies
    frontend_langs = {"javascript", "typescript", "html", "css", "scss", "sass", "vue", "jsx"}
    frontend_frameworks = {"react", "angular", "vue", "svelte", "next.js", "nuxt", "gatsby", "ember"}
    frontend_score = 0.0
    for lang in frontend_langs:
        if lang in lang_lower:
            frontend_score += lang_lower[lang] / max(sum(languages.values()), 1)
    for fw in frontend_frameworks:
        if any(fw in f for f in framework_lower):
            frontend_score += 0.1
    indicators["frontend_tech"] = min(frontend_score, 1.0)
    
    # Backend technologies  
    backend_langs = {"python", "java", "c#", "go", "rust", "scala", "kotlin", "php", "ruby"}
    backend_frameworks = {"django", "flask", "fastapi", "spring", "express", "koa", "rails", "laravel", "gin"}
    backend_score = 0.0
    for lang in backend_langs:
        if lang in lang_lower:
            backend_score += lang_lower[lang] / max(sum(languages.values()), 1)
    for fw in backend_frameworks:
        if any(fw in f for f in framework_lower):
            backend_score += 0.15
    indicators["backend_tech"] = min(backend_score, 1.0)
    
    # Mobile technologies
    mobile_langs = {"swift", "kotlin", "dart", "objective-c"}
    mobile_frameworks = {"flutter", "react native", "ionic", "xamarin", "cordova"}
    mobile_score = 0.0
    for lang in mobile_langs:
        if lang in lang_lower:
            mobile_score += lang_lower[lang] / max(sum(languages.values()), 1)
    for fw in mobile_frameworks:
        if any(fw in f for f in framework_lower):
            mobile_score += 0.2
    indicators["mobile_tech"] = min(mobile_score, 1.0)
    indicators["mobile_languages"] = mobile_score * 0.7
    indicators["mobile_frameworks"] = min(len([fw for fw in framework_lower if any(mf in fw for mf in mobile_frameworks)]) / 2.0, 1.0)
    
    # Data/ML technologies
    data_langs = {"python", "r", "julia", "scala", "sql"}
    ml_frameworks = {"tensorflow", "pytorch", "sklearn", "pandas", "numpy", "scipy", "keras", "spark", "hadoop"}
    ml_score = 0.0
    for lang in data_langs:
        if lang in lang_lower:
            ml_score += lang_lower[lang] / max(sum(languages.values()), 1) * 0.5
    for fw in ml_frameworks:
        if any(fw in f for f in framework_lower):
            ml_score += 0.15
    indicators["ml_tech"] = min(ml_score, 1.0)
    indicators["data_tech"] = ml_score
    
    # Game development
    game_frameworks = {"unity", "unreal", "godot", "pygame", "cocos2d", "opengl", "directx", "vulkan"}
    game_score = 0.0
    for fw in game_frameworks:
        if any(fw in f for f in framework_lower):
            game_score += 0.2
    if "c++" in lang_lower or "cpp" in lang_lower:
        game_score += 0.2  # C++ common in games
    indicators["game_tech"] = min(game_score, 1.0)
    
    # DevOps indicators
    devops_frameworks = {"docker", "kubernetes", "terraform", "ansible", "jenkins", "github actions", "gitlab ci"}
    cloud_frameworks = {"aws", "azure", "gcp", "google cloud", "amazon web services"}
    devops_score = 0.0
    if has_docker:
        devops_score += 0.3
    if has_ci_cd:
        devops_score += 0.3
    for fw in devops_frameworks:
        if any(fw in f for f in framework_lower):
            devops_score += 0.1
    indicators["devops_tools"] = min(devops_score, 1.0)
    
    cloud_score = 0.0
    for fw in cloud_frameworks:
        if any(fw in f for f in framework_lower):
            cloud_score += 0.2
    indicators["cloud_tech"] = min(cloud_score, 1.0)
    
    # Systems programming
    systems_langs = {"c", "c++", "rust", "go", "assembly", "asm"}
    systems_score = 0.0
    for lang in systems_langs:
        if lang in lang_lower:
            systems_score += lang_lower[lang] / max(sum(languages.values()), 1)
    indicators["systems_languages"] = min(systems_score, 1.0)
    
    # OOP mastery (from analysis results)
    oop_score = 0.0
    total_oop_score = 0
    oop_count = 0
    
    if oop_analysis and "error" not in oop_analysis:
        oop_points = oop_analysis.get("oop_score", 0)
        total_oop_score += oop_points
        oop_count += 1
    
    if java_oop and "error" not in java_oop:
        # Calculate Java OOP score
        java_classes = java_oop.get("total_classes", 0)
        java_interfaces = java_oop.get("interface_count", 0) 
        java_inheritance = java_oop.get("classes_with_inheritance", 0)
        java_points = min((java_classes + java_interfaces + java_inheritance) / 10.0 * 6, 6)
        total_oop_score += java_points
        oop_count += 1
    
    if cpp_oop and "error" not in cpp_oop:
        # Calculate C++ OOP score
        cpp_classes = cpp_oop.get("total_classes", 0)
        cpp_virtual = cpp_oop.get("virtual_methods", 0)
        cpp_inheritance = cpp_oop.get("classes_with_inheritance", 0)
        cpp_points = min((cpp_classes + cpp_virtual + cpp_inheritance) / 10.0 * 6, 6)
        total_oop_score += cpp_points
        oop_count += 1
    
    if oop_count > 0:
        oop_score = (total_oop_score / oop_count) / 6.0  # Normalize to 0-1
    indicators["oop_mastery"] = oop_score
    
    # Project maturity
    maturity_score = 0.0
    if test_files > 0:
        maturity_score += 0.3
    if has_docker:
        maturity_score += 0.25
    if has_ci_cd:
        maturity_score += 0.25
    if total_commits >= 50:
        maturity_score += 0.2
    indicators["project_maturity"] = min(maturity_score, 1.0)
    
    # Language-specific indicators
    python_ratio = lang_lower.get("python", 0) / max(sum(languages.values()), 1)
    indicators["python_heavy"] = python_ratio
    
    cpp_ratio = (lang_lower.get("c++", 0) + lang_lower.get("cpp", 0)) / max(sum(languages.values()), 1)
    indicators["cpp_heavy"] = cpp_ratio
    
    # Web languages
    web_langs = {"javascript", "typescript", "html", "css", "php"}
    web_score = sum(lang_lower.get(lang, 0) for lang in web_langs) / max(sum(languages.values()), 1)
    indicators["web_languages"] = web_score
    
    # Scripting languages
    script_langs = {"python", "bash", "shell", "powershell", "perl", "ruby"}
    script_score = sum(lang_lower.get(lang, 0) for lang in script_langs) / max(sum(languages.values()), 1)
    indicators["scripting_languages"] = script_score
    
    # Additional framework categories
    ui_frameworks = {"react", "angular", "vue", "svelte", "flutter", "qt", "tkinter", "javafx"}
    ui_count = len([fw for fw in framework_lower if any(ui in fw for ui in ui_frameworks)])
    indicators["ui_frameworks"] = min(ui_count / 3.0, 1.0)
    
    web_frameworks = {"django", "flask", "express", "fastapi", "spring boot", "rails", "laravel"}
    web_count = len([fw for fw in framework_lower if any(wf in fw for wf in web_frameworks)])
    indicators["web_frameworks"] = min(web_count / 3.0, 1.0)
    
    api_frameworks = {"fastapi", "express", "flask", "spring boot", "gin", "echo"}
    api_count = len([fw for fw in framework_lower if any(af in fw for af in api_frameworks)])
    indicators["api_frameworks"] = min(api_count / 2.0, 1.0)
    
    # Database usage (inferred from frameworks/languages)
    db_frameworks = {"sqlalchemy", "hibernate", "mongoose", "sequelize", "prisma", "sql", "postgresql", "mysql"}
    db_count = len([fw for fw in framework_lower if any(db in fw for db in db_frameworks)])
    db_lang_score = lang_lower.get("sql", 0) / max(sum(languages.values()), 1)
    indicators["database_usage"] = min((db_count / 3.0) + db_lang_score, 1.0)
    
    # Analytics and big data
    analytics_tools = {"pandas", "numpy", "scipy", "matplotlib", "seaborn", "plotly", "d3.js"}
    analytics_count = len([fw for fw in framework_lower if any(at in fw for at in analytics_tools)])
    indicators["analytics_tools"] = min(analytics_count / 3.0, 1.0)
    
    big_data_tools = {"spark", "hadoop", "kafka", "elasticsearch", "mongodb", "cassandra"}
    big_data_count = len([fw for fw in framework_lower if any(bd in fw for bd in big_data_tools)])
    indicators["big_data"] = min(big_data_count / 2.0, 1.0)
    
    # Architecture and patterns (based on complexity and OOP)
    arch_score = 0.0
    if composite_score >= 70:
        arch_score += 0.4
    if oop_score >= 0.6:
        arch_score += 0.3
    if total_contributors >= 3:
        arch_score += 0.2
    if test_files > code_files * 0.3:  # Good test coverage
        arch_score += 0.1
    indicators["architecture_patterns"] = min(arch_score, 1.0)
    
    # Basic patterns (for junior detection)
    basic_score = 0.0
    if composite_score <= 40:
        basic_score += 0.4
    if oop_score <= 0.3:
        basic_score += 0.3
    if test_files == 0:
        basic_score += 0.2
    if total_commits <= 30:
        basic_score += 0.1
    indicators["basic_patterns"] = min(basic_score, 1.0)
    
    # Additional specialized indicators
    indicators["graphics_tech"] = min(len([fw for fw in framework_lower if any(gf in fw for gf in ["opengl", "directx", "vulkan", "metal"])]) / 2.0, 1.0)
    indicators["realtime_systems"] = cpp_ratio + min(len([fw for fw in framework_lower if "real" in fw or "time" in fw]) / 2.0, 1.0)
    indicators["low_level_tech"] = (lang_lower.get("c", 0) + lang_lower.get("assembly", 0) + lang_lower.get("asm", 0)) / max(sum(languages.values()), 1)
    indicators["embedded_tech"] = min(len([fw for fw in framework_lower if any(ef in fw for ef in ["arduino", "raspberry", "embedded", "firmware"])]) / 2.0, 1.0)
    indicators["performance_focus"] = cpp_ratio + lang_lower.get("rust", 0) / max(sum(languages.values()), 1) + lang_lower.get("go", 0) / max(sum(languages.values()), 1)
    indicators["data_science"] = min(len([fw for fw in framework_lower if any(ds in fw for ds in ["jupyter", "sklearn", "pandas", "numpy", "matplotlib"])]) / 3.0, 1.0)
    indicators["research_patterns"] = min(len([fw for fw in framework_lower if any(rp in fw for rp in ["jupyter", "notebook", "research", "academic"])]) / 2.0, 1.0)
    
    return indicators


def format_role_prediction(prediction: RolePrediction) -> str:
    """
    Format role prediction for display in CLI output.
    
    Args:
        prediction: RolePrediction object
        
    Returns:
        Formatted string for display
    """
    
    output = []
    output.append(f"   PREDICTED ROLE: {prediction.predicted_role.value}")
    output.append(f"   Confidence: {prediction.confidence_score:.1%}")
    
    if prediction.alternative_roles:
        output.append(f"   Alternative roles:")
        for role, score in prediction.alternative_roles:
            output.append(f"      • {role.value} ({score:.1%})")
    
    if prediction.reasoning:
        output.append(f"   Key indicators:")
        for reason in prediction.reasoning:
            output.append(f"      • {reason}")
    
    return "\n".join(output)