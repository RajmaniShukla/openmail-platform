'use client'

import { useEffect } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { emailApi } from '@/lib/api'
import { useEmailStore } from '@/stores/emailStore'
import EmailList from '@/components/mail/EmailList'
import EmailView from '@/components/mail/EmailView'
import { Info, Trash2 } from 'lucide-react'
import toast from 'react-hot-toast'

export default function TrashPage() {
  const { selectedEmail, emails, setEmails, setCurrentFolder, setIsLoading } = useEmailStore()
  const queryClient = useQueryClient()

  const { data, isLoading, error } = useQuery({
    queryKey: ['emails', 'trash'],
    queryFn: async () => {
      const response = await emailApi.list({ folder: 'trash' })
      return response.data.data || response.data
    },
  })

  const emptyTrashMutation = useMutation({
    mutationFn: async () => {
      await emailApi.emptyFolder('trash')
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['emails', 'trash'] })
      toast.success('Trash emptied')
    },
    onError: () => {
      toast.error('Failed to empty trash')
    },
  })

  useEffect(() => {
    setCurrentFolder('trash')
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
        <p className="text-red-500">Failed to load trash</p>
      </div>
    )
  }

  return (
    <div className="h-full flex flex-col">
      {/* Trash info banner */}
      {emails.length > 0 && (
        <div className="bg-gray-50 dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 px-4 py-3 flex items-center justify-between">
          <div className="flex items-center gap-2 text-gray-600 dark:text-gray-400">
            <Info className="w-5 h-5" />
            <span className="text-sm">
              Messages that have been in Trash more than 30 days will be automatically deleted.
            </span>
          </div>
          <button
            onClick={() => emptyTrashMutation.mutate()}
            disabled={emptyTrashMutation.isPending}
            className="flex items-center gap-2 px-3 py-1.5 bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-400 rounded hover:bg-red-200 dark:hover:bg-red-900/50 text-sm font-medium disabled:opacity-50"
          >
            <Trash2 className="w-4 h-4" />
            {emptyTrashMutation.isPending ? 'Emptying...' : 'Empty Trash'}
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
