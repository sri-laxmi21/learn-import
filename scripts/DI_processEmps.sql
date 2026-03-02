DROP FUNCTION IF EXISTS DI_processEmps(INTEGER);

CREATE OR REPLACE FUNCTION DI_processEmps(
    p_runId INTEGER DEFAULT NULL
)
RETURNS TABLE(
    processed_count INTEGER,
    inserted_count INTEGER,
    updated_count INTEGER,
    failed_count INTEGER
) AS $$
DECLARE
    v_inserted INTEGER := 0;
    v_updated  INTEGER := 0;
    v_failed   INTEGER := 0;
BEGIN
    ------------------------------------------------------------------
    -- STEP 1: VALIDATION (Required fields)
    ------------------------------------------------------------------
    UPDATE DI_emp
    SET
        processstatus = 1,          -- Changed from 2 to 1 as per requirement
        deleted = 1,
        errormsg = 'Validation Error: Missing required PersonNumber'
    WHERE processstatus = 0
      AND (p_runId IS NULL OR runId = p_runId)
      AND (
            PersonNumber IS NULL OR TRIM(PersonNumber) = ''
      );

    GET DIAGNOSTICS v_failed = ROW_COUNT;

    ------------------------------------------------------------------
    -- STEP 2: UPDATE EXISTING EMPLOYEES
    ------------------------------------------------------------------
    UPDATE Person p
    SET
        firstname        = d.FirstName,
        middlename       = d.MiddleName,
        lastname         = d.LastName,
        preferredname    = d.Preferredname,
        email            = d.Email,
        title            = d.title,
        -- role_cd          = d.Role_Cd, -- Column missing in Person table
        photourl         = d.photourl,
        -- currency_cd      = d.Currency_Cd, -- Column missing in Person table
        statuscodeid     = CASE WHEN d.StatusCodeId ~ '^[0-9]+$' THEN d.StatusCodeId::INTEGER ELSE NULL END,
        typecodeid       = CASE WHEN d.TypeCodeId ~ '^[0-9]+$' THEN d.TypeCodeId::INTEGER ELSE NULL END,
        startdate        = d.StartDate,
        enddate          = d.EndDate,
        city             = d.City,
        state            = d.State,
        -- mgrpersonnumber  = d.MgrPersonNumber, -- Column missing in Person table
        isdeleted        = COALESCE(d.IsDeleted, 0),
        active           = COALESCE(d.Active, 1),
        loginenabled     = COALESCE(d.LoginEnabled, 0),
        inst             = COALESCE(d.Inst, 0),
        ModifiedDate     = timezone('utc', now()),
        ModifiedBy       = -1,
        CreatedBy        = COALESCE(p.CreatedBy, -1),
        CreatedDate      = COALESCE(p.CreatedDate, timezone('utc', now()))
    FROM DI_emp d
    WHERE LOWER(p.personnumber) = LOWER(d.PersonNumber)
      AND d.processstatus = 0
      AND (p_runId IS NULL OR d.runId = p_runId);

    GET DIAGNOSTICS v_updated = ROW_COUNT;

    -- Mark updated as processed
    UPDATE DI_emp d
    SET
        processstatus = 1,
        errormsg = NULL
    FROM Person p
    WHERE LOWER(p.personnumber) = LOWER(d.PersonNumber)
      AND d.processstatus = 0
      AND (p_runId IS NULL OR d.runId = p_runId);

    ------------------------------------------------------------------
    -- STEP 3: INSERT NEW EMPLOYEES
    ------------------------------------------------------------------
    WITH to_insert AS (
        SELECT d.*
        FROM DI_emp d
        LEFT JOIN Person p
          ON LOWER(p.personnumber) = LOWER(d.PersonNumber)
        WHERE d.processstatus = 0
          AND p.personnumber IS NULL
          AND (p_runId IS NULL OR d.runId = p_runId)
    )
    INSERT INTO Person (
        personnumber,
        firstname,
        middlename,
        lastname,
        preferredname,
        email,
        title,
        -- role_cd,
        photourl,
        -- currency_cd,
        statuscodeid,
        typecodeid,
        startdate,
        enddate,
        city,
        state,
        -- mgrpersonnumber,
        isdeleted,
        active,
        loginenabled,
        inst,
        CreatedDate,
        ModifiedDate,
        CreatedBy,
        ModifiedBy
    )
    SELECT
        PersonNumber,
        FirstName,
        MiddleName,
        LastName,
        Preferredname,
        Email,
        title,
        -- Role_Cd,
        photourl,
        -- Currency_Cd,
        CASE WHEN StatusCodeId ~ '^[0-9]+$' THEN StatusCodeId::INTEGER ELSE NULL END,
        CASE WHEN TypeCodeId ~ '^[0-9]+$' THEN TypeCodeId::INTEGER ELSE NULL END,
        StartDate,
        EndDate,
        City,
        State,
        -- MgrPersonNumber,
        COALESCE(IsDeleted, 0),
        COALESCE(Active, 1),
        COALESCE(LoginEnabled, 0),
        COALESCE(Inst, 0),
        timezone('utc', now()),
        timezone('utc', now()),
        -1,
        -1
    FROM to_insert
    ORDER BY processfilepk;

    GET DIAGNOSTICS v_inserted = ROW_COUNT;

    -- Mark inserted as processed
    UPDATE DI_emp d
    SET
        processstatus = 1,
        errormsg = NULL
    FROM Person p
    WHERE LOWER(p.personnumber) = LOWER(d.PersonNumber)
      AND d.processstatus = 0
      AND (p_runId IS NULL OR d.runId = p_runId);

    ------------------------------------------------------------------
    -- RETURN SUMMARY
    ------------------------------------------------------------------
    RETURN QUERY
    SELECT
        v_inserted + v_updated + v_failed,
        v_inserted,
        v_updated,
        v_failed;

END;
$$ LANGUAGE plpgsql;
