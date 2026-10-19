import { useMutation, useQuery, type UseMutationOptions, type UseQueryOptions } from '@tanstack/react-query'
import createClient, { type Middleware } from 'openapi-fetch'

import type { paths } from '@docu/api-types'
import { useWorkspaceStore } from '@/stores/workspace'

export class ApiError extends Error {
  status: number
  code: string
  details: Record<string, unknown>

  constructor(status: number, code: string, details: Record<string, unknown>) {
    super(code)
    this.name = 'ApiError'
    this.status = status
    this.code = code
    this.details = details
  }
}

function cookie(name: string): string | null {
  const row = document.cookie.split('; ').find((part) => part.startsWith(`${name}=`))
  return row ? decodeURIComponent(row.slice(name.length + 1)) : null
}

const middleware: Middleware = {
  async onRequest({ request }) {
    if (request.method !== 'GET' && request.method !== 'HEAD') {
      const csrf = cookie('docu_csrf')
      if (csrf) request.headers.set('x-csrf-token', csrf)
    }
    const workspaceId = useWorkspaceStore.getState().workspaceId
    if (workspaceId) request.headers.set('x-workspace-id', workspaceId)
    return request
  },
  async onResponse({ response }) {
    if (response.ok) return response
    if (response.status === 401) {
      const next = `${window.location.pathname}${window.location.search}`
      window.location.assign(`/login?next=${encodeURIComponent(next)}`)
    }
    let code = 'internal'
    let details: Record<string, unknown> = {}
    try {
      const body = (await response.clone().json()) as {
        error?: { code?: string; details?: Record<string, unknown> }
      }
      code = body.error?.code ?? code
      details = body.error?.details ?? {}
    } catch {
      code = 'internal'
    }
    throw new ApiError(response.status, code, details)
  },
}

export const api = createClient<paths>({ baseUrl: '' })
api.use(middleware)

export function useApiQuery<T>(
  key: readonly unknown[],
  queryFn: () => Promise<T>,
  options?: Omit<UseQueryOptions<T, ApiError>, 'queryKey' | 'queryFn'>,
) {
  return useQuery({ queryKey: key, queryFn, ...options })
}

export function useApiMutation<T, V>(
  mutationFn: (variables: V) => Promise<T>,
  options?: UseMutationOptions<T, ApiError, V>,
) {
  return useMutation({ mutationFn, ...options })
}

export type HealthResponse = paths['/v1/health']['get']
