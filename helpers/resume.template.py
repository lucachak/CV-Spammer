from dataclasses import dataclass, field, asdict
from typing import List, Dict, Optional, Any

# ==========================================
# 1. DEFINIÇÃO DAS ESTRUTURAS (DATACLASSES)
# ==========================================

@dataclass
class Contact:
    phone: str
    email: str

@dataclass
class PersonalInformation:
    name: str
    title: str
    location: str
    citizenship: str
    contact: Contact
    links: List[str] = field(default_factory=list)

@dataclass
class TechnicalSkills:
    languages_and_frameworks: List[str] = field(default_factory=list)
    infrastructure_and_tools: List[str] = field(default_factory=list)
    security_and_practices: List[str] = field(default_factory=list)

@dataclass
class Experience:
    role: str
    period: str
    location: Optional[str] = None
    institution: Optional[str] = None
    bullet_points: List[str] = field(default_factory=list)

@dataclass
class Project:
    name: str
    technologies: List[str] = field(default_factory=list)
    bullet_points: List[str] = field(default_factory=list)

@dataclass
class EducationDetails:
    awards: List[str] = field(default_factory=list)
    extracurriculars: List[str] = field(default_factory=list)

@dataclass
class Education:
    degree: str
    institution: str
    period: str
    status: str
    details: EducationDetails

@dataclass
class Resume:
    personal_information: PersonalInformation
    summary: str
    technical_skills: TechnicalSkills
    experience: List[Experience] = field(default_factory=list)
    projects: List[Project] = field(default_factory=list)
    education: Optional[Education] = None
    certifications_and_continuous_learning: List[str] = field(default_factory=list)
    languages: Dict[str, str] = field(default_factory=dict)
    years_of_experience: Dict[str, int] = field(default_factory=dict)

    # --- Métodos de Flexibilidade e Atualização ---

    def to_dict(self) -> Dict[str, Any]:
        """Exporta o currículo atualizado para um dicionário Python."""
        return asdict(self)

    def add_experience(self, role: str, period: str, location: Optional[str] = None, 
                       institution: Optional[str] = None, bullet_points: List[str] = None):
        """Adiciona uma nova experiência profissional na lista."""
        self.experience.append(
            Experience(role=role, period=period, location=location, 
                       institution=institution, bullet_points=bullet_points or [])
        )

    def add_project(self, name: str, technologies: List[str], bullet_points: List[str]):
        """Adiciona um novo projeto na lista."""
        self.projects.append(
            Project(name=name, technologies=technologies, bullet_points=bullet_points)
        )

    def add_skill(self, category: str, skill_name: str):
        """Adiciona uma skill específica na categoria desejada."""
        if category == "languages_and_frameworks":
            self.technical_skills.languages_and_frameworks.append(skill_name)
        elif category == "infrastructure_and_tools":
            self.technical_skills.infrastructure_and_tools.append(skill_name)
        elif category == "security_and_practices":
            self.technical_skills.security_and_practices.append(skill_name)
        else:
            raise ValueError("Categoria de skill inválida.")

# ==========================================
# 2. SEUS DADOS INJETADOS NA CLASSE (TEMPLATE)
# ==========================================

meu_curriculo = Resume(
    personal_information=PersonalInformation(
        name="YOUR NAME",
        title="Your Professional Title",
        location="City, State, Country",
        citizenship="Your Citizenship/s",
        contact=Contact(
            phone="+00 00 00000-0000",
            email="your.email@example.com"
        ),
        links=[
            "github.com/yourusername",
            "linkedin.com/in/yourprofile"
        ]
    ),
    summary=(
        "A brief but compelling professional summary or bio. "
        "Explain your main areas of expertise, key strengths, "
        "and what drives your technical background."
    ),
    technical_skills=TechnicalSkills(
        languages_and_frameworks=[
            "Python (Django, FastAPI)",
            "SQL",
            "JavaScript"
        ],
        infrastructure_and_tools=[
            "Docker",
            "Linux",
            "Git"
        ],
        security_and_practices=[
            "REST API Security",
            "OWASP principles",
            "Clean Architecture"
        ]
    ),
    experience=[
        Experience(
            role="Software Engineer",
            location="Remote",
            period="January 2023 - Present",
            bullet_points=[
                "Architected and deployed custom web applications and microservices using modern web frameworks.",
                "Automated critical business processes using custom scripting tools, increasing workflow efficiency.",
                "Collaborated in design and code reviews to enforce software reliability and quality standards."
            ]
        )
    ],
    projects=[
        Project(
            name="Project Example",
            technologies=["Python", "FastAPI"],
            bullet_points=[
                "Designed and implemented optimized web APIs capable of handling high transaction throughput.",
                "Implemented secure authentication and dynamic data serialization features."
            ]
        )
    ],
    education=Education(
        degree="Bachelor of Science in Computer Science",
        institution="Your University Name",
        period="Sept 2020 - June 2024",
        status="Completed",
        details=EducationDetails(
            awards=[
                "Academic Excellence Scholarship"
            ],
            extracurriculars=[
                "Competitive programming participant"
            ]
        )
    ),
    certifications_and_continuous_learning=[
        "Certification Course 1",
        "Certification Course 2"
    ],
    languages={
        "Portuguese": "Native",
        "English": "Fluent",
        "Spanish": "Basic"
    },
    years_of_experience={
        "python": 3.0,
        "fastapi": 2.0,
        "django": 2.5,
        "docker": 1.0,
        "linux": 5.0,
        "git": 4.0,
        "rest api": 3.0,
        "clean architecture": 2.0
    }
)
