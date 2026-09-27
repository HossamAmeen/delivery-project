import { describe, expect, it } from 'vitest'
import { mount } from '@vue/test-utils'

import EmptyState from '../EmptyState.vue'
import ErrorState from '../ErrorState.vue'
import LoadingState from '../LoadingState.vue'
import UnavailableState from '../UnavailableState.vue'

describe('state components', () => {
  it('LoadingState announces politely with a default label', () => {
    const wrapper = mount(LoadingState)
    expect(wrapper.attributes('role')).toBe('status')
    expect(wrapper.attributes('aria-live')).toBe('polite')
    expect(wrapper.text()).toBe('Loading…')
    expect(mount(LoadingState, { props: { label: 'Checking' } }).text()).toBe('Checking')
  })

  it('EmptyState renders title, description and slot', () => {
    const wrapper = mount(EmptyState, {
      props: { title: 'Nothing here', description: 'Come back later' },
      slots: { default: '<a href="#">Action</a>' },
    })
    expect(wrapper.text()).toContain('Nothing here')
    expect(wrapper.text()).toContain('Come back later')
    expect(wrapper.find('a').text()).toBe('Action')
  })

  it('ErrorState is an alert and emits retry', async () => {
    const wrapper = mount(ErrorState, { props: { title: 'Failed', message: 'Oops' } })
    expect(wrapper.attributes('role')).toBe('alert')
    await wrapper.find('button').trigger('click')
    expect(wrapper.emitted('retry')).toHaveLength(1)
  })

  it('ErrorState can hide the retry button', () => {
    const wrapper = mount(ErrorState, { props: { title: 'Failed', retryable: false } })
    expect(wrapper.find('button').exists()).toBe(false)
  })

  it('UnavailableState shows retry only when retryable', async () => {
    expect(
      mount(UnavailableState, { props: { title: 'Closed' } })
        .find('button')
        .exists(),
    ).toBe(false)
    const wrapper = mount(UnavailableState, { props: { title: 'Closed', retryable: true } })
    await wrapper.find('button').trigger('click')
    expect(wrapper.emitted('retry')).toHaveLength(1)
  })
})
