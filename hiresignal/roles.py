"""Job-title normalisation into role families and seniority levels."""
from __future__ import annotations

import re

# Order matters: the first family whose pattern matches wins.
FAMILIES = [
    ("Engineering Management", r"engineering manager|head of (?:engineering|data|ai|ml|product|platform)|"
                               r"\bvp\b|vice president|\bcto\b|director of eng|chief technology"),
    ("ML / AI Engineering", r"machine learning|\bml\b|\bai\b|\bllm\b|deep learning|applied scientist|"
                            r"research (?:scientist|engineer)|computer vision|\bnlp\b|genai|mlops|perception"),
    ("Data Science & Analytics", r"data scien|data analy|analytics|business intelligence|\bbi\b|statistician|quant"),
    ("Data Engineering", r"data engineer|analytics engineer|\betl\b|data platform|data architect"),
    ("Embedded & Hardware", r"embedded|firmware|hardware|fpga|asic|electrical|electronics|\brf\b|robotics|"
                            r"mechatronic|silicon|verification engineer|pcb|controls engineer|avionics"),
    ("DevOps / SRE / Cloud", r"devops|\bsre\b|site reliability|platform engineer|infrastructure|cloud engineer|"
                             r"cloud architect|systems engineer|reliability|devsecops|kubernetes"),
    ("Security", r"security|appsec|penetration|\bsoc\b analyst|cyber"),
    ("Mobile", r"\bios\b|android|mobile|react native|flutter"),
    ("Frontend", r"front[\s\-]?end|frontend|\bui engineer|web developer|javascript developer|react developer"),
    ("Full-stack", r"full[\s\-]?stack"),
    ("Backend", r"back[\s\-]?end|backend|\bapi\b|server[\s\-]side|java developer|python developer|"
                r"golang|\bgo engineer|ruby|php|\.net|rails|django|node"),
    ("QA / Test", r"\bqa\b|quality assurance|\btest(?:ing)? engineer|\bsdet\b|tester|automation engineer"),
    ("Product & Design", r"product manager|product owner|product designer|\bux\b|\bui\b|designer|design lead"),
    ("Software Engineering (general)", r"software|developer|engineer|programmer|\bswe\b|architect|founding|tech lead|"
                                       r"entwickler|informatiker"),
    ("Business & Operations", r"sales|account (?:executive|manager)|marketing|customer success|support|"
                              r"recruit|talent|\bhr\b|finance|accountant|operations|consultant|content|"
                              r"business development|sachbearbeiter|kaufm|vertrieb|berater|buchhalt|"
                              r"project manager|program manager|projektleiter|specialist|analyst|director|"
                              r"administrat|coordinator|assistant|payroll|legal|counsel|writer|editor|"
                              r"mitarbeiter|referent|manager|executive|officer|representative"),
]
FAMILIES = [(name, re.compile(p, re.I)) for name, p in FAMILIES]

SENIORITY = [
    ("Intern", r"\bintern(ship)?\b|praktikum|werkstudent|working student|trainee|apprentice|ausbildung"),
    ("Lead / Manager", r"\blead\b|\bhead\b|manager|director|\bvp\b|chief|\bcto\b|leiter"),
    ("Staff / Principal", r"\bstaff\b|principal|distinguished|architect"),
    ("Senior", r"\bsenior\b|\bsr\.?\b|\biii\b|\bsenior\b"),
    ("Junior", r"\bjunior\b|\bjr\.?\b|entry[\s\-]level|graduate|new grad|\bassociate\b|\bi\b$"),
]
SENIORITY = [(name, re.compile(p, re.I)) for name, p in SENIORITY]


def role_family(title: str | None) -> str:
    t = title or ""
    for name, rg in FAMILIES:
        if rg.search(t):
            return name
    return "Other"


def seniority(title: str | None) -> str:
    t = title or ""
    for name, rg in SENIORITY:
        if rg.search(t):
            return name
    return "Mid / Unspecified"
