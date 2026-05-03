import os
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from sqlalchemy import and_  # noqa: E402

from app.db.base import Base  # noqa: E402
from app.db.session import SessionLocal, engine  # noqa: E402
from app.models import Prompt, PromptCategory, UserLevel  # noqa: E402

PROMPTS = [
    # Beginner (10)
    (UserLevel.beginner, PromptCategory.opinion, "Do you think homework should be optional in schools? Why or why not?"),
    (UserLevel.beginner, PromptCategory.opinion, "Is it better to study in the morning or at night? Explain your preference."),
    (UserLevel.beginner, PromptCategory.opinion, "Should people use cashless payments for everything?"),
    (UserLevel.beginner, PromptCategory.narration, "Describe a memorable day from your school life."),
    (UserLevel.beginner, PromptCategory.narration, "Talk about a time you helped someone and how it felt."),
    (UserLevel.beginner, PromptCategory.narration, "Describe your daily routine and one habit you want to improve."),
    (UserLevel.beginner, PromptCategory.explanation, "Explain how to prepare your favorite meal step by step."),
    (UserLevel.beginner, PromptCategory.explanation, "Explain why learning English can be useful in everyday life."),
    (UserLevel.beginner, PromptCategory.argument, "Argue whether online classes are better than offline classes."),
    (UserLevel.beginner, PromptCategory.argument, "Argue for or against having uniforms in colleges."),
    # Intermediate (10)
    (UserLevel.intermediate, PromptCategory.opinion, "Should social media platforms be held responsible for misinformation?"),
    (UserLevel.intermediate, PromptCategory.opinion, "Do you think remote work improves productivity? Why?"),
    (UserLevel.intermediate, PromptCategory.opinion, "Should universities prioritize skills over grades in admissions?"),
    (UserLevel.intermediate, PromptCategory.narration, "Share a challenge you faced while learning a new skill and how you handled it."),
    (UserLevel.intermediate, PromptCategory.narration, "Describe a team project where communication made a big difference."),
    (UserLevel.intermediate, PromptCategory.narration, "Talk about an unexpected problem you solved under pressure."),
    (UserLevel.intermediate, PromptCategory.explanation, "Explain how climate change affects local communities."),
    (UserLevel.intermediate, PromptCategory.explanation, "Explain the pros and cons of using AI tools in education."),
    (UserLevel.intermediate, PromptCategory.argument, "Argue whether governments should regulate AI-generated content."),
    (UserLevel.intermediate, PromptCategory.argument, "Argue for or against a four-day work week."),
    # Advanced (10)
    (UserLevel.advanced, PromptCategory.opinion, "Should algorithmic systems used in hiring be auditable by law?"),
    (UserLevel.advanced, PromptCategory.opinion, "Is economic growth compatible with long-term environmental sustainability?"),
    (UserLevel.advanced, PromptCategory.opinion, "Should personal data ownership be treated as a fundamental digital right?"),
    (UserLevel.advanced, PromptCategory.narration, "Narrate a complex professional conflict and how you negotiated a resolution."),
    (UserLevel.advanced, PromptCategory.narration, "Describe a leadership decision you disagreed with and how you responded constructively."),
    (UserLevel.advanced, PromptCategory.narration, "Narrate a moment when your viewpoint changed after strong evidence."),
    (UserLevel.advanced, PromptCategory.explanation, "Explain how monetary policy decisions can influence employment and inflation."),
    (UserLevel.advanced, PromptCategory.explanation, "Explain the trade-offs between privacy, security, and convenience in digital platforms."),
    (UserLevel.advanced, PromptCategory.argument, "Argue whether universal basic income is a viable long-term policy."),
    (UserLevel.advanced, PromptCategory.argument, "Argue for or against strict global governance of frontier AI systems."),
]


def seed() -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    inserted = 0

    try:
        for level, category, text in PROMPTS:
            exists = (
                db.query(Prompt)
                .filter(
                    and_(
                        Prompt.level == level,
                        Prompt.category == category,
                        Prompt.text == text,
                    )
                )
                .first()
            )
            if exists:
                continue

            db.add(Prompt(level=level, category=category, text=text))
            inserted += 1

        db.commit()
        print(f"Seed complete. Inserted {inserted} prompts.")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
