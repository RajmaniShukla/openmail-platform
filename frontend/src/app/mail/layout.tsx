'use client'

import { useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { useAuthStore } from '@/stores/authStore'
import { useEmailStore } from '@/stores/emailStore'
import { folderApi, labelApi, mailboxApi } from '@/lib/api'
import { useWebSocket } from '@/hooks/useWebSocket'
import Sidebar from '@/components/mail/Sidebar'
import Header from '@/components/mail/Header'

export default function MailLayout({
  children,
}: {
  children: React.ReactNode
}) {
  const router = useRouter()
  const { isAuthenticated, user } = useAuthStore()
  const { setFolders, setLabels, setMailboxes } = useEmailStore()
  const { requestNotificationPermission } = useWebSocket()

  useEffect(() => {
    if (!isAuthenticated) {
      router.push('/login')
      return
    }

    // Load initial data
    const loadData = async () => {
      try {
        const [foldersRes, labelsRes, mailboxesRes] = await Promise.all([
          folderApi.list(),
          labelApi.list(),
          mailboxApi.list(),
        ])
        setFolders(foldersRes.data.data || foldersRes.data)
        setLabels(labelsRes.data.data || labelsRes.data)
        setMailboxes(mailboxesRes.data.data || mailboxesRes.data)
      } catch (error) {
        console.error('Failed to load mail data:', error)
      }
    }

    loadData()
  }, [isAuthenticated, router, setFolders, setLabels, setMailboxes])

  if (!isAuthenticated) {
    return null
  }

  return (
    <div className="h-screen flex bg-gray-50 dark:bg-gray-900">
      {/* Sidebar */}
      <Sidebar />

      {/* Main content */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Header */}
        <Header />

        {/* Content */}
        <main className="flex-1 overflow-hidden">
          {children}
        </main>
      </div>
    </div>
  )
}
