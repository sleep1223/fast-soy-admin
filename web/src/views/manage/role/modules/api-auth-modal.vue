<script setup lang="ts">
import { computed, shallowRef, watch } from 'vue';
import { $t } from '@/locales';
import { fetchGetApiTree, fetchGetRoleApi, fetchUpdateRoleApi } from '@/service/api';

defineOptions({
  name: 'ApiAuthModal'
});

interface Props {
  /** the roleId */
  roleId: number;
}

const props = defineProps<Props>();

const visible = defineModel<boolean>('visible', {
  default: false
});

function closeModal() {
  visible.value = false;
}

const title = computed(() => $t('common.edit') + $t('page.manage.role.buttonAuth'));

// type ApiConfig = {
//   id: number;
//   label: string;
//   pId: number;
// };

// const tree = shallowRef<ApiConfig[]>([]);
const tree = shallowRef<Api.SystemManage.MenuTree[]>([]);

async function getTree() {
  // request
  tree.value = [
    { id: 1, label: 'API模块', pId: 0, children: [{ id: 2, label: '查看API模块', pId: 1 }] },
    { id: 3, label: '基础模块', pId: 0, children: [{ id: 4, label: '获取token', pId: 3 }] }
  ];

  const { error, data } = await fetchGetApiTree();

  if (!error) {
    tree.value = data;
  }
}

const apiIds = shallowRef<number[]>([]);

async function getChecks() {
  // console.log(props.roleId);
  // request
  apiIds.value = [1, 2, 3, 4, 5];

  const { error, data } = await fetchGetRoleApi({ id: props.roleId });
  if (!error) {
    apiIds.value = data.apiIds || [];
  }
}

async function handleSubmit() {
  // console.log(apiIds.value, props.roleId);
  // request
  const { error } = await fetchUpdateRoleApi({
    id: props.roleId,
    apiIds: apiIds.value.filter(item => typeof item === 'number')
  });
  if (!error) {
    window.$message?.success?.($t('common.modifySuccess'));
  }

  closeModal();
}

function init() {
  getChecks();
  getTree();
}

watch(visible, val => {
  if (val) {
    init();
  }
});
</script>

<template>
  <NModal v-model:show="visible" :title="title" preset="card" class="w-480px">
    <NTree
      v-model:checked-keys="apiIds"
      :data="tree"
      key-field="id"
      label-field="summary"
      default-expand-all
      block-line
      cascade
      checkable
      expand-on-click
      virtual-scroll
      class="h-280px"
    />
    <template #footer>
      <NSpace justify="end">
        <NButton size="small" class="mt-16px" @click="closeModal">
          {{ $t('common.cancel') }}
        </NButton>
        <NButton type="primary" size="small" class="mt-16px" @click="handleSubmit">
          {{ $t('common.confirm') }}
        </NButton>
      </NSpace>
    </template>
  </NModal>
</template>

<style scoped></style>
