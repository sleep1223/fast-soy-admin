// 自动生成（cli-gen-web）— 模块：劳务管理
// 由 web/src/locales/locale.ts 通过 import.meta.glob 自动合并到 zh-CN messages。
// 修改字段含义请改对应模型 description 后重跑 cli-gen-web；未涵盖的文案可在本文件追加。

export default {
  route: {
    'labor-management': '劳务管理',
    'labor-management_labor-project': '劳务项目',
    'labor-management_labor-worker': '劳务人员',
    'labor-management_labor-work-hour': '工票对应的工时'
  },
  page: {
    labor_management: {
      common: { status: '状态', form: { status: '请选择状态' } },
      labor_project: {
        importedAt: '导入时间',
        paintingUnavailable: '状态不可用',
        paintingUnavailableHint: '请先完成无需刷漆字段的数据库迁移并重新加载后端',
        workpieceName: '工件名称',
        inconsistent: '不一致',
        notProvided: '未填写',
        paintingStatus: '是否刷漆',
        paintingRequired: '需要刷漆',
        paintingAll: '全部',
        ticketsExistTitle: '该项目已有工票',
        ticketsExistConfirm: '该项目关联的订单已有工票，是否仍要标记为无需刷漆？请确认是否选错项目。已有工票会保留。',
        verifyTicketsFailed: '无法检查关联工票，请确认订单及工票查询权限后重试',
        skipPainting: '无需刷漆',
        orderCount: '订单数量',
        ticketCodeRequired: '请输入不超过 100 个字符的工票码',
        createWorkHourFailed: '工票创建失败，请重试',
        workHoursRequired: '请输入不小于零的工时',
        matchedWorkHours: '工票工时',
        noMatchedWorkHours: '该订单暂无匹配工票',
        workHoursLoadFailed: '工票工时加载失败，请重试',
        matchedOrders: '关联订单',
        noMatchedOrders: '暂无匹配订单',
        ordersLoadFailed: '订单加载失败，请重试',
        retryOrders: '重新加载',
        copy: '复制',
        copied: '已复制',
        copyFailed: '复制失败，请检查浏览器剪贴板权限',
        ticketDropHint: '可直接拖动工票图片到此处识别',
        pageTitle: '劳务项目',
        partNo: '项目号',
        form: { partNo: '请输入项目号' },
        addLaborProject: '新增劳务项目',
        editLaborProject: '编辑劳务项目'
      },
      labor_worker: {
        pageTitle: '劳务人员',
        employeeNo: '工号',
        trade: '工种',
        name: '姓名',
        remark: '备注',
        form: {
          employeeNo: '请输入工号',
          trade: '请输入工种',
          name: '请输入姓名',
          remark: '请输入备注'
        },
        addLaborWorker: '新增劳务人员',
        editLaborWorker: '编辑劳务人员'
      },
      labor_work_hour: {
        assignmentStatus: '分配状态',
        assigned: '已分配',
        unassigned: '未分配',
        allocationMonth: '分配月份',
        allocationMonthRequired: '请选择分配月份',
        ocrUpload: '选择图片识别工票码',
        ocrSelect: '选择识别文字并核对工票码',
        ocrEmpty: '未识别到文字，请手动输入',
        pageTitle: '工票对应的工时',
        ticketCode: '工票码',
        workHours: '工时（小时）',
        orderNo: '订单号',
        worker: '劳务人员',
        form: {
          ticketCode: '请输入工票码',
          workHours: '请输入工时（小时）',
          orderNo: '请输入订单号',
          worker: '请选择劳务人员'
        },
        addLaborWorkHour: '新增工票对应的工时',
        editLaborWorkHour: '编辑工票对应的工时'
      }
    }
  }
};
