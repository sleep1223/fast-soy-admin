const local: App.I18n.BaseSchema = {
  ocrTools: {
    select: 'Choose image',
    replace: 'Replace image',
    dropHint: 'Click to choose an image, or drag/paste a screenshot here.',
    dropUnavailable: 'No image file was available. Copy the screenshot and try again.',
    invalid: 'Choose a non-empty JPG, PNG, GIF or WebP image up to {size} MB',
    recognize: 'Recognize',
    recognizing: 'Recognizing…',
    clear: 'Clear',
    result: 'Recognized text',
    confidence: 'Confidence {value}%',
    lowConfidence: 'Low confidence, review manually',
    emptyText: 'No text recognized. Retry or enter it manually.',
    truncated: 'Too many results; only the first {count} items are returned.',
    failed: 'Recognition failed. Try again.',
    tip: 'The image is recognized in local service memory. It is not stored in the image library, and recognized text is not written to logs.',
    editHint: 'Correct the recognized text here before the business layer parses it.',
    imageAlt: 'Image to recognize'
  },
  imageTools: {
    dropHint: 'Click to upload or drop images here, including downloaded image files from WeChat or WeCom chats.',
    dropUnavailable: 'No image file was available. Download the chat image first, or save it locally and upload it.',
    thumbnail: 'Thumbnail',
    name: 'File name',
    format: 'Format',
    fileSize: 'File size',
    dimensions: 'Dimensions',
    uploader: 'Uploaded by',
    uploadTime: 'Upload time',
    updateTime: 'Updated at',
    detail: 'Details',
    deleteHint: 'Permanently delete the image file and record? Existing references will stop displaying this image.',
    invalidName: 'Enter a name without path separators or control characters',
    renameHint: 'Only the display name changes. Image URLs and existing references remain unchanged.',
    moveEarlier: 'Move image earlier',
    moveLater: 'Move image later',
    imageAlt: 'Image {index}',
    add: 'Upload images',
    invalid: 'Choose a non-empty JPG, PNG, GIF or WebP image up to {size} MB',
    limit: 'Upload up to {count} images',
    tip: 'JPG / PNG / GIF / WebP, up to {size} MB each and {count} images. Click a thumbnail to preview; failed uploads can be retried.',
    settings: 'Local upload settings',
    directory: 'Server storage directory',
    directoryHint:
      'This directory is on the backend server. Relative paths start at the project root. Saving checks write access. Changes affect new uploads only; keep previous directories for existing images. Images are public through random links; do not upload private files.',
    maxSize: 'Maximum image size (MB)',
    library: 'Image library',
    search: 'Search by filename',
    empty: 'No uploaded images',
    copy: 'Copy image link',
    copied: 'Image link copied',
    copyFailed: 'Copy failed. Check browser clipboard permissions.',
    sourceHint:
      'Image fields generate upload controls and preview thumbnails. Names such as avatar, cover, image and images are detected automatically. Add [image] or [images] to other field descriptions. Multiple images use TextField (comma-separated) or JSONField (string array). Declare fields in models.py before parsing again; grant business roles the Upload images button permission.'
  },
  system: {
    title: 'SoybeanAdmin',
    updateTitle: 'System Version Update Notification',
    updateContent: 'A new version of the system has been detected. Do you want to refresh the page immediately?',
    updateConfirm: 'Refresh immediately',
    updateCancel: 'Later'
  },
  common: {
    excelPreview: 'Import preview',
    excelExactMatch:
      'Headers must exactly match a configured name or alias, including case, spaces and character width. Unknown columns are ignored by default. You can map them manually, then validate again.',
    excelSheet: 'Worksheet',
    excelHeaderRow: 'Header row (1–100, blank for auto detection)',
    excelValidate: 'Detect and validate',
    excelSourceColumn: 'Source column',
    excelTargetField: 'Target field',
    excelSamples: 'Samples (first 3 rows)',
    excelSelectField: 'Select a field or ignore',
    excelIgnoreColumn: 'Ignore this column',
    excelRowCount: '{count} non-empty rows; up to 20 validation errors shown',
    excelConfirmImport: 'Confirm import',
    excelImport: 'Import Excel',
    excelExport: 'Export Excel',
    excelExportFiltered: 'Export filtered results',
    excelExportSelected: 'Export selected ({count})',
    excelDetailExport: 'Export parent and details',
    excelParentFields: 'Parent fields included with each detail',
    excelParentFieldsHint:
      'The workbook includes the parent and its detail sheets. Select the parent fields to repeat on each detail row, or clear all.',
    excelTemplate: 'Download import template',
    excelFileLimit: 'Upload an .xlsx file no larger than 5MB',
    excelImportSuccess: 'Created {created} records, updated {updated} records',
    action: 'Action',
    add: 'Add',
    addSuccess: 'Add Success',
    backToHome: 'Back to home',
    batchApprove: 'Batch Approve',
    batchReject: 'Batch Reject',
    batchDelete: 'Batch Delete',
    cancel: 'Cancel',
    close: 'Close',
    check: 'Check',
    selectAll: 'Select All',
    expandColumn: 'Expand Column',
    columnSetting: 'Column Setting',
    config: 'Config',
    confirm: 'Confirm',
    delete: 'Delete',
    deleteSuccess: 'Delete Success',
    confirmDelete: 'Are you sure you want to delete?',
    approve: 'Approve',
    approveSuccess: 'Approve Success',
    confirmApprove: 'Are you sure you want to approve?',
    reject: 'Reject',
    rejectSuccess: 'Approve Reject',
    confirmReject: 'Are you sure you want to reject?',
    edit: 'Edit',
    view: 'View',
    warning: 'Warning',
    error: 'Error',
    index: 'Index',
    keywordSearch: 'Please enter keyword',
    logout: 'Logout',
    logoutConfirm: 'Are you sure you want to log out?',
    lookForward: 'Coming soon',
    modify: 'Modify',
    modifySuccess: 'Modify Success',
    noData: 'No Data',
    operate: 'Operate',
    pleaseCheckValue: 'Please check whether the value is valid',
    refresh: 'Refresh',
    reset: 'Reset',
    search: 'Search',
    switch: 'Switch',
    tip: 'Tip',
    trigger: 'Trigger',
    update: 'Update',
    updateSuccess: 'Update Success',
    userCenter: 'User Center',
    yesOrNo: {
      yes: 'Yes',
      no: 'No'
    }
  },
  request: {
    logout: 'Logout user after request failed',
    logoutMsg: 'User status is invalid, please log in again',
    logoutWithModal: 'Pop up modal after request failed and then log out user',
    logoutWithModalMsg: 'User status is invalid, please log in again',
    refreshToken: 'The requested token has expired, refresh the token',
    tokenExpired: 'The requested token has expired'
  },
  theme: {
    themeDrawerTitle: 'Theme Configuration',
    tabs: {
      appearance: 'Appearance',
      layout: 'Layout',
      general: 'General',
      preset: 'Preset'
    },
    appearance: {
      themeSchema: {
        title: 'Theme Schema',
        light: 'Light',
        dark: 'Dark',
        auto: 'Follow System'
      },
      grayscale: 'Grayscale',
      colourWeakness: 'Colour Weakness',
      themeColor: {
        title: 'Theme Color',
        primary: 'Primary',
        info: 'Info',
        success: 'Success',
        warning: 'Warning',
        error: 'Error',
        followPrimary: 'Follow Primary'
      },
      themeRadius: {
        title: 'Theme Radius'
      },
      recommendColor: 'Apply Recommended Color Algorithm',
      recommendColorDesc: 'The recommended color algorithm refers to',
      preset: {
        title: 'Theme Presets',
        apply: 'Apply',
        applySuccess: 'Preset applied successfully',
        default: {
          name: 'Default Preset',
          desc: 'Default theme preset with balanced settings'
        },
        dark: {
          name: 'Dark Preset',
          desc: 'Dark theme preset for night time usage'
        },
        compact: {
          name: 'Compact Preset',
          desc: 'Compact layout preset for small screens'
        },
        azir: {
          name: "Azir's Preset",
          desc: 'It is a cold and elegant preset that Azir likes'
        }
      }
    },
    layout: {
      layoutMode: {
        title: 'Layout Mode',
        vertical: 'Vertical Mode',
        horizontal: 'Horizontal Mode',
        'vertical-mix': 'Vertical Mix Mode',
        'vertical-hybrid-header-first': 'Left Hybrid Header-First',
        'top-hybrid-sidebar-first': 'Top-Hybrid Sidebar-First',
        'top-hybrid-header-first': 'Top-Hybrid Header-First',
        vertical_detail: 'Vertical menu layout, with the menu on the left and content on the right.',
        'vertical-mix_detail':
          'Vertical mix-menu layout, with the primary menu on the dark left side and the secondary menu on the lighter left side.',
        'vertical-hybrid-header-first_detail':
          'Left hybrid layout, with the primary menu at the top, the secondary menu on the dark left side, and the tertiary menu on the lighter left side.',
        horizontal_detail: 'Horizontal menu layout, with the menu at the top and content below.',
        'top-hybrid-sidebar-first_detail':
          'Top hybrid layout, with the primary menu on the left and the secondary menu at the top.',
        'top-hybrid-header-first_detail':
          'Top hybrid layout, with the primary menu at the top and the secondary menu on the left.'
      },
      tab: {
        title: 'Tab Settings',
        visible: 'Tab Visible',
        cache: 'Tag Bar Info Cache',
        cacheTip: 'One-click to open/close global keepalive',
        height: 'Tab Height',
        mode: {
          title: 'Tab Mode',
          slider: 'Slider',
          chrome: 'Chrome',
          button: 'Button'
        },
        closeByMiddleClick: 'Close Tab by Middle Click',
        closeByMiddleClickTip: 'Enable closing tabs by clicking with the middle mouse button'
      },
      header: {
        title: 'Header Settings',
        height: 'Header Height',
        breadcrumb: {
          visible: 'Breadcrumb Visible',
          showIcon: 'Breadcrumb Icon Visible'
        }
      },
      sider: {
        title: 'Sider Settings',
        inverted: 'Dark Sider',
        width: 'Sider Width',
        collapsedWidth: 'Sider Collapsed Width',
        mixWidth: 'Mix Sider Width',
        mixCollapsedWidth: 'Mix Sider Collapse Width',
        mixChildMenuWidth: 'Mix Child Menu Width',
        autoSelectFirstMenu: 'Auto Select First Submenu',
        autoSelectFirstMenuTip:
          'When a first-level menu is clicked, the first submenu is automatically selected and navigated to the deepest level'
      },
      footer: {
        title: 'Footer Settings',
        visible: 'Footer Visible',
        fixed: 'Fixed Footer',
        height: 'Footer Height',
        right: 'Right Footer'
      },
      content: {
        title: 'Content Area Settings',
        scrollMode: {
          title: 'Scroll Mode',
          tip: 'The theme scroll only scrolls the main part, the outer scroll can carry the header and footer together',
          wrapper: 'Wrapper',
          content: 'Content'
        },
        page: {
          animate: 'Page Animate',
          mode: {
            title: 'Page Animate Mode',
            fade: 'Fade',
            'fade-slide': 'Slide',
            'fade-bottom': 'Fade Zoom',
            'fade-scale': 'Fade Scale',
            'zoom-fade': 'Zoom Fade',
            'zoom-out': 'Zoom Out',
            none: 'None'
          }
        },
        fixedHeaderAndTab: 'Fixed Header And Tab'
      }
    },
    general: {
      title: 'General Settings',
      watermark: {
        title: 'Watermark Settings',
        visible: 'Watermark Full Screen Visible',
        text: 'Custom Watermark Text',
        enableUserName: 'Enable User Name Watermark',
        enableTime: 'Show Current Time',
        timeFormat: 'Time Format'
      },
      multilingual: {
        title: 'Multilingual Settings',
        visible: 'Display multilingual button'
      },
      globalSearch: {
        title: 'Global Search Settings',
        visible: 'Display GlobalSearch button'
      }
    },
    configOperation: {
      copyConfig: 'Copy Config',
      copySuccessMsg: 'Copy Success, Please replace the variable "themeSettings" in "src/theme/settings.ts"',
      resetConfig: 'Reset Config',
      resetSuccessMsg: 'Reset Success'
    }
  },
  route: {
    login: 'Login',
    403: 'No Permission',
    404: 'Page Not Found',
    500: 'Server Error',
    home: 'Home',
    'user-center': 'User Center',
    manage: 'System Manage',
    manage_api: 'API Manage',
    manage_user: 'User Manage',
    'manage_user-detail': 'User Detail',
    manage_role: 'Role Manage',
    manage_menu: 'Menu Manage',
    manage_codegen: 'Code Generator',
    manage_upload: 'Upload Management',
    manage_radar: 'Radar',
    manage_radar_overview: 'Dashboard',
    manage_radar_requests: 'Requests',
    manage_radar_queries: 'SQL Queries',
    manage_radar_exceptions: 'Exceptions',
    manage_radar_monitor: 'System Monitor'
  },
  page: {
    login: {
      common: {
        loginOrRegister: 'Login / Register',
        userNamePlaceholder: 'Please enter user name',
        phonePlaceholder: 'Please enter phone number',
        codePlaceholder: 'Please enter verification code',
        passwordPlaceholder: 'Please enter password',
        confirmPasswordPlaceholder: 'Please enter password again',
        codeLogin: 'Verification code login',
        confirm: 'Confirm',
        back: 'Back',
        validateSuccess: 'Verification passed',
        loginSuccess: 'Login successfully',
        welcomeBack: 'Welcome back, {nickName} !'
      },
      pwdLogin: {
        title: 'Password Login',
        rememberMe: 'Remember me',
        forgetPassword: 'Forget password?',
        register: 'Register',
        otherAccountLogin: 'Other Account Login',
        otherLoginMode: 'Other Login Mode',
        superAdmin: 'Super Admin',
        admin: 'Admin',
        user: 'User'
      },
      codeLogin: {
        title: 'Verification Code Login',
        getCode: 'Get verification code',
        reGetCode: 'Reacquire after {time}s',
        sendCodeSuccess: 'Verification code sent successfully',
        imageCodePlaceholder: 'Please enter image verification code'
      },
      register: {
        title: 'Register',
        agreement: 'I have read and agree to',
        protocol: '《User Agreement》',
        policy: '《Privacy Policy》'
      },
      resetPwd: {
        title: 'Reset Password'
      },
      bindWeChat: {
        title: 'Bind WeChat'
      }
    },
    about: {
      title: 'About',
      introduction: `SoybeanAdmin is an elegant and powerful admin template, based on the latest front-end technology stack, including Vue3, Vite8, TypeScript, Pinia and UnoCSS. It has built-in rich theme configuration and components, strict code specifications, and an automated file routing system. In addition, it also uses the online mock data solution based on ApiFox. SoybeanAdmin provides you with a one-stop admin solution, no additional configuration, and out of the box. It is also a best practice for learning cutting-edge technologies quickly.`,
      projectInfo: {
        title: 'Project Info',
        version: 'Version',
        latestBuildTime: 'Latest Build Time',
        githubLink: 'Github Link',
        previewLink: 'Preview Link'
      },
      prdDep: 'Production Dependency',
      devDep: 'Development Dependency'
    },
    home: {
      branchDesc:
        'For the convenience of everyone in developing and updating the merge, we have streamlined the code of the main branch, only retaining the homepage menu, and the rest of the content has been moved to the example branch for maintenance. The preview address displays the content of the example branch.',
      greeting: 'Good morning, {userName}, today is another day full of vitality!',
      weatherDesc: 'Today is cloudy to clear, 20℃ - 25℃!',
      projectCount: 'Project Count',
      todo: 'Todo',
      message: 'Message',
      downloadCount: 'Download Count',
      registerCount: 'Register Count',
      schedule: 'Work and rest Schedule',
      study: 'Study',
      work: 'Work',
      rest: 'Rest',
      entertainment: 'Entertainment',
      visitCount: 'Visit Count',
      turnover: 'Turnover',
      dealCount: 'Deal Count',
      projectNews: {
        title: 'Project News',
        moreNews: 'More News',
        desc1: 'Soybean created the open source project soybean-admin on May 28, 2021!',
        desc2: 'Yanbowe submitted a bug to soybean-admin, the multi-tab bar will not adapt.',
        desc3: 'Soybean is ready to do sufficient preparation for the release of soybean-admin!',
        desc4: 'Soybean is busy writing project documentation for soybean-admin!',
        desc5: 'Soybean just wrote some of the workbench pages casually, and it was enough to see!'
      },
      creativity: 'Creativity'
    },
    function: {
      tab: {
        tabOperate: {
          title: 'Tab Operation',
          addTab: 'Add Tab',
          addTabDesc: 'To about page',
          closeTab: 'Close Tab',
          closeCurrentTab: 'Close Current Tab',
          closeAboutTab: 'Close "About" Tab',
          addMultiTab: 'Add Multi Tab',
          addMultiTabDesc1: 'To MultiTab page',
          addMultiTabDesc2: 'To MultiTab page(with query params)'
        },
        tabTitle: {
          title: 'Tab Title',
          changeTitle: 'Change Title',
          change: 'Change',
          resetTitle: 'Reset Title',
          reset: 'Reset'
        }
      },
      multiTab: {
        routeParam: 'Route Param',
        backTab: 'Back function_tab'
      },
      toggleAuth: {
        toggleAccount: 'Toggle Account',
        authHook: 'Auth Hook Function `hasAuth`',
        superAdminVisible: 'Super Admin Visible',
        adminVisible: 'Admin Visible',
        adminOrUserVisible: 'Admin and User Visible'
      },
      request: {
        repeatedErrorOccurOnce: 'Repeated Request Error Occurs Once',
        repeatedError: 'Repeated Request Error',
        repeatedErrorMsg1: 'Custom Request Error 1',
        repeatedErrorMsg2: 'Custom Request Error 2'
      }
    },
    alova: {
      scenes: {
        captchaSend: 'Captcha Send',
        autoRequest: 'Auto Request',
        visibilityRequestTips: 'Automatically request when switching browser window',
        pollingRequestTips: 'It will request every 3 seconds',
        networkRequestTips: 'Automatically request after network reconnecting',
        refreshTime: 'Refresh Time',
        startRequest: 'Start Request',
        stopRequest: 'Stop Request',
        requestCrossComponent: 'Request Cross Component',
        triggerAllRequest: 'Manually Trigger All Automated Requests'
      }
    },
    proNaive: {
      form: {
        basic: {
          title: 'Basic Example',
          appName: 'ApplicationName',
          appStatus: 'ApplicationStatus',
          createTime: 'CreateTime',
          responseDate: 'ResponseDate',
          specificationInfo: 'SpecificationInfo',
          specificate: 'Specificate',
          specificationName: 'SpecificationName',
          specificationValue: 'SpecificationValue',
          specificationColorRed: 'Red',
          specificationColorOrange: 'Orange',
          addSpecificateItem: 'Add Specificate Item',
          fillValue: 'FillValue',
          reset: 'Reset',
          submit: 'Submit',
          add: 'Add',
          delete: 'Delete',
          color: 'Color',
          normal: 'Normal',
          anomaly: 'Anomaly'
        },
        query: {
          title1: 'Query Example, which expands by default',
          title2: 'Query Example, which fold by default, and two lines are retained when folding',
          appName: 'ApplicationName',
          appStatus: 'ApplicationStatus',
          createTime: 'CreateTime',
          responseDate: 'ResponseDate',
          endDate: 'EndDate',
          field: 'Field'
        },
        step: {
          title: 'Step Form',
          step1: {
            title: 'Form 1',
            field: 'Form 1 field',
            nextStep: 'Next Step'
          },
          step2: {
            title: 'Form 2',
            field: 'Form 2 field',
            prevStep: 'Prev Step',
            submit: 'Submit'
          }
        }
      },
      table: {
        remote: {
          filterCondition: 'Filter Condition',
          name: 'Name',
          createTime: 'CreateTime',
          responseTime: 'ResponseTime',
          title: 'Remote Loading',
          replicableText: 'Replicable Text',
          tags: 'Tags',
          dateFormatting: 'Date Formatting',
          image: 'Image'
        },
        rowEdit: {
          title: 'Edit Table',
          reset: 'Reset',
          submit: 'Submit',
          edit: 'Edit',
          delete: 'Delete',
          save: 'Save',
          task: 'Task',
          score: 'Score',
          time: 'Time',
          name: 'Name',
          action: 'Action'
        }
      }
    },
    manage: {
      common: {
        statusType: {
          enable: 'Enable',
          disable: 'Disable'
        },
        updatedInfo: 'Updated Info',
        updatedBy: 'Updated By',
        updatedAt: 'Updated At',
        createdBy: 'Created By',
        createdAt: 'Created At'
      },
      role: {
        title: 'Role List',
        roleName: 'Role Name',
        roleCode: 'Role Code',
        rolestatusType: 'Role statusType',
        roleDesc: 'Role Description',
        menuAuth: 'Menu Auth',
        buttonAuth: 'Button Auth',
        apiAuth: 'Api Auth',
        form: {
          roleName: 'Please enter role name',
          roleCode: 'Please enter role code',
          rolestatusType: 'Please select role statusType',
          roleDesc: 'Please enter role description'
        },
        addRole: 'Add Role',
        editRole: 'Edit Role'
      },
      user: {
        title: 'User List',
        userName: 'User Name',
        password: 'Password',
        userGender: 'Gender',
        nickName: 'Nick Name',
        userPhone: 'Phone Number',
        userEmail: 'Email',
        userStatusType: 'User statusType',
        userRole: 'User Role',
        form: {
          userName: 'Please enter user name',
          password: 'Please enter password',
          passwordEditHint: 'Leave blank to keep current password',
          userGender: 'Please select gender',
          nickName: 'Please enter nick name',
          userPhone: 'Please enter phone number',
          userEmail: 'Please enter email',
          userStatusType: 'Please select user statusType',
          userRole: 'Please select user role'
        },
        offline: 'Offline',
        batchOffline: 'Batch Offline',
        confirmOffline: 'Are you sure to force this user offline?',
        offlineSuccess: 'User has been forced offline',
        impersonate: {
          button: 'Impersonate',
          confirm: 'Are you sure to impersonate as {name}?',
          switchSuccess: 'Impersonation started',
          nowActingAs: 'Now acting as {name}',
          actingAs: 'Impersonating: {name}',
          exit: 'Exit Impersonation',
          exitSuccess: 'Impersonation ended'
        },
        addUser: 'Add User',
        editUser: 'Edit User',
        gender: {
          male: 'Male',
          female: 'Female',
          unknow: 'Unknow'
        }
      },
      menu: {
        home: 'Home',
        title: 'Menu List',
        id: 'ID',
        parentId: 'Parent Menu',
        menuType: 'Menu Type',
        menuName: 'Menu Name',
        routeName: 'Route Name',
        routePath: 'Route Path',
        pathParam: 'Path Param',
        layout: 'Layout Component',
        page: 'Page Component',
        i18nKey: 'I18n Key',
        icon: 'Icon',
        localIcon: 'Local Icon',
        iconTypeTitle: 'Icon Type',
        order: 'Order',
        constant: 'Constant',
        keepAlive: 'Keep Alive',
        href: 'Href',
        hideInMenu: 'Hide In Menu',
        activeMenu: 'Active Menu',
        multiTab: 'Multi Tab',
        fixedIndexInTab: 'Fixed Index In Tab',
        query: 'Query Params',
        button: 'Button',
        buttonCode: 'Button Code',
        buttonDesc: 'Button Desc',
        menuStatusType: 'Menu statusType',
        form: {
          home: 'Please select home',
          menuType: 'Please select menu type',
          menuName: 'Please enter menu name',
          routeName: 'Please enter route name',
          routePath: 'Please enter route path',
          pathParam: 'Please enter path param',
          page: 'Please select page component',
          layout: 'Please select layout component',
          i18nKey: 'Please enter i18n key',
          icon: 'Please enter iconify name',
          localIcon: 'Please enter local icon name',
          order: 'Please enter order',
          keepAlive: 'Please select whether to cache route',
          href: 'Please enter href',
          hideInMenu: 'Please select whether to hide menu',
          activeMenu: 'Please select route name of the highlighted menu',
          multiTab: 'Please select whether to support multiple tabs',
          fixedInTab: 'Please select whether to fix in the tab',
          fixedIndexInTab: 'Please enter the index fixed in the tab',
          queryKey: 'Please enter route parameter Key',
          queryValue: 'Please enter route parameter Value',
          button: 'Please select whether it is a button',
          buttonCode: 'Please enter button code',
          buttonDesc: 'Please enter button description',
          menuStatusType: 'Please select menu statusType'
        },
        addMenu: 'Add Menu',
        editMenu: 'Edit Menu',
        addChildMenu: 'Add Child Menu',
        includeBusiness: 'Business Menus',
        includeBusinessWarningTitle: 'Show business menus?',
        includeBusinessWarning:
          "Business menus are declared by each module's init_data.py. Subtrees guarded by reconcile_menu_subtree are rebuilt from the declarations on every restart — menus you delete here will be restored, and menus you add under them will be removed.",
        dontShowAgain: "Don't show again",
        type: {
          directory: 'Directory',
          menu: 'Menu'
        },
        iconType: {
          iconify: 'Iconify Icon',
          local: 'Local Icon'
        }
      },
      api: {
        title: '',
        path: '',
        method: '',
        summary: '',
        tags: '',
        statusType: '',
        includeSystem: 'Include system APIs',
        form: {
          path: '',
          method: '',
          summary: '',
          tags: '',
          statusType: ''
        },
        addApi: '',
        editApi: '',
        methods: {
          GET: '',
          POST: '',
          PUT: '',
          PATCH: '',
          DELETE: ''
        }
      },
      radar: {
        purge: 'Purge Data',
        purgeConfirm: 'Purge monitoring data older than 24 hours?',
        purgeSuccess: 'Records purged',
        overview: {
          title: 'Dashboard',
          requestCount: 'Total Requests',
          avgDuration: 'Avg Duration',
          errorCount: 'Errors',
          errorRate: 'Error Rate',
          queryCount: 'SQL Queries',
          slowQueryCount: 'Slow Queries',
          userLogCount: 'User Logs'
        },
        dashboard: {
          totalRequests: 'Total Requests',
          avgResponseTime: 'Avg Response Time',
          dbQueries: 'DB Queries',
          exceptions: 'Exceptions',
          perfOverview: 'Performance Overview',
          successRate: 'Success Rate',
          errorRate: 'Error Rate',
          rps: 'Requests/s',
          responseTime: 'Response Time',
          queryPerf: 'Query Performance',
          requestDist: 'Request Distribution',
          responseTimeTrend: 'Response Time Trend',
          queryActivity: 'Database Activity'
        },
        monitor: {
          title: 'System Monitor',
          autoRefresh: 'Auto Refresh',
          paused: 'Paused',
          cpuUsage: 'CPU Usage',
          cores: 'Cores',
          threads: 'Threads',
          memoryUsage: 'Memory Usage',
          used: 'Used',
          total: 'Total',
          diskUsage: 'Disk Usage',
          diskIO: 'Disk IO',
          read: 'Read',
          write: 'Write',
          totalRead: 'Total Read',
          totalWrite: 'Total Write',
          networkIO: 'Network IO',
          activeConnections: 'Active Conn',

          upload: 'Upload',
          download: 'Download',
          totalSent: 'Total Sent',
          totalRecv: 'Total Recv',
          basicInfo: 'Basic Info',
          hostname: 'Hostname',
          ipAddress: 'IP Address',
          os: 'OS',
          architecture: 'Architecture',
          processor: 'Processor',
          pythonVersion: 'Python Version',
          systemStatus: 'System Status',
          systemLoad: 'System Load',
          loadAvg: '1/5/15 min load avg',
          uptime: 'Uptime',
          bootTime: 'Boot Time',
          processes: 'Processes',
          running: 'Running',
          sleeping: 'Sleeping',
          onlineUsers: 'Online Users',
          updateTime: 'Update Time',
          networkTrend: 'Network Usage Trend',
          topProcesses: 'Top 10 Processes',
          processName: 'Process Name',
          memPercent: 'Memory%',
          status: 'Status',
          createTime: 'Create Time'
        },
        requests: {
          title: 'Requests',
          method: 'Method',
          path: 'Path',
          status: 'Status',
          businessCode: 'Business Code',
          businessMsg: 'Message',
          duration: 'Duration',
          error: 'Error',
          createdAt: 'Time',
          detail: 'Request Detail',
          queryParams: 'Query Params',
          minDuration: 'Min Duration',
          hasError: 'Has Error',
          xRequestId: 'Request ID',
          clientIp: 'Client IP',
          requestHeaders: 'Request Headers',
          requestBody: 'Request Body',
          responseHeaders: 'Response Headers',
          responseBody: 'Response Body'
        },
        queries: {
          title: 'SQL Queries',
          operation: 'Operation',
          connection: 'Connection',
          slowOnly: 'Slow Only',
          threshold: 'Threshold'
        },
        exceptions: {
          title: 'Exceptions',
          errorType: 'Error Type',
          errorMessage: 'Error Message',
          detail: 'Exception Detail',
          status: 'Status',
          resolved: 'Resolved',
          unresolved: 'Unresolved'
        },
        userLogs: {
          title: 'User Logs'
        }
      }
    },
    userCenter: {
      profile: {
        title: 'Profile',
        userName: 'Username',
        nickName: 'Nickname',
        roles: 'Roles',
        impersonating: 'You are impersonating another user'
      },
      password: {
        title: 'Change Password',
        oldPassword: 'Old Password',
        newPassword: 'New Password',
        confirmPassword: 'Confirm Password',
        oldPasswordPlaceholder: 'Enter old password',
        newPasswordPlaceholder: 'Enter new password',
        confirmPasswordPlaceholder: 'Re-enter new password',
        submit: 'Submit',
        success: 'Password changed, please log in again'
      }
    },
    hr: {
      common: {
        status: 'Status',
        form: {
          status: 'Please select status'
        }
      },
      employee: {
        title: 'Employee List',
        name: 'Name',
        userName: 'Username',
        employeeNo: 'Employee No.',
        email: 'Email',
        phone: 'Phone',
        position: 'Position',
        avatar: 'Avatar',
        avatarUploadSuccess: 'Avatar uploaded successfully',
        department: 'Department',
        tags: 'Tags',
        form: {
          name: 'Please enter name',
          userName: 'Please enter username (phone)',
          email: 'Please enter email',
          phone: 'Please enter phone',
          position: 'Please enter position',
          department: 'Please select department',
          tags: 'Please select tags',
          status: 'Please select employee status'
        },
        status: {
          pending: 'Pending',
          onboarding: 'Onboarding',
          active: 'Active',
          resigned: 'Resigned'
        },
        transition: {
          toOnboarding: 'Start Onboarding',
          toActive: 'Mark Active',
          toResigned: 'Mark Resigned',
          confirm: 'Confirm employee status change?',
          success: 'Employee status updated'
        },
        addEmployee: 'Add Employee',
        editEmployee: 'Edit Employee'
      },
      department: {
        title: 'Department List',
        name: 'Department Name',
        code: 'Department Code',
        description: 'Description',
        form: {
          name: 'Please enter department name',
          code: 'Please enter department code',
          description: 'Please enter description'
        },
        addDepartment: 'Add Department',
        editDepartment: 'Edit Department'
      },
      tag: {
        title: 'Tag List',
        name: 'Tag Name',
        category: 'Category',
        description: 'Description',
        form: {
          name: 'Please enter tag name',
          category: 'Please select category',
          description: 'Please enter description'
        },
        addTag: 'Add Tag',
        editTag: 'Edit Tag'
      },
      my: {
        profileTitle: 'My Profile',
        tagTitle: 'My Tags',
        colleaguesTitle: 'Department Colleagues',
        editProfile: 'Edit My Profile',
        editTags: 'Edit My Tags',
        avatarUploadSuccess: 'Avatar uploaded successfully'
      },
      team: {
        title: 'Subordinates',
        department: 'Department',
        total: 'Headcount',
        statusBreakdown: 'Status Breakdown',
        addSubordinate: 'Add Subordinate',
        editSubordinate: 'Edit Subordinate',
        editTags: 'Edit Tags'
      }
    }
  },
  form: {
    required: 'Cannot be empty',
    userName: {
      required: 'Please enter user name',
      invalid: 'User name format is incorrect'
    },
    phone: {
      required: 'Please enter phone number',
      invalid: 'Phone number format is incorrect'
    },
    pwd: {
      required: 'Please enter password',
      invalid: '6-18 characters, including letters, numbers, and underscores'
    },
    confirmPwd: {
      required: 'Please enter password again',
      invalid: 'The two passwords are inconsistent'
    },
    code: {
      required: 'Please enter verification code',
      invalid: 'Verification code format is incorrect'
    },
    email: {
      required: 'Please enter email',
      invalid: 'Email format is incorrect'
    }
  },
  dropdown: {
    closeCurrent: 'Close Current',
    closeOther: 'Close Other',
    closeLeft: 'Close Left',
    closeRight: 'Close Right',
    closeAll: 'Close All',
    pin: 'Pin Tab',
    unpin: 'Unpin Tab'
  },
  icon: {
    themeConfig: 'Theme Configuration',
    themeSchema: 'Theme Schema',
    lang: 'Switch Language',
    fullscreen: 'Fullscreen',
    fullscreenExit: 'Exit Fullscreen',
    reload: 'Reload Page',
    collapse: 'Collapse Menu',
    expand: 'Expand Menu',
    pin: 'Pin',
    unpin: 'Unpin'
  },
  datatable: {
    itemCount: 'Total {total} items',
    fixed: {
      left: 'Left Fixed',
      right: 'Right Fixed',
      unFixed: 'Unfixed'
    }
  }
};

export default local;
