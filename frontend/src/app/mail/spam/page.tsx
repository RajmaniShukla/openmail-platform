'use client'

import { useEffect } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { emailApi } from '@/lib/api'
import { useEmailStore } from '@/stores/emailStore'
import EmailList from '@/components/mail/EmailList'
import EmailView from '@/components/mail/EmailView'
import { AlertTriangle, Trash2 } from 'lucide-react'
import toast from 'react-hot-toast'

export default function SpamPage() {
  const { selectedEmail, emails, setEmails, setCurrentFolder, setIsLoading } = useEmailStore()
  const queryClient = useQueryClient()

  const { data, isLoading, error } = useQuery({
    queryKey: ['emails', 'spam'],
    queryFn: async () => {
      const response = await emailApi.list({ folder: 'spam' })
      return response.data.data || response.data
    },
  })

  const emptySpamMutation = useMutation({
    mutationFn: async () => {
      await emailApi.emptyFolder('spam')
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['emails', 'spam'] })
      toast.success('Spam folder emptied')
    },
    onError: () => {
      toast.error('Failed to empty spam folder')
    },
  })

  useEffect(() => {
    setCurrentFolder('spam')
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
        <p className="text-red-500">Failed to load spam</p>
      </div>
    )
  }

  return (
    <div className="h-full flex flex-col">
      {/* Spam warning banner */}
      {emails.length > 0 && (
        <div className="bg-yellow-50 dark:bg-yellow-900/20 border-b border-yellow-200 dark:border-yellow-800 px-4 py-3 flex items-center justify-between">
          <div className="flex items-center gap-2 text-yellow-700 dark:text-yellow-400">
            <AlertTriangle className="w-5 h-5" />
            <span className="text-sm">
              Messages that have been in Spam more than 30 days will be automatically deleted.
            </span>
          </div>
          <button
            onClick={() => emptySpamMutation.mutate()}
            disabled={emptySpamMutation.isPending}
            className="flex items-center gap-2 px-3 py-1.5 bg-yellow-100 dark:bg-yellow-800 text-yellow-700 dark:text-yellow-300 rounded hover:bg-yellow-200 dark:hover:bg-yellow-700 text-sm font-medium disabled:opacity-50"
          >
            <Trash2 className="w-4 h-4" />
            {emptySpamMutation.isPending ? 'Emptying...' : 'Empty Spam'}
          </button>
        </div>
      )}

      <div className="flex-1 flex">
        <div className={`${selectedEmail ? 'w-1/3' : 'w-full'} border-r border-gray-200 dark:border-gray-700 overflow-hidden`}>
          <EmailList />
        </div>
        {selectedEmail && (
          <div className="flex-1 overflow-hidden">
            <EmailView />
          </div>
        )}
      </div>
    </div>
  )
}
