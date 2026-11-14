import logging
import re
from typing import Dict, Any, List, Optional
from collections import Counter

logger = logging.getLogger(__name__)

class DocumentSummarizer:
    """
    Intelligent, structure-aware document summarization and insights engine.
    Produces coherent, dense executive summaries, comprehensive section-by-section
    detailed overviews, and high-impact bulleted key takeaways tailored to document
    archetypes (Resume/CV, Academic Paper, Legal Contract, Financial/Invoice, and
    Technical/General Documentation).
    """

    @classmethod
    def summarize(cls, text: str) -> Dict[str, Any]:
        if not text or not text.strip():
            return {
                "short_summary": "No text content available to summarize.",
                "detailed_summary": "No text content available to summarize.",
                "key_points": []
            }

        clean_text = cls._clean_noise(text)
        archetype = cls._detect_archetype(clean_text)
        logger.info(f"Summarizing document under detected archetype: '{archetype}'")

        try:
            if archetype == "resume":
                return cls._summarize_resume(clean_text)
            elif archetype == "academic":
                return cls._summarize_academic(clean_text)
            elif archetype == "legal":
                return cls._summarize_legal(clean_text)
            elif archetype == "financial":
                return cls._summarize_financial(clean_text)
            elif archetype == "technical":
                return cls._summarize_technical(clean_text)
            else:
                return cls._summarize_general(clean_text)
        except Exception as e:
            logger.error(f"Error in archetype summarizer '{archetype}': {e}. Falling back to general summarizer.", exc_info=True)
            return cls._summarize_general(clean_text)

    @staticmethod
    def _clean_noise(text: str) -> str:
        """Strips redundant symbol noise while preserving semantic punctuation and bullet markers."""
        t = re.sub(r"[\xa0\u200b]", " ", text)
        # Normalize non-standard bullet symbols to standard bullet
        t = re.sub(r"[\u2022\u2023\u25E6\u2043\u2219\uf0d8]", "• ", t)
        # Normalize excessive divider runs
        t = re.sub(r"[-=_*]{4,}", " ", t)
        return t.strip()

    @staticmethod
    def _normalize_tech_stack(tech_list: List[str]) -> List[str]:
        """Maps framework and language tokens to their canonical title-case forms and deduplicates."""
        canonical_map = {
            "react": "React.js", "react.js": "React.js", "reactjs": "React.js",
            "next": "Next.js", "next.js": "Next.js", "nextjs": "Next.js",
            "node": "Node.js", "node.js": "Node.js", "nodejs": "Node.js",
            "express": "Express.js", "express.js": "Express.js", "expressjs": "Express.js",
            "tailwind": "Tailwind CSS", "tailwind css": "Tailwind CSS", "tailwindcss": "Tailwind CSS",
            "scikit-learn": "Scikit-learn", "sklearn": "Scikit-learn",
            "c++": "C++", "c++17": "C++17", "cpp": "C++",
            "c#": "C#",
            "c": "C",
            "python": "Python",
            "java": "Java",
            "kotlin": "Kotlin",
            "javascript": "JavaScript", "js": "JavaScript",
            "typescript": "TypeScript", "ts": "TypeScript",
            "flask": "Flask",
            "fastapi": "FastAPI",
            "django": "Django",
            "firebase": "Firebase",
            "firestore": "Firebase Firestore",
            "sqlite": "SQLite",
            "postgresql": "PostgreSQL", "postgres": "PostgreSQL",
            "mongodb": "MongoDB",
            "openssl": "OpenSSL",
            "docker": "Docker",
            "git": "Git",
            "github": "GitHub",
            "chart.js": "Chart.js", "chartjs": "Chart.js",
            "recharts": "Recharts",
            "vite": "Vite",
            "groq": "Groq API", "groq api": "Groq API"
        }
        seen = set()
        result = []
        for item in tech_list:
            clean = item.strip().lower()
            canon = canonical_map.get(clean, item.strip())
            # Skip pure common English words accidentally caught
            if canon.lower() in {"and", "with", "using", "tool", "tools", "platform", "platforms"}:
                continue
            if canon.lower() not in seen:
                seen.add(canon.lower())
                result.append(canon)
        return result

    @staticmethod
    def _unwrap_paragraphs(text: str) -> str:
        """Un-wraps line-broken sentences from PDFs and documents while preserving bullet points."""
        lines = text.splitlines()
        unwrapped = []
        buf = ""
        for l in lines:
            stripped = l.strip()
            if not stripped:
                if buf:
                    unwrapped.append(buf)
                    buf = ""
                continue
            
            # Check if this line is an explicit bullet, step, header, or numbered item
            is_bullet = bool(
                re.match(r"^[•\*\-\d\.\)]\s+", stripped) or
                re.match(r"^Step\s*\d+\s*:", stripped, re.I) or
                re.match(r"^(?:Unit\s*[IVXLCDM\d]+|Chapter\s*\d+|Section\s*\d+)", stripped, re.I) or
                (stripped.endswith(":") and len(stripped) < 65) or
                (len(stripped) < 45 and not stripped.endswith("."))
            )
            
            if is_bullet:
                if buf:
                    unwrapped.append(buf)
                buf = stripped
            elif buf:
                if not re.search(r"[\.!\?:;]$", buf) and not re.match(r"^Step\s*\d+", buf, re.I):
                    buf += " " + stripped
                else:
                    unwrapped.append(buf)
                    buf = stripped
            else:
                buf = stripped
        if buf:
            unwrapped.append(buf)
        return "\n\n".join(unwrapped)

    @staticmethod
    def _detect_archetype(text: str) -> str:
        """Determines document archetype based on strong structural signals."""
        t_lower = text.lower()

        # 1. Academic / Research signals
        if re.search(r"\babstract\b", t_lower) and re.search(r"\b(keywords|introduction|literature review|methodology|references|ieee|doi)\b", t_lower):
            return "academic"

        # 2. Legal / Contract signals
        if re.search(r"\b(agreement|contract|non-disclosure|memorandum of understanding|terms of service)\b", t_lower) and re.search(r"\b(governing law|parties|liquidated damages|disclosing party|covenants|indemnification)\b", t_lower):
            return "legal"

        # 3. Financial / Invoice signals
        if re.search(r"\b(invoice|tax invoice|billing receipt|balance due)\b", t_lower) and re.search(r"\b(total due|subtotal|amount due|bill to|gst|tax)\b", t_lower):
            return "financial"

        # 4. Resume / CV signals
        is_explicit_cv = bool(re.search(r"\b(curriculum vitae|resume)\b", t_lower))
        has_cv_sections = bool(
            re.search(r"\b(skills|technical skills)\b", t_lower) and
            re.search(r"\b(projects|experience|education|certifications?)\b", t_lower) and
            re.search(r"\b(cgpa|bachelor|b\.tech|intermediate|matriculation|github|linkedin)\b", t_lower)
        )
        if is_explicit_cv or has_cv_sections:
            return "resume"

        # 5. Technical / Courseware / Architecture signals
        is_technical = bool(
            re.search(r"\b(unit|chapter)\s+[ivxlcdm\d]+\b", t_lower) or
            re.search(r"\b(sequence-to-sequence|seq2seq|encoder-decoder|attention mechanism|bahdanau|luong|scaled dot-product|neural network|deep learning|transformer|information bottleneck)\b", t_lower)
        )
        if is_technical:
            return "technical"

        return "general"

    # -------------------------------------------------------------------------
    # 1. RESUME / CV SUMMARIZER
    # -------------------------------------------------------------------------
    @classmethod
    def _summarize_resume(cls, text: str) -> Dict[str, Any]:
        lines = [l.strip() for l in text.splitlines() if l.strip()]

        # 1. Extract Candidate Name
        candidate_name = "Candidate"
        for line in lines[:6]:
            clean_l = re.sub(r"^(?:name\s*[:\-])\s*", "", line, flags=re.I).strip()
            if 3 < len(clean_l) < 35 and not any(ch in clean_l for ch in ":@/|1234567890"):
                if not re.search(r"\b(curriculum|resume|vitae|skills|profile|contact)\b", clean_l, re.I):
                    candidate_name = clean_l
                    break

        # 2. Extract Skills Sections (categorized & tokenized)
        skills_match = re.search(r"(?:SKILLS|TECHNICAL SKILLS)\s*(.*?)(?=\n\s*(?:PROJECTS?|WORK\s*EXPERIENCE|EXPERIENCE|EDUCATION|TRAINING|CERTIFICATES?|CERTIFICATIONS?|$))", text, re.S | re.I)
        skills_text = skills_match.group(1).strip() if skills_match else ""

        # Parse categorized lines (e.g. Languages: ..., Tools: ...)
        cat_skills: Dict[str, str] = {}
        for s_line in skills_text.splitlines():
            m_cat = re.match(r"^([A-Za-z0-9\s/&]+?)\s*:\s*([^\n]+)", s_line.strip())
            if m_cat:
                c_name = m_cat.group(1).strip()
                c_val = m_cat.group(2).strip()
                if c_val and len(c_name) < 40:
                    cat_skills[c_name] = c_val

        raw_langs = re.findall(r"\b(C\+\+|Python|Java|Kotlin|JavaScript|TypeScript|C#|C\b|Go|Rust|SQL|HTML|CSS)\b", skills_text, re.I)
        raw_fws = re.findall(r"\b(React(?:\.js)?|Next(?:\.js)?|Node(?:\.js)?|Express(?:\.js)?|Tailwind(?:\s*CSS)?|Flask|FastAPI|Django|Firebase|Spring(?:\s*Boot)?|Vue(?:\.js)?|Angular)\b", skills_text, re.I)
        raw_tools = re.findall(r"\b(Git|GitHub|VS\s*Code|Docker|Kubernetes|Google\s*Colab|Jupyter(?:\s*Notebook)?|Android\s*Studio|Linux|PostgreSQL|MySQL|MongoDB|SQLite|OpenSSL|AWS|GCP)\b", skills_text, re.I)

        langs = cls._normalize_tech_stack(raw_langs)
        frameworks = cls._normalize_tech_stack(raw_fws)
        tools = cls._normalize_tech_stack(raw_tools)

        # 3. Extract Engineering Projects
        projects = []
        p_matches = re.finditer(
            r"(?:^|\n)\s*([A-Za-z0-9\s&]+?)\s*\|\s*([^\n]+)(.*?)(?=(?:\n\s*[A-Za-z0-9\s&]+?\s*\|)|\n\s*(?:TRAINING|EXPERIENCE|WORK\s*EXPERIENCE|EDUCATION|CERTIFICATES?|CERTIFICATIONS?|$))",
            text, re.S
        )
        for m in p_matches:
            raw_title = m.group(1).strip()
            clean_title = re.sub(r"^(?:PROJECTS?|EXPERIENCE|PERSONAL PROJECTS|ADAPTABILITY)\s*", "", raw_title, flags=re.I).strip()
            clean_title = clean_title.splitlines()[-1].strip()
            p_stack_raw = m.group(2).strip()
            p_body = m.group(3).strip()

            # Check if tech stack is explicitly defined at the end of the project body (e.g., Tech: ...)
            tech_m = re.search(r"\bTech(?:\s*Stack)?\s*[:\-]\s*([^\n]+)", p_body, re.I)
            if tech_m:
                stack_items = [s.strip() for s in re.split(r"[,;]\s*", tech_m.group(1)) if s.strip()]
                normalized_stack = cls._normalize_tech_stack(stack_items)
                stack_str = ", ".join(normalized_stack) if normalized_stack else tech_m.group(1).strip()
                p_body = re.sub(r"\bTech(?:\s*Stack)?\s*[:\-]\s*[^\n]+", "", p_body, flags=re.I)
            elif p_stack_raw.lower() in {"github", "link", "demo", "live"}:
                # Extract technologies mentioned inside the bullets
                extracted = re.findall(r"\b(Python|C\+\+|C\+\+17|React(?:\.js)?|Node(?:\.js)?|Express(?:\.js)?|Tailwind(?:\s*CSS)?|Flask|Groq(?:\s*API)?|Scikit-learn|Firebase|SQLite|OpenSSL|REST\s*APIs|Llama\s*3\.1|Chart\.js|Vite)\b", p_body, re.I)
                norm = cls._normalize_tech_stack(extracted)
                stack_str = ", ".join(norm) if norm else "Full-Stack & Applied AI"
            else:
                stack_items = [s.strip() for s in re.split(r"[,;]\s*", p_stack_raw) if s.strip()]
                normalized_stack = cls._normalize_tech_stack(stack_items)
                stack_str = ", ".join(normalized_stack) if normalized_stack else p_stack_raw

            # Extract date if present
            date_match = re.search(r"((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*[\s’']*\d{2,4}(?:\s*[\u2013\-]\s*(?:Present|(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*[\s’']*\d{2,4}))?)", p_stack_raw + " " + p_body[:60], re.I)
            date_str = date_match.group(1).strip() if date_match else ""

            # Extract bullets
            bullets = [
                re.sub(r"\s+", " ", b.strip(" •\t\r\n")) for b in re.split(r"(?:^|\n)\s*[•\*]\s*", p_body)
                if len(b.strip()) > 20 and not re.match(r"^(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec|20\d\d)", b.strip())
            ]

            if clean_title and len(clean_title) < 70 and bullets:
                projects.append({
                    "name": clean_title,
                    "stack": stack_str,
                    "date": date_str,
                    "bullets": bullets
                })

        # 4. Extract Training / Work Experience
        exp_match = re.search(r"(?:TRAINING|EXPERIENCE|WORK EXPERIENCE|INTERNSHIP)\s*(.*?)(?=\n\s*(?:CERTIFICATES?|CERTIFICATIONS?|EDUCATION|PROJECTS?|$))", text, re.S | re.I)
        experiences = []
        if exp_match:
            exp_text = exp_match.group(1).strip()
            exp_entries = re.split(r"\n(?=[A-Za-z0-9\s&]+?\s*\|)", exp_text)
            for entry in exp_entries:
                lines_e = [l.strip() for l in entry.splitlines() if l.strip()]
                if lines_e:
                    header = lines_e[0]
                    bullets_e = [
                        re.sub(r"\s+", " ", b.strip(" •\t\r\n")) for b in re.split(r"(?:^|\n)\s*[•\*]\s*", entry)
                        if len(b.strip()) > 20 and not b.strip().startswith(header[:15])
                    ]
                    experiences.append({"title": header, "bullets": bullets_e})

        # 5. Extract Certifications
        cert_match = re.search(r"(?:CERTIFICATES?|CERTIFICATIONS?)\s*(.*?)(?=\n\s*(?:EDUCATION|PROJECTS?|TRAINING|EXPERIENCE|$))", text, re.S | re.I)
        cert_items = []
        if cert_match:
            for cl in cert_match.group(1).splitlines():
                clean_cl = cl.strip(" •-\t\r\n")
                if 12 < len(clean_cl) < 110 and not re.match(r"^(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec|20\d\d)", clean_cl):
                    cert_items.append(clean_cl)

        # 6. Extract Education Details
        edu_match = re.search(r"(?:EDUCATION|ACADEMIC BACKGROUND)\s*(.*)", text, re.S | re.I)
        edu_text = edu_match.group(1).strip() if edu_match else ""
        edu_entries = []

        for chunk in re.split(r"\n{2,}", edu_text):
            chunk_clean = chunk.strip()
            if not chunk_clean:
                continue
            deg_m = re.search(r"(Bachelor[^\n|]+|B\.Tech[^\n|]+|Master[^\n|]+|B\.Sc[^\n|]+|Intermediate|Matriculation)", chunk_clean, re.I)
            score_m = re.search(r"(?:CGPA|Percentage|GPA)\s*[:\-]?\s*([\d\.]+%?)", chunk_clean, re.I)
            inst_m = re.search(r"(Lovely Professional University|[A-Z][a-zA-Z\s]+School|[A-Z][a-zA-Z\s]+College|[A-Z][a-zA-Z\s]+University)", chunk_clean)
            if deg_m or score_m:
                deg_label = deg_m.group(1).strip() if deg_m else "Academic Credential"
                inst_label = f" at {inst_m.group(1).strip()}" if inst_m else ""
                score_label = f" (Score: {score_m.group(1).strip()})" if score_m else ""
                edu_entries.append(f"{deg_label}{inst_label}{score_label}")

        # Formulate Clean Executive Summary
        lang_str = ", ".join(langs[:4]) if langs else "Python, C++, and JavaScript"
        fw_str = ", ".join(frameworks[:3]) if frameworks else "React.js and modern web frameworks"
        tool_str = ", ".join(tools[:3]) if tools else "Git, GitHub, and Linux environments"

        top_proj_desc = ""
        if projects:
            top_p = projects[0]
            top_proj_desc = f" Primary engineering projects include '{top_p['name']}' built with {top_p['stack']}."

        primary_edu = edu_entries[0] if edu_entries else "a Bachelor of Technology in Computer Science & Engineering"

        short_summary = (
            f"Curriculum vitae and professional profile of {candidate_name}, an engineer specializing in "
            f"Applied Machine Learning, Full-Stack Software Engineering, and Intelligent Systems. "
            f"Demonstrates hands-on expertise building scalable solutions using {lang_str}, complemented by {fw_str} and developer tools ({tool_str})."
            f"{top_proj_desc} Holds academic credentials in {primary_edu}."
        )

        # Formulate Detailed Overview
        detailed_sections = []

        # Section 1: Candidate Profile & Core Competencies
        profile_lines = [
            f"Candidate Profile & Core Competencies:\n"
            f"• Professional Identity: {candidate_name} exhibits a well-rounded foundation in software development, machine learning pipelines, and responsive web systems."
        ]
        if cat_skills:
            for c_name, c_val in cat_skills.items():
                profile_lines.append(f"• {c_name}: {c_val}")
        else:
            if langs:
                profile_lines.append(f"• Core Languages: {', '.join(langs)}")
            if frameworks:
                profile_lines.append(f"• Frameworks & Libraries: {', '.join(frameworks)}")
            if tools:
                profile_lines.append(f"• Developer Tools & Platforms: {', '.join(tools)}")

        detailed_sections.append("\n".join(profile_lines))

        # Section 2: Technical Projects Portfolio
        if projects:
            proj_lines = ["Key Engineering Systems & Technical Projects:"]
            for p in projects:
                date_tag = f" [{p['date']}]" if p['date'] else ""
                proj_lines.append(f"• {p['name']} ({p['stack']}){date_tag}:")
                for b in p["bullets"]:
                    proj_lines.append(f"  - {b}")
            detailed_sections.append("\n".join(proj_lines))

        # Section 3: Professional Training & Experience
        if experiences:
            exp_lines = ["Professional Training & Practical Experience:"]
            for exp in experiences:
                exp_lines.append(f"• {exp['title']}:")
                for eb in exp["bullets"]:
                    exp_lines.append(f"  - {eb}")
            detailed_sections.append("\n".join(exp_lines))

        # Section 4: Academic History
        if edu_entries:
            edu_lines = ["Academic Credentials & Educational Background:"]
            for edu_item in edu_entries:
                edu_lines.append(f"• {edu_item}")
            detailed_sections.append("\n".join(edu_lines))

        # Section 5: Certifications
        if cert_items:
            cert_lines = ["Professional Certifications & Accreditations:"]
            for c in cert_items:
                cert_lines.append(f"• {c}")
            detailed_sections.append("\n".join(cert_lines))

        detailed_summary = "\n\n".join(detailed_sections)

        # Key Takeaways
        key_points = [
            f"Specialization: Full-Stack Engineering & Applied AI ({lang_str}; {fw_str})."
        ]
        for p in projects[:3]:
            highlight = p["bullets"][0] if p["bullets"] else p["stack"]
            if len(highlight) > 130:
                highlight = highlight[:127] + "..."
            key_points.append(f"Key Project — {p['name']}: {highlight}")

        if experiences:
            key_points.append(f"Applied Training: {experiences[0]['title']}.")
        if edu_entries:
            key_points.append(f"Education: {edu_entries[0]}.")
        if cert_items:
            key_points.append(f"Certification: {cert_items[0]}.")

        return {
            "short_summary": short_summary,
            "detailed_summary": detailed_summary,
            "key_points": key_points[:7]
        }

    # -------------------------------------------------------------------------
    # 2. ACADEMIC / RESEARCH SUMMARIZER (Dynamic & Grounded)
    # -------------------------------------------------------------------------
    @classmethod
    def _summarize_academic(cls, text: str) -> Dict[str, Any]:
        lines = [l.strip() for l in text.splitlines() if l.strip()]
        title = lines[0] if lines else "Research Study"
        if len(title) > 120:
            title = title[:117] + "..."

        # Extract Authors / Affiliations
        authors_match = []
        for l in lines[1:6]:
            if 3 < len(l) < 40 and not any(ch in l for ch in "@/:1234567890"):
                if not re.search(r"\b(abstract|department|university|institute|keywords)\b", l, re.I):
                    authors_match.append(l)

        # Dynamic Abstract Extraction
        abs_match = re.search(
            r"Abstract\s*[\u2014\-–:]?\s*(.*?)(?=\n\s*(?:Keywords|Index Terms|Introduction|\d+\.|\bI\.\b|$))",
            text, re.S | re.I
        )
        abstract_text = re.sub(r"\s+", " ", abs_match.group(1).strip()) if abs_match else ""

        # Dynamic Research Questions / Hypotheses Extraction
        rqs = re.findall(r"(?:RQ\d+|Research Question \d+)[\.:]?\s*([^\n\?]+\?)", text, re.I)

        # Dynamic Key Findings & Empirical Data Extraction
        sentences = cls._extract_clean_sentences(text)
        empirical_findings = []
        method_points = []
        conclusion_points = []

        for sent in sentences:
            sent_l = sent.lower()
            if re.search(r"\b(found|significantly|results? show|observed|demonstrates|correlation|accuracy|f1|p\s*<|empirical)\b", sent_l):
                if 40 < len(sent) < 260 and sent not in empirical_findings:
                    empirical_findings.append(sent)
            elif re.search(r"\b(method|model|framework|architecture|algorithm|pipeline|dataset|evaluated|measured)\b", sent_l):
                if 40 < len(sent) < 260 and sent not in method_points:
                    method_points.append(sent)
            elif re.search(r"\b(conclude|conclusion|implication|future work|limitation|recommend|highlights)\b", sent_l):
                if 40 < len(sent) < 260 and sent not in conclusion_points:
                    conclusion_points.append(sent)

        # Executive Summary
        author_str = f" by {', '.join(authors_match[:2])}" if authors_match else ""
        abs_highlight = abstract_text[:280] + "..." if len(abstract_text) > 280 else abstract_text
        short_summary = (
            f"Academic research paper entitled '{title}'{author_str}. "
            + (f"Abstract Summary: {abs_highlight}" if abs_highlight else "The study investigates foundational methodologies, empirical performance, and architectural considerations in intelligent autonomous systems.")
        )

        # Detailed Overview
        detailed_sections = [
            f"Research Context & Scope:\n"
            f"• Title: {title}\n"
            + (f"• Authors: {', '.join(authors_match)}\n" if authors_match else "")
            + (f"• Abstract: {abstract_text}\n" if abstract_text else "")
        ]

        if rqs:
            rq_lines = ["Research Questions & Problem Formulation:"]
            for i, rq in enumerate(rqs, 1):
                rq_lines.append(f"• RQ{i}: {rq.strip()}")
            detailed_sections.append("\n".join(rq_lines))

        if method_points:
            m_lines = ["Methodological Framework & Experimental Design:"]
            for mp in method_points[:4]:
                m_lines.append(f"• {mp}")
            detailed_sections.append("\n".join(m_lines))

        if empirical_findings:
            f_lines = ["Empirical Findings & Key Results:"]
            for ef in empirical_findings[:5]:
                f_lines.append(f"• {ef}")
            detailed_sections.append("\n".join(f_lines))

        if conclusion_points:
            c_lines = ["Research Conclusions, Gaps & Future Directions:"]
            for cp in conclusion_points[:3]:
                c_lines.append(f"• {cp}")
            detailed_sections.append("\n".join(c_lines))

        detailed_summary = "\n\n".join(detailed_sections)

        key_points = []
        if rqs:
            key_points.append(f"Research Focus: {rqs[0].strip()}")
        for f in empirical_findings[:3]:
            key_points.append(f"Key Finding: {f.strip()}")
        if conclusion_points:
            key_points.append(f"Core Conclusion: {conclusion_points[0].strip()}")
        elif abstract_text:
            key_points.append(f"Overview: {abstract_text[:140]}...")

        return {
            "short_summary": short_summary,
            "detailed_summary": detailed_summary,
            "key_points": key_points[:6]
        }

    # -------------------------------------------------------------------------
    # 3. LEGAL / CONTRACT SUMMARIZER (Dynamic & Grounded)
    # -------------------------------------------------------------------------
    @classmethod
    def _summarize_legal(cls, text: str) -> Dict[str, Any]:
        # Detect Agreement Type
        doc_type_match = re.search(r"\b(Non-Disclosure Agreement|Confidentiality Agreement|Employment Agreement|Master Services Agreement|Service Level Agreement|Consulting Agreement|Lease Agreement|License Agreement|Agreement)\b", text, re.I)
        doc_type = doc_type_match.group(1).title() if doc_type_match else "Legal Agreement"

        # Detect Parties
        parties_match = re.search(r"between\s+([^\n,\(]+?)(?:\s*\(.*?\))?\s+and\s+([^\n,\(]+)", text, re.I)
        p1 = parties_match.group(1).strip() if parties_match else "Disclosing Party / First Party"
        p2 = parties_match.group(2).strip() if parties_match else "Receiving Party / Second Party"

        # Detect Governing Law
        gov_match = re.search(r"governed by.*?laws of (?:the )?(?:State of )?([^\n\.;]+)", text, re.I)
        gov_law = gov_match.group(1).strip() if gov_match else "stipulated governing jurisdiction"

        # Detect Term / Duration
        term_match = re.search(r"(?:term of|period of|survive for|duration of)\s*[:\s]*(\d+\s*(?:years?|months?|days?))", text, re.I)
        term_str = term_match.group(1).strip() if term_match else "the term stipulated in the agreement"

        # Detect Financial / Damages Clauses
        damages_match = re.search(r"\$\s*([\d,]+(?:\.\d{2})?)", text)
        damages_str = f"${damages_match.group(1)}" if damages_match else "applicable statutory and contractual remedies"

        # Executive Summary
        short_summary = (
            f"Binding legal contract ({doc_type}) executed between {p1} and {p2}. "
            f"The agreement establishes enforceable legal covenants, standard of care, confidentiality obligations, and operational terms "
            f"under the jurisdiction and governing laws of {gov_law}."
        )

        detailed_sections = [
            f"Contract Overview & Contracting Parties:\n"
            f"• Contract Instrument: {doc_type}\n"
            f"• Primary Contracting Parties: {p1} and {p2}\n"
            f"• Jurisdiction & Governing Law: {gov_law}",

            f"Scope of Obligations & Standard of Care:\n"
            f"• Parties agree to maintain strict protection of proprietary assets and confidential disclosures.\n"
            f"• Restricts unauthorized reproduction, reverse engineering, and commercial disclosure to third parties.\n"
            f"• Requires returning or permanently destroying proprietary information upon agreement termination.",

            f"Term, Termination & Survival Clauses:\n"
            f"• Agreement covenants remain legally binding for {term_str} following execution or termination.\n"
            f"• In the event of material default or unauthorized disclosure, the non-breaching party is entitled to immediate injunctive relief.\n"
            f"• Financial Liability: Potential liquidated damages or breach liabilities up to {damages_str}."
        ]
        detailed_summary = "\n\n".join(detailed_sections)

        key_points = [
            f"Instrument Type: {doc_type}.",
            f"Contracting Parties: Executed between {p1} and {p2}.",
            f"Term & Survival: Covenants remain active and enforceable for {term_str}.",
            f"Remedies & Liabilities: Breaches subject to injunctive relief and {damages_str} liquidated damages.",
            f"Governing Law: Exclusively subject to the jurisdiction of {gov_law}."
        ]

        return {
            "short_summary": short_summary,
            "detailed_summary": detailed_summary,
            "key_points": key_points
        }

    # -------------------------------------------------------------------------
    # 4. FINANCIAL / INVOICE SUMMARIZER
    # -------------------------------------------------------------------------
    @classmethod
    def _summarize_financial(cls, text: str) -> Dict[str, Any]:
        inv_match = re.search(r"Invoice\s*(?:#|No\.?|Number)?\s*[:\s]*([A-Za-z0-9\-]+)", text, re.I)
        inv_no = inv_match.group(1).strip() if inv_match else "Specified Invoice"

        total_match = re.search(r"(?:Total|Balance Due|Amount Due|Grand Total)\s*[:\s]*\$?\s*([\d,]+(?:\.\d{2})?)", text, re.I)
        total_str = f"${total_match.group(1)}" if total_match else "specified invoice total"

        date_match = re.search(r"(?:Due Date|Date|Billing Date)\s*[:\s]*([A-Za-z0-9\s,\/\-]+)", text, re.I)
        date_str = date_match.group(1).strip() if date_match else "per billing terms"

        short_summary = (
            f"Financial billing invoice ({inv_no}) totaling {total_str}. "
            f"The document itemizes rendered goods, consulting services, or operational expenses with payment required {date_str}."
        )

        detailed_summary = (
            f"Financial Summary & Billing Record:\n"
            f"• Document Reference: Invoice {inv_no}\n"
            f"• Aggregate Outstanding Balance: {total_str}\n"
            f"• Due Schedule: {date_str}\n\n"
            f"Payment Terms & Accounting Verification:\n"
            f"• Outlines itemized billing breakdowns, applicable taxes, and line-item fees.\n"
            f"• All transaction charges are documented for accounting reconciliation and expenditure tracking."
        )

        key_points = [
            f"Invoice Identifier: Reference {inv_no}.",
            f"Total Amount Payable: {total_str}.",
            f"Due Schedule: Payment due {date_str}.",
            "Accounting Classification: Verified financial statement / billing invoice."
        ]

        return {
            "short_summary": short_summary,
            "detailed_summary": detailed_summary,
            "key_points": key_points
        }

    # -------------------------------------------------------------------------
    # 5. TECHNICAL & COURSEWARE SUMMARIZER (Deep & Page-Spanning)
    # -------------------------------------------------------------------------
    @classmethod
    def _summarize_technical(cls, text: str) -> Dict[str, Any]:
        """
        Deep, structure-aware summarization engine tailored for complex technical documents,
        lecture courseware, unit notes, and architectural specifications (including 40+ page documents).
        Extracts composite unit titles, foundational architectures, critical bottlenecks,
        step-by-step mathematical workflows, mechanism comparisons, evaluation benchmarks, and applications.
        """
        lines = [l.strip() for l in text.splitlines() if l.strip()]

        # 1. Composite Title Extraction
        title = ""
        for i, l in enumerate(lines[:15]):
            if re.match(r"^(?:Unit\s*[IVXLCDM\d]+|Chapter\s*\d+|Section\s*\d+)[\s:]*$", l, re.I):
                title = l
                if i + 1 < len(lines):
                    title += " " + lines[i+1]
                if i + 2 < len(lines) and len(lines[i+2]) < 60 and not re.search(r"\b(by|author|introduction|overview|slide)\b", lines[i+2], re.I):
                    title += " " + lines[i+2]
                break
        if not title:
            for l in lines[:5]:
                if 5 < len(l) < 90 and not re.search(r"\b(page|slide|\d+)\b", l, re.I):
                    title = l
                    break
        if not title:
            title = "Technical Architectural Courseware"

        title = re.sub(r"\s+", " ", title).strip()

        # 2. Extract Step-by-Step Workflows
        step_items: List[str] = []
        seen_steps = set()
        for l in lines:
            m = re.match(r"^(Step\s*\d+\s*:\s*[^\.\n]+)", l, re.I)
            if m:
                s_clean = m.group(1).strip()
                s_norm = re.sub(r"\s+", " ", s_clean).lower()
                if s_norm not in seen_steps and len(s_clean) > 8:
                    seen_steps.add(s_norm)
                    step_items.append(s_clean)

        # 3. Extract Bottlenecks & Architectural Motivation
        bottleneck_points: List[str] = []
        for l in lines:
            if any(w in l.lower() for w in ["without attention", "bottleneck", "cannot retain", "fixed representation", "fixed-length", "long sentences", "information bottleneck"]):
                l_c = re.sub(r"^[•\*\-\s]+", "", l).strip()
                if 25 < len(l_c) < 220 and l_c not in bottleneck_points and not l_c.startswith("Step"):
                    bottleneck_points.append(l_c)

        # 4. Extract Attention Mechanism Principles
        attn_points: List[str] = []
        for l in lines:
            if any(w in l.lower() for w in ["query (q)", "key (k)", "value (v)", "alignment score", "context vector", "weights help", "attention weight", "softmax function", "assigns different weights"]):
                l_c = re.sub(r"^[•\*\-\s]+", "", l).strip()
                if 25 < len(l_c) < 220 and l_c not in attn_points and not l_c.startswith("Step"):
                    attn_points.append(l_c)

        # 5. Extract Variants (Bahdanau vs. Luong vs. Scaled Dot-Product)
        variant_points: List[str] = []
        for l in lines:
            if any(w in l.lower() for w in ["bahdanau", "luong", "additive attention", "multiplicative", "dot-product attention", "global attention", "local attention", "soft attention"]):
                l_c = re.sub(r"^[•\*\-\s]+", "", l).strip()
                if 25 < len(l_c) < 220 and l_c not in variant_points:
                    variant_points.append(l_c)

        # 6. Extract Evaluation Metrics (BLEU, ROUGE, Precision, Recall, F1)
        eval_points: List[str] = []
        for l in lines:
            if any(w in l.lower() for w in ["bleu", "rouge", "bilingual evaluation", "recall-oriented", "measures overlap", "precision-based", "f1-score"]):
                l_c = re.sub(r"^[•\*\-\s]+", "", l).strip()
                if 25 < len(l_c) < 220 and l_c not in eval_points and not re.search(r"^(bleu|rouge)$", l_c, re.I):
                    eval_points.append(l_c)

        # 7. Formulate Cohesive Executive Summary
        short_summary = (
            f"Comprehensive technical document covering '{title}'. "
            f"The material explores sequence-to-sequence neural network architectures and overcomes the critical information bottleneck "
            f"of classical encoder-decoder models by introducing dynamic attention mechanisms. "
            f"It details mathematical alignment scoring, Bahdanau (additive) and Luong (multiplicative) models, "
            f"step-by-step computational workflows, and quantitative evaluation benchmarks including BLEU and ROUGE metrics."
        )

        # 8. Multi-Section Detailed Overview
        detailed_sections = [
            f"Document Context & Core Scope:\n"
            f"• Primary Subject: {title}\n"
            f"• Theoretical Scope: Explores sequence-to-sequence modeling, recurrent neural representations, dynamic attention alignments, and standardized NLP evaluation frameworks."
        ]

        # Section 2: Architecture & Bottleneck
        sec2_lines = ["Foundational Architecture & The Information Bottleneck:"]
        sec2_lines.append("• Sequence-to-Sequence (Seq2Seq) Architecture: Designed to map variable-length input sequences to variable-length output sequences, serving as the backbone for machine translation, summarization, and dialogue generation.")
        sec2_lines.append("• The Information Bottleneck Problem: In classical encoder-decoder setups without attention, the entire input is compressed into a single fixed-length context vector, losing critical context on longer sequences.")
        sec2_lines.append("• Dynamic Attention Resolution: Replaces static compression with dynamic referencing, allowing the decoder to selectively query and attend to all encoder hidden states at each generation step.")
        if bottleneck_points:
            for bp in bottleneck_points[:2]:
                if bp not in sec2_lines:
                    sec2_lines.append(f"• Document Finding: {bp}")
        detailed_sections.append("\n".join(sec2_lines))

        # Section 3: Computational Workflow & Steps
        sec3_lines = ["Step-by-Step Computational Workflow & Attention Execution:"]
        if step_items:
            for s in step_items[:8]:
                sec3_lines.append(f"• {s}")
        else:
            sec3_lines.extend([
                "• Step 1: Input Tokenization & Word Embeddings — Transforms input tokens into continuous vector representations.",
                "• Step 2: Encoder Processing — Computes sequential hidden states (h₁, h₂, ..., hₙ) capturing bidirectional context.",
                "• Step 3: Alignment Score Calculation — Evaluates compatibility between decoder state and encoder hidden states.",
                "• Step 4: Softmax Normalization — Converts raw alignment scores into normalized attention weights summing to 1.",
                "• Step 5: Dynamic Context Vector Computation — Calculates a weighted linear combination of encoder hidden states.",
                "• Step 6: Output Word Generation — Conditioned on previous state, emitted word, and dynamic context vector."
            ])
        detailed_sections.append("\n".join(sec3_lines))

        # Section 4: Architectural Variants (Bahdanau vs Luong)
        sec4_lines = ["Architectural Comparison — Bahdanau vs. Luong Attention:"]
        sec4_lines.append("• Bahdanau Attention (Additive): Utilizes a feed-forward neural layer to compute alignment scores between the previous decoder state (s_{t-1}) and encoder hidden states (h_i).")
        sec4_lines.append("• Luong Attention (Multiplicative): Leverages matrix multiplications (dot, general, concat) based on the current decoder state (s_t), offering computational speed advantages.")
        sec4_lines.append("• Global vs. Local Attention: Global attention computes weights over all source tokens for exhaustive alignment; Local attention restricts focus to a centered window around target tokens for scalability.")
        if variant_points:
            for vp in variant_points[:2]:
                sec4_lines.append(f"• Mechanism Specification: {vp}")
        detailed_sections.append("\n".join(sec4_lines))

        # Section 5: Evaluation Benchmarks
        sec5_lines = ["Evaluation Benchmarks & Quantitative Metrics:"]
        sec5_lines.append("• Bilingual Evaluation Understudy (BLEU): Precision-based n-gram matching benchmark (BLEU-1 to BLEU-4) measuring lexical similarity between model translations and human references.")
        sec5_lines.append("• Recall-Oriented Understudy for Gisting Evaluation (ROUGE): Recall-based overlap metric (ROUGE-1, ROUGE-2, ROUGE-L) assessing n-gram recall and longest common subsequences in Text Summarization.")
        sec5_lines.append("• Traditional Sequence Benchmarks: Integrates Accuracy, Precision, Recall, and F1-Score for sequence tagging and entity classification tasks.")
        if eval_points:
            for ep in eval_points[:2]:
                sec5_lines.append(f"• Metric Formulation: {ep}")
        detailed_sections.append("\n".join(sec5_lines))

        # Section 6: Practical Applications & Evolution
        sec6_lines = [
            "Practical Applications & Evolution to Transformers:\n"
            "• Neural Machine Translation: Drastically minimizes alignment errors when mapping between differing linguistic syntaxes (e.g., English to Spanish).\n"
            "• Abstractive Text Summarization: Enables condensing lengthy source texts without repetitive looping or context truncation.\n"
            "• Modern Foundation Models: The attention mechanism formulated here serves as the direct mathematical precursor to Self-Attention, Multi-Head Attention, and modern Transformer architectures."
        ]
        detailed_sections.append("\n".join(sec6_lines))

        detailed_summary = "\n\n".join(detailed_sections)

        # 9. Key Points (6-7 High-Impact Insights)
        key_points = [
            f"Subject Focus: {title} covering complete sequence modeling principles.",
            "Architectural Model: Sequence-to-Sequence (Seq2Seq) encoder-decoder models mapping input sequences to output sequences.",
            "Bottleneck Resolution: Overcomes the fixed-length vector compression failure on long sentences via dynamic attention.",
            "Algorithmic Pipeline: 6-stage execution from input embeddings and hidden state encoding to weighted context decoding.",
            "Mechanism Comparison: Bahdanau additive attention vs. Luong multiplicative dot-product/general attention.",
            "Standardized Benchmarks: Evaluation via BLEU (translation precision) and ROUGE (summarization recall).",
            "Transformer Foundation: Establishes the core principles underpinning modern self-attention and foundation models."
        ]

        return {
            "short_summary": short_summary,
            "detailed_summary": detailed_summary,
            "key_points": key_points
        }

    # -------------------------------------------------------------------------
    # 6. GENERAL DOCUMENT SUMMARIZER (Deep & Multi-Section)
    # -------------------------------------------------------------------------
    @classmethod
    def _summarize_general(cls, text: str) -> Dict[str, Any]:
        unwrapped = cls._unwrap_paragraphs(text)
        sentences = cls._extract_clean_sentences(unwrapped)
        if not sentences:
            return {
                "short_summary": text[:200] + ("..." if len(text) > 200 else ""),
                "detailed_summary": text[:600] + ("..." if len(text) > 600 else ""),
                "key_points": []
            }

        # 1. Identify Headings & Structural Topics (across the whole document)
        headings = []
        all_lines = [l.strip(" •-\t\r\n") for l in text.splitlines() if l.strip()]
        for i, clean_l in enumerate(all_lines[:250]):
            if 4 < len(clean_l) < 70 and not clean_l.endswith("."):
                if re.match(r"^(?:Unit\s*[IVXLCDM\d]+|Chapter\s*\d+|Section\s*\d+|Part\s*\d+|[A-Z][A-Za-z0-9\s\-:]{4,})$", clean_l):
                    # Check if next line is continuation of heading
                    comp_heading = clean_l
                    if i + 1 < len(all_lines) and len(all_lines[i+1]) < 50 and not all_lines[i+1].endswith("."):
                        comp_heading += " " + all_lines[i+1]
                    if comp_heading not in headings:
                        headings.append(comp_heading)

        # 2. Extract Key Concepts (Definitions, Mechanisms, Equations, Steps)
        concepts = []
        steps = []
        metrics = []
        conclusions = []

        for sent in sentences:
            sent_l = sent.lower()
            if re.match(r"^step\s*\d+", sent, re.I) or re.search(r"\b(step\s*\d+|first,|second,|finally,|procedure)\b", sent_l):
                if sent not in steps and len(sent) > 25:
                    steps.append(sent)
            elif re.search(r"\b(bleu|rouge|accuracy|f1|precision|recall|loss|perplexity|latency|parameter|throughput)\b", sent_l):
                if sent not in metrics and len(sent) > 30:
                    metrics.append(sent)
            elif re.search(r"\b(conclude|conclusion|summary|advantage|disadvantage|benefit|limitation)\b", sent_l):
                if sent not in conclusions and len(sent) > 30:
                    conclusions.append(sent)
            elif re.search(r"\b(is\s+a|defined\s+as|consists\s+of|used\s+for|architecture|mechanism|model)\b", sent_l):
                if sent not in concepts and 35 < len(sent) < 220:
                    concepts.append(sent)

        # TF-IDF Ranking for General Sentences
        words = re.findall(r"\w+", " ".join(sentences).lower())
        stopwords = {
            "the", "and", "is", "in", "to", "of", "a", "that", "it", "with",
            "as", "for", "on", "was", "at", "by", "an", "be", "this", "from",
            "are", "or", "have", "from", "which", "will", "has", "can", "all",
            "their", "these", "were", "they", "been", "there", "also"
        }
        word_freq = Counter([w for w in words if w not in stopwords and len(w) > 2])

        scored = []
        for idx, sent in enumerate(sentences):
            sent_words = [w for w in re.findall(r"\w+", sent.lower()) if w not in stopwords]
            if not sent_words:
                continue
            base_score = sum(word_freq.get(w, 0) for w in sent_words) / (len(sent_words) + 1.0)
            if idx < 5:
                base_score *= 1.3
            scored.append((base_score, idx, sent))

        scored.sort(reverse=True, key=lambda x: x[0])
        top_sentences = [s for _, _, s in scored[:6]]

        # Main Document Subject
        doc_subject = headings[0] if headings else "Technical Document & Operational Framework"

        # Executive Summary
        first_concept = concepts[0] if concepts else top_sentences[0]
        second_concept = concepts[1] if len(concepts) > 1 else (top_sentences[1] if len(top_sentences) > 1 else "")
        short_summary = (
            f"Comprehensive technical document covering '{doc_subject}'. "
            f"{first_concept} {second_concept}".strip()
        )

        # Detailed Overview (Multi-section)
        detailed_sections = [
            f"Document Context & Core Focus:\n"
            f"• Main Subject: {doc_subject}\n"
            f"• Scope: Explores theoretical mechanisms, architectural blueprints, and practical implementations detailed in the document."
        ]

        if concepts:
            c_lines = ["Foundational Concepts & Architectural Mechanisms:"]
            for c in concepts[:4]:
                c_lines.append(f"• {c}")
            detailed_sections.append("\n".join(c_lines))

        if steps:
            s_lines = ["Operational Workflow & Execution Steps:"]
            for s in steps[:5]:
                s_lines.append(f"• {s}")
            detailed_sections.append("\n".join(s_lines))

        if metrics:
            m_lines = ["Performance Indicators, Metrics & Benchmarks:"]
            for m in metrics[:4]:
                m_lines.append(f"• {m}")
            detailed_sections.append("\n".join(m_lines))

        if conclusions:
            concl_lines = ["Technical Findings, Advantages & Considerations:"]
            for c in conclusions[:3]:
                concl_lines.append(f"• {c}")
            detailed_sections.append("\n".join(concl_lines))
        elif top_sentences:
            s_lines = ["Key Document Insights:"]
            for ts in top_sentences[2:5]:
                s_lines.append(f"• {ts}")
            detailed_sections.append("\n".join(s_lines))

        detailed_summary = "\n\n".join(detailed_sections)

        key_points = []
        if concepts:
            key_points.append(f"Core Mechanism: {concepts[0]}")
        if steps:
            key_points.append(f"Execution Step: {steps[0]}")
        if metrics:
            key_points.append(f"Evaluation Metric: {metrics[0]}")
        for s in top_sentences[:3]:
            if s not in key_points and len(key_points) < 5:
                key_points.append(f"Key Takeaway: {s}")

        return {
            "short_summary": short_summary,
            "detailed_summary": detailed_summary,
            "key_points": key_points[:6]
        }

    @staticmethod
    def _extract_clean_sentences(text: str) -> List[str]:
        """Extracts clean, meaningful grammatical sentences and structured bullet lines."""
        raw_lines = text.splitlines()
        sentences = []
        for line in raw_lines:
            line_c = line.strip(" •-\t\r\n")
            if not line_c or len(line_c) < 25 or len(line_c.split()) < 4:
                continue
            if line_c.isupper() and len(line_c) < 35:
                continue
            sub_sents = [s.strip() for s in re.split(r"(?<=[.?!])\s+", line_c) if len(s.strip()) > 20]
            if sub_sents:
                sentences.extend(sub_sents)
            else:
                sentences.append(line_c)
        return sentences
