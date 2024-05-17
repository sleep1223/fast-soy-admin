<script setup lang="ts">
import { computed, shallowRef, watch } from 'vue';
import { $t } from '@/locales';
import { fetchGetAllPages, fetchGetMenuTree, fetchGetRoleMenu, fetchUpdateRoleMenu } from '@/service/api';

defineOptions({
  name: 'MenuAuthModal'
});

interface Props {
  /** the roleId */
  roleId: number;
  roleHome: string;
}

const props = defineProps<Props>();

const visible = defineModel<boolean>('visible', {
  default: false
});

function closeModal() {
  visible.value = false;
}

const title = computed(() => $t('common.edit') + $t('page.manage.role.menuAuth'));

const home = shallowRef('');
home.value = 'home';

async function updateHome(val: string) {
  // request
  home.value = val;
  await fetchUpdateRoleMenu({ id: props.roleId, roleHome: val });
}

const pages = shallowRef<string[]>([]);

async function getPages() {
  const { error, data } = await fetchGetAllPages();

  if (!error) {
    pages.value = data;
  }
}

const pageSelectOptions = computed(() => {
  const opts: CommonType.Option[] = pages.value.map(page => ({
    label: page,
    value: page
  }));

  return opts;
});

const tree = shallowRef<Api.SystemManage.MenuTree[]>([]);

async function getMenuTree() {
  const { error, data } = await fetchGetMenuTree();

  if (!error) {
    tree.value = data;
  }
}

const checks = shallowRef<number[]>([]);

async function getChecks() {
  // console.log(props.roleId);
  // request
  checks.value = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21];

  const { error, data } = await fetchGetRoleMenu({ id: props.roleId });
  if (!error) {
    checks.value = data.menuIds || [];
    home.value = data.roleHome || props.roleHome;
  }
}

async function handleSubmit() {
  // console.log(checks.value, props.roleId);
  // request

  const { error } = await fetchUpdateRoleMenu({ id: props.roleId, roleHome: home.value, menuIds: checks.value });
  if (!error) {
    window.$message?.success?.($t('common.modifySuccess'));
  }

  closeModal();
}

function init() {
  getChecks();
  getPages();
  getMenuTree();
}

watch(visible, val => {
  if (val) {
    init();
  }
});
</script>

<template>
  <NModal v-model:show="visible" :title="title" preset="card" class="w-480px">
    <div class="flex-y-center gap-16px pb-12px">
      <div>{{ $t('page.manage.menu.home') }}</div>
      <NSelect :value="home" :options="pageSelectOptions" size="small" class="w-160px" @update:value="updateHome" />
    </div>
    <NTree
      v-model:checked-keys="checks"
      :data="tree"
      key-field="id"
      cascade
      checkable
      expand-on-click
      virtual-scroll
      block-line
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
