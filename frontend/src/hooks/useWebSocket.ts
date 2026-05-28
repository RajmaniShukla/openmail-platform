/**
 * OpenMail - useWebSocket hook
 * Connects to the backend WebSocket for real-time inbox push.
 * Automatically reconnects with exponential back-off.
 */

import { useEffect, useRef, useCallback } from 'react'
import { useAuthStore } from '@/stores/authStore'
import { useEmailStore } from '@/stores/emailStore'
import { useQueryClient } from '@tanstack/react-query'

const WS_URL = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000/ws'
const MAX_RECONNECT_DELAY_MS = 30_000
const INITIAL_RECONNECT_DELAY_MS = 1_000

interface WSMessage {
  type: string
  data: Record<string, unknown>
}

export function useWebSocket() {
  const { accessToken, isAuthenticated } = useAuthStore()
  const { addEmail, markAsRead } = useEmailStore()
  const queryClient = useQueryClient()

  const wsRef = useRef<WebSocket | null>(null)
  const reconnectDelay = useRef(INITIAL_RECONNECT_DELAY_MS)
  const reconnectTimer = useRef<ReturnType<typeof setTimeout> | null>(null)
  const isMounted = useRef(true)

  const handleMessage = useCallback(
    (event: MessageEvent) => {
      try {
        const msg: WSMessage = JSON.parse(event.data)

        switch (msg.type) {
          case 'new_email': {
            // Add email optimistically to inbox list
            const email = msg.data as any
            addEmail(email)
            // Invalidate react-query cache so the inbox re-fetches
            queryClient.invalidateQueries({ queryKey: ['emails', 'inbox'] })
            // Browser notification (if permitted)
            if (typeof window !== 'undefined' && Notification.permission === 'granted') {
              new Notification(`New email from ${email.from_name || email.from_address}`, {
                body: email.snippet || email.subject || '',
                icon: '/favicon.ico',
              })
            }
            break
          }

          case 'email_read': {
            const { email_id } = msg.data as { email_id: string }
            if (email_id) markAsRead([email_id])
            break
          }

          case 'notification': {
            // Generic notification — could extend with toast here
            console.info('[WS] notification:', msg.data)
            break
          }

          case 'ping':
            // Server ping — respond with pong
            wsRef.current?.send('ping')
            break

          case 'pong':
            break

          default:
            break
        }
      } catch {
        // Ignore malformed messages
      }
    },
    [addEmail, markAsRead, queryClient]
  )

  const connect = useCallback(() => {
    if (!isMounted.current || !isAuthenticated || !accessToken) return

    const url = `${WS_URL}?token=${encodeURIComponent(accessToken)}`
    const ws = new WebSocket(url)
    wsRef.current = ws

    ws.onopen = () => {
      reconnectDelay.current = INITIAL_RECONNECT_DELAY_MS
    }

    ws.onmessage = handleMessage

    ws.onclose = () => {
      if (!isMounted.current) return
      // Exponential back-off reconnect
      reconnectTimer.current = setTimeout(() => {
        reconnectDelay.current = Math.min(
          reconnectDelay.current * 2,
          MAX_RECONNECT_DELAY_MS
        )
        connect()
      }, reconnectDelay.current)
    }

    ws.onerror = () => {
      ws.close()
    }
  }, [accessToken, isAuthenticated, handleMessage])

  useEffect(() => {
    isMounted.current = true
    connect()

    return () => {
      isMounted.current = false
      if (reconnectTimer.current) clearTimeout(reconnectTimer.current)
      wsRef.current?.close()
    }
  }, [connect])

  /** Request browser notification permission */
  const requestNotificationPermission = useCallback(async () => {
    if (typeof window !== 'undefined' && 'Notification' in window) {
      await Notification.requestPermission()
    }
  }, [])

  return { requestNotificationPermission }
}
