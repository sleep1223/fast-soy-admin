<script setup lang="ts">
import { computed, shallowRef, watch } from 'vue';
import { $t } from '@/locales';
import { fetchGetMenuButtonTree, fetchGetRoleButton, fetchUpdateRoleButton } from '@/service/api';

defineOptions({
  name: 'ButtonAuthModal'
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

// type ButtonConfig = {
//   id: number;
//   label: string;
//   code: string;
// };

// const tree = shallowRef<ButtonConfig[]>([]);
const tree = shallowRef<Api.SystemManage.ButtonTree[]>([]);

async function getButtonTree() {
  // request
  tree.value = [
    {
      id: 32,
      label: '关于',
      pId: 0,
      children: [
        {
          id: 2,
          label: 'button1',
          pId: 32
        }
      ]
    },
    {
      id: 26,
      label: '系统管理',
      pId: 0,
      children: [
        {
          id: 27,
          label: 'API管理',
          pId: 26,
          children: [
            {
              id: 3,
              label: 'B_refreshAPI',
              pId: 27
            }
          ]
        }
      ]
    }
  ];

  const { error, data } = await fetchGetMenuButtonTree();

  if (!error) {
    tree.value = data;
  }
}

const buttonIds = shallowRef<number[]>([]);

async function getChecks() {
  // console.log(props.roleId);
  // request
  // checks.value = [1, 2, 3, 4, 5];
  buttonIds.value = [1, 2, 3];
  const { error, data } = await fetchGetRoleButton({ id: props.roleId });
  if (!error) {
    buttonIds.value = data.buttonIds || [];
  }
}

async function handleSubmit() {
  // console.log(checks.value, props.roleId);
  // request

  const { error } = await fetchUpdateRoleButton({
    id: props.roleId,
    buttonIds: buttonIds.value.filter(item => typeof item === 'number')
  });
  if (!error) {
    window.$message?.success?.($t('common.modifySuccess'));
  }

  closeModal();
}

function init() {
  getChecks();
  getButtonTree();
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
      v-model:checked-keys="buttonIds"
      :data="tree"
      key-field="id"
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
