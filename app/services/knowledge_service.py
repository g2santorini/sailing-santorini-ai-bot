from pathlib import Path


def get_company_knowledge() -> str:
    try:
        project_root = Path(__file__).resolve().parent.parent.parent
        knowledge_file = project_root / "company_knowledge.md"

        if not knowledge_file.exists():
            print("❌ company_knowledge.md NOT FOUND")
            return ""

        content = knowledge_file.read_text(encoding="utf-8").strip()

        if not content:
            print("⚠️ company_knowledge.md is EMPTY")
            return ""

        return content

    except Exception as e:
        print(f"❌ Error loading company knowledge: {e}")
        return ""