DROP FUNCTION IF EXISTS DI_processSkills(INTEGER);

CREATE OR REPLACE FUNCTION DI_processSkills(
    p_runId INTEGER DEFAULT NULL
)
RETURNS TABLE (
    processed_count INTEGER,
    inserted_count  INTEGER,
    updated_count   INTEGER,
    failed_count    INTEGER,
    deleted_count   INTEGER
) AS $$
DECLARE
    v_inserted INTEGER := 0;
    v_updated  INTEGER := 0;
    v_failed   INTEGER := 0;
    v_deleted  INTEGER := 0;
    v_total    INTEGER := 0;
    v_rows     INTEGER := 0;
BEGIN
    ------------------------------------------------------------------
    -- STEP 0: Normalize DI flags (CRITICAL FIX)
    ------------------------------------------------------------------
    UPDATE di_skill
    SET
        processstatus = 0,
        deleted = COALESCE(deleted,0),
        active  = COALESCE(active,1)
    WHERE processstatus IS NULL
      AND (p_runId IS NULL OR runId = p_runId);

    ------------------------------------------------------------------
    -- STEP 1: Check pending records
    ------------------------------------------------------------------
    SELECT COUNT(*) INTO v_total
    FROM di_skill
    WHERE COALESCE(processstatus,0) IN (0, 1)
      AND (p_runId IS NULL OR runId = p_runId);

    IF v_total = 0 THEN
        RETURN QUERY SELECT 0,0,0,0,0;
        RETURN;
    END IF;

    ------------------------------------------------------------------
    -- STEP 2: Mandatory field validation
    ------------------------------------------------------------------
    UPDATE di_skill
    SET
        processstatus = 1,  -- Changed from 2 to 1 as per requirement
        deleted = 1,
        errormsg = 'Validation Error: Missing Skill Id or Skill Name'
    WHERE COALESCE(processstatus,0) IN (0, 1)
      AND (p_runId IS NULL OR runId = p_runId)
      AND (
            skill_id IS NULL OR TRIM(skill_id) = ''
         OR skill_name IS NULL OR TRIM(skill_name) = ''
      );

    GET DIAGNOSTICS v_deleted = ROW_COUNT;

    ------------------------------------------------------------------
    -- STEP 1.5: Validate SkillType exists (Blocking validation REMOVED to allow insertion)
    ------------------------------------------------------------------
    /*
    UPDATE di_skill d
    SET
        processstatus = 1,
        deleted = 1,
        errormsg = 'Validation Error: Invalid SkillType (Code not found)'
    FROM (
        SELECT d2.processfilepk
        FROM di_skill d2
        LEFT JOIN Code c ON c.CatCd = 1003 AND c.ItmCd = d2.skilltype::text AND c.IsDeleted = 0
        WHERE d2.processstatus = 0
          AND (p_runId IS NULL OR d2.runId = p_runId)
          AND c.ItmId IS NULL
    ) invalid
    WHERE d.processfilepk = invalid.processfilepk;

    DECLARE v_invalid_type INTEGER;
    BEGIN
        GET DIAGNOSTICS v_invalid_type = ROW_COUNT;
        v_deleted := v_deleted + v_invalid_type;
    END;
    */

    -- STEP 2 Update existing skills
    UPDATE Skill s
    SET
        Name = d.skill_name,
        -- Code = d.skill_code, -- Code is typically the key, don't update it unless needed, but here we join on it? 
        -- Wait, join is on LOWER(s.Code) = LOWER(d.skill_id) usually? 
        -- The CSV has skill_id and skill_code. 
        -- If CSV skill_id is the unique key, and it maps to Skill.Code.
        SkillTypeCodeId = c.ItmId,
        -- Category = d.category, -- Column missing
        Description = d.description,
        -- SkillLevel = d.level, -- Column missing
        IsActive = COALESCE(d.active, 1),
        IsDeleted = COALESCE(d.deleted, 0),
        LstUpd = timezone('utc', now()),
        LstUpdBy = -1
        -- CreatedBy/Date seem missing or named differently? 
        -- Output checks: lstupd, lstupdby. No created.
    FROM di_skill d
    LEFT JOIN Code c ON c.CatCd = 1003 AND c.ItmCd = d.skilltype::text AND c.IsDeleted = 0
    WHERE LOWER(s.Code) = LOWER(d.skill_id) -- Assuming skill_id in CSV maps to Code
      AND s.IsDeleted = 0
      AND d.processstatus = 0
      AND (p_runId IS NULL OR d.runId = p_runId);

    GET DIAGNOSTICS v_updated = ROW_COUNT;

    -- Mark updated as processed
    UPDATE di_skill d
    SET
        processstatus = 1,
        objpk = s.SkillPK,
        errormsg = NULL
    FROM Skill s
    WHERE LOWER(s.Code) = LOWER(d.skill_id)
      AND d.processstatus = 0
      AND (p_runId IS NULL OR d.runId = p_runId);

    -- STEP 3: Insert new skills
    WITH to_insert AS (
        SELECT 
            d.skill_id,
            d.skill_name,
            d.skill_code,
            c.ItmId as type_id,
            d.category,
            d.description,
            d.level,
            COALESCE(d.active, 1) as is_active,
            COALESCE(d.deleted, 0) as is_deleted,
            d.processfilepk
        FROM di_skill d
        LEFT JOIN Skill s ON LOWER(s.Code) = LOWER(d.skill_id) AND s.IsDeleted = 0
        LEFT JOIN Code c ON c.CatCd = 1003 AND c.ItmCd = d.skilltype::text AND c.IsDeleted = 0
        WHERE d.processstatus = 0
          AND s.SkillPK IS NULL
          AND (p_runId IS NULL OR d.runId = p_runId)
    )
    INSERT INTO Skill (
        Code,
        Name,
        SkillTypeCodeId,
        -- Category,
        Description,
        -- SkillLevel,
        IsActive,
        IsDeleted,
        LstUpd,
        LstUpdBy
    )
    SELECT
        skill_id, -- Mapping skill_id to Code
        skill_name,
        type_id,
        description,
        is_active,
        is_deleted,
        timezone('utc', now()),
        -1
    FROM to_insert
    ORDER BY processfilepk;

    GET DIAGNOSTICS v_inserted = ROW_COUNT;

    -- Mark inserted as processed
    UPDATE di_skill d
    SET
        processstatus = 1,
        objpk = s.SkillPK,
        errormsg = NULL
    FROM Skill s
    WHERE LOWER(s.Code) = LOWER(d.skill_id)
      AND d.processstatus = 0
      AND (p_runId IS NULL OR d.runId = p_runId);

    -- STEP 4: Remaining failures
    UPDATE di_skill
    SET
        processstatus = 1,  -- Changed from 2 to 1 as per requirement
        deleted = 1,
        errormsg = 'Processing Error: Failed to insert/update (Check SkillType)'
    WHERE processstatus = 0
      AND (p_runId IS NULL OR runId = p_runId);

    GET DIAGNOSTICS v_failed = ROW_COUNT;

    RETURN QUERY
    SELECT
        v_inserted + v_updated + v_failed + v_deleted,
        v_inserted,
        v_updated,
        v_failed,
        v_deleted;

END;
$$ LANGUAGE plpgsql;
