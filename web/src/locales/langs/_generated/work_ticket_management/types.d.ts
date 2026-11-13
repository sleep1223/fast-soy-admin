// 自动生成（cli-gen-web）— 模块 work_ticket_management 的 i18n 类型扩展。
// 通过 interface declaration merging 注入 App.I18n.GeneratedPages。

declare global {
  namespace App.I18n {
    interface GeneratedPages {
      work_ticket_management: {
        common: {
          status: string;
          form: { status: string };
        };
        production_unit: {
          pageTitle: string;
          code: string;
          name: string;
          enabled: string;
          remark: string;
          form: {
            code: string;
            name: string;
            enabled: string;
            remark: string;
          };
          addProductionUnit: string;
          editProductionUnit: string;
        };
        worker: {
          pageTitle: string;
          workerNo: string;
          name: string;
          enabled: string;
          remark: string;
          productionUnit: string;
          form: {
            workerNo: string;
            name: string;
            enabled: string;
            remark: string;
            productionUnit: string;
          };
          addWorker: string;
          editWorker: string;
        };
        order_unit_mapping: {
          pageTitle: string;
          remark: string;
          order: string;
          productionUnit: string;
          form: {
            remark: string;
            order: string;
            productionUnit: string;
          };
          addOrderUnitMapping: string;
          editOrderUnitMapping: string;
        };
        work_month: {
          pageTitle: string;
          yearMonth: string;
          status: string;
          remark: string;
          revision: string;
          closedAt: string;
          closedBy: string;
          reopenedAt: string;
          reopenCount: string;
          productionUnit: string;
          form: {
            yearMonth: string;
            status: string;
            remark: string;
            revision: string;
            closedAt: string;
            closedBy: string;
            reopenedAt: string;
            reopenCount: string;
            productionUnit: string;
          };
          addWorkMonth: string;
          editWorkMonth: string;
        };
        monthly_import_batch: {
          pageTitle: string;
          sourceType: string;
          status: string;
          sourceName: string;
          contentHash: string;
          rowCount: string;
          voidReason: string;
          voidedAt: string;
          voidedBy: string;
          remark: string;
          workMonth: string;
          form: {
            sourceType: string;
            status: string;
            sourceName: string;
            contentHash: string;
            rowCount: string;
            voidReason: string;
            voidedAt: string;
            voidedBy: string;
            remark: string;
            workMonth: string;
          };
          addMonthlyImportBatch: string;
          editMonthlyImportBatch: string;
        };
        monthly_import_row: {
          pageTitle: string;
          rowNumber: string;
          rawPartNo: string;
          normalizedPartNo: string;
          matchStatus: string;
          matchSource: string;
          sourceQuantity: string;
          rawData: string;
          handlingStatus: string;
          handlingNote: string;
          handledAt: string;
          handledBy: string;
          note: string;
          batch: string;
          order: string;
          duplicateOfRow: string;
          form: {
            rowNumber: string;
            rawPartNo: string;
            normalizedPartNo: string;
            matchStatus: string;
            matchSource: string;
            sourceQuantity: string;
            rawData: string;
            handlingStatus: string;
            handlingNote: string;
            handledAt: string;
            handledBy: string;
            note: string;
            batch: string;
            order: string;
            duplicateOfRow: string;
          };
          addMonthlyImportRow: string;
          editMonthlyImportRow: string;
        };
        work_ticket: {
          pageTitle: string;
          orderNoSnapshot: string;
          partNoSnapshot: string;
          nameSnapshot: string;
          ticketCode: string;
          ticketCodeKey: string;
          codeSource: string;
          codeRuleVersion: string;
          codeConfidence: string;
          status: string;
          reconcileStatus: string;
          reconcileNote: string;
          voidReason: string;
          voidedAt: string;
          voidedBy: string;
          remark: string;
          revision: string;
          workMonth: string;
          order: string;
          sourceImportRow: string;
          form: {
            orderNoSnapshot: string;
            partNoSnapshot: string;
            nameSnapshot: string;
            ticketCode: string;
            ticketCodeKey: string;
            codeSource: string;
            codeRuleVersion: string;
            codeConfidence: string;
            status: string;
            reconcileStatus: string;
            reconcileNote: string;
            voidReason: string;
            voidedAt: string;
            voidedBy: string;
            remark: string;
            revision: string;
            workMonth: string;
            order: string;
            sourceImportRow: string;
          };
          addWorkTicket: string;
          editWorkTicket: string;
        };
        work_ticket_assignment: {
          pageTitle: string;
          source: string;
          remark: string;
          ticket: string;
          worker: string;
          form: {
            source: string;
            remark: string;
            ticket: string;
            worker: string;
          };
          addWorkTicketAssignment: string;
          editWorkTicketAssignment: string;
        };
        work_time_entry: {
          pageTitle: string;
          workDate: string;
          accountingMonth: string;
          hours: string;
          remark: string;
          assignment: string;
          form: {
            workDate: string;
            accountingMonth: string;
            hours: string;
            remark: string;
            assignment: string;
          };
          addWorkTimeEntry: string;
          editWorkTimeEntry: string;
        };
        work_month_status_log: {
          pageTitle: string;
          fromStatus: string;
          toStatus: string;
          action: string;
          reason: string;
          summary: string;
          workMonth: string;
          form: {
            fromStatus: string;
            toStatus: string;
            action: string;
            reason: string;
            summary: string;
            workMonth: string;
          };
          addWorkMonthStatusLog: string;
          editWorkMonthStatusLog: string;
        };
      };
    }
  }
}

export {};
