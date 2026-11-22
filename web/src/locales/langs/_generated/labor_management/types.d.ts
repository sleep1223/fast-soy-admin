// 自动生成（cli-gen-web）— 模块 labor_management 的 i18n 类型扩展。
// 通过 interface declaration merging 注入 App.I18n.GeneratedPages。

declare global {
  namespace App.I18n {
    interface GeneratedPages {
      labor_management: {
        common: {
          status: string;
          form: { status: string };
        };
        labor_project: {
          importedAt: string;
          paintingUnavailable: string;
          paintingUnavailableHint: string;
          workpieceName: string;
          inconsistent: string;
          notProvided: string;
          paintingStatus: string;
          paintingRequired: string;
          paintingAll: string;
          ticketsExistTitle: string;
          ticketsExistConfirm: string;
          verifyTicketsFailed: string;
          skipPainting: string;
          orderCount: string;
          ticketCodeRequired: string;
          createWorkHourFailed: string;
          workHoursRequired: string;
          matchedWorkHours: string;
          noMatchedWorkHours: string;
          workHoursLoadFailed: string;
          matchedOrders: string;
          noMatchedOrders: string;
          ordersLoadFailed: string;
          retryOrders: string;
          pageTitle: string;
          partNo: string;
          form: { partNo: string };
          addLaborProject: string;
          editLaborProject: string;
        };
        labor_worker: {
          pageTitle: string;
          employeeNo: string;
          trade: string;
          name: string;
          remark: string;
          form: {
            employeeNo: string;
            trade: string;
            name: string;
            remark: string;
          };
          addLaborWorker: string;
          editLaborWorker: string;
        };
        labor_work_hour: {
          assignmentStatus: string;
          assigned: string;
          unassigned: string;
          allocationMonth: string;
          allocationMonthRequired: string;
          ocrUpload: string;
          ocrSelect: string;
          ocrEmpty: string;
          pageTitle: string;
          ticketCode: string;
          workHours: string;
          orderNo: string;
          worker: string;
          form: {
            ticketCode: string;
            workHours: string;
            orderNo: string;
            worker: string;
          };
          addLaborWorkHour: string;
          editLaborWorkHour: string;
        };
      };
    }
  }
}

export {};
