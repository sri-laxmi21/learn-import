CREATE OR REPLACE FUNCTION DI_processJobs(
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
    -- STEP 1: Validate required fields in DI_job
    UPDATE DI_job
    SET
        processstatus = 2,
        deleted = 1,
        errormsg = 'Validation Error: Missing required job fields'
    WHERE processstatus = 0
      AND (p_runId IS NULL OR runId = p_runId)
      AND (
          job_code IS NULL OR TRIM(job_code) = '' OR
          job_title IS NULL OR TRIM(job_title) = '' 
          -- min_salary IS NULL OR max_salary IS NULL OR
          -- min_salary > max_salary
      );

    GET DIAGNOSTICS v_failed = ROW_COUNT;

    -- STEP 2: Update existing jobs
    UPDATE Job j
    SET
        name = d.job_title,
        -- department = d.department,
        -- level = d.level,
        -- min_salary = d.min_salary,
        -- max_salary = d.max_salary,
        isdeleted = CASE WHEN (d.active::text = '1' OR d.active::text = 'true') THEN 0 ELSE 1 END,
        ModifiedDate = timezone('utc', now()),
        ModifiedBy = -1,
        CreatedBy = COALESCE(j.CreatedBy, -1),
        CreatedDate = COALESCE(j.CreatedDate, timezone('utc', now()))
    FROM DI_job d
    WHERE LOWER(j.code) = LOWER(d.job_code)
      AND d.processstatus = 0
      AND (p_runId IS NULL OR d.runId = p_runId);

    GET DIAGNOSTICS v_updated = ROW_COUNT;

    -- Mark updated jobs as processed
    UPDATE DI_job d
    SET
        processstatus = 1,
        errormsg = NULL
    FROM Job j
    WHERE LOWER(j.code) = LOWER(d.job_code)
      AND d.processstatus = 0
      AND (p_runId IS NULL OR d.runId = p_runId);

    -- STEP 3: Insert new jobs
    WITH to_insert AS (
        SELECT d.*
        FROM DI_job d
        LEFT JOIN Job j 
          ON LOWER(j.code) = LOWER(d.job_code)
        WHERE d.processstatus = 0
          AND j.code IS NULL
          AND (p_runId IS NULL OR d.runId = p_runId)
    )
    INSERT INTO Job (
        code,
        name,
        -- department,
        -- level,
        -- min_salary,
        -- max_salary,
        isdeleted,
        CreatedDate,
        ModifiedDate,
        CreatedBy,
        ModifiedBy
    )
    SELECT
        job_code,
        job_title,
        -- department,
        -- level,
        -- min_salary,
        -- max_salary,
        CASE WHEN (active::text = '1' OR active::text = 'true') THEN 0 ELSE 1 END,
        timezone('utc', now()),
        timezone('utc', now()),
        -1,
        -1
    FROM to_insert
    ORDER BY processfilepk;

    GET DIAGNOSTICS v_inserted = ROW_COUNT;

    -- Mark inserted jobs as processed
    UPDATE DI_job d
    SET
        processstatus = 1,
        errormsg = NULL
    FROM Job j
    WHERE LOWER(j.code) = LOWER(d.job_code)
      AND d.processstatus = 0
      AND (p_runId IS NULL OR d.runId = p_runId);

    -- RETURN summary
    RETURN QUERY
    SELECT
        v_inserted + v_updated + v_failed,
        v_inserted,
        v_updated,
        v_failed;

END;
$$ LANGUAGE plpgsql;
