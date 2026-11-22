import { mount } from '@vue/test-utils';
import { NSwitch, NTag, NTooltip } from 'naive-ui';
import { expect, it, vi } from 'vitest';
import PaintingStatusSwitch from '../painting-status-switch.vue';

vi.mock('@/locales', () => ({ $t: (key: string) => key }));

const components = { NSwitch, NTag, NTooltip };

it('keeps the switch off when a proposed change is not confirmed', async () => {
  const wrapper = mount(PaintingStatusSwitch, {
    props: { value: false, loading: false, canEdit: true },
    global: { components }
  });
  const button = wrapper.get('[role="switch"]');
  await button.trigger('click');
  expect(wrapper.emitted('change')).toEqual([[true]]);
  expect(button.attributes('aria-checked')).toBe('false');
  await wrapper.setProps({ value: true });
  expect(button.attributes('aria-checked')).toBe('true');
  wrapper.unmount();
});

it('does not offer a switch when the backend has not returned the field', () => {
  const wrapper = mount(PaintingStatusSwitch, { props: { loading: false, canEdit: true }, global: { components } });
  expect(wrapper.find('[role="switch"]').exists()).toBe(false);
  expect(wrapper.text()).toContain('paintingUnavailable');
  wrapper.unmount();
});
