DROP FUNCTION IF EXISTS DI_processOrgs(INTEGER);

CREATE OR REPLACE FUNCTION DI_processOrgs(
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
    -- STEP 0: Check pending records
    ------------------------------------------------------------------
    SELECT COUNT(*) INTO v_total
    FROM DI_org
    WHERE processstatus = 0
      AND (p_runId IS NULL OR runId = p_runId);

    IF v_total = 0 THEN
        RETURN QUERY SELECT 0,0,0,0,0;
        RETURN;
    END IF;

    ------------------------------------------------------------------
    -- STEP 1: Mandatory field validation
    ------------------------------------------------------------------
    UPDATE DI_org
    SET
        processstatus = 1,
        deleted = 1,
        errormsg = 'Validation Error: Missing Org Name, Code or Type'
    WHERE processstatus = 0
      AND (p_runId IS NULL OR runId = p_runId)
      AND (
            org_name IS NULL OR TRIM(org_name) = ''
         OR org_code IS NULL OR TRIM(org_code) = ''
         OR orgtype  IS NULL OR TRIM(orgtype)  = ''
      );

    -- Additional check: Validate OrgType exists in Code table
    -- COMMENTED OUT: Allow insertion even if OrgType is missing (will result in NULL OrgTypeCodeId)
    /*
    UPDATE DI_org d
    SET
        processstatus = 1,
        deleted = 1,
        errormsg = 'Validation Error: Invalid OrgType (Code not found)'
    FROM (
        SELECT d2.processfilepk
        FROM DI_org d2
        LEFT JOIN Code c ON c.CatCd = 1001 AND LOWER(c.ItmCd) = LOWER(d2.orgtype) AND c.IsDeleted = 0
        WHERE d2.processstatus = 0
          AND (p_runId IS NULL OR d2.runId = p_runId)
          AND c.ItmId IS NULL
    ) invalid
    WHERE d.processfilepk = invalid.processfilepk;
    */

    GET DIAGNOSTICS v_deleted = ROW_COUNT;

    -- STEP 2: Update existing organizations
    UPDATE Organization o
    SET
        Name = d.org_name,
        Description = d.description,
        ParentOrgFK = p_org.OrgPK,
        OrgTypeCodeId = c.ItmId,
        OrgDomainInd = CASE WHEN d.active = 0 THEN 0 ELSE 1 END,
        IsDeleted = COALESCE(d.deleted, 0),
        ModifiedDate = timezone('utc', now()),
        ModifiedBy = -1,
        CreatedBy = COALESCE(o.CreatedBy, -1),
        CreatedDate = COALESCE(o.CreatedDate, timezone('utc', now()))
    FROM DI_org d
    LEFT JOIN Organization p_org ON LOWER(p_org.Code) = LOWER(d.parent_org_id) AND p_org.IsDeleted = 0
    LEFT JOIN Code c ON c.CatCd = 1001 AND LOWER(c.ItmCd) = LOWER(d.orgtype) AND c.IsDeleted = 0
    WHERE LOWER(o.Code) = LOWER(d.org_code)
      AND o.IsDeleted = 0
      AND d.processstatus = 0
      AND (p_runId IS NULL OR d.runId = p_runId);

    GET DIAGNOSTICS v_updated = ROW_COUNT;

    -- Mark updated as processed
    UPDATE DI_org d
    SET
        processstatus = 1,
        objpk = o.OrgPK,
        errormsg = NULL
    FROM Organization o
    WHERE LOWER(o.Code) = LOWER(d.org_code)
      AND d.processstatus = 0
      AND (p_runId IS NULL OR d.runId = p_runId);

    -- STEP 3: Insert new organizations
    WITH to_insert AS (
        SELECT 
            d.org_code,
            d.org_name,
            d.description,
            p_org.OrgPK as parent_pk,
            c.ItmId as type_id,
            CASE WHEN d.active = 0 THEN 0 ELSE 1 END as domain_ind,
            COALESCE(d.deleted, 0) as is_deleted,
            d.processfilepk
        FROM DI_org d
        LEFT JOIN Organization o ON LOWER(o.Code) = LOWER(d.org_code) AND o.IsDeleted = 0
        LEFT JOIN Organization p_org ON LOWER(p_org.Code) = LOWER(d.parent_org_id) AND p_org.IsDeleted = 0
        LEFT JOIN Code c ON c.CatCd = 1001 AND LOWER(c.ItmCd) = LOWER(d.orgtype) AND c.IsDeleted = 0
        WHERE d.processstatus = 0
          AND o.OrgPK IS NULL
          AND (p_runId IS NULL OR d.runId = p_runId)
    )
    INSERT INTO Organization (
        Code, Name, Description,
        ParentOrgFK, OrgTypeCodeId,
        OrgDomainInd, IsDeleted,
        CreatedDate,
        ModifiedDate,
        CreatedBy,
        ModifiedBy
    )
    SELECT
        org_code,
        org_name,
        description,
        parent_pk,
        type_id,
        domain_ind,
        is_deleted,
        timezone('utc', now()),
        timezone('utc', now()),
        -1,
        -1
    FROM to_insert
    ORDER BY processfilepk;

    GET DIAGNOSTICS v_inserted = ROW_COUNT;

    -- Mark inserted as processed
    UPDATE DI_org d
    SET
        processstatus = 1,
        objpk = o.OrgPK,
        errormsg = NULL
    FROM Organization o
    WHERE LOWER(o.Code) = LOWER(d.org_code)
      AND d.processstatus = 0
      AND (p_runId IS NULL OR d.runId = p_runId);

    -- STEP 4: Remaining failures
    UPDATE DI_org
    SET
        processstatus = 1,
        deleted = 1,
        errormsg = 'Processing Error: Failed to insert/update (Check OrgType or ParentOrg validity)'
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
