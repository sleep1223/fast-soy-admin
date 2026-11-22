declare namespace Api {
  namespace LaborManagementManage {
    type CommonDeleteParams = { id: string };
    type CommonBatchDeleteParams = { ids: string[] };
    type CommonSearchParams = Pick<Common.PaginatingCommonParams, 'current' | 'size'>;

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
        workerId?: string;
      } & CommonSearchParams
    >;

    type LaborWorkHourList = Common.PaginatingQueryRecord<LaborWorkHour>;
  }
}
