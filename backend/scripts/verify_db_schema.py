"""
Script to verify the database schema matches the SQLAlchemy models.
This will show which columns exist in the sessions table.

Usage:
    python -m scripts.verify_db_schema
"""

from sqlalchemy import text, inspect
from app.db.session import engine
from app.models.entities import Session


def verify_sessions_table():
    """Verify the sessions table schema."""
    
    print("=" * 60)
    print("DATABASE SCHEMA VERIFICATION")
    print("=" * 60)
    
    with engine.connect() as conn:
        # Get columns from actual database
        result = conn.execute(text("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns 
            WHERE table_name='sessions'
            ORDER BY ordinal_position
        """))
        
        db_columns = {row[0]: {'type': row[1], 'nullable': row[2]} for row in result}
        
        print("\n📊 Columns in 'sessions' table:")
        print("-" * 60)
        for col_name, col_info in db_columns.items():
            nullable = "NULL" if col_info['nullable'] == 'YES' else "NOT NULL"
            print(f"  • {col_name:<25} {col_info['type']:<20} {nullable}")
        
        # Check for ideal_answer specifically
        print("\n" + "=" * 60)
        if 'ideal_answer' in db_columns:
            print("✓ 'ideal_answer' column EXISTS in database")
            print(f"  Type: {db_columns['ideal_answer']['type']}")
            print(f"  Nullable: {db_columns['ideal_answer']['nullable']}")
        else:
            print("✗ 'ideal_answer' column MISSING from database")
            print("\n⚠️  ACTION REQUIRED:")
            print("  Run: python -m scripts.add_ideal_answer_column")
        print("=" * 60)
        
        # Get model columns
        inspector = inspect(Session)
        model_columns = {col.key for col in inspector.mapper.column_attrs}
        
        # Compare
        missing_in_db = model_columns - set(db_columns.keys())
        extra_in_db = set(db_columns.keys()) - model_columns
        
        if missing_in_db:
            print("\n⚠️  Columns in MODEL but MISSING in DATABASE:")
            for col in missing_in_db:
                print(f"  • {col}")
        
        if extra_in_db:
            print("\n⚠️  Columns in DATABASE but NOT in MODEL:")
            for col in extra_in_db:
                print(f"  • {col}")
        
        if not missing_in_db and not extra_in_db:
            print("\n✓ Database schema matches SQLAlchemy model perfectly!")


if __name__ == "__main__":
    try:
        verify_sessions_table()
    except Exception as e:
        print(f"\n✗ Error: {e}")
        raise
