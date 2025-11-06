from sqlalchemy import text
from app.core.database_postgres import SessionLocal


def create_extension():
    db = SessionLocal()
    try:
      extension1 = text("CREATE EXTENSION IF NOT EXISTS pg_trgm;")
      extension2 = text("CREATE EXTENSION IF NOT EXISTS unaccent;")

      db.execute(extension1)
      db.execute(extension2)
      
      db.commit()
      
    
    except Exception as e:
        db.rollback()
        print("Error while altering table:", e)

    finally:
        db.close()

def rooms_search_text():
    db = SessionLocal()
    try:
        # --- Drop old objects ---
        db.execute(text("DROP TRIGGER IF EXISTS trg_update_rooms_search_text ON rooms;"))
        db.execute(text("DROP FUNCTION IF EXISTS update_rooms_search_text() CASCADE;"))
        db.execute(text("DROP INDEX IF EXISTS rooms_search_text_idx;"))
        db.execute(text("ALTER TABLE rooms DROP COLUMN IF EXISTS search_text;"))
        db.commit()
        print("Old trigram trigger/function/index dropped successfully.")

        # --- Add search_text column ---
        db.execute(text("ALTER TABLE rooms ADD COLUMN IF NOT EXISTS search_text TEXT;"))

        # --- Create trigger function ---
        db.execute(text("""
        CREATE OR REPLACE FUNCTION update_rooms_search_text()
        RETURNS trigger AS $$
        DECLARE
          room_type_name TEXT;
          room_type_base_price TEXT;
          room_type_no_of_adult TEXT;
          room_type_no_of_child TEXT;
          feature_names TEXT;
          bed_type_names TEXT;
          floor_no TEXT;
        BEGIN
          SELECT
            rts.room_name::text, rts.base_price::text, rts.no_of_adult::text, rts.no_of_child::text
          INTO
            room_type_name, room_type_base_price, room_type_no_of_adult, room_type_no_of_child
          FROM room_type_with_sizes AS rts
          WHERE rts.id = NEW.room_type_id;

          SELECT frt.floor_no::text INTO floor_no FROM floors AS frt WHERE frt.id = NEW.floor_id;

          SELECT string_agg(f.feature_name, ' ') INTO feature_names
          FROM features AS f
          JOIN room_type_features AS rtf ON rtf.feature_id = f.id
          WHERE rtf.room_type_id = NEW.room_type_id;

          SELECT string_agg(bt.bed_type_name, ' ') INTO bed_type_names
          FROM bed_types AS bt
          JOIN room_type_bed_types AS rtbt ON rtbt.bed_type_id = bt.id
          WHERE rtbt.room_type_id = NEW.room_type_id;

          NEW.search_text := concat_ws(' ',
              COALESCE(floor_no, ''),
              COALESCE(NEW.room_no::text, ''),
              COALESCE(room_type_name, ''),
              COALESCE(room_type_base_price, ''),
              COALESCE(room_type_no_of_adult, ''),
              COALESCE(room_type_no_of_child, ''),
              COALESCE(NEW.status::text, ''),
              COALESCE(bed_type_names, ''),
              COALESCE(feature_names, ''),
              to_char(NEW.created_at, 'YYYY-MM-DD HH24:MI:SS'),
              to_char(NEW.updated_at, 'YYYY-MM-DD HH24:MI:SS')
          );

          RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
        """))

        # --- Connect trigger ---
        db.execute(text("""
        CREATE TRIGGER trg_update_rooms_search_text
        BEFORE INSERT OR UPDATE ON rooms
        FOR EACH ROW
        EXECUTE FUNCTION update_rooms_search_text();
        """))

        # --- Add GIN Trigram index ---
        db.execute(text("""
        CREATE INDEX IF NOT EXISTS rooms_search_text_idx
        ON rooms USING gin (search_text gin_trgm_ops);
        """))
        db.commit()
        print("Trigram search_text trigger and index created successfully.")

        # --- Backfill existing records ---
        db.execute(text("""
        UPDATE rooms AS r
        SET search_text = concat_ws(' ',
            COALESCE(f.floor_no::text, ''),
            COALESCE(r.room_no::text, ''),
            COALESCE(rts.room_name::text, ''),
            COALESCE(rts.base_price::text, ''),
            COALESCE(rts.no_of_adult::text, ''),
            COALESCE(rts.no_of_child::text, ''),
            COALESCE(r.status::text, ''),
            COALESCE((
                SELECT string_agg(ftr.feature_name, ' ')
                FROM features AS ftr
                JOIN room_type_features AS rtf ON rtf.feature_id = ftr.id
                WHERE rtf.room_type_id = r.room_type_id
            ), ''),
            COALESCE((
                SELECT string_agg(bt.bed_type_name, ' ')
                FROM bed_types AS bt
                JOIN room_type_bed_types AS rtbt ON rtbt.bed_type_id = bt.id
                WHERE rtbt.room_type_id = r.room_type_id
            ), ''),
            to_char(r.created_at, 'YYYY-MM-DD HH24:MI:SS'),
            to_char(r.updated_at, 'YYYY-MM-DD HH24:MI:SS')
        )
        FROM room_type_with_sizes AS rts, floors AS f
        WHERE rts.id = r.room_type_id AND f.id = r.floor_id;
        """))
        db.commit()
        print("Existing room search_text data backfilled successfully!")

    except Exception as e:
        db.rollback()
        print("Error in rooms_search_text():", e)

    finally:
        db.close()

def rooms_search_vector():
    db = SessionLocal()
    try:
      
        drop_trigger = text("""
        DROP TRIGGER IF EXISTS trg_update_rooms_search_vector ON rooms;
        """)

        drop_function = text("""
        DROP FUNCTION IF EXISTS update_rooms_search_vector() CASCADE;
        """)

        drop_index = text("""
        DROP INDEX IF EXISTS rooms_fts;
        """)

        drop_column = text("""
        ALTER TABLE rooms DROP COLUMN IF EXISTS search_vector;
        """)

        db.execute(drop_trigger)
        db.execute(drop_function)
        db.execute(drop_index)
        db.execute(drop_column)
        db.commit()

        print("Old trigger, function, index, and column dropped successfully.")

        add_search_vector_column = text("""
        ALTER TABLE rooms 
        ADD COLUMN IF NOT EXISTS search_vector tsvector;
        """)

        add_trigger_function = text("""
        CREATE OR REPLACE FUNCTION update_rooms_search_vector()
        RETURNS trigger AS $$
        DECLARE
        
          room_type_name TEXT;
          room_type_base_price TEXT;
          room_type_no_of_adult TEXT;
          room_type_no_of_child TEXT;
          feature_names TEXT;
          bed_type_names TEXT;
          floor_no TEXT;
          
        BEGIN
        
        SELECT
        
          rts.room_name :: text,
          rts.base_price :: text,
          rts.no_of_adult::text,
          rts.no_of_child::text
          
        INTO
        
          room_type_name,
          room_type_base_price,
          room_type_no_of_adult,
          room_type_no_of_child
          
        FROM room_type_with_sizes as rts
        WHERE rts.id = NEW.room_type_id;
        
        SELECT
        
          frt.floor_no :: text
          
        INTO
        
          floor_no
        
        FROM floors as frt
        WHERE frt.id = NEW.floor_id;
        
        SELECT string_agg(f.feature_name, ' ')
        INTO feature_names
        FROM features AS f
        JOIN room_type_features AS rtf 
          ON rtf.feature_id = f.id
        WHERE rtf.room_type_id = NEW.room_type_id;
        
        SELECT string_agg(bt.bed_type_name, ' ')
        INTO bed_type_names
        FROM bed_types AS bt
        JOIN room_type_bed_types AS rtbt 
          ON rtbt.bed_type_id = bt.id
        WHERE rtbt.room_type_id = NEW.room_type_id;
        
        NEW.search_vector :=
          setweight(to_tsvector('simple', COALESCE(floor_no::text, '')), 'A') ||
          setweight(to_tsvector('simple', COALESCE(NEW.room_no::text, '')), 'A') || 
          setweight(to_tsvector('english', COALESCE(room_type_name, '')), 'A') ||
          setweight(to_tsvector('english', COALESCE(room_type_base_price, '')), 'B') ||
          setweight(to_tsvector('english', COALESCE(room_type_no_of_adult, '')), 'B') ||
          setweight(to_tsvector('english', COALESCE(room_type_no_of_child, '')), 'B') ||
          setweight(to_tsvector('english', COALESCE(NEW.status::text, '')), 'B') ||
          setweight(to_tsvector('english', COALESCE(bed_type_names, '')), 'C') ||
          setweight(to_tsvector('english', COALESCE(feature_names, '')), 'C') ||
          setweight(to_tsvector('english', to_char(NEW.created_at, 'YYYY-MM-DD HH24:MI:SS')), 'C')||
          setweight(to_tsvector('english', to_char(NEW.updated_at, 'YYYY-MM-DD HH24:MI:SS')), 'C');

        RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
        """)

        connect_function = text("""
        CREATE TRIGGER trg_update_rooms_search_vector
        BEFORE INSERT OR UPDATE ON rooms
        FOR EACH ROW
        EXECUTE FUNCTION update_rooms_search_vector();
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

        print("Search vector column, trigger, and index recreated successfully!")
        backfill_search_vector = text("""
          UPDATE rooms AS r
          SET search_vector =
              setweight(to_tsvector('simple', COALESCE(f.floor_no::text, '')), 'A') ||
              setweight(to_tsvector('simple', COALESCE(r.room_no::text, '')), 'A') ||
              setweight(to_tsvector('english', COALESCE(rts.room_name::text, '')), 'A') ||
              setweight(to_tsvector('english', COALESCE(rts.base_price::text, '')), 'B') ||
              setweight(to_tsvector('english', COALESCE(rts.no_of_adult::text, '')), 'B') ||
              setweight(to_tsvector('english', COALESCE(rts.no_of_child::text, '')), 'B') ||
              setweight(to_tsvector('english', COALESCE(r.status::text, '')), 'B') ||
              setweight(
                  to_tsvector(
                      'english',
                      COALESCE((
                          SELECT string_agg(ftr.feature_name, ' ')
                          FROM features AS ftr
                          JOIN room_type_features AS rtf
                              ON rtf.feature_id = ftr.id
                          WHERE rtf.room_type_id = r.room_type_id
                      ), '')
                  ), 'B'
              ) ||
              setweight(
                  to_tsvector(
                      'english',
                      COALESCE((
                          SELECT string_agg(bt.bed_type_name, ' ')
                          FROM bed_types AS bt
                          JOIN room_type_bed_types AS rtbt
                              ON rtbt.bed_type_id = bt.id
                          WHERE rtbt.room_type_id = r.room_type_id
                      ), '')
                  ), 'B'
              ) ||
              setweight(to_tsvector('english', to_char(r.created_at, 'YYYY-MM-DD HH24:MI:SS')), 'C') ||
              setweight(to_tsvector('english', to_char(r.updated_at, 'YYYY-MM-DD HH24:MI:SS')), 'C')
          FROM room_type_with_sizes AS rts, floors AS f
          WHERE rts.id = r.room_type_id
            AND f.id = r.floor_id;
      """)


        db.execute(backfill_search_vector)
        db.commit()
        print("Existing rooms records successfully updated with search_vector values!")

    except Exception as e:
        db.rollback()
        print("Error while altering table:", e)

    finally:
        db.close()

#---------------------------------------------------------------------------------------------------------------------------------------

def rooms_types_search_vector():
    db = SessionLocal()
    try:
        drop_trigger = text("""
        DROP TRIGGER IF EXISTS trg_update_rooms_type_search_vector ON room_type_with_sizes;
        """)

        drop_function = text("""
        DROP FUNCTION IF EXISTS update_rooms_type_search_vector() CASCADE;
        """)

        drop_index = text("""
        DROP INDEX IF EXISTS rooms_types_fts;
        """)

        drop_column = text("""
        ALTER TABLE room_type_with_sizes DROP COLUMN IF EXISTS search_vector;
        """)

        db.execute(drop_trigger)
        db.execute(drop_function)
        db.execute(drop_index)
        db.execute(drop_column)
        db.commit()

        print("Old trigger, function, index, and column dropped successfully.")


        add_search_vector_column = text("""
        ALTER TABLE room_type_with_sizes
        ADD COLUMN IF NOT EXISTS search_vector tsvector;
        """)

        add_trigger_function = text("""
        CREATE OR REPLACE FUNCTION update_rooms_type_search_vector()
        RETURNS trigger AS $$
        
        DECLARE
       
          feature_names TEXT;
          bed_type_names TEXT;
          
        BEGIN
          SELECT string_agg(f.feature_name, ' ')
          INTO feature_names
          FROM features AS f
          JOIN room_type_features AS rtf 
            ON rtf.feature_id = f.id
          WHERE rtf.room_type_id = NEW.id;
          
          SELECT string_agg(bt.bed_type_name, ' ')
          INTO bed_type_names
          FROM bed_types AS bt
          JOIN room_type_bed_types AS rtbt 
            ON rtbt.bed_type_id = bt.id
          WHERE rtbt.room_type_id = NEW.id;
        
          NEW.search_vector :=
            setweight(to_tsvector('english', COALESCE(NEW.room_name, '')), 'A') ||
            setweight(to_tsvector('english', COALESCE(NEW.base_price::text, '')), 'A') ||
            setweight(to_tsvector('english', COALESCE(feature_names::text, '')), 'B') ||
            setweight(to_tsvector('english', COALESCE(bed_type_names::text, '')), 'B') ||
            setweight(to_tsvector('english', COALESCE(NEW.no_of_adult::text, '')), 'B') ||
            setweight(to_tsvector('english', COALESCE(NEW.no_of_child::text, '')), 'B') ||
            setweight(to_tsvector('english', to_char(NEW.created_at, 'YYYY-MM-DD HH24:MI:SS')), 'C')||
            setweight(to_tsvector('english', to_char(NEW.updated_at, 'YYYY-MM-DD HH24:MI:SS')), 'C');
            
          RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
        """)

        connect_function = text("""
        CREATE TRIGGER trg_update_rooms_type_search_vector
        BEFORE INSERT OR UPDATE ON room_type_with_sizes
        FOR EACH ROW
        EXECUTE FUNCTION update_rooms_type_search_vector();
        """)

        add_gin_index = text("""
        CREATE INDEX IF NOT EXISTS rooms_types_fts 
        ON room_type_with_sizes USING gin(search_vector);
        """)

        
        db.execute(add_search_vector_column)
        db.execute(add_trigger_function)
        db.execute(connect_function)
        db.execute(add_gin_index)
        db.commit()

        print("Search vector column, trigger, and index recreated successfully!")

        backfill_search_vector = text("""
        UPDATE room_type_with_sizes AS rts
        SET search_vector =
            setweight(to_tsvector('english', COALESCE(rts.room_name, '')), 'A') ||
            setweight(to_tsvector('english', COALESCE(rts.base_price::text, '')), 'A') ||
            setweight(
              to_tsvector(
                'english',
                COALESCE((
                  SELECT string_agg(f.feature_name, ' ')
                  FROM features AS f
                  JOIN room_type_features AS rtf 
                    ON rtf.feature_id = f.id
                  WHERE rtf.room_type_id = rts.id
                ), '')
              ), 'B'
            ) ||
            setweight(
              to_tsvector(
                'english',
                COALESCE((
                  SELECT string_agg(bt.bed_type_name, ' ')
                  FROM bed_types AS bt
                  JOIN room_type_bed_types AS rtbt 
                    ON rtbt.bed_type_id = bt.id
                  WHERE rtbt.room_type_id = rts.id
                ), '')
              ), 'B'
            ) ||
            setweight(to_tsvector('english', COALESCE(rts.no_of_adult::text, '')), 'B') ||
            setweight(to_tsvector('english', COALESCE(rts.no_of_child::text, '')), 'B') ||
            setweight(to_tsvector('english', to_char(rts.created_at, 'YYYY-MM-DD HH24:MI:SS')), 'C') ||
            setweight(to_tsvector('english', to_char(rts.updated_at, 'YYYY-MM-DD HH24:MI:SS')), 'C');
        """)


        db.execute(backfill_search_vector)
        db.commit()
        print("Existing rooms records successfully updated with search_vector values!")

    except Exception as e:
        db.rollback()
        print("Error while altering table:", e)

    finally:
        db.close()

def room_types_search_text():
    db = SessionLocal()
    try:
        # --- Drop existing trigger, function, index, and column ---
        drop_trigger = text("""
        DROP TRIGGER IF EXISTS trg_update_room_type_search_text ON room_type_with_sizes;
        """)

        drop_function = text("""
        DROP FUNCTION IF EXISTS update_room_type_search_text() CASCADE;
        """)

        drop_index = text("""
        DROP INDEX IF EXISTS room_type_search_text_idx;
        """)

        drop_column = text("""
        ALTER TABLE room_type_with_sizes DROP COLUMN IF EXISTS search_text;
        """)

        db.execute(drop_trigger)
        db.execute(drop_function)
        db.execute(drop_index)
        db.execute(drop_column)
        db.commit()

        print("Old trigger, function, index, and column dropped successfully.")

        # --- Add new column for search text ---
        add_search_text_column = text("""
        ALTER TABLE room_type_with_sizes
        ADD COLUMN IF NOT EXISTS search_text TEXT;
        """)

        db.execute(add_search_text_column)
        db.commit()

        # --- Create function to update search_text automatically ---
        add_trigger_function = text("""
        CREATE OR REPLACE FUNCTION update_room_type_search_text()
        RETURNS trigger AS $$
        DECLARE
          feature_names TEXT;
          bed_type_names TEXT;
        BEGIN
          SELECT string_agg(f.feature_name, ' ')
          INTO feature_names
          FROM features AS f
          JOIN room_type_features AS rtf 
            ON rtf.feature_id = f.id
          WHERE rtf.room_type_id = NEW.id;

          SELECT string_agg(bt.bed_type_name, ' ')
          INTO bed_type_names
          FROM bed_types AS bt
          JOIN room_type_bed_types AS rtbt 
            ON rtbt.bed_type_id = bt.id
          WHERE rtbt.room_type_id = NEW.id;

          NEW.search_text := 
              COALESCE(NEW.room_name, '') || ' ' ||
              COALESCE(NEW.base_price::text, '') || ' ' ||
              COALESCE(feature_names, '') || ' ' ||
              COALESCE(bed_type_names, '') || ' ' ||
              COALESCE(NEW.no_of_adult::text, '') || ' ' ||
              COALESCE(NEW.no_of_child::text, '') || ' ' ||
              to_char(NEW.created_at, 'YYYY-MM-DD HH24:MI:SS') || ' ' ||
              to_char(NEW.updated_at, 'YYYY-MM-DD HH24:MI:SS');

          RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
        """)

        db.execute(add_trigger_function)

        # --- Attach trigger to table ---
        connect_function = text("""
        CREATE TRIGGER trg_update_room_type_search_text
        BEFORE INSERT OR UPDATE ON room_type_with_sizes
        FOR EACH ROW
        EXECUTE FUNCTION update_room_type_search_text();
        """)

        db.execute(connect_function)

        # --- Add index for fast ILIKE searches ---
        add_gin_index = text("""
        CREATE INDEX IF NOT EXISTS room_type_search_text_idx
        ON room_type_with_sizes USING gin (search_text gin_trgm_ops);
        """)

        db.execute(add_gin_index)
        db.commit()

        print("Search text column, trigger, and trigram index created successfully.")

        # --- Backfill existing data ---
        backfill_search_text = text("""
        UPDATE room_type_with_sizes AS rts
        SET search_text =
            COALESCE(rts.room_name, '') || ' ' ||
            COALESCE(rts.base_price::text, '') || ' ' ||
            COALESCE((
                SELECT string_agg(f.feature_name, ' ')
                FROM features AS f
                JOIN room_type_features AS rtf 
                  ON rtf.feature_id = f.id
                WHERE rtf.room_type_id = rts.id
            ), '') || ' ' ||
            COALESCE((
                SELECT string_agg(bt.bed_type_name, ' ')
                FROM bed_types AS bt
                JOIN room_type_bed_types AS rtbt 
                  ON rtbt.bed_type_id = bt.id
                WHERE rtbt.room_type_id = rts.id
            ), '') || ' ' ||
            COALESCE(rts.no_of_adult::text, '') || ' ' ||
            COALESCE(rts.no_of_child::text, '') || ' ' ||
            to_char(rts.created_at, 'YYYY-MM-DD HH24:MI:SS') || ' ' ||
            to_char(rts.updated_at, 'YYYY-MM-DD HH24:MI:SS');
        """)

        db.execute(backfill_search_text)
        db.commit()

        print("Existing records successfully backfilled with search_text values!")

    except Exception as e:
        db.rollback()
        print("Error while altering table:", e)

    finally:
        db.close()

#---------------------------------------------------------------------------------------------------------------------------------------
                       
def bookings_search_vector():
  
    db = SessionLocal()
    
    try :
      
        drop_trigger = text("""
        DROP TRIGGER IF EXISTS trg_update_booking_search_vector ON bookings;
        """)

        drop_function = text("""
        DROP FUNCTION IF EXISTS update_booking_search_vector() CASCADE;
        """)

        drop_index = text("""
        DROP INDEX IF EXISTS booking_fts;
        """)

        drop_column = text("""
        ALTER TABLE bookings DROP COLUMN IF EXISTS search_vector;
        """)

        db.execute(drop_trigger)
        db.execute(drop_function)
        db.execute(drop_index)
        db.execute(drop_column)
        db.commit()

        print("Old trigger, function, index, and column dropped successfully.")


        add_search_vector_column = text(
        """
            alter table bookings add column if not exists search_vector tsvector;
        """
        )

        add_trigger_function = text("""
        CREATE OR REPLACE FUNCTION update_booking_search_vector()
        RETURNS trigger AS $$
        DECLARE
          room_type_name TEXT;
          room_type_base_price TEXT;
          no_of_adult TEXT;
          no_of_child TEXT;
          feature_names TEXT;
          bed_type_names TEXT;
          floor_no TEXT;
          room_no TEXT;
          first_name TEXT;
          last_name TEXT;
          phone_no TEXT;
          email TEXT;
          dob_text TEXT;
          street TEXT;
          city TEXT;
          state TEXT;
          country TEXT;
          pincode TEXT;
          role_name TEXT;
        BEGIN
          SELECT r.room_no::text
          INTO room_no
          FROM rooms AS r
          WHERE r.id = NEW.room_id;

          SELECT
            rts.room_name::text,
            rts.base_price::text,
            rts.no_of_adult::text,
            rts.no_of_child::text
          INTO
            room_type_name,
            room_type_base_price,
            no_of_adult,
            no_of_child
          FROM room_type_with_sizes AS rts
          JOIN rooms AS r ON r.room_type_id = rts.id
          WHERE r.id = NEW.room_id;

          SELECT
            f.floor_no::text
          INTO
            floor_no
          FROM floors AS f
          JOIN rooms AS r ON r.floor_id = f.id
          WHERE r.id = NEW.room_id;

          SELECT string_agg(f.feature_name, ' ')
          INTO feature_names
          FROM features AS f
          JOIN room_type_features AS rtf ON rtf.feature_id = f.id
          JOIN room_type_with_sizes AS rts ON rts.id = rtf.room_type_id
          JOIN rooms AS r ON r.room_type_id = rts.id
          WHERE r.id = NEW.room_id;

          SELECT string_agg(bt.bed_type_name, ' ')
          INTO bed_type_names
          FROM bed_types AS bt
          JOIN room_type_bed_types AS rtbt ON rtbt.bed_type_id = bt.id
          JOIN room_type_with_sizes AS rts ON rts.id = rtbt.room_type_id
          JOIN rooms AS r ON r.room_type_id = rts.id
          WHERE r.id = NEW.room_id;

          SELECT
            u.first_name::text,
            u.last_name::text,
            u.phone_no::text,
            u.email::text
          INTO
            first_name,
            last_name,
            phone_no,
            email
          FROM users u
          WHERE u.id = NEW.user_id;

          SELECT
            p.DOB::text,
            (p.address).street,
            (p.address).city,
            (p.address).state,
            (p.address).country,
            (p.address).pincode
          INTO
            dob_text, street, city, state, country, pincode
          FROM profiles AS p
          WHERE p.user_id = NEW.user_id;

          SELECT
            r.role_name::text
          INTO
            role_name
          FROM roles AS r
          JOIN users u ON r.id = u.role_id
          WHERE u.id = NEW.user_id;

          NEW.search_vector :=
            setweight(to_tsvector('english', COALESCE(NEW.user_id::text, '')), 'A') ||
            setweight(to_tsvector('english', COALESCE(NEW.room_id::text, '')), 'A') ||
            setweight(to_tsvector('english', COALESCE(room_type_name::text, '')), 'A') ||
            setweight(to_tsvector('english', COALESCE(room_type_base_price::text, '')), 'A') ||
            setweight(to_tsvector('english', COALESCE(no_of_adult::text, '')), 'C') ||
            setweight(to_tsvector('english', COALESCE(no_of_child::text, '')), 'C') ||
            setweight(to_tsvector('english', COALESCE(feature_names::text, '')), 'B') ||
            setweight(to_tsvector('english', COALESCE(bed_type_names::text, '')), 'B') ||
            setweight(to_tsvector('english', COALESCE(floor_no::text, '')), 'B') ||
            setweight(to_tsvector('english', COALESCE(room_no::text, '')), 'B') ||
            setweight(to_tsvector('english', COALESCE(first_name::text, '')), 'B') ||
            setweight(to_tsvector('english', COALESCE(last_name::text, '')), 'B') ||
            setweight(to_tsvector('english', COALESCE(phone_no::text, '')), 'B') ||
            setweight(to_tsvector('english', COALESCE(email::text, '')), 'B') ||
            setweight(to_tsvector('english', COALESCE(dob_text::text, '')), 'B') ||
            setweight(to_tsvector('english', COALESCE(street::text, '')), 'B') ||
            setweight(to_tsvector('english', COALESCE(city::text, '')), 'B') ||
            setweight(to_tsvector('english', COALESCE(state::text, '')), 'B') ||
            setweight(to_tsvector('english', COALESCE(country::text, '')), 'B') ||
            setweight(to_tsvector('english', COALESCE(pincode::text, '')), 'B') ||
            setweight(to_tsvector('english', COALESCE(role_name::text, '')), 'B') ||
            setweight(to_tsvector('english', COALESCE(NEW.booking_status::text, '')), 'B') ||
            setweight(to_tsvector('english', COALESCE(NEW.payment_status::text, '')), 'B') ||
            setweight(to_tsvector('english', COALESCE(NEW.total_amount::text, '')), 'B') ||
            setweight(to_tsvector('english', to_char(NEW.check_in, 'YYYY-MM-DD')), 'C') ||
            setweight(to_tsvector('english', to_char(NEW.check_out, 'YYYY-MM-DD')), 'C') ||
            setweight(to_tsvector('english', to_char(NEW.created_at, 'YYYY-MM-DD HH24:MI:SS')), 'C') ||
            setweight(to_tsvector('english', to_char(NEW.updated_at, 'YYYY-MM-DD HH24:MI:SS')), 'C');

          RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;

        """)

        connect_function = text("""
        CREATE TRIGGER trg_update_booking_search_vector
        BEFORE INSERT OR UPDATE ON bookings
        FOR EACH ROW
        EXECUTE FUNCTION update_booking_search_vector();
        """)

        add_gin_index = text("""
        CREATE INDEX IF NOT EXISTS booking_fts 
        ON bookings USING gin(search_vector);
        """)

        db.execute(add_search_vector_column)
        db.execute(add_trigger_function)
        db.execute(connect_function)
        db.execute(add_gin_index)
        db.commit()
        backfill_search_vector = text("""
          UPDATE bookings AS b
          SET search_vector =
            setweight(to_tsvector('english', COALESCE(b.user_id::text, '')), 'A') ||
            setweight(to_tsvector('english', COALESCE(b.room_id::text, '')), 'A') ||
            setweight(to_tsvector('english', COALESCE(rts.room_name, '')), 'A') ||
            setweight(to_tsvector('english', COALESCE(rts.base_price::text, '')), 'A') ||
            setweight(to_tsvector('english', COALESCE(rts.no_of_adult::text, '')), 'B') ||
            setweight(to_tsvector('english', COALESCE(rts.no_of_child::text, '')), 'B') ||
            setweight(to_tsvector('english', COALESCE(f.floor_no::text, '')), 'B') ||
            setweight(to_tsvector('english', COALESCE(r.room_no::text, '')), 'B') ||
            setweight(to_tsvector('english', COALESCE(u.first_name, '')), 'B') ||
            setweight(to_tsvector('english', COALESCE(u.last_name, '')), 'B') ||
            setweight(to_tsvector('english', COALESCE(u.phone_no, '')), 'B') ||
            setweight(to_tsvector('english', COALESCE(u.email, '')), 'B') ||
            setweight(to_tsvector('english', COALESCE(p.dob::text, '')), 'B') ||
            setweight(to_tsvector('english', COALESCE((p.address).street, '')), 'B') ||
            setweight(to_tsvector('english', COALESCE((p.address).city, '')), 'B') ||
            setweight(to_tsvector('english', COALESCE((p.address).state, '')), 'B') ||
            setweight(to_tsvector('english', COALESCE((p.address).country, '')), 'B') ||
            setweight(to_tsvector('english', COALESCE((p.address).pincode, '')), 'B') ||
            setweight(to_tsvector('english', COALESCE(rl.role_name, '')), 'B') ||
            setweight(
                to_tsvector('english',
                  COALESCE((
                    SELECT string_agg(f.feature_name, ' ')
                    FROM features AS f
                    JOIN room_type_features AS rtf ON rtf.feature_id = f.id
                    WHERE rtf.room_type_id = rts.id
                  ), '')
                ), 'B'
            ) ||
            setweight(
                to_tsvector('english',
                  COALESCE((
                    SELECT string_agg(bt.bed_type_name, ' ')
                    FROM bed_types AS bt
                    JOIN room_type_bed_types AS rtbt ON rtbt.bed_type_id = bt.id
                    WHERE rtbt.room_type_id = rts.id
                  ), '')
                ), 'B'
            ) ||
            setweight(to_tsvector('english', COALESCE(b.booking_status :: text, '')), 'B') ||
            setweight(to_tsvector('english', COALESCE(b.payment_status  :: text, '')), 'B') ||
            setweight(to_tsvector('english', COALESCE(b.total_amount::text, '')), 'B') ||
            setweight(to_tsvector('english', to_char(b.check_in, 'YYYY-MM-DD')), 'C') ||
            setweight(to_tsvector('english', to_char(b.check_out, 'YYYY-MM-DD')), 'C') ||
            setweight(to_tsvector('english', to_char(b.created_at, 'YYYY-MM-DD HH24:MI:SS')), 'C') ||
            setweight(to_tsvector('english', to_char(b.updated_at, 'YYYY-MM-DD HH24:MI:SS')), 'C')
          FROM rooms AS r
          JOIN room_type_with_sizes AS rts ON rts.id = r.room_type_id
          LEFT JOIN floors AS f ON f.id = r.floor_id
          JOIN users AS u ON TRUE                
          LEFT JOIN profiles AS p ON p.user_id = u.id
          LEFT JOIN roles AS rl ON rl.id = u.role_id
          WHERE r.id = b.room_id
          AND u.id = b.user_id;               

        """)

        db.execute(backfill_search_vector)
        db.commit()
        print("Existing booking records successfully updated with search_vector values!")
        
    except Exception as e:
        db.rollback()
        print("Error while altering table:", e)
    finally:
        db.close()

def bookings_search_text():
    db = SessionLocal()
    try:
        # --- Drop existing trigger, function, index, and column ---
        drop_trigger = text("""
        DROP TRIGGER IF EXISTS trg_update_booking_search_text ON bookings;
        """)

        drop_function = text("""
        DROP FUNCTION IF EXISTS update_booking_search_text() CASCADE;
        """)

        drop_index = text("""
        DROP INDEX IF EXISTS booking_search_text_idx;
        """)

        drop_column = text("""
        ALTER TABLE bookings DROP COLUMN IF EXISTS search_text;
        """)

        db.execute(drop_trigger)
        db.execute(drop_function)
        db.execute(drop_index)
        db.execute(drop_column)
        db.commit()

        print("Old trigger, function, index, and column dropped successfully.")

        # --- Add new search_text column ---
        add_search_text_column = text("""
        ALTER TABLE bookings
        ADD COLUMN IF NOT EXISTS search_text TEXT;
        """)
        db.execute(add_search_text_column)
        db.commit()

        # --- Create trigger function ---
        add_trigger_function = text("""
        CREATE OR REPLACE FUNCTION update_booking_search_text()
        RETURNS trigger AS $$
        DECLARE
          room_type_name TEXT;
          room_type_base_price TEXT;
          no_of_adult TEXT;
          no_of_child TEXT;
          feature_names TEXT;
          bed_type_names TEXT;
          floor_no TEXT;
          room_no TEXT;
          first_name TEXT;
          last_name TEXT;
          phone_no TEXT;
          email TEXT;
          dob_text TEXT;
          street TEXT;
          city TEXT;
          state TEXT;
          country TEXT;
          pincode TEXT;
          role_name TEXT;
        BEGIN
          SELECT r.room_no::text
          INTO room_no
          FROM rooms AS r
          WHERE r.id = NEW.room_id;

          SELECT
            rts.room_name::text,
            rts.base_price::text,
            rts.no_of_adult::text,
            rts.no_of_child::text
          INTO
            room_type_name,
            room_type_base_price,
            no_of_adult,
            no_of_child
          FROM room_type_with_sizes AS rts
          JOIN rooms AS r ON r.room_type_id = rts.id
          WHERE r.id = NEW.room_id;

          SELECT
            f.floor_no::text
          INTO
            floor_no
          FROM floors AS f
          JOIN rooms AS r ON r.floor_id = f.id
          WHERE r.id = NEW.room_id;

          SELECT string_agg(f.feature_name, ' ')
          INTO feature_names
          FROM features AS f
          JOIN room_type_features AS rtf ON rtf.feature_id = f.id
          JOIN room_type_with_sizes AS rts ON rts.id = rtf.room_type_id
          JOIN rooms AS r ON r.room_type_id = rts.id
          WHERE r.id = NEW.room_id;

          SELECT string_agg(bt.bed_type_name, ' ')
          INTO bed_type_names
          FROM bed_types AS bt
          JOIN room_type_bed_types AS rtbt ON rtbt.bed_type_id = bt.id
          JOIN room_type_with_sizes AS rts ON rts.id = rtbt.room_type_id
          JOIN rooms AS r ON r.room_type_id = rts.id
          WHERE r.id = NEW.room_id;

          SELECT
            u.first_name::text,
            u.last_name::text,
            u.phone_no::text,
            u.email::text
          INTO
            first_name,
            last_name,
            phone_no,
            email
          FROM users u
          WHERE u.id = NEW.user_id;

          SELECT
            p.dob::text,
            (p.address).street,
            (p.address).city,
            (p.address).state,
            (p.address).country,
            (p.address).pincode
          INTO
            dob_text, street, city, state, country, pincode
          FROM profiles AS p
          WHERE p.user_id = NEW.user_id;

          SELECT
            r.role_name::text
          INTO
            role_name
          FROM roles AS r
          JOIN users u ON r.id = u.role_id
          WHERE u.id = NEW.user_id;

          NEW.search_text :=
              COALESCE(NEW.user_id::text, '') || ' ' ||
              COALESCE(NEW.room_id::text, '') || ' ' ||
              COALESCE(room_type_name, '') || ' ' ||
              COALESCE(room_type_base_price, '') || ' ' ||
              COALESCE(no_of_adult, '') || ' ' ||
              COALESCE(no_of_child, '') || ' ' ||
              COALESCE(feature_names, '') || ' ' ||
              COALESCE(bed_type_names, '') || ' ' ||
              COALESCE(floor_no, '') || ' ' ||
              COALESCE(room_no, '') || ' ' ||
              COALESCE(first_name, '') || ' ' ||
              COALESCE(last_name, '') || ' ' ||
              COALESCE(phone_no, '') || ' ' ||
              COALESCE(email, '') || ' ' ||
              COALESCE(dob_text, '') || ' ' ||
              COALESCE(street, '') || ' ' ||
              COALESCE(city, '') || ' ' ||
              COALESCE(state, '') || ' ' ||
              COALESCE(country, '') || ' ' ||
              COALESCE(pincode, '') || ' ' ||
              COALESCE(role_name, '') || ' ' ||
              COALESCE(NEW.booking_status::text, '') || ' ' ||
              COALESCE(NEW.payment_status::text, '') || ' ' ||
              COALESCE(NEW.total_amount::text, '') || ' ' ||
              to_char(NEW.check_in, 'YYYY-MM-DD') || ' ' ||
              to_char(NEW.check_out, 'YYYY-MM-DD') || ' ' ||
              to_char(NEW.created_at, 'YYYY-MM-DD HH24:MI:SS') || ' ' ||
              to_char(NEW.updated_at, 'YYYY-MM-DD HH24:MI:SS');

          RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
        """)

        db.execute(add_trigger_function)

        # --- Attach trigger ---
        connect_function = text("""
        CREATE TRIGGER trg_update_booking_search_text
        BEFORE INSERT OR UPDATE ON bookings
        FOR EACH ROW
        EXECUTE FUNCTION update_booking_search_text();
        """)
        db.execute(connect_function)

        # --- Create trigram index ---
        add_gin_index = text("""
        CREATE INDEX IF NOT EXISTS booking_search_text_idx
        ON bookings USING gin (search_text gin_trgm_ops);
        """)
        db.execute(add_gin_index)
        db.commit()

        print("Search text column, trigger, and trigram index created successfully.")

        # --- Backfill for existing rows ---
        backfill_search_text = text("""
          UPDATE bookings AS b
          SET search_text = sub.search_text
          FROM (
              SELECT
                  b2.id AS booking_id,
                  COALESCE(b2.user_id::text, '') || ' ' ||
                  COALESCE(b2.room_id::text, '') || ' ' ||
                  COALESCE(rts.room_name, '') || ' ' ||
                  COALESCE(rts.base_price::text, '') || ' ' ||
                  COALESCE(rts.no_of_adult::text, '') || ' ' ||
                  COALESCE(rts.no_of_child::text, '') || ' ' ||
                  COALESCE(f.floor_no::text, '') || ' ' ||
                  COALESCE(r.room_no::text, '') || ' ' ||
                  COALESCE(u.first_name, '') || ' ' ||
                  COALESCE(u.last_name, '') || ' ' ||
                  COALESCE(u.phone_no, '') || ' ' ||
                  COALESCE(u.email, '') || ' ' ||
                  COALESCE(p.dob::text, '') || ' ' ||
                  COALESCE((p.address).street, '') || ' ' ||
                  COALESCE((p.address).city, '') || ' ' ||
                  COALESCE((p.address).state, '') || ' ' ||
                  COALESCE((p.address).country, '') || ' ' ||
                  COALESCE((p.address).pincode, '') || ' ' ||
                  COALESCE(rl.role_name, '') || ' ' ||
                  COALESCE((
                      SELECT string_agg(f2.feature_name, ' ')
                      FROM features AS f2
                      JOIN room_type_features AS rtf ON rtf.feature_id = f2.id
                      WHERE rtf.room_type_id = rts.id
                  ), '') || ' ' ||
                  COALESCE((
                      SELECT string_agg(bt.bed_type_name, ' ')
                      FROM bed_types AS bt
                      JOIN room_type_bed_types AS rtbt ON rtbt.bed_type_id = bt.id
                      WHERE rtbt.room_type_id = rts.id
                  ), '') || ' ' ||
                  COALESCE(b2.booking_status::text, '') || ' ' ||
                  COALESCE(b2.payment_status::text, '') || ' ' ||
                  COALESCE(b2.total_amount::text, '') || ' ' ||
                  to_char(b2.check_in, 'YYYY-MM-DD') || ' ' ||
                  to_char(b2.check_out, 'YYYY-MM-DD') || ' ' ||
                  to_char(b2.created_at, 'YYYY-MM-DD HH24:MI:SS') || ' ' ||
                  to_char(b2.updated_at, 'YYYY-MM-DD HH24:MI:SS') AS search_text
              FROM bookings AS b2
              JOIN rooms AS r ON r.id = b2.room_id
              JOIN room_type_with_sizes AS rts ON rts.id = r.room_type_id
              LEFT JOIN floors AS f ON f.id = r.floor_id
              JOIN users AS u ON u.id = b2.user_id
              LEFT JOIN profiles AS p ON p.user_id = u.id
              LEFT JOIN roles AS rl ON rl.id = u.role_id
          ) AS sub
          WHERE b.id = sub.booking_id;
      """)




        db.execute(backfill_search_text)
        db.commit()

        print("Existing booking records successfully backfilled with search_text values!")

    except Exception as e:
        db.rollback()
        print("Error while altering table:", e)
    finally:
        db.close()

#---------------------------------------------------------------------------------------------------------------------------------------

def floors_search_vector():
    db = SessionLocal()
    try:
        drop_trigger = text("""
        DROP TRIGGER IF EXISTS trg_update_floors_search_vector ON floors;
        """)

        drop_function = text("""
        DROP FUNCTION IF EXISTS update_floors_search_vector() CASCADE;
        """)

        drop_index = text("""
        DROP INDEX IF EXISTS floors_fts;
        """)

        drop_column = text("""
        ALTER TABLE floors DROP COLUMN IF EXISTS search_vector;
        """)

        db.execute(drop_trigger)
        db.execute(drop_function)
        db.execute(drop_index)
        db.execute(drop_column)
        db.commit()

        print("Old trigger, function, index, and column dropped successfully.")


        add_search_vector_column = text("""
        ALTER TABLE  floors
        ADD COLUMN IF NOT EXISTS search_vector tsvector;
        """)

        add_trigger_function = text("""
        CREATE OR REPLACE FUNCTION update_floors_search_vector()
        RETURNS trigger AS $$
        BEGIN
        
          NEW.search_vector :=
            setweight(to_tsvector('english', COALESCE(NEW.floor_no::text, '')), 'A') ||
            setweight(to_tsvector('english', to_char(NEW.created_at, 'YYYY-MM-DD HH24:MI:SS')), 'C')||
            setweight(to_tsvector('english', to_char(NEW.updated_at, 'YYYY-MM-DD HH24:MI:SS')), 'C');
            
          RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
        """)

        connect_function = text("""
        CREATE TRIGGER trg_update_floors_search_vector
        BEFORE INSERT OR UPDATE ON floors
        FOR EACH ROW
        EXECUTE FUNCTION update_floors_search_vector();
        """)

        add_gin_index = text("""
        CREATE INDEX IF NOT EXISTS floors_fts 
        ON floors USING gin(search_vector);
        """)

        
        db.execute(add_search_vector_column)
        db.execute(add_trigger_function)
        db.execute(connect_function)
        db.execute(add_gin_index)
        db.commit()

        print("Search vector column, trigger, and index recreated successfully!")

        backfill_search_vector = text("""
        UPDATE floors
        SET search_vector =
          setweight(to_tsvector('english', COALESCE(floor_no::text, '')), 'A') ||
          setweight(to_tsvector('english', to_char(created_at, 'YYYY-MM-DD HH24:MI:SS')), 'C')||
          setweight(to_tsvector('english', to_char(updated_at, 'YYYY-MM-DD HH24:MI:SS')), 'C');
        """)

        db.execute(backfill_search_vector)
        db.commit()
        print("Existing rooms records successfully updated with search_vector values!")

    except Exception as e:
        db.rollback()
        print("Error while altering table:", e)

    finally:
        db.close()

def floors_search_text():
    db = SessionLocal()
    try:
        # Drop old objects if exist
        drop_trigger = text("""
        DROP TRIGGER IF EXISTS trg_update_floors_search_text ON floors;
        """)

        drop_function = text("""
        DROP FUNCTION IF EXISTS update_floors_search_text() CASCADE;
        """)

        drop_index = text("""
        DROP INDEX IF EXISTS floors_trgm_idx;
        """)

        drop_column = text("""
        ALTER TABLE floors DROP COLUMN IF EXISTS search_text;
        """)

        db.execute(drop_trigger)
        db.execute(drop_function)
        db.execute(drop_index)
        db.execute(drop_column)
        db.commit()

        print("Old trigger, function, index, and column dropped successfully for floors_search_text.")

        # Add column
        add_search_text_column = text("""
        ALTER TABLE floors
        ADD COLUMN IF NOT EXISTS search_text TEXT;
        """)

        db.execute(add_search_text_column)
        db.commit()

        # Trigger function for maintaining search_text
        add_trigger_function = text("""
        CREATE OR REPLACE FUNCTION update_floors_search_text()
        RETURNS trigger AS $$
        BEGIN
          NEW.search_text :=
            COALESCE(NEW.floor_no::text, '') || ' ' ||
            COALESCE(to_char(NEW.created_at, 'YYYY-MM-DD HH24:MI:SS'), '') || ' ' ||
            COALESCE(to_char(NEW.updated_at, 'YYYY-MM-DD HH24:MI:SS'), '');
          RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
        """)

        # Create trigger to update on insert/update
        connect_function = text("""
        CREATE TRIGGER trg_update_floors_search_text
        BEFORE INSERT OR UPDATE ON floors
        FOR EACH ROW
        EXECUTE FUNCTION update_floors_search_text();
        """)

        db.execute(add_trigger_function)
        db.execute(connect_function)
        db.commit()

        print("Trigger and function created successfully for floors_search_text.")

        # Add trigram index for prefix/suffix/substring search
        add_trgm_index = text("""
        CREATE INDEX IF NOT EXISTS floors_trgm_idx
        ON floors
        USING gin(search_text gin_trgm_ops);
        """)

        db.execute(add_trgm_index)
        db.commit()

        # Backfill existing rows
        backfill = text("""
        UPDATE floors
        SET search_text =
          COALESCE(floor_no::text, '') || ' ' ||
          COALESCE(to_char(created_at, 'YYYY-MM-DD HH24:MI:SS'), '') || ' ' ||
          COALESCE(to_char(updated_at, 'YYYY-MM-DD HH24:MI:SS'), '');
        """)

        db.execute(backfill)
        db.commit()

        print("Existing floor records successfully updated with search_text values!")

    except Exception as e:
        db.rollback()
        print("Error while creating floors_search_text:", e)
    finally:
        db.close()

#---------------------------------------------------------------------------------------------------------------------------------------

def features_search_vector():
    db = SessionLocal()
    try:
        drop_trigger = text("""
        DROP TRIGGER IF EXISTS trg_update_features_search_vector ON features;
        """)

        drop_function = text("""
        DROP FUNCTION IF EXISTS update_features_search_vector() CASCADE;
        """)

        drop_index = text("""
        DROP INDEX IF EXISTS features_fts;
        """)

        drop_column = text("""
        ALTER TABLE features DROP COLUMN IF EXISTS search_vector;
        """)

        db.execute(drop_trigger)
        db.execute(drop_function)
        db.execute(drop_index)
        db.execute(drop_column)
        db.commit()

        print("Old trigger, function, index, and column dropped successfully.")

        add_search_vector_column = text("""
        ALTER TABLE  features
        ADD COLUMN IF NOT EXISTS search_vector tsvector;
        """)

        add_trigger_function = text("""
        CREATE OR REPLACE FUNCTION update_features_search_vector()
        RETURNS trigger AS $$
        BEGIN
        
          NEW.search_vector :=
            setweight(to_tsvector('english', COALESCE(NEW.feature_name, '')), 'A') ||
            setweight(to_tsvector('english', to_char(NEW.created_at, 'YYYY-MM-DD HH24:MI:SS')), 'C')||
            setweight(to_tsvector('english', to_char(NEW.updated_at, 'YYYY-MM-DD HH24:MI:SS')), 'C');
            
          RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
        """)

        connect_function = text("""
        CREATE TRIGGER trg_update_features_search_vector
        BEFORE INSERT OR UPDATE ON features
        FOR EACH ROW
        EXECUTE FUNCTION update_features_search_vector();
        """)

        add_gin_index = text("""
        CREATE INDEX IF NOT EXISTS features_fts 
        ON features USING gin(search_vector);
        """)

        
        db.execute(add_search_vector_column)
        db.execute(add_trigger_function)
        db.execute(connect_function)
        db.execute(add_gin_index)
        db.commit()

        print("Search vector column, trigger, and index recreated successfully!")

        backfill_search_vector = text("""
        UPDATE features
        SET search_vector =
          setweight(to_tsvector('english', COALESCE(feature_name, '')), 'A') ||
          setweight(to_tsvector('english', to_char(created_at, 'YYYY-MM-DD HH24:MI:SS')), 'C')||
          setweight(to_tsvector('english', to_char(updated_at, 'YYYY-MM-DD HH24:MI:SS')), 'C');
        """)

        db.execute(backfill_search_vector)
        db.commit()
        print("Existing rooms records successfully updated with search_vector values!")

    except Exception as e:
        db.rollback()
        print("Error while altering table:", e)

    finally:
        db.close()

def features_search_text():
    db = SessionLocal()
    try:
        # --- Drop existing objects if any ---
        drop_trigger = text("""
        DROP TRIGGER IF EXISTS trg_update_features_search_text ON features;
        """)

        drop_function = text("""
        DROP FUNCTION IF EXISTS update_features_search_text() CASCADE;
        """)

        drop_index = text("""
        DROP INDEX IF EXISTS features_trgm_idx;
        """)

        drop_column = text("""
        ALTER TABLE features DROP COLUMN IF EXISTS search_text;
        """)

        db.execute(drop_trigger)
        db.execute(drop_function)
        db.execute(drop_index)
        db.execute(drop_column)
        db.commit()
        print("Old trigger, function, index, and column dropped successfully for features_search_text.")


        # --- Add search_text column ---
        add_search_text_column = text("""
        ALTER TABLE features
        ADD COLUMN IF NOT EXISTS search_text TEXT;
        """)
        db.execute(add_search_text_column)
        db.commit()


        # --- Create trigger function ---
        add_trigger_function = text("""
        CREATE OR REPLACE FUNCTION update_features_search_text()
        RETURNS trigger AS $$
        BEGIN
          NEW.search_text :=
            COALESCE(NEW.feature_name, '') || ' ' ||
            COALESCE(to_char(NEW.created_at, 'YYYY-MM-DD HH24:MI:SS'), '') || ' ' ||
            COALESCE(to_char(NEW.updated_at, 'YYYY-MM-DD HH24:MI:SS'), '');
          RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
        """)

        # --- Create trigger ---
        connect_function = text("""
        CREATE TRIGGER trg_update_features_search_text
        BEFORE INSERT OR UPDATE ON features
        FOR EACH ROW
        EXECUTE FUNCTION update_features_search_text();
        """)

        db.execute(add_trigger_function)
        db.execute(connect_function)
        db.commit()
        print("Trigger and function created successfully for features_search_text.")


        # --- Create trigram index ---
        add_trgm_index = text("""
        CREATE INDEX IF NOT EXISTS features_trgm_idx
        ON features
        USING gin(search_text gin_trgm_ops);
        """)
        db.execute(add_trgm_index)
        db.commit()


        # --- Backfill existing rows ---
        backfill = text("""
        UPDATE features
        SET search_text =
          COALESCE(feature_name, '') || ' ' ||
          COALESCE(to_char(created_at, 'YYYY-MM-DD HH24:MI:SS'), '') || ' ' ||
          COALESCE(to_char(updated_at, 'YYYY-MM-DD HH24:MI:SS'), '');
        """)
        db.execute(backfill)
        db.commit()

        print("Existing feature records successfully updated with search_text values!")

    except Exception as e:
        db.rollback()
        print("Error while creating features_search_text:", e)
    finally:
        db.close()

#------------------------------------------------------------------------------------------------------

def addons_search_vector():
    db = SessionLocal()
    try:
        drop_trigger = text("""
        DROP TRIGGER IF EXISTS trg_update_addons_search_vector ON addons;
        """)

        drop_function = text("""
        DROP FUNCTION IF EXISTS update_addons_search_vector() CASCADE;
        """)

        drop_index = text("""
        DROP INDEX IF EXISTS addons_fts;
        """)

        drop_column = text("""
        ALTER TABLE addons DROP COLUMN IF EXISTS search_vector;
        """)

        db.execute(drop_trigger)
        db.execute(drop_function)
        db.execute(drop_index)
        db.execute(drop_column)
        db.commit()

        print("Old trigger, function, index, and column dropped successfully.")

        add_search_vector_column = text("""
        ALTER TABLE  addons
        ADD COLUMN IF NOT EXISTS search_vector tsvector;
        """)

        add_trigger_function = text("""
        CREATE OR REPLACE FUNCTION update_addons_search_vector()
        RETURNS trigger AS $$
        BEGIN
        
          NEW.search_vector :=
            setweight(to_tsvector('english', COALESCE(NEW.addon_name, '')), 'A') ||
            setweight(to_tsvector('english', COALESCE(NEW.base_price :: text, '')), 'B') ||
            setweight(to_tsvector('english', to_char(NEW.created_at, 'YYYY-MM-DD HH24:MI:SS')), 'C')||
            setweight(to_tsvector('english', to_char(NEW.updated_at, 'YYYY-MM-DD HH24:MI:SS')), 'C');
            
          RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
        """)

        connect_function = text("""
        CREATE TRIGGER trg_update_addons_search_vector
        BEFORE INSERT OR UPDATE ON addons
        FOR EACH ROW
        EXECUTE FUNCTION update_addons_search_vector();
        """)

        add_gin_index = text("""
        CREATE INDEX IF NOT EXISTS addons_fts 
        ON addons USING gin(search_vector);
        """)

        
        db.execute(add_search_vector_column)
        db.execute(add_trigger_function)
        db.execute(connect_function)
        db.execute(add_gin_index)
        db.commit()

        print("Search vector column, trigger, and index recreated successfully!")

        backfill_search_vector = text("""
        UPDATE addons
        SET search_vector =
          setweight(to_tsvector('english', COALESCE(addon_name, '')), 'A') ||
          setweight(to_tsvector('english', COALESCE(base_price :: text, '')), 'B') ||
          setweight(to_tsvector('english', to_char(created_at, 'YYYY-MM-DD HH24:MI:SS')), 'C')||
          setweight(to_tsvector('english', to_char(updated_at, 'YYYY-MM-DD HH24:MI:SS')), 'C');
        """)

        db.execute(backfill_search_vector)
        db.commit()
        print("Existing rooms records successfully updated with search_vector values!")

    except Exception as e:
        db.rollback()
        print("Error while altering table:", e)

    finally:
        db.close()

def addons_search_text():
    db = SessionLocal()
    try:
        # --- Drop existing objects if any ---
        drop_trigger = text("""
        DROP TRIGGER IF EXISTS trg_update_addons_search_text ON addons;
        """)

        drop_function = text("""
        DROP FUNCTION IF EXISTS update_addons_search_text() CASCADE;
        """)

        drop_index = text("""
        DROP INDEX IF EXISTS addons_trgm_idx;
        """)

        drop_column = text("""
        ALTER TABLE addons DROP COLUMN IF EXISTS search_text;
        """)

        db.execute(drop_trigger)
        db.execute(drop_function)
        db.execute(drop_index)
        db.execute(drop_column)
        db.commit()
        print("Old trigger, function, index, and column dropped successfully for addons_search_text.")


        # --- Add search_text column ---
        add_search_text_column = text("""
        ALTER TABLE addons
        ADD COLUMN IF NOT EXISTS search_text TEXT;
        """)
        db.execute(add_search_text_column)
        db.commit()


        # --- Create trigger function ---
        add_trigger_function = text("""
        CREATE OR REPLACE FUNCTION update_addons_search_text()
        RETURNS trigger AS $$
        BEGIN
          NEW.search_text :=
            COALESCE(NEW.addon_name, '') || ' ' ||
            COALESCE(NEW.base_price::text, '') || ' ' ||
            COALESCE(to_char(NEW.created_at, 'YYYY-MM-DD HH24:MI:SS'), '') || ' ' ||
            COALESCE(to_char(NEW.updated_at, 'YYYY-MM-DD HH24:MI:SS'), '');
          RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
        """)

        # --- Create trigger ---
        connect_function = text("""
        CREATE TRIGGER trg_update_addons_search_text
        BEFORE INSERT OR UPDATE ON addons
        FOR EACH ROW
        EXECUTE FUNCTION update_addons_search_text();
        """)

        db.execute(add_trigger_function)
        db.execute(connect_function)
        db.commit()
        print("Trigger and function created successfully for addons_search_text.")


        # --- Create trigram index ---
        add_trgm_index = text("""
        CREATE INDEX IF NOT EXISTS addons_trgm_idx
        ON addons
        USING gin(search_text gin_trgm_ops);
        """)
        db.execute(add_trgm_index)
        db.commit()


        # --- Backfill existing rows ---
        backfill = text("""
        UPDATE addons
        SET search_text =
          COALESCE(addon_name, '') || ' ' ||
          COALESCE(base_price::text, '') || ' ' ||
          COALESCE(to_char(created_at, 'YYYY-MM-DD HH24:MI:SS'), '') || ' ' ||
          COALESCE(to_char(updated_at, 'YYYY-MM-DD HH24:MI:SS'), '');
        """)
        db.execute(backfill)
        db.commit()

        print("Existing addon records successfully updated with search_text values!")

    except Exception as e:
        db.rollback()
        print("Error while creating addons_search_text:", e)
    finally:
        db.close()

#-----------------------------------------------------------------------------------------------------------------

def bed_types_search_vector():
    db = SessionLocal()
    try:
        drop_trigger = text("""
        DROP TRIGGER IF EXISTS trg_update_bed_types_search_vector ON bed_types;
        """)

        drop_function = text("""
        DROP FUNCTION IF EXISTS update_bed_types_search_vector() CASCADE;
        """)

        drop_index = text("""
        DROP INDEX IF EXISTS bed_types_fts;
        """)

        drop_column = text("""
        ALTER TABLE bed_types DROP COLUMN IF EXISTS search_vector;
        """)

        db.execute(drop_trigger)
        db.execute(drop_function)
        db.execute(drop_index)
        db.execute(drop_column)
        db.commit()

        print("Old trigger, function, index, and column dropped successfully.")

        add_search_vector_column = text("""
        ALTER TABLE  bed_types
        ADD COLUMN IF NOT EXISTS search_vector tsvector;
        """)

        add_trigger_function = text("""
        CREATE OR REPLACE FUNCTION update_bed_types_search_vector()
        RETURNS trigger AS $$
        
        BEGIN
        
          NEW.search_vector :=
            setweight(to_tsvector('english', COALESCE(NEW.bed_type_name, '')), 'A') ||
            setweight(to_tsvector('english', to_char(NEW.created_at, 'YYYY-MM-DD HH24:MI:SS')), 'C')||
            setweight(to_tsvector('english', to_char(NEW.updated_at, 'YYYY-MM-DD HH24:MI:SS')), 'C');
            
          RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
        """)

        connect_function = text("""
        CREATE TRIGGER trg_update_bed_types_search_vector
        BEFORE INSERT OR UPDATE ON bed_types
        FOR EACH ROW
        EXECUTE FUNCTION update_bed_types_search_vector();
        """)

        add_gin_index = text("""
        CREATE INDEX IF NOT EXISTS bed_types_fts 
        ON bed_types USING gin(search_vector);
        """)

        
        db.execute(add_search_vector_column)
        db.execute(add_trigger_function)
        db.execute(connect_function)
        db.execute(add_gin_index)
        db.commit()

        print("Search vector column, trigger, and index recreated successfully!")

        backfill_search_vector = text("""
        UPDATE bed_types
        SET search_vector =
          setweight(to_tsvector('english', COALESCE(bed_type_name, '')), 'A') ||
          setweight(to_tsvector('english', to_char(created_at, 'YYYY-MM-DD HH24:MI:SS')), 'C')||
          setweight(to_tsvector('english', to_char(updated_at, 'YYYY-MM-DD HH24:MI:SS')), 'C');
        """)

        db.execute(backfill_search_vector)
        db.commit()
        print("Existing rooms records successfully updated with search_vector values!")

    except Exception as e:
        db.rollback()
        print("Error while altering table:", e)

    finally:
        db.close()

def bed_types_search_text():
    db = SessionLocal()
    try:
        # --- DROP existing objects if they exist ---
        drop_trigger = text("""
        DROP TRIGGER IF EXISTS trg_update_bed_types_search_text ON bed_types;
        """)

        drop_function = text("""
        DROP FUNCTION IF EXISTS update_bed_types_search_text() CASCADE;
        """)

        drop_index = text("""
        DROP INDEX IF EXISTS bed_types_trgm_idx;
        """)

        drop_column = text("""
        ALTER TABLE bed_types DROP COLUMN IF EXISTS search_text;
        """)

        db.execute(drop_trigger)
        db.execute(drop_function)
        db.execute(drop_index)
        db.execute(drop_column)
        db.commit()
        print("Old trigger, function, index, and column dropped successfully.")

        # --- Add new column ---
        add_search_text_column = text("""
        ALTER TABLE bed_types
        ADD COLUMN IF NOT EXISTS search_text TEXT;
        """)

        # --- Create trigger function ---
        add_trigger_function = text("""
        CREATE OR REPLACE FUNCTION update_bed_types_search_text()
        RETURNS trigger AS $$
        BEGIN
          NEW.search_text :=
              COALESCE(NEW.bed_type_name, '') || ' ' ||
              COALESCE(to_char(NEW.created_at, 'YYYY-MM-DD HH24:MI:SS'), '') || ' ' ||
              COALESCE(to_char(NEW.updated_at, 'YYYY-MM-DD HH24:MI:SS'), '');
          RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
        """)

        # --- Create trigger ---
        connect_function = text("""
        CREATE TRIGGER trg_update_bed_types_search_text
        BEFORE INSERT OR UPDATE ON bed_types
        FOR EACH ROW
        EXECUTE FUNCTION update_bed_types_search_text();
        """)

        # --- Create GIN index using pg_trgm ---
        add_gin_index = text("""
        CREATE INDEX IF NOT EXISTS bed_types_trgm_idx
        ON bed_types USING gin (search_text gin_trgm_ops);
        """)

        db.execute(add_search_text_column)
        db.execute(add_trigger_function)
        db.execute(connect_function)
        db.execute(add_gin_index)
        db.commit()
        print("search_text column, trigger, and trigram index created successfully!")

        # --- Backfill data ---
        backfill_search_text = text("""
        UPDATE bed_types
        SET search_text =
            COALESCE(bed_type_name, '') || ' ' ||
            COALESCE(to_char(created_at, 'YYYY-MM-DD HH24:MI:SS'), '') || ' ' ||
            COALESCE(to_char(updated_at, 'YYYY-MM-DD HH24:MI:SS'), '');
        """)

        db.execute(backfill_search_text)
        db.commit()
        print("Existing bed_types records successfully updated with search_text values!")

    except Exception as e:
        db.rollback()
        print("Error while altering table:", e)

    finally:
        db.close()

#---------------------------------------------------------------------------------------------------------

def users_search_vector():
    db = SessionLocal()
    try:
        drop_trigger = text("""
        DROP TRIGGER IF EXISTS trg_update_users_search_vector ON users;
        """)

        drop_function = text("""
        DROP FUNCTION IF EXISTS update_users_search_vector() CASCADE;
        """)

        drop_index = text("""
        DROP INDEX IF EXISTS users_fts;
        """)

        drop_column = text("""
        ALTER TABLE users DROP COLUMN IF EXISTS search_vector;
        """)

        db.execute(drop_trigger)
        db.execute(drop_function)
        db.execute(drop_index)
        db.execute(drop_column)
        db.commit()

        print("Old trigger, function, index, and column dropped successfully.")

        add_search_vector_column = text("""
        ALTER TABLE  users
        ADD COLUMN IF NOT EXISTS search_vector tsvector;
        """)

        add_trigger_function = text("""
          CREATE OR REPLACE FUNCTION update_users_search_vector()
          RETURNS trigger AS $$

          DECLARE
              dob_text TEXT;
              street TEXT;
              city TEXT;
              state TEXT;
              country TEXT;
              pincode TEXT;
              role_name TEXT;

          BEGIN
              -- Fetch profile details for this user
              SELECT
                  p.dob::text,
                  (p.address).street,
                  (p.address).city,
                  (p.address).state,
                  (p.address).country,
                  (p.address).pincode
              INTO
                  dob_text, street, city, state, country, pincode
              FROM profiles AS p
              WHERE p.user_id = NEW.id;

              -- Fetch role name for this user
              SELECT
                  r.role_name::text
              INTO
                  role_name
              FROM roles AS r
              WHERE r.id = NEW.role_id;

              -- Build search vector
              NEW.search_vector :=
                  setweight(to_tsvector('english', COALESCE(NEW.first_name, '')), 'A') ||
                  setweight(to_tsvector('english', COALESCE(NEW.last_name, '')), 'A') ||
                  setweight(to_tsvector('english', COALESCE(NEW.phone_no, '')), 'A') ||
                  setweight(to_tsvector('english', COALESCE(NEW.email, '')), 'A') ||
                  setweight(to_tsvector('english', COALESCE(dob_text, '')), 'B') ||
                  setweight(to_tsvector('english', COALESCE(street, '')), 'B') ||
                  setweight(to_tsvector('english', COALESCE(city, '')), 'B') ||
                  setweight(to_tsvector('english', COALESCE(state, '')), 'B') ||
                  setweight(to_tsvector('english', COALESCE(country, '')), 'B') ||
                  setweight(to_tsvector('english', COALESCE(pincode, '')), 'B') ||
                  setweight(to_tsvector('english', COALESCE(role_name, '')), 'B') ||
                  setweight(to_tsvector('english', to_char(NEW.created_at, 'YYYY-MM-DD HH24:MI:SS')), 'C');

              RETURN NEW;
          END;
          $$ LANGUAGE plpgsql;
          """)

        connect_function = text("""
        CREATE TRIGGER trg_update_users_search_vector
        BEFORE INSERT OR UPDATE ON users
        FOR EACH ROW
        EXECUTE FUNCTION update_users_search_vector();
        """)

        add_gin_index = text("""
        CREATE INDEX IF NOT EXISTS users_fts 
        ON users USING gin(search_vector);
        """)

        
        db.execute(add_search_vector_column)
        db.execute(add_trigger_function)
        db.execute(connect_function)
        db.execute(add_gin_index)
        db.commit()

        print("Search vector column, trigger, and index recreated successfully!")

        backfill_search_vector = text("""
        UPDATE users AS u
        SET search_vector =
            setweight(to_tsvector('english', COALESCE(u.first_name, '')), 'A') ||
            setweight(to_tsvector('english', COALESCE(u.last_name, '')), 'A') ||
            setweight(to_tsvector('english', COALESCE(u.phone_no, '')), 'A') ||
            setweight(to_tsvector('english', COALESCE(u.email, '')), 'A') ||
            setweight(to_tsvector('english', COALESCE(p.dob::text, '')), 'B') ||
            setweight(to_tsvector('english', COALESCE((p.address).street, '')), 'B') ||
            setweight(to_tsvector('english', COALESCE((p.address).city, '')), 'B') ||
            setweight(to_tsvector('english', COALESCE((p.address).state, '')), 'B') ||
            setweight(to_tsvector('english', COALESCE((p.address).country, '')), 'B') ||
            setweight(to_tsvector('english', COALESCE((p.address).pincode, '')), 'B') ||
            setweight(to_tsvector('english', COALESCE(r.role_name, '')), 'B') ||
            setweight(to_tsvector('english', to_char(u.created_at, 'YYYY-MM-DD HH24:MI:SS')), 'C')
        FROM profiles AS p
        LEFT JOIN roles AS r ON r.id = p.user_id::integer
        WHERE p.user_id = u.id;
        """)
        db.execute(backfill_search_vector)
        db.commit()
        print("Existing rooms records successfully updated with search_vector values!")

    except Exception as e:
        db.rollback()
        print("Error while altering table:", e)

    finally:
        db.close()

def users_search_text():
    db = SessionLocal()
    try:
        # --- DROP existing objects if they exist ---
        drop_trigger = text("""
        DROP TRIGGER IF EXISTS trg_update_users_search_text ON users;
        """)

        drop_function = text("""
        DROP FUNCTION IF EXISTS update_users_search_text() CASCADE;
        """)

        drop_index = text("""
        DROP INDEX IF EXISTS users_trgm_idx;
        """)

        drop_column = text("""
        ALTER TABLE users DROP COLUMN IF EXISTS search_text;
        """)

        db.execute(drop_trigger)
        db.execute(drop_function)
        db.execute(drop_index)
        db.execute(drop_column)
        db.commit()
        print("Old trigger, function, index, and column dropped successfully.")

        # --- Add new column ---
        add_search_text_column = text("""
        ALTER TABLE users
        ADD COLUMN IF NOT EXISTS search_text TEXT;
        """)

        # --- Create trigger function ---
        add_trigger_function = text("""
        CREATE OR REPLACE FUNCTION update_users_search_text()
        RETURNS trigger AS $$
        DECLARE
            dob_text TEXT;
            street TEXT;
            city TEXT;
            state TEXT;
            country TEXT;
            pincode TEXT;
            role_name TEXT;
        BEGIN
            -- Fetch profile details for this user
            SELECT
                p.dob::text,
                (p.address).street,
                (p.address).city,
                (p.address).state,
                (p.address).country,
                (p.address).pincode
            INTO
                dob_text, street, city, state, country, pincode
            FROM profiles AS p
            WHERE p.user_id = NEW.id;

            -- Fetch role name for this user
            SELECT
                r.role_name::text
            INTO
                role_name
            FROM roles AS r
            WHERE r.id = NEW.role_id;

            -- Build searchable combined text
            NEW.search_text :=
                COALESCE(NEW.first_name, '') || ' ' ||
                COALESCE(NEW.last_name, '') || ' ' ||
                COALESCE(NEW.phone_no, '') || ' ' ||
                COALESCE(NEW.email, '') || ' ' ||
                COALESCE(dob_text, '') || ' ' ||
                COALESCE(street, '') || ' ' ||
                COALESCE(city, '') || ' ' ||
                COALESCE(state, '') || ' ' ||
                COALESCE(country, '') || ' ' ||
                COALESCE(pincode, '') || ' ' ||
                COALESCE(role_name, '') || ' ' ||
                COALESCE(to_char(NEW.created_at, 'YYYY-MM-DD HH24:MI:SS'), '');
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
        """)

        # --- Create trigger ---
        connect_function = text("""
        CREATE TRIGGER trg_update_users_search_text
        BEFORE INSERT OR UPDATE ON users
        FOR EACH ROW
        EXECUTE FUNCTION update_users_search_text();
        """)

        # --- Create pg_trgm GIN index ---
        add_gin_index = text("""
        CREATE INDEX IF NOT EXISTS users_trgm_idx
        ON users USING gin (search_text gin_trgm_ops);
        """)

        db.execute(add_search_text_column)
        db.execute(add_trigger_function)
        db.execute(connect_function)
        db.execute(add_gin_index)
        db.commit()
        print("search_text column, trigger, and trigram index created successfully!")

        # --- Backfill existing users ---
        backfill_search_text = text("""
        UPDATE users AS u
        SET search_text = sub.search_text
        FROM (
            SELECT
                u2.id AS user_id,
                COALESCE(u2.first_name, '') || ' ' ||
                COALESCE(u2.last_name, '') || ' ' ||
                COALESCE(u2.phone_no, '') || ' ' ||
                COALESCE(u2.email, '') || ' ' ||
                COALESCE(p.dob::text, '') || ' ' ||
                COALESCE((p.address).street, '') || ' ' ||
                COALESCE((p.address).city, '') || ' ' ||
                COALESCE((p.address).state, '') || ' ' ||
                COALESCE((p.address).country, '') || ' ' ||
                COALESCE((p.address).pincode, '') || ' ' ||
                COALESCE(r.role_name, '') || ' ' ||
                COALESCE(to_char(u2.created_at, 'YYYY-MM-DD HH24:MI:SS'), '') AS search_text
            FROM users AS u2
            LEFT JOIN profiles AS p ON p.user_id = u2.id
            LEFT JOIN roles AS r ON r.id = u2.role_id
        ) AS sub
        WHERE u.id = sub.user_id;
    """)


        db.execute(backfill_search_text)
        db.commit()
        print("Existing users records successfully updated with search_text values!")

    except Exception as e:
        db.rollback()
        print("Error while altering table:", e)

    finally:
        db.close()

def check_and_enable_trigram():
    db = SessionLocal()
    try:
        # Check if pg_trgm is installed
        result = db.execute(text("""
            SELECT * FROM pg_extension WHERE extname = 'pg_trgm';
        """)).fetchone()
        
        if result:
            print("✓ pg_trgm extension is installed")
        else:
            print("✗ pg_trgm extension is NOT installed")
            print("Attempting to install...")
            db.execute(text("CREATE EXTENSION IF NOT EXISTS pg_trgm;"))
            db.commit()
            print("✓ pg_trgm extension installed successfully")
        
        # Test trigram functionality
        test_result = db.execute(text("""
            SELECT similarity('deluxe', 'dul') as sim;
        """)).fetchone()
        
        print(f"✓ Trigram test: similarity('deluxe', 'dul') = {test_result[0]}")
        
    except Exception as e:
        print(f"Error checking trigram: {e}")
        db.rollback()
    finally:
        db.close()
        
if __name__ == "__main__":
    # create_extension()
    # rooms_search_text()
    # rooms_search_vector()
    # rooms_types_search_vector()
    # room_types_search_text()
    # bookings_search_vector()
    # bookings_search_text()
    # floors_search_vector()
    # floors_search_text()
    # features_search_vector()
    # features_search_text()
    # addons_search_vector()
    # addons_search_text()
    # bed_types_search_vector()
    # bed_types_search_text()
    # users_search_vector()
    # users_search_text()
    check_and_enable_trigram()
    
    
    