// 自动生成（cli-gen-web）— 模块：工票工时管理
// 由 web/src/locales/locale.ts 通过 import.meta.glob 自动合并到 zh-CN messages。
// 修改字段含义请改对应模型 description 后重跑 cli-gen-web；未涵盖的文案可在本文件追加。

export default {
  route: {
    'work-ticket-management': '工票工时管理',
    'work-ticket-management_production-unit': '生产单位',
    'work-ticket-management_worker': '生产人员',
    'work-ticket-management_order-unit-mapping': '订单与生产单位关系',
    'work-ticket-management_work-month': '月度任务',
    'work-ticket-management_monthly-import-batch': '月度导入批次',
    'work-ticket-management_monthly-import-row': '导入原始明细',
    'work-ticket-management_work-ticket': '工票台账',
    'work-ticket-management_work-ticket-assignment': '工票人员分配',
    'work-ticket-management_work-time-entry': '工时明细',
    'work-ticket-management_work-month-status-log': '月度状态日志'
  },
  page: {
    work_ticket_management: {
      common: { status: '状态', form: { status: '请选择状态' } },
      production_unit: {
        pageTitle: '生产单位',
        code: '单位编码',
        name: '单位名称',
        enabled: '是否启用',
        remark: '备注',
        form: {
          code: '请输入单位编码',
          name: '请输入单位名称',
          enabled: '请输入是否启用',
          remark: '请输入备注'
        },
        addProductionUnit: '新增生产单位',
        editProductionUnit: '编辑生产单位'
      },
      worker: {
        pageTitle: '生产人员',
        workerNo: '人员编号',
        name: '姓名',
        enabled: '是否在用',
        remark: '备注',
        productionUnit: '默认所属生产单位',
        form: {
          workerNo: '请输入人员编号',
          name: '请输入姓名',
          enabled: '请输入是否在用',
          remark: '请输入备注',
          productionUnit: '请选择默认所属生产单位'
        },
        addWorker: '新增生产人员',
        editWorker: '编辑生产人员'
      },
      order_unit_mapping: {
        pageTitle: '订单与生产单位关系',
        remark: '备注',
        order: '订单',
        productionUnit: '生产单位',
        form: {
          remark: '请输入备注',
          order: '请选择订单',
          productionUnit: '请选择生产单位'
        },
        addOrderUnitMapping: '新增订单与生产单位关系',
        editOrderUnitMapping: '编辑订单与生产单位关系'
      },
      work_month: {
        pageTitle: '月度任务',
        yearMonth: '归属月份 YYYY-MM',
        status: '状态',
        remark: '备注',
        revision: '修订版本',
        closedAt: '关闭时间',
        closedBy: '关闭人',
        reopenedAt: '最近重开时间',
        reopenCount: '重开次数',
        productionUnit: '生产单位',
        form: {
          yearMonth: '请输入归属月份 YYYY-MM',
          status: '请选择状态',
          remark: '请输入备注',
          revision: '请输入修订版本',
          closedAt: '请输入关闭时间',
          closedBy: '请输入关闭人',
          reopenedAt: '请输入最近重开时间',
          reopenCount: '请输入重开次数',
          productionUnit: '请选择生产单位'
        },
        addWorkMonth: '新增月度任务',
        editWorkMonth: '编辑月度任务'
      },
      monthly_import_batch: {
        pageTitle: '月度导入批次',
        sourceType: '来源类型',
        status: '批次状态',
        sourceName: '来源文件名或说明',
        contentHash: '文件内容 SHA-256',
        rowCount: '来源数据行数',
        voidReason: '作废原因',
        voidedAt: '作废时间',
        voidedBy: '作废人',
        remark: '备注',
        workMonth: '月度任务',
        form: {
          sourceType: '请选择来源类型',
          status: '请选择批次状态',
          sourceName: '请输入来源文件名或说明',
          contentHash: '请输入文件内容 SHA-256',
          rowCount: '请输入来源数据行数',
          voidReason: '请输入作废原因',
          voidedAt: '请输入作废时间',
          voidedBy: '请输入作废人',
          remark: '请输入备注',
          workMonth: '请选择月度任务'
        },
        addMonthlyImportBatch: '新增月度导入批次',
        editMonthlyImportBatch: '编辑月度导入批次'
      },
      monthly_import_row: {
        pageTitle: '导入原始明细',
        rowNumber: '源文件行号',
        rawPartNo: '原始项目号',
        normalizedPartNo: '规范化项目号',
        matchStatus: '订单匹配状态',
        matchSource: '匹配方式',
        sourceQuantity: '来源数量',
        rawData: '原始行数据',
        handlingStatus: '人工处理状态',
        handlingNote: '人工处理说明',
        handledAt: '处理时间',
        handledBy: '处理人',
        note: '备注',
        batch: '导入批次',
        order: '匹配订单',
        duplicateOfRow: '重复来源行',
        form: {
          rowNumber: '请输入源文件行号',
          rawPartNo: '请输入原始项目号',
          normalizedPartNo: '请输入规范化项目号',
          matchStatus: '请选择订单匹配状态',
          matchSource: '请选择匹配方式',
          sourceQuantity: '请输入来源数量',
          rawData: '请输入原始行数据',
          handlingStatus: '请选择人工处理状态',
          handlingNote: '请输入人工处理说明',
          handledAt: '请输入处理时间',
          handledBy: '请输入处理人',
          note: '请输入备注',
          batch: '请选择导入批次',
          order: '请选择匹配订单',
          duplicateOfRow: '请选择重复来源行'
        },
        addMonthlyImportRow: '新增导入原始明细',
        editMonthlyImportRow: '编辑导入原始明细'
      },
      work_ticket: {
        pageTitle: '工票台账',
        orderNoSnapshot: '订单号快照',
        partNoSnapshot: '项目号快照',
        nameSnapshot: '名称快照',
        ticketCode: '工票码',
        ticketCodeKey: '工票码比较键',
        codeSource: '工票码来源',
        codeRuleVersion: '工票码规则版本',
        codeConfidence: 'OCR 置信度',
        status: '工票状态',
        reconcileStatus: '核对状态',
        reconcileNote: '核对说明',
        voidReason: '作废原因',
        voidedAt: '作废时间',
        voidedBy: '作废人',
        remark: '备注',
        revision: '修订版本',
        workMonth: '月度任务',
        order: '关联订单',
        sourceImportRow: '来源导入行',
        form: {
          orderNoSnapshot: '请输入订单号快照',
          partNoSnapshot: '请输入项目号快照',
          nameSnapshot: '请输入名称快照',
          ticketCode: '请输入工票码',
          ticketCodeKey: '请输入工票码比较键',
          codeSource: '请选择工票码来源',
          codeRuleVersion: '请输入工票码规则版本',
          codeConfidence: '请输入OCR 置信度',
          status: '请选择工票状态',
          reconcileStatus: '请选择核对状态',
          reconcileNote: '请输入核对说明',
          voidReason: '请输入作废原因',
          voidedAt: '请输入作废时间',
          voidedBy: '请输入作废人',
          remark: '请输入备注',
          revision: '请输入修订版本',
          workMonth: '请选择月度任务',
          order: '请选择关联订单',
          sourceImportRow: '请选择来源导入行'
        },
        addWorkTicket: '新增工票台账',
        editWorkTicket: '编辑工票台账'
      },
      work_ticket_assignment: {
        pageTitle: '工票人员分配',
        source: '分配来源',
        remark: '备注',
        ticket: '工票',
        worker: '生产人员',
        form: {
          source: '请选择分配来源',
          remark: '请输入备注',
          ticket: '请选择工票',
          worker: '请选择生产人员'
        },
        addWorkTicketAssignment: '新增工票人员分配',
        editWorkTicketAssignment: '编辑工票人员分配'
      },
      work_time_entry: {
        pageTitle: '工时明细',
        workDate: '实际工作日期',
        accountingMonth: '跨月归属月份 YYYY-MM',
        hours: '工时小时',
        remark: '备注',
        assignment: '工票人员分配',
        form: {
          workDate: '请输入实际工作日期',
          accountingMonth: '请输入跨月归属月份 YYYY-MM',
          hours: '请输入工时小时',
          remark: '请输入备注',
          assignment: '请选择工票人员分配'
        },
        addWorkTimeEntry: '新增工时明细',
        editWorkTimeEntry: '编辑工时明细'
      },
      work_month_status_log: {
        pageTitle: '月度状态日志',
        fromStatus: '原状态',
        toStatus: '新状态',
        action: '动作',
        reason: '原因',
        summary: '状态变更统计快照',
        workMonth: '月度任务',
        form: {
          fromStatus: '请选择原状态',
          toStatus: '请选择新状态',
          action: '请选择动作',
          reason: '请输入原因',
          summary: '请输入状态变更统计快照',
          workMonth: '请选择月度任务'
        },
        addWorkMonthStatusLog: '新增月度状态日志',
        editWorkMonthStatusLog: '编辑月度状态日志'
      }
    }
  }
};
