"""Document analyzer for essays and academic papers.

This module analyzes text documents (essays, research papers) to extract:
- Citation style and count
- Writing quality metrics (readability, complexity)
- Document structure (paragraphs, sections)
- Resume-ready highlights
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple

try:
    import textstat
except ImportError:
    textstat = None

try:
    import nltk
    from nltk.tokenize import sent_tokenize
except ImportError:
    nltk = None
    sent_tokenize = None


@dataclass
class CitationAnalysis:
    """Analysis results for citations in a document."""

    style: Optional[str] = None  # APA, MLA, Chicago, IEEE, Harvard
    in_text_count: int = 0
    bibliography_count: int = 0
    has_consistent_style: bool = False
    confidence: str = "low"  # low, medium, high


@dataclass
class WritingMetrics:
    """Writing quality and complexity metrics."""

    word_count: int = 0
    page_estimate: float = 0.0  # Based on 250 words per page
    flesch_kincaid_grade: Optional[float] = None
    flesch_reading_ease: Optional[float] = None
    avg_sentence_length: float = 0.0
    sentence_count: int = 0
    has_formal_tone: bool = False
    has_technical_vocabulary: bool = False
    reading_level_description: str = ""


@dataclass
class StructureAnalysis:
    """Document structure analysis."""

    paragraph_count: int = 0
    avg_paragraph_length: float = 0.0
    has_introduction: bool = False
    has_conclusion: bool = False
    structure_quality: str = "basic"  # basic, good, well-organized


@dataclass
class DocumentAnalysis:
    """Complete document analysis results."""

    file_path: str
    file_type: str  # txt, pdf, docx, md
    citation_analysis: CitationAnalysis = field(default_factory=CitationAnalysis)
    writing_metrics: WritingMetrics = field(default_factory=WritingMetrics)
    structure_analysis: StructureAnalysis = field(default_factory=StructureAnalysis)
    resume_highlights: List[str] = field(default_factory=list)
    analysis_type: str = "non_llm"


class CitationDetector:
    """Detects citation styles and counts citations in academic text."""

    # Citation style patterns
    APA_IN_TEXT = [
        r'\([A-Z][a-zA-Z]+,?\s+(?:et al\.,?\s+)?\d{4}[a-z]?\)',  # (Author, 2020) or (Author et al., 2020)
        r'[A-Z][a-zA-Z]+\s+(?:et al\.\s+)?\(\d{4}[a-z]?\)',  # Author (2020)
    ]

    MLA_IN_TEXT = [
        r'\([A-Z][a-zA-Z]+(?:\s+and\s+[A-Z][a-zA-Z]+)?\s+\d+[-–]?\d*\)',  # (Author 123) or (Author 123-125)
        r'\([A-Z][a-zA-Z]+(?:\s+and\s+[A-Z][a-zA-Z]+)?\)',  # (Author and Author)
    ]

    CHICAGO_IN_TEXT = [
        r'\[\d+\]',  # [1] footnote style
        r'\([A-Z][a-zA-Z]+\s+\d{4},\s*\d+\)',  # (Author 2020, 45)
    ]

    IEEE_IN_TEXT = [
        r'\[\d+\]',  # [1]
        r'\[\d+[-–]\d+\]',  # [1-3]
        r'\[\d+,\s*\d+(?:,\s*\d+)*\]',  # [1, 2, 3]
    ]

    HARVARD_IN_TEXT = [
        r'\([A-Z][a-zA-Z]+\s+\d{4}\)',  # (Author 2020)
        r'\([A-Z][a-zA-Z]+\s+\d{4}:\s*\d+\)',  # (Author 2020: 45)
    ]

    BIBLIOGRAPHY_PATTERNS = {
        'APA': r'^[A-Z][a-zA-Z]+,\s+[A-Z]\.\s*(?:[A-Z]\.\s*)?\(\d{4}\)',  # Author, A. (2020)
        'MLA': r'^[A-Z][a-zA-Z]+,\s+[A-Z][a-zA-Z]+\.',  # Author, Firstname.
        'Chicago': r'^\d+\.\s+[A-Z][a-zA-Z]+',  # 1. Author
        'IEEE': r'^\[\d+\]\s+[A-Z]',  # [1] Author
        'Harvard': r'^[A-Z][a-zA-Z]+,\s+[A-Z]\.\s+\(\d{4}\)',  # Author, A. (2020)
    }

    def __init__(self, text: str):
        """Initialize citation detector with document text.

        Args:
            text: Full text of the document
        """
        self.text = text
        self.lines = text.split('\n')

    def detect_citation_style(self) -> CitationAnalysis:
        """Detect the primary citation style used in the document.

        Returns:
            CitationAnalysis with detected style and counts
        """
        analysis = CitationAnalysis()

        # Count citations for each style
        style_scores = {
            'APA': self._count_citations(self.APA_IN_TEXT),
            'MLA': self._count_citations(self.MLA_IN_TEXT),
            'Chicago': self._count_citations(self.CHICAGO_IN_TEXT),
            'IEEE': self._count_citations(self.IEEE_IN_TEXT),
            'Harvard': self._count_citations(self.HARVARD_IN_TEXT),
        }

        # Find the style with most matches
        max_style = max(style_scores.items(), key=lambda x: x[1])

        if max_style[1] > 0:
            analysis.style = max_style[0]
            analysis.in_text_count = max_style[1]

            # Count bibliography entries
            analysis.bibliography_count = self._count_bibliography_entries(max_style[0])

            # Determine confidence
            if max_style[1] >= 10:
                analysis.confidence = "high"
            elif max_style[1] >= 5:
                analysis.confidence = "medium"
            else:
                analysis.confidence = "low"

            # Check consistency (no other style has more than 30% of the max)
            other_counts = [count for style, count in style_scores.items() if style != max_style[0]]
            if not other_counts or max(other_counts) < max_style[1] * 0.3:
                analysis.has_consistent_style = True

        return analysis

    def _count_citations(self, patterns: List[str]) -> int:
        """Count citations matching the given patterns.

        Args:
            patterns: List of regex patterns to match

        Returns:
            Total count of matches
        """
        count = 0
        for pattern in patterns:
            matches = re.findall(pattern, self.text)
            count += len(matches)
        return count

    def _count_bibliography_entries(self, style: str) -> int:
        """Count bibliography/reference entries for a given style.

        Args:
            style: Citation style name

        Returns:
            Number of bibliography entries found
        """
        if style not in self.BIBLIOGRAPHY_PATTERNS:
            return 0

        pattern = self.BIBLIOGRAPHY_PATTERNS[style]
        count = 0

        # Check last 30% of document (where references usually are)
        start_idx = int(len(self.lines) * 0.7)
        for line in self.lines[start_idx:]:
            if re.match(pattern, line.strip()):
                count += 1

        return count


class WritingMetricsCalculator:
    """Calculates writing quality and complexity metrics."""

    FORMAL_INDICATORS = [
        r'\bhowever\b', r'\bmoreover\b', r'\bfurthermore\b', r'\bnevertheless\b',
        r'\bconsequently\b', r'\btherefore\b', r'\bthus\b', r'\bhence\b',
        r'\bsubsequently\b', r'\baccordingly\b', r'\bindeed\b', r'\bspecifically\b'
    ]

    TECHNICAL_INDICATORS = [
        r'\banalysis\b', r'\bmethodology\b', r'\bhypothesis\b', r'\bframework\b',
        r'\bparadigm\b', r'\bempirical\b', r'\btheoretical\b', r'\bsignificant\b',
        r'\bcorrelation\b', r'\bvariable\b', r'\bdata\b', r'\bresearch\b'
    ]

    def __init__(self, text: str):
        """Initialize metrics calculator with document text.

        Args:
            text: Full text of the document
        """
        self.text = text

    def calculate_metrics(self) -> WritingMetrics:
        """Calculate all writing metrics for the document.

        Returns:
            WritingMetrics with calculated values
        """
        metrics = WritingMetrics()

        # Word count
        words = self.text.split()
        metrics.word_count = len(words)
        metrics.page_estimate = round(metrics.word_count / 250, 1)

        # Sentence analysis
        sentences = self._get_sentences()
        metrics.sentence_count = len(sentences)

        if sentences:
            total_words = sum(len(s.split()) for s in sentences)
            metrics.avg_sentence_length = round(total_words / len(sentences), 1)

        # Readability metrics (if textstat is available)
        if textstat:
            try:
                metrics.flesch_kincaid_grade = round(textstat.flesch_kincaid_grade(self.text), 1)
                metrics.flesch_reading_ease = round(textstat.flesch_reading_ease(self.text), 1)

                # Reading level description
                grade = metrics.flesch_kincaid_grade
                if grade >= 16:
                    metrics.reading_level_description = "Grade 16+ (College Senior/Graduate)"
                elif grade >= 13:
                    metrics.reading_level_description = f"Grade {int(grade)} (College)"
                elif grade >= 9:
                    metrics.reading_level_description = f"Grade {int(grade)} (High School)"
                else:
                    metrics.reading_level_description = f"Grade {int(grade)}"
            except Exception:
                pass

        # Tone analysis
        metrics.has_formal_tone = self._check_formal_tone()
        metrics.has_technical_vocabulary = self._check_technical_vocabulary()

        return metrics

    def _get_sentences(self) -> List[str]:
        """Split text into sentences.

        Returns:
            List of sentences
        """
        if sent_tokenize:
            try:
                return sent_tokenize(self.text)
            except Exception:
                pass

        # Fallback: split on common sentence endings
        sentences = re.split(r'[.!?]+\s+', self.text)
        return [s.strip() for s in sentences if s.strip()]

    def _check_formal_tone(self) -> bool:
        """Check if the text uses formal academic language.

        Returns:
            True if formal tone detected
        """
        formal_count = 0
        for pattern in self.FORMAL_INDICATORS:
            matches = re.findall(pattern, self.text, re.IGNORECASE)
            formal_count += len(matches)

        # Consider formal if at least 3 formal indicators per 1000 words
        words_count = len(self.text.split())
        return formal_count >= (words_count / 1000) * 3

    def _check_technical_vocabulary(self) -> bool:
        """Check if the text uses technical/academic vocabulary.

        Returns:
            True if technical vocabulary detected
        """
        technical_count = 0
        for pattern in self.TECHNICAL_INDICATORS:
            matches = re.findall(pattern, self.text, re.IGNORECASE)
            technical_count += len(matches)

        # Consider technical if at least 5 technical terms per 1000 words
        words_count = len(self.text.split())
        return technical_count >= (words_count / 1000) * 5


class StructureAnalyzer:
    """Analyzes document structure and organization."""

    INTRO_KEYWORDS = [
        r'\bintroduction\b', r'\bthis\s+paper\b', r'\bthis\s+essay\b',
        r'\bthis\s+study\b', r'\bthis\s+research\b', r'\bbegin\s+by\b',
        r'\bfirstly\b', r'\bin\s+this\s+paper\b'
    ]

    CONCLUSION_KEYWORDS = [
        r'\bconclusion\b', r'\bin\s+conclusion\b', r'\bto\s+conclude\b',
        r'\bin\s+summary\b', r'\bto\s+summarize\b', r'\bfinally\b',
        r'\bin\s+closing\b', r'\bultimately\b'
    ]

    def __init__(self, text: str):
        """Initialize structure analyzer with document text.

        Args:
            text: Full text of the document
        """
        self.text = text
        self.paragraphs = self._extract_paragraphs()

    def analyze_structure(self) -> StructureAnalysis:
        """Analyze the document's structural organization.

        Returns:
            StructureAnalysis with structural metrics
        """
        analysis = StructureAnalysis()

        # Paragraph metrics
        analysis.paragraph_count = len(self.paragraphs)

        if self.paragraphs:
            word_counts = [len(p.split()) for p in self.paragraphs]
            analysis.avg_paragraph_length = round(sum(word_counts) / len(word_counts), 0)

        # Check for introduction and conclusion
        analysis.has_introduction = self._has_section(self.INTRO_KEYWORDS, first_third=True)
        analysis.has_conclusion = self._has_section(self.CONCLUSION_KEYWORDS, last_third=True)

        # Determine structure quality
        if analysis.has_introduction and analysis.has_conclusion and analysis.paragraph_count >= 10:
            analysis.structure_quality = "well-organized"
        elif (analysis.has_introduction or analysis.has_conclusion) and analysis.paragraph_count >= 5:
            analysis.structure_quality = "good"
        else:
            analysis.structure_quality = "basic"

        return analysis

    def _extract_paragraphs(self) -> List[str]:
        """Extract paragraphs from text.

        Returns:
            List of paragraph strings
        """
        # Split on double newlines (common paragraph separator)
        paragraphs = re.split(r'\n\s*\n', self.text)

        # Filter out very short paragraphs (likely not real paragraphs)
        paragraphs = [p.strip() for p in paragraphs if len(p.strip().split()) >= 20]

        return paragraphs

    def _has_section(self, keywords: List[str], first_third: bool = False, last_third: bool = False) -> bool:
        """Check if a section (intro/conclusion) exists based on keywords.

        Args:
            keywords: List of regex patterns to search for
            first_third: Only search in first third of document
            last_third: Only search in last third of document

        Returns:
            True if section indicators found
        """
        text_to_search = self.text.lower()

        if first_third:
            cutoff = len(text_to_search) // 3
            text_to_search = text_to_search[:cutoff]
        elif last_third:
            cutoff = (len(text_to_search) * 2) // 3
            text_to_search = text_to_search[cutoff:]

        for pattern in keywords:
            if re.search(pattern, text_to_search, re.IGNORECASE):
                return True

        return False


class DocumentAnalyzer:
    """Main analyzer that coordinates all document analysis components."""

    def __init__(self, file_path: str, text: str):
        """Initialize document analyzer.

        Args:
            file_path: Path to the document file
            text: Extracted text content from the document
        """
        self.file_path = file_path
        self.text = text
        self.file_type = Path(file_path).suffix.lower().lstrip('.')

    def analyze(self) -> DocumentAnalysis:
        """Perform complete document analysis.

        Returns:
            DocumentAnalysis with all analysis results
        """
        # Initialize analysis result
        analysis = DocumentAnalysis(
            file_path=self.file_path,
            file_type=self.file_type
        )

        # Run all analyzers
        citation_detector = CitationDetector(self.text)
        analysis.citation_analysis = citation_detector.detect_citation_style()

        metrics_calculator = WritingMetricsCalculator(self.text)
        analysis.writing_metrics = metrics_calculator.calculate_metrics()

        structure_analyzer = StructureAnalyzer(self.text)
        analysis.structure_analysis = structure_analyzer.analyze_structure()

        # Generate resume highlights
        analysis.resume_highlights = self._generate_resume_highlights(analysis)

        return analysis

    def _generate_resume_highlights(self, analysis: DocumentAnalysis) -> List[str]:
        """Generate resume-ready skill highlights based on analysis.

        Args:
            analysis: Complete document analysis

        Returns:
            List of resume bullet points
        """
        highlights = []

        # Citation skills
        if analysis.citation_analysis.style:
            style = analysis.citation_analysis.style
            count = analysis.citation_analysis.in_text_count
            if count >= 5:
                highlights.append(f"Proficient in {style} citation format")

                if count >= 10:
                    pages = int(analysis.writing_metrics.page_estimate)
                    highlights.append(
                        f"Authored {pages}-page research paper with {count} scholarly citations"
                    )

        # Writing level
        if analysis.writing_metrics.flesch_kincaid_grade:
            grade = analysis.writing_metrics.flesch_kincaid_grade
            if grade >= 16:
                highlights.append("Academic writing at advanced level (Grade 16+ reading level)")
            elif grade >= 13:
                highlights.append(f"College-level academic writing (Grade {int(grade)} reading level)")

        # Academic skills
        if analysis.writing_metrics.has_formal_tone and analysis.writing_metrics.has_technical_vocabulary:
            highlights.append("Demonstrated strong research and analytical writing skills")
            highlights.append("Maintained formal academic tone with technical vocabulary")

        # Structure skills
        if analysis.structure_analysis.structure_quality == "well-organized":
            para_count = analysis.structure_analysis.paragraph_count
            highlights.append(
                f"Structured complex ideas across {para_count} well-organized paragraphs"
            )

        # General research skills if paper has good metrics
        if (analysis.citation_analysis.in_text_count >= 10 and
            analysis.writing_metrics.word_count >= 1500 and
            analysis.structure_analysis.has_introduction and
            analysis.structure_analysis.has_conclusion):
            highlights.append(
                "Developed strong analytical and research skills through evidence-based academic writing"
            )

        return highlights


def analyze_document(file_path: str, text: str) -> DocumentAnalysis:
    """Analyze a document and return complete analysis.

    Args:
        file_path: Path to the document file
        text: Extracted text content

    Returns:
        DocumentAnalysis with all results
    """
    analyzer = DocumentAnalyzer(file_path, text)
    return analyzer.analyze()
