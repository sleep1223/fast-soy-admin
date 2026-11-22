declare namespace Api {
  namespace LaborManagementManage {
    type CommonDeleteParams = { id: string };
    type CommonBatchDeleteParams = { ids: string[] };
    type CommonSearchParams = Pick<Common.PaginatingCommonParams, 'current' | 'size'>;

    // ---- LaborProject ----
    type LaborProject = Common.CommonRecord<{
      partNo: string;
      skipPainting: boolean;
      importedAt: number | null;
      fmtImportedAt?: string;
    }>;

    type LaborProjectAddParams = {
      partNo: string;
      skipPainting?: boolean;
    };

    type LaborProjectUpdateParams = { id?: string; importedAt?: string } & Partial<LaborProjectAddParams>;

    type LaborProjectSearchParams = CommonType.RecordNullable<
      {
        partNo?: string;
        skipPainting?: boolean;
        importedAtStart?: string;
        importedAtEnd?: string;
      } & CommonSearchParams
    >;

    type LaborProjectList = Common.PaginatingQueryRecord<LaborProject>;

    // ---- LaborWorker ----
    type LaborWorker = Common.CommonRecord<{
      employeeNo: string;
      trade: string;
      name: string;
      remark: string | null;
    }>;

    type LaborWorkerAddParams = {
      employeeNo: string;
      trade: string;
      name: string;
      remark?: string | null;
    };

    type LaborWorkerUpdateParams = { id?: string } & Partial<LaborWorkerAddParams>;

    type LaborWorkerSearchParams = CommonType.RecordNullable<
      {
        employeeNo?: string;
        trade?: string;
        name?: string;
        remark?: string;
      } & CommonSearchParams
    >;

    type LaborWorkerList = Common.PaginatingQueryRecord<LaborWorker>;

    // ---- LaborWorkHour ----
    type LaborWorkHour = Common.CommonRecord<{
      ticketCode: string;
      workHours: number;
      orderNo: string;
      workerId: string | null;
      allocationMonth?: string | null;
    }>;

    type LaborWorkHourAddParams = {
      ticketCode: string;
      workHours: number;
      orderNo: string;
      workerId?: string | null;
      allocationMonth?: string | null;
    };

    type LaborWorkHourUpdateParams = { id?: string } & Partial<LaborWorkHourAddParams>;

    type LaborWorkHourSearchParams = CommonType.RecordNullable<
      {
        ticketCode?: string;
        orderNo?: string;
        orderNos?: string[];
        workerId?: string;
        isAssigned?: boolean;
      } & CommonSearchParams
    >;

    type LaborWorkHourList = Common.PaginatingQueryRecord<LaborWorkHour>;
  }
}
