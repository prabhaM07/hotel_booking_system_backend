from sqlalchemy import text
from core.database_postgres import SessionLocal

def alter_table():
  db = SessionLocal()
  

    # add_search_vector_column = """
    # alter table bookings
    # add column if not exists search_vector tsvector 
    # generated always as (setweight(to_tsvector('english',booking_status),'A') || 
    # (setweight(to_tsvector('english',payment_status),'B')) 
    # stored;
    # """
    # add_gin_index = """
    # create index bookings_fts on bookings using gin 
    # (search_vector);
    # """
    
    
  try:
      add_search_vector_column = text("""
      ALTER TABLE rooms 
      ADD COLUMN IF NOT EXISTS search_vector tsvector;
      """)
      
      add_trigger_function = text("""
      CREATE OR REPLACE FUNCTION update_room_search_vector()
      RETURNS trigger AS $$
      BEGIN
        SELECT setweight(to_tsvector('english', COALESCE(rt.room_name, '')), 'A') ||
                setweight(to_tsvector('english', COALESCE(NEW.status::text, '')), 'B')
        INTO NEW.search_vector
        FROM room_type_with_size rt
        WHERE rt.id = NEW.room_type_id;

        RETURN NEW;
      END;
      $$ LANGUAGE plpgsql;
      """)
      
      connect_function = text("""
      CREATE TRIGGER trg_update_room_search_vector
      BEFORE INSERT OR UPDATE ON rooms
      FOR EACH ROW
      EXECUTE FUNCTION update_room_search_vector();
      """)
      
      add_gin_index = text("""
      CREATE INDEX IF NOT EXISTS rooms_fts 
      ON rooms USING gin(search_vector);
      """)
      
      db.execute(add_search_vector_column)
      db.execute(add_trigger_function)
      db.execute(connect_function)
      db.execute(add_gin_index)
      db.commit()
      print("Search vector column, trigger, and index created successfully!")

  except Exception as e:
      db.rollback()
      print("Error while altering table:", e)
  
  finally:
      db.close()
    
    
if __name__ == "__main__":
  alter_table()

