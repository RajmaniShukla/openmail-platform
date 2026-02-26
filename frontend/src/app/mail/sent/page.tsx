'use client'

import { useEffect } from 'react'
import { useQuery } from '@tanstack/react-query'
import { emailApi } from '@/lib/api'
import { useEmailStore } from '@/stores/emailStore'
import EmailList from '@/components/mail/EmailList'
import EmailView from '@/components/mail/EmailView'

export default function SentPage() {
  const { selectedEmail, setEmails, setCurrentFolder, setIsLoading } = useEmailStore()

  const { data, isLoading, error } = useQuery({
    queryKey: ['emails', 'sent'],
    queryFn: async () => {
      const response = await emailApi.list({ folder: 'sent' })
      return response.data.data || response.data
    },
  })

  useEffect(() => {
    setCurrentFolder('sent')
  }, [setCurrentFolder])

  useEffect(() => {
    setIsLoading(isLoading)
    if (data) {
      setEmails(data)
    }
  }, [data, isLoading, setEmails, setIsLoading])

  if (error) {
    return (
      <div className="flex items-center justify-center h-full">
        <p className="text-red-500">Failed to load sent emails</p>
      </div>
    )
  }

  return (
    <div className="h-full flex">
      <div className={`${selectedEmail ? 'w-1/3' : 'w-full'} border-r border-gray-200 dark:border-gray-700 overflow-hidden`}>
        <EmailList />
      </div>
      {selectedEmail && (
        <div className="flex-1 overflow-hidden">
          <EmailView />
        </div>
      )}
    </div>
  )
}
