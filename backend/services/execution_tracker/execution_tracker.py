import os
from datetime import datetime
import pandas as pd
from sqlalchemy import text
from database.connections.postgres_connection import engine

# ---------------------------------------------------
# Role Definition and Hierarchy Mapping
# ---------------------------------------------------
ROLE_HIERARCHY = {
    'MD': 5,
    'ED': 4,
    'RM': 3,
    'ZM': 2,
    'Senior Store Manager': 1,
    'Store Manager': 0
}

def get_role_from_email(email):
    if not email:
        return 'Store Manager'
    email = email.lower().strip()
    if email in ['md.desk@forgebi.in', 'business.sroy@gmail.com', 'demo@admin.com']:
        return 'MD'
    elif email == 'ed.desk@forgebi.in':
        return 'ED'
    elif 'rm' in email:
        return 'RM'
    elif 'zm' in email:
        return 'ZM'
    elif email in ['sr.sm1@forgebi.in', 'sr.sm2@forgebi.in']:
        return 'Senior Store Manager'
    else:
        return 'Store Manager'

def get_name_from_email(email):
    if not email:
        return "Unknown"
    name_part = email.split('@')[0]
    parts = name_part.replace('.', ' ').replace('_', ' ').split()
    return " ".join([p.capitalize() for p in parts])

# ---------------------------------------------------
# Database Table Initialization
# ---------------------------------------------------
def db_init():
    if engine is None:
        print("Warning: PostgreSQL engine is not initialized. Cannot create tables.")
        return
        
    with engine.begin() as conn:
        # Create execution_goals table
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS execution_goals (
                goal_id SERIAL PRIMARY KEY,
                parent_goal_id INTEGER REFERENCES execution_goals(goal_id) ON DELETE SET NULL,
                title VARCHAR(255) NOT NULL,
                description TEXT,
                goal_category VARCHAR(100) NOT NULL,
                priority VARCHAR(50) NOT NULL,
                assigned_by_employee_code VARCHAR(255) NOT NULL,
                assigned_by_name VARCHAR(255) NOT NULL,
                assigned_by_role VARCHAR(100) NOT NULL,
                assigned_to_employee_code VARCHAR(255) NOT NULL,
                assigned_to_name VARCHAR(255) NOT NULL,
                assigned_to_role VARCHAR(100) NOT NULL,
                due_date DATE NOT NULL,
                status VARCHAR(50) NOT NULL,
                progress_pct INTEGER DEFAULT 0,
                reason_for_delay TEXT,
                expected_outcome TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                completed_at TIMESTAMP,
                last_updated_by VARCHAR(255),
                last_updated_by_role VARCHAR(100),
                is_escalated BOOLEAN DEFAULT FALSE,
                attachment_name VARCHAR(255),
                attachment_data BYTEA
            );
        """))

        # Add columns if table already existed without them
        if conn.dialect.name != 'sqlite':
            conn.execute(text("ALTER TABLE execution_goals ADD COLUMN IF NOT EXISTS attachment_name VARCHAR(255);"))
        if conn.dialect.name != 'sqlite':
            conn.execute(text("ALTER TABLE execution_goals ADD COLUMN IF NOT EXISTS attachment_data BYTEA;"))

        # Create goal_comments table
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS goal_comments (
                comment_id SERIAL PRIMARY KEY,
                goal_id INTEGER NOT NULL REFERENCES execution_goals(goal_id) ON DELETE CASCADE,
                comment_by_employee_code VARCHAR(255) NOT NULL,
                comment_by_name VARCHAR(255) NOT NULL,
                comment_by_role VARCHAR(100) NOT NULL,
                comment_text TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """))

        # Create goal_updates table
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS goal_updates (
                update_id SERIAL PRIMARY KEY,
                goal_id INTEGER NOT NULL REFERENCES execution_goals(goal_id) ON DELETE CASCADE,
                updated_by_employee_code VARCHAR(255) NOT NULL,
                old_status VARCHAR(50),
                new_status VARCHAR(50),
                old_progress INTEGER,
                new_progress INTEGER,
                update_reason TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """))

        # Create goal_attachments table
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS goal_attachments (
                attachment_id SERIAL PRIMARY KEY,
                goal_id INTEGER NOT NULL REFERENCES execution_goals(goal_id) ON DELETE CASCADE,
                uploaded_by_employee_code VARCHAR(255) NOT NULL,
                uploaded_by_name VARCHAR(255) NOT NULL,
                uploaded_by_role VARCHAR(100) NOT NULL,
                attachment_name VARCHAR(255) NOT NULL,
                attachment_data BYTEA NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """))

        # Migrate existing attachments from execution_goals to goal_attachments if any
        try:
            conn.execute(text("""
                INSERT INTO goal_attachments (goal_id, uploaded_by_employee_code, uploaded_by_name, uploaded_by_role, attachment_name, attachment_data)
                SELECT goal_id, assigned_by_employee_code, assigned_by_name, assigned_by_role, attachment_name, attachment_data
                FROM execution_goals eg
                WHERE eg.attachment_name IS NOT NULL AND eg.attachment_data IS NOT NULL
                  AND NOT EXISTS (
                      SELECT 1 FROM goal_attachments ga 
                      WHERE ga.goal_id = eg.goal_id 
                        AND ga.attachment_name = eg.attachment_name
                  );
            """))
        except Exception as e:
            print(f"Migration warning: {e}")

        # Migrate parent_goal_id foreign key constraint to ON DELETE CASCADE
        try:
            conn.execute(text("ALTER TABLE execution_goals DROP CONSTRAINT IF EXISTS execution_goals_parent_goal_id_fkey;"))
            conn.execute(text("""
                ALTER TABLE execution_goals 
                ADD CONSTRAINT execution_goals_parent_goal_id_fkey 
                FOREIGN KEY (parent_goal_id) REFERENCES execution_goals(goal_id) ON DELETE CASCADE;
            """))
        except Exception as e:
            print(f"Migration warning: Failed to update parent_goal_id foreign key to CASCADE: {e}")

        print("Execution Tracker tables initialized successfully in PostgreSQL.")

# Run database setup immediately on import
db_init()

# ---------------------------------------------------
# Escalation Logic (Triggered prior to queries)
# ---------------------------------------------------
def auto_escalate_overdue():
    if engine is None:
        return
    with engine.begin() as conn:
        conn.execute(text("""
            UPDATE execution_goals
            SET status = 'Overdue', is_escalated = TRUE, updated_at = NOW()
            WHERE due_date < CURRENT_DATE AND status NOT IN ('Completed', 'Cancelled', 'Overdue');
        """))

# ---------------------------------------------------
# Get Subordinates (For Goal Assignment dropdown)
# ---------------------------------------------------
def get_subordinates(email):
    from backend.cache.data_cache import user_access_df
    my_role = get_role_from_email(email)
    my_level = ROLE_HIERARCHY.get(my_role, 0)
    
    if my_level == 0:
        return []
        
    my_user_row = user_access_df[user_access_df['email'] == email]
    if my_user_row.empty:
        return []
        
    my_locs_str = my_user_row.iloc[0]['locations']
    my_locs = [l.strip().upper() for l in my_locs_str.split(',') if l.strip()]
    
    subordinates = []
    for _, row in user_access_df.iterrows():
        cand_email = row['email']
        if cand_email == email:
            continue
            
        cand_role = get_role_from_email(cand_email)
        cand_level = ROLE_HIERARCHY.get(cand_role, 0)
        
        # Subordinates must have lower hierarchy level
        if cand_level < my_level:
            # Check allowed locations overlap
            cand_locs_str = row['locations']
            cand_locs = [l.strip().upper() for l in cand_locs_str.split(',') if l.strip()]
            
            if 'ALL' in my_locs or any(loc in my_locs for loc in cand_locs):
                subordinates.append({
                    'email': cand_email,
                    'name': get_name_from_email(cand_email),
                    'role': cand_role
                })
    return subordinates

# ---------------------------------------------------
# CRUD Business Logic for Goals
# ---------------------------------------------------
def get_goals_for_user(email):
    if engine is None:
        return pd.DataFrame()
        
    # Auto-escalate before query
    auto_escalate_overdue()
    
    role = get_role_from_email(email)
    role_level = ROLE_HIERARCHY.get(role, 0)
    
    # MD & ED see all goals
    if role_level >= 4:
        query = """
        SELECT * FROM execution_goals g
        WHERE parent_goal_id IS NULL OR parent_goal_id NOT IN (SELECT goal_id FROM execution_goals)
        ORDER BY created_at DESC
        """
        df = pd.read_sql_query(query, engine)
    else:
        # Others use recursive CTE RLS filter
        query = """
        WITH RECURSIVE delegation_tree AS (
            -- Anchor: goals assigned to or by the user
            SELECT *
            FROM execution_goals
            WHERE LOWER(assigned_to_employee_code) = LOWER(:email) OR LOWER(assigned_by_employee_code) = LOWER(:email)
            
            UNION ALL
            
            -- Recursive: child goals delegated below them
            SELECT g.*
            FROM execution_goals g
            INNER JOIN delegation_tree dt ON g.parent_goal_id = dt.goal_id
        )
        SELECT DISTINCT * 
        FROM delegation_tree d
        WHERE d.parent_goal_id IS NULL OR d.parent_goal_id NOT IN (SELECT goal_id FROM delegation_tree)
        ORDER BY d.created_at DESC;
        """
        df = pd.read_sql_query(text(query), engine, params={"email": email})
        
    # Standardize column mapping
    return df

def get_goal_by_id(goal_id):
    if engine is None:
        return None
    try:
        goal_id = int(goal_id)
    except (ValueError, TypeError):
        return None
    with engine.connect() as conn:
        res = conn.execute(
            text("SELECT * FROM execution_goals WHERE goal_id = :goal_id"),
            {"goal_id": goal_id}
        )
        row = res.fetchone()
        if row:
            return dict(zip(res.keys(), row))
    return None


def create_goal(title, description, category, priority, assigned_by_email, assigned_to_email, due_date, expected_outcome, parent_goal_id=None, attachment_name=None, attachment_data=None, attachments=None):
    if engine is None:
        return None
        
    assigned_by_name = get_name_from_email(assigned_by_email)
    assigned_by_role = get_role_from_email(assigned_by_email)
    assigned_to_name = get_name_from_email(assigned_to_email)
    assigned_to_role = get_role_from_email(assigned_to_email)
    
    due_date_dt = pd.to_datetime(due_date).date()
    is_escalated = False
    status = 'Open'
    
    # Check initial overdue
    if due_date_dt < datetime.today().date():
        status = 'Overdue'
        is_escalated = True
        
    query = """
    INSERT INTO execution_goals (
        parent_goal_id, title, description, goal_category, priority,
        assigned_by_employee_code, assigned_by_name, assigned_by_role,
        assigned_to_employee_code, assigned_to_name, assigned_to_role,
        due_date, status, progress_pct, expected_outcome, is_escalated,
        created_at, updated_at
    ) VALUES (
        :parent_goal_id, :title, :description, :goal_category, :priority,
        :assigned_by_employee_code, :assigned_by_name, :assigned_by_role,
        :assigned_to_employee_code, :assigned_to_name, :assigned_to_role,
        :due_date, :status, 0, :expected_outcome, :is_escalated,
        NOW(), NOW()
    ) RETURNING goal_id;
    """
    
    with engine.begin() as conn:
        result = conn.execute(text(query), {
            "parent_goal_id": parent_goal_id,
            "title": title,
            "description": description,
            "goal_category": category,
            "priority": priority,
            "assigned_by_employee_code": assigned_by_email,
            "assigned_by_name": assigned_by_name,
            "assigned_by_role": assigned_by_role,
            "assigned_to_employee_code": assigned_to_email,
            "assigned_to_name": assigned_to_name,
            "assigned_to_role": assigned_to_role,
            "due_date": due_date_dt,
            "status": status,
            "expected_outcome": expected_outcome,
            "is_escalated": is_escalated
        })
        new_id = result.fetchone()[0]
        
        # Save attachments to new table
        all_atts = []
        if attachments:
            all_atts.extend(attachments)
        if attachment_name and attachment_data:
            all_atts.append({"name": attachment_name, "data": attachment_data})
            
        for att in all_atts:
            conn.execute(text("""
                INSERT INTO goal_attachments (
                    goal_id, uploaded_by_employee_code, uploaded_by_name, uploaded_by_role, attachment_name, attachment_data
                ) VALUES (
                    :goal_id, :uploader, :uploader_name, :uploader_role, :name, :data
                )
            """), {
                "goal_id": new_id,
                "uploader": assigned_by_email,
                "uploader_name": assigned_by_name,
                "uploader_role": assigned_by_role,
                "name": att["name"],
                "data": att["data"]
            })
        
    return new_id

def update_goal(goal_id, email, status, progress, delay_reason, comment=None, due_date=None, attachment_name=None, attachment_data=None, attachments=None):
    if engine is None:
        return False
        
    role = get_role_from_email(email)
    
    # Get current state
    with engine.connect() as conn:
        curr = conn.execute(
            text("SELECT status, progress_pct, assigned_by_employee_code, completed_at FROM execution_goals WHERE goal_id = :goal_id"),
            {"goal_id": goal_id}
        ).fetchone()
        
    if not curr:
        return False
        
    old_status, old_progress, assigned_by, old_completed_at = curr[0], curr[1], curr[2], curr[3]
    
    due_date_dt = None
    new_status = status
    
    # Check if due_date is updated by the creator
    if due_date and (assigned_by or "").lower().strip() == (email or "").lower().strip():
        due_date_dt = pd.to_datetime(due_date).date()
        # If new due date is in the future and status was 'Overdue', reset status to 'Open' or keep current
        if due_date_dt >= datetime.today().date():
            if status == 'Overdue':
                new_status = 'Open'
        else:
            if status not in ['Completed', 'Cancelled']:
                new_status = 'Overdue'
                
    completed_at = None
    if new_status == 'Completed':
        if old_status == 'Completed':
            completed_at = old_completed_at
        else:
            completed_at = datetime.now()
    else:
        completed_at = None
        
    update_goal_query = """
    UPDATE execution_goals
    SET status = :status,
        progress_pct = :progress,
        reason_for_delay = :delay_reason,
        updated_at = NOW(),
        completed_at = :completed_at,
        last_updated_by = :email,
        last_updated_by_role = :role,
        due_date = COALESCE(:due_date, due_date),
        is_escalated = CASE 
            WHEN :due_date IS NOT NULL THEN (:due_date < CURRENT_DATE AND :status NOT IN ('Completed', 'Cancelled'))
            ELSE is_escalated
        END
    WHERE goal_id = :goal_id;
    """
    
    with engine.begin() as conn:
        # Update goal table
        update_params = {
            "status": new_status,
            "progress": progress,
            "delay_reason": delay_reason,
            "completed_at": completed_at,
            "email": email,
            "role": role,
            "due_date": due_date_dt,
            "goal_id": goal_id
        }
        conn.execute(text(update_goal_query), update_params)
        
        # Save attachments to new table
        all_atts = []
        if attachments:
            all_atts.extend(attachments)
        if attachment_name and attachment_data:
            all_atts.append({"name": attachment_name, "data": attachment_data})
            
        for att in all_atts:
            conn.execute(text("""
                INSERT INTO goal_attachments (
                    goal_id, uploaded_by_employee_code, uploaded_by_name, uploaded_by_role, attachment_name, attachment_data
                ) VALUES (
                    :goal_id, :uploader, :uploader_name, :uploader_role, :name, :data
                )
            """), {
                "goal_id": goal_id,
                "uploader": email,
                "uploader_name": get_name_from_email(email),
                "uploader_role": role,
                "name": att["name"],
                "data": att["data"]
            })
        
        # Log to goal_updates
        conn.execute(text("""
            INSERT INTO goal_updates (
                goal_id, updated_by_employee_code, old_status, new_status,
                old_progress, new_progress, update_reason, updated_at
            ) VALUES (
                :goal_id, :email, :old_status, :new_status,
                :old_progress, :new_progress, :update_reason, NOW()
            );
        """), {
            "goal_id": goal_id,
            "email": email,
            "old_status": old_status,
            "new_status": status,
            "old_progress": old_progress,
            "new_progress": progress,
            "update_reason": delay_reason
        })
        
        # Log comment if present
        if comment and str(comment).strip() != "":
            conn.execute(text("""
                INSERT INTO goal_comments (
                    goal_id, comment_by_employee_code, comment_by_name, comment_by_role,
                    comment_text, created_at
                ) VALUES (
                    :goal_id, :email, :name, :role, :comment_text, NOW()
                );
            """), {
                "goal_id": goal_id,
                "email": email,
                "name": get_name_from_email(email),
                "role": role,
                "comment_text": str(comment).strip()
            })
            
    return True

def delete_goal(goal_id, email):
    if engine is None:
        return False
        
    role = get_role_from_email(email)
    role_level = ROLE_HIERARCHY.get(role, 0)
    
    with engine.connect() as conn:
        goal = conn.execute(
            text("SELECT assigned_by_employee_code FROM execution_goals WHERE goal_id = :goal_id"),
            {"goal_id": goal_id}
        ).fetchone()
        
    if not goal:
        return False
        
    assigned_by = goal[0]
    
    # Delete allowed if user is assigner OR MD/ED
    if (assigned_by or "").lower().strip() == (email or "").lower().strip() or role_level >= 4:
        with engine.begin() as conn:
            conn.execute(text("DELETE FROM execution_goals WHERE goal_id = :goal_id"), {"goal_id": goal_id})
        return True
        
    return False

def get_goal_hierarchy(goal_id):
    if engine is None:
        return []
        
    # Recursive CTE queries up to find the root parent, then down to fetch the complete chain
    query = """
    WITH RECURSIVE ancestor AS (
        SELECT goal_id, parent_goal_id
        FROM execution_goals
        WHERE goal_id = :goal_id
        
        UNION ALL
        
        SELECT g.goal_id, g.parent_goal_id
        FROM execution_goals g
        INNER JOIN ancestor a ON g.goal_id = a.parent_goal_id
    ),
    root_ancestor AS (
        SELECT goal_id FROM ancestor WHERE parent_goal_id IS NULL LIMIT 1
    ),
    delegation_tree AS (
        SELECT * FROM execution_goals WHERE goal_id = (SELECT goal_id FROM root_ancestor)
        
        UNION ALL
        
        SELECT g.*
        FROM execution_goals g
        INNER JOIN delegation_tree dt ON g.parent_goal_id = dt.goal_id
    )
    SELECT * FROM delegation_tree ORDER BY created_at ASC;
    """
    
    with engine.connect() as conn:
        res = conn.execute(text(query), {"goal_id": goal_id})
        cols = res.keys()
        rows = [dict(zip(cols, row)) for row in res.fetchall()]
    return rows

def get_goal_comments(goal_id):
    if engine is None:
        return []
        
    query = """
    SELECT comment_by_name as name, comment_by_role as role, comment_text as comment, created_at
    FROM goal_comments
    WHERE goal_id = :goal_id
    ORDER BY created_at DESC;
    """
    with engine.connect() as conn:
        res = conn.execute(text(query), {"goal_id": goal_id})
        cols = res.keys()
        rows = [dict(zip(cols, row)) for row in res.fetchall()]
    return rows

def get_goal_attachments_by_user(goal_id, email):
    if engine is None:
        return []
    query = """
    SELECT attachment_id, attachment_name, uploaded_by_employee_code, uploaded_by_name, uploaded_by_role, created_at
    FROM goal_attachments
    WHERE goal_id = :goal_id AND LOWER(uploaded_by_employee_code) = LOWER(:email)
    ORDER BY created_at ASC;
    """
    with engine.connect() as conn:
        res = conn.execute(text(query), {"goal_id": goal_id, "email": email})
        cols = res.keys()
        rows = [dict(zip(cols, row)) for row in res.fetchall()]
    return rows

def get_all_attachments_for_goal(goal_id):
    if engine is None:
        return []
    query = """
    SELECT attachment_id, attachment_name, uploaded_by_employee_code, uploaded_by_name, uploaded_by_role, created_at
    FROM goal_attachments
    WHERE goal_id = :goal_id
    ORDER BY created_at ASC;
    """
    with engine.connect() as conn:
        res = conn.execute(text(query), {"goal_id": goal_id})
        cols = res.keys()
        rows = [dict(zip(cols, row)) for row in res.fetchall()]
    return rows

def get_attachment_by_id(attachment_id):
    if engine is None:
        return None
    query = """
    SELECT attachment_id, attachment_name, attachment_data, uploaded_by_employee_code
    FROM goal_attachments
    WHERE attachment_id = :attachment_id;
    """
    with engine.connect() as conn:
        res = conn.execute(text(query), {"attachment_id": attachment_id})
        row = res.fetchone()
        if row:
            d = dict(zip(res.keys(), row))
            if d.get("attachment_data") is not None:
                if isinstance(d["attachment_data"], memoryview):
                    d["attachment_data"] = d["attachment_data"].tobytes()
                elif not isinstance(d["attachment_data"], bytes):
                    d["attachment_data"] = bytes(d["attachment_data"])
            return d
    return None

def delete_attachment_by_id(attachment_id, email):
    if engine is None:
        return False
    with engine.begin() as conn:
        curr = conn.execute(
            text("SELECT uploaded_by_employee_code FROM goal_attachments WHERE attachment_id = :attachment_id"),
            {"attachment_id": attachment_id}
        ).fetchone()
        if curr and curr[0].lower().strip() == email.lower().strip():
            conn.execute(
                text("DELETE FROM goal_attachments WHERE attachment_id = :attachment_id"),
                {"attachment_id": attachment_id}
            )
            return True
    return False
