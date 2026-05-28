/**
 * useEmailThread — fetches all emails in the same thread as the selected email.
 * Returns them sorted oldest-first so the conversation reads top-to-bottom.
 */

import { useQuery } from '@tanstack/react-query'
import { emailApi } from '@/lib/api'

interface ThreadEmail {
  id: string
  thread_id?: string
  from_address: string
  from_name?: string
  subject?: string
  snippet?: string
  body_text?: string
  body_html?: string
  date: string
  is_read: boolean
  is_starred: boolean
  has_attachments: boolean
  attachments?: Array<{ id: string; filename: string; content_type: string; size_bytes: number }>
}

export function useEmailThread(email: ThreadEmail | null) {
  const threadId = email?.thread_id

  return useQuery<ThreadEmail[]>({
    queryKey: ['thread', threadId],
    enabled: !!threadId,
    queryFn: async () => {
      if (!threadId) return []
      // Fetch all emails in this thread using the search endpoint
      const res = await emailApi.list({ q: threadId, per_page: 100, sort: 'date', order: 'asc' })
      const all: ThreadEmail[] = res.data.data || res.data || []
      // Filter to same thread_id (in case q matches something else)
      return all.filter((e) => e.thread_id === threadId)
    },
    // Keep previous data while re-fetching so the UI doesn't flash
    placeholderData: (prev) => prev,
  })
}
