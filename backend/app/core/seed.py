import asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.profile import SkillCategory, Skill, SkillAlias
from app.core.database import async_session_factory

async def seed_skills(db: AsyncSession):
    categories = {
        "Languages": ["Python", "SQL", "C", "C++", "Java", "HTML", "CSS"],
        "Machine Learning": ["PyTorch", "TensorFlow", "Scikit-learn", "XGBoost", "CatBoost", "SHAP"],
        "Data Science": ["NumPy", "Pandas", "Matplotlib", "Seaborn"],
        "Web Development": ["FastAPI", "Streamlit"],
        "Tools": ["Git", "GitHub", "Jupyter Notebook"],
        "Soft Skills": [
            "Communication",
            "Leadership",
            "Teamwork",
            "Problem Solving",
            "Critical Thinking",
            "Adaptability",
            "Time Management",
            "Presentation",
        ],
    }
    
    aliases = {
        "Python": ["python3", "py"],
        "C++": ["cpp", "c plus plus"],
        "PyTorch": ["torch"],
        "TensorFlow": ["tf"],
        "Scikit-learn": ["sklearn", "scikit learn"],
        "NumPy": ["numpy"],
        "Pandas": ["pandas"],
        "Matplotlib": ["matplotlib"],
        "Seaborn": ["seaborn"],
        "FastAPI": ["fast-api"],
        "GitHub": ["git hub"],
        "Jupyter Notebook": ["jupyter", "jupyter-notebook"],
        "Communication": ["verbal communication", "written communication", "interpersonal communication"],
        "Leadership": ["team leadership", "mentorship"],
        "Teamwork": ["collaboration", "cross-functional collaboration"],
        "Problem Solving": ["problem-solving", "troubleshooting", "analytical skills"],
        "Critical Thinking": ["analytical thinking", "critical evaluation"],
        "Adaptability": ["flexibility", "agility"],
        "Time Management": ["prioritization", "task management"],
        "Presentation": ["public speaking", "presenting"],
    }

    # Insert Categories
    cat_objs = {}
    for cat_name in categories.keys():
        stmt = select(SkillCategory).where(SkillCategory.name == cat_name)
        res = await db.execute(stmt)
        cat = res.scalar_one_or_none()
        if not cat:
            cat = SkillCategory(name=cat_name, slug=cat_name.lower().replace(' ', '-'), description=f"{cat_name} skills")
            db.add(cat)
            await db.flush()
        cat_objs[cat_name] = cat

    # Insert Skills
    for cat_name, skills in categories.items():
        cat_id = cat_objs[cat_name].id
        for skill_name in skills:
            # Check normalized_name
            norm_name = skill_name.strip().lower()
            stmt = select(Skill).where(Skill.normalized_name == norm_name)
            res = await db.execute(stmt)
            skill = res.scalar_one_or_none()
            if not skill:
                skill = Skill(
                    category_id=cat_id,
                    name=skill_name,
                    normalized_name=norm_name,
                    description=f"{skill_name} skill"
                )
                db.add(skill)
                await db.flush()
            
            # Insert Aliases
            skill_aliases = aliases.get(skill_name, [])
            for alias_name in skill_aliases:
                astmt = select(SkillAlias).where(SkillAlias.alias == alias_name.lower())
                ares = await db.execute(astmt)
                alias = ares.scalar_one_or_none()
                if not alias:
                    alias = SkillAlias(skill_id=skill.id, alias=alias_name.lower(), normalized_alias=alias_name.lower())
                    db.add(alias)
                    
    await db.commit()

async def run_seed():
    async with async_session_factory() as db:
        await seed_skills(db)

if __name__ == "__main__":
    asyncio.run(run_seed())
